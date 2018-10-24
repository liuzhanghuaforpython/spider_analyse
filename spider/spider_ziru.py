#导入这个模块
import save_to_mongo
import time
#这个库是为了识别图片数字
import pytesseract
#需要tesseract-ocr的支持，需要下载tesseract-ocr，将路径指定，下面是我保存的地址路径
pytesseract.pytesseract.tesseract_cmd = 'D:\\Tesseract-OCR\\tesseract.exe'
#这个库主要是用于打开图片，配合tesseract结合使用
from PIL import Image
import re
import requests

#这个是为了重试的时候设置延迟
from retrying import retry
from lxml import etree

#这个是为了显示下载进度
from tqdm import tqdm

# 接入selenium
#该方法是封装好的headless，直接拿来调用browser即可，老师也讲过
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# -----浏览器初始化
print('正在初始化无界面Chrome浏览器...')
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')  # 解决DevToolsActivePort文件不存在的报错
chrome_options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
chrome_options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
chrome_options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
# 添加代理 proxy
# chrome_options.add_argument('--proxy-server=http://' + proxy)
browser = webdriver.Chrome(chrome_options=chrome_options)
print('浏览器初始化完毕')
print('-' * 20)

#每次重试的时候都会等待2秒，单位为毫秒
@retry(wait_fixed=2000)
#定义一个得到该区的总页数的函数
def get_page_num(url):
    #模拟请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/47.0.2526.108 Safari/537.36 2345Explorer/8.8.0.16453 '
    }
    #用request.get方法获得响应
    response=requests.get(url=url,headers=headers)
    #获取响应的内容
    content=response.text
    #用etree解析网页
    data=etree.HTML(content)
    #这里使用try，except是因为前面几个区的“共*页”是在span2中，后几个区的是在span1中
    try:
        #用xpath获取共多少页，比如徐汇，这里pages就是“共17页”
        pages=data.xpath('//div[@id="page"]/span[2]/text()')[0]
        #用正则的search方法去匹配共多少页，group方法得到匹配的数据
        #比如 共17 页 就是得到17，共20页就匹配 20
        final_page=re.search(r"\d+",pages).group()
        #返回页数
        return final_page
    except Exception:
        pages=data.xpath('//div[@id="page"]/span[1]/text()')[0]
        final_page=re.search(r"\d+",pages).group()
        return final_page

#定义方法得到请求的页面
def get_page(raw_url,page):
    """
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/47.0.2526.108 Safari/537.36 2345Explorer/8.8.0.16453 '
        }
        """
    print('正在爬取第'+str(page)+'页')
    #每一页的url地址拼接
    url=raw_url +'?p='+str(page)
    #在这里页面是js动态加载，requests获取不到我们想要的数据
    #response=requests.get(url=url,headers=headers)
    #调用上面selenium+headless得到的浏览器对象去获取页面
    browser.get(url)
    #休眠一秒
    time.sleep(1)
    #调用page_source获得真实数据
    response=browser.page_source
    #返回结果
    return response

#定义一个方法去得到图片中的数字列表
def get_image_number(html):
    #找到js加载的动态图片<script>里面，用正则去匹配图片url
    photo=re.findall('var ROOM_PRICE = {"image":"(//.*?.png)"', html)[0]
    #由于图片url路径不完整，所以请求加上http:   图片是字节码数据，调用content，而不是text
    image=requests.get("http:"+photo).content
    #将查询的图片保存到本地
    f=open('price.png','wb')
    f.write(image)
    f.close()
    #定义一个空列表
    num=[]
    #应用机器学习的库去识别图片的数字，由于图片数字是0-9组成，config配置数字即可
    number=pytesseract.image_to_string(Image.open('price.png'),config='-psm 8 -c tessedit_char_whitelist=1234567890')
    #遍历图片上的每一个数字，添加到列表中
    for i in number:
        num.append(i)
    #返回该列表
    return num

