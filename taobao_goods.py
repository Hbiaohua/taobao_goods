from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from pyquery import PyQuery as pq
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]  #指定数据库

browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
wait = WebDriverWait(browser, 10)
browser.set_window_size(1400,900)

def search():
    print('正在搜索')
    try:
        browser.get("https://www.taobao.com/")
        input = wait.until(
                EC.presence_of_element_located((By.ID, "q"))     #判断(输入框)是否加载成功
            )
        submit = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#J_TSearchForm > div.search-button > button"))
            )                                                 #判断按钮的加载条件（可点击）
        input.send_keys(KEYWORD)                              #输入框传入关键字（美食）
        submit.click()                                        #点击输入框按钮
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total'))  #判断是否加载出页码
        )
        get_goods()                                        #调用获取商品信息函数，那得到商品信息
        return total.text                                    #返回网页总页数
    except TimeoutError:
        return search()                                      #超时异常，无法得到目标，再一次请求

#获取下一页
def next_page(page_number):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
        )                                                     #判断输入（页码框）是否加载成功
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit"))
        )                                                      #判断确定按钮的加载条件（可点击）
        input.clear()                                          #清除输入框内容
        input.send_keys(page_number)                           #传入当前页码
        submit.click()                                         #点击确认按钮
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number))
        )                                                     #判断当前页面是否等于传入的页码
        get_goods()                                         #调用商品函数，得到翻页商品信息
    except:
        return next_page(page_number)

#解析得到商品信息
def get_goods():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))  #判断商品信息是否加载成功
    html = browser.page_source
    doc = pq(html)                                            #pyquery解析网页
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        goods = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[0:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(goods)
        save_to_mongo(goods)                                #保存信息至mongodb

def save_to_mongo(goods):
    try:
        if db[MONGO_TABLE].insert(goods):
            print('存储到MONGO成功',goods)
    except Exception:
        print('存储到MONGO失败',goods)

def main():
    try:
        total = search()
        total = int(re.compile('(\d+)').search(total).group(1))  #提取页码数字
        for i in range(2,total+1):                               #循环全部页码
            next_page(i)
    except:
        print('出现错误')
    finally:
        browser.close()

if __name__=='__main__':
    main()