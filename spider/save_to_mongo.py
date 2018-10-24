#导入pymongo
import pymongo


#设置Mongodb数据库的基本参数，主机，端口，数据库，集合
MONGO_HOST='localhost'
MONGO_PORT=27017
MONGO_DB='Ziru_housing'
MONGO_COLLECTION='Shanghai_renting'

#调用pymongo链接到客户端
client=pymongo.MongoClient(host=MONGO_HOST,port=MONGO_PORT)
#连接到本地数据库
db=client[MONGO_DB]

#定义一个函数用来保存数据
def save(data):
    #为了使程序的健壮性更好，可以把它放到try，except中
    try:
        #此处向集合中插入文档数据，有值代表不为空
        if db[MONGO_COLLECTION].insert(data):
            print('存储到MongoDB成功')
    except Exception:
        print('存储到MogoDB失败')