#每次重试的时候都会等待2秒，单位为毫秒
@retry(wait_fixed=2000)
#定义一个方法去解析页面
def parse_page(html, district_name, num_list):
    tree=etree.HTML(html)
    #用xpath找到每一个li列表
    li_list=tree.xpath('//ul[@id="houseList"]/li[@class="clearfix"]')
    #遍历每一个li
    for li in li_list:
        #定义一个空列表，用来接收style的偏移量，就是下面房价映射字典的多少px这个数字，30的倍数
        temp_list=[]
        #定义一个空列表，用来接收价格
        price_list=[]
        #找到房租信息标题列表
        title_list=li.xpath('./div[2]/h3/a/text()')
        #print(title_list)
        #无空格去拼接
        title=''.join(title_list)
        #print(title)
        #从标题中匹配房租类型如“整租”  整租 · 东安二村1居室-南   一个.匹配一个汉字， .是匹配除换行外所有的
        house_type=re.search(r"^..",title).group()
        #print(house_type)
        area_list=li.xpath('./div[2]/div/p[1]/span/text()')
        #匹配区域大小  如 36.37 ㎡| 03/4层| 1室1厅
        area=''.join(area_list)
        #print(area)
        metro_list=li.xpath('./div[2]/div/p[2]/span/text()')
        #匹配离地铁远近 如 距7号线东安路站直线188米
        metro=''.join(metro_list)
        #print(metro)
        #---------price是重点
        #position()>1代表位置大于1的span
        prices = li.xpath('./div[3]/p[1]/span[position()>1]/@style')
        #item   background-position:-210px这种类型的数据
        for item in prices:
            temp_list.append(item.replace("background-position:-", "").replace("px", ""))
        #print(temp_list)
        for number in temp_list:
            #每一个数据对应的值是30的倍数，并且是作为索引找到对应的价格
            price=num_list[int(int(number)/30)]
            #print(price)
            price_list.append(price)
        #print(price_list)
        #获取到最终价格
        final_price=''.join(price_list)
        print("="*40)
        info={
            'type':house_type,
            'title':title,
            'area':area,
            'metro':metro,
            'price':final_price,
            'district':district_name
        }
        print(info)
        #将数据转化为字典保存到mongodb数据库中
        save_to_mongo.save(info)
    time.sleep(1)


"""
# 房价映射字典
price_dict = {
    'background-position:-210px': '9',
    'background-position:-0px': '4',
    'background-position:-240px': '7',
    'background-position:-90px': '5',
    'background-position:-60px': '3',
    'background-position:-120px': '1',
    'background-position:-270px': '6',
    'background-position:-30px': '0',
    'background-position:-180px': '2',
    'background-position:-150px': '8',
}
"""


if __name__ == '__main__':
    #这里i是为了方便后面计数
    i=0
    print('正在初始化地区模块...')
    #这里将ziru_district模块导入进来
    import ziru_district
    #然后这个模块的districts方法返回的一个元组，索引为0的是url的列表
    url_items=ziru_district.districts()[0]
    #索引为1的是区域名称的列表
    name_items=ziru_district.districts()[1]
    print('地区模块初始化完毕')
    print('-'*20)
    #休眠1秒
    time.sleep(1)
    #--------------------
    #对每个区的url列表进行遍历
    for url_item in url_items:
        #得到每个区的url
        url=url_item
        #然后定义一个方法去得到这个区需要爬取的页数是多少
        end=get_page_num(url)
        print('...')
        print('正在爬取 {name} 的房源'.format(name=name_items[i]))
        print('共有',end,'页')
        #遍历每个区域的每一页
        for page in tqdm(range(1,int(end)+1)):
            #调用该方法得到每个区每一页的页面数据
            html=get_page(url,page)
            #调用该方法得到图片的数字列表
            num_list=get_image_number(html)
            print(num_list)
            #调用函数解析页面
            parse_page(html,name_items[i],num_list)
        i = i + 1