#coding:utf-8
import urllib
import sys
import re
import sqlite3
import requests
import urllib2
import os
import hashlib
from os.path import join,getsize
from bs4 import BeautifulSoup

#返回bs4类型参数
def get_html(url):
    try:
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        soup = BeautifulSoup(response,'html5lib')
        return soup
    except Exception, e:
        pass

#返回app的名字
def find_name(url):
    name_list=[]
    content = get_html(url).find_all('h1','app-name')
    for item in content:
        name_list.append(item['title'])
    return name_list

#返回app的下载次数
def find_download_count(url):
    download_list=[]
    content = get_html(url).find_all('span','download-count')
    for item in content:
        download_list.append(item.string)
    return download_list

#返回详细信息的网址
def enter_detail_web(url,mainurl):
    try:
        extend_url_list=[]
        tail_url = get_html(url).find_all('a','view-detail has-border')
        for item in tail_url:
            extend_url_list.append(mainurl+item['href'])
    except Exception, e:
        pass
    return extend_url_list

#返回app的详细信息
def find_more_detail(url):
    try:
        detail_list=[]
        content = get_html(url).find_all('p','art-content')
        for item in content:
            detail_list.append(item.string)
        del detail_list[5]
        del detail_list[6:8]
        return detail_list
    except Exception, e:
        pass

#返回网页中的下载地址
def find_download_url(url):
    try:
        download_app_list=[]
        content = get_html(url).find_all('a','download_app')
        for item in content:
            download_app_list.append(item['href'])
        return download_app_list[0]
    except Exception, e:
        print '下载地址未找到'

#从给出的url中解析下载apk
def download_apk(url,mydir):
    try:
        content = get_html(url).find_all('img','Content_Icon')
        for title in content:
            name = title['title']
        download = requests.get(find_download_url(url),stream=True)
        fname = mydir+'/'+md5_encrypt(to_str(name))+".apk"
        fname = fname.encode("GBK", 'ignore')
        f = open(fname,"wb")
        f.write(download.content)
        f.close()
        print to_str(name),'下载完成'
    except Exception, e:
        pass

#判断apk状态：已下载、有更新、未完成j
def judge(app_info,name,detail_list,mydir,url):
    dic = get_download_apk_info(mydir)
    if to_str(app_info[0]) == name and apk_exist(dic,to_str(md5_encrypt(to_str(app_info[0])))): 
        if to_str(app_info[4]) == detail_list[2] and to_str(app_info[3]) == detail_list[1] and (abs(find_apksize(dic,to_str(md5_encrypt(to_str(app_info[0])))) - int(detail_list[0][9:-4])) <= 1):
            print to_str(app_info[0]),"已下载"
        elif to_str(app_info[4]) != detail_list[2] and to_str(app_info[3]) != detail_list[1]:
            print to_str(app_info[0]),"有更新"
        elif to_str(app_info[4]) == detail_list[2] and to_str(app_info[3]) == detail_list[1] and (abs(find_apksize(dic,to_str(md5_encrypt(to_str(app_info[0])))) - int(detail_list[0][9:-4])) > 1):
            print to_str(app_info[0]),"未下载完成，继续下载中"
            download_apk(url,mydir)
        else:
            print "Error"

#爬虫入口
def crew(end_page,mainurl,mydir):
    num = [0,0]
    for item in range(1,end_page+1):
        page = item  
        url = "http://www.appchina.com/category/30/1_1_"+str(page)+"_1_0_0_0.html"
        num = get_simple_info(url,num[0],num[1],mainurl,mydir)

#进入目录页面得到基础数据
def get_simple_info(url,start_num,fail_num,mainurl,mydir):
    num = [start_num, fail_num]
    name = find_name(url)
    download_count = find_download_count(url)
    extent_url = enter_detail_web(url,mainurl)
    length = len(name)
    download_url = enter_detail_web(url,mainurl)
    return main_crew(length,name,download_count,extent_url,download_url,num,mydir)

