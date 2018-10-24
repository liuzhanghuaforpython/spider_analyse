import  requests
#使用python的第三方库requests
from lxml import etree
#使用xpath提取数据


#定义一个请求html的函数
def get_html():
    #模拟请求头
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/47.0.2526.108 Safari/537.36 2345Explorer/8.8.0.16453 '
    }
    #此url是自如整租的url，http://sh.ziroom.com/z/nl/z2.html是友家合租的url
    #爬取完此url，更换url，即可获得合租的数据
    url = 'http://sh.ziroom.com/z/nl/z1.html'
    #此请求为get请求，用request.get获取响应
    response = requests.get(url=url, headers=header)
    #response.text表示获取的网页数据，response.content表示获取的二进制数据
    return response.text


#获取网页后再定义一个解析网页的函数
def parse_html(html):
    #定义一个空的url_list列表，用于接收上海14个区的url
    url_list=[]
    # 定义一个空的name_list列表，用于接收上海14个区的名称
    name_list=[]
    #使用etree解析网页得到tree
    tree=etree.HTML(html)
    #调用xpath获取到每一个li的列表
    li_list=tree.xpath('//div[@id="selection"]/div/div/dl[2]/dd/ul/li[position()>1]')
    #遍历这个li列表
    for li in li_list:
        #得到每个区的href的列表
        href=li.xpath('./span/a/@href')
        #得到每个区的名字的列表
        name=li.xpath('./span/a/text()')
        # print(href[0].replace('//', ''))
        #因为得到的href是不完整的，缺少http: 所以需要用replace函数替换，得到完整的url
        #再添加到url_list中，使用索引是取出对象，才能调用方法
        url_list.append(href[0].replace('//', 'http://'))
        #将得到的上海14个区的名称添加到name_list中
        name_list.append(name[0])
    print(url_list)
    print(name_list)
    #就会得到['徐汇', '闵行', '浦东', '闸北', '嘉定', '松江', '普陀', '杨浦', '虹口', '长宁', '宝山', '静安', '黄浦', '青浦']
    #以及他们所对应的url地址
    return url_list,name_list

#定义一个函数用于得到网页和数据
def districts():
    #调用此函数得到html页面
    html=get_html()
    #调用此函数解析页面得到数据
    tup=parse_html(html)
    #返回的是一个元祖，元组中第一个元素是url列表，第二个元素是区域名称列表
    return tup

if __name__ == '__main__':
    #调用此函数即可运行
    districts()