#进入app单独页面，得到详细信息并下载
def main_crew(length,name,download_count,extent_url,download_url,num,mydir):
    for item in range(length):
        num[0] = num[0] + 1
        try:
            app_info = []
            detail_list = []
            for detail in find_more_detail(extent_url[item]):
                detail_list.append(to_str(detail))
            app_info = select_db(to_str(name[item]))
            if len(app_info) != 0:
                judge(app_info,to_str(name[item]),detail_list,mydir,download_url[item])
            else:
                print to_str(name[item]),"未下载,正在下载中......"
                insert_into_db(to_str(name[item]),to_str(download_count[item]),detail_list[0],detail_list[1],detail_list[2],detail_list[3],detail_list[4],detail_list[5])
                download_apk(to_str(download_url[item]),mydir)
                print "------共有",str(num[0]),"个软件------","下载成功",str(num[0] - num[1]),"个软件------","下载失败",str(num[1]),"个软件------"
        except Exception, e:
            num[1] = num[1] + 1
            print name[num[0]%30-1],"未找到更多信息"
    return num

#创建数据库
def creat_db():
    try:
        db = sqlite3.connect("apk.db")
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS PACKET")
        sql = """CREATE TABLE APK(
                    Name CHAR(20),
                    Download CHAR(20),
                    Size CHAR(20),
                    Updatetime CHAR(20),
                    Edition CHAR(20),
                    Mode CHAR(20),
                    Category CHAR(20),
                    Require CHAR(20))"""
        cursor.execute(sql)
        db.commit()
    except Exception, e:
        pass

#将数据存放入数据库中
def insert_into_db(name,download_count,size,updatetime,edition,mode,category,require):
    db = sqlite3.connect("apk.db")
    cursor = db.cursor()
    sql = """INSERT INTO APK(Name,Download,Size,Updatetime,Edition,Mode,Category,Require)
                            VALUES("%s","%s","%s","%s","%s","%s","%s","%s")"""
    cursor.execute(sql%(name,download_count,size,updatetime,edition,mode,category,require))
    db.commit()    
    db.close()

#从数据库中查找数据
def select_db(name):
    db = sqlite3.connect("apk.db")
    cursor = db.cursor()
    apk_info = []
    sql = """SELECT Name,Download,Size,Updatetime,Edition,Mode,Category,Require FROM APK
                where Name = '%s' """
    info = cursor.execute(sql%(name))
    for item in info:
        for elem in range(0,8):
            apk_info.append(item[elem])
    db.commit()    
    db.close()
    return apk_info

#将未编码的Unicode类型转变为str
def to_str(uncode):
    return uncode.encode('utf-8')

#进行md5加密
def md5_encrypt(name):
    m = hashlib.md5()
    m.update(name)
    return m.hexdigest()

#返回本地对应名字的apk的大小
def find_apksize(dic,name):
    for item in dic:
        if item == name:
            return dic[item]

#判断apk名字是否在本地存在
def apk_exist(dic,name):
    for item in dic:
        if item == name:
            return True
    return False

#获取下载目录中所有apk的大小
def getfilesize(dirs):
    file_size_list = [] 
    size = 0L
    for root, dirs, files in os.walk(dirs):
        for name in files:
            file_size_list.append(getsize(join(root,name))/1024/1000)
    return file_size_list

#获取下载目录中的所有apk加密后的名字
def getfilename(dirs):
    file_name_list = []
    f_list = os.listdir(dirs)
    for i in f_list:
        if os.path.splitext(i)[1] == '.apk':
            file_name_list.append(i)
    return file_name_list 

#获取已下载apk的文件名和大小，放入字典中
def get_download_apk_info(dirs):
    dic = {}
    num = 0
    file_size_list = getfilesize(dirs)
    file_name_list = getfilename(dirs)
    real_name_list = []
    for item in file_name_list:
        real_name_list.append(item[0:-4])
    for item in real_name_list:
        dic[real_name_list[num]]=file_size_list[num]
        num += 1
    return dic

#主函数
if __name__ == '__main__':
    mydir = 'download'
    mainurl = "http://www.appchina.com"
    url = "http://www.appchina.com/category/30/1_1_1_1_0_0_0.html"

    if (not os.path.exists(mydir)):
        os.makedirs(mydir)

    if len(sys.argv) == 1:
        end_page = 1
    else:
        end_page = int(sys.argv[1])

    creat_db()
    crew(end_page,mainurl,mydir)
