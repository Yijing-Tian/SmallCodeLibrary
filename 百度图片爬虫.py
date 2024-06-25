# -*- coding:utf8 -*-
import requests
import json
from urllib import parse
import os
import time

class BaiduImageSpider(object):
    def __init__(self):
        self.json_count = 0  # 请求到的json文件数量（一个json文件包含30个图像文件）
        self.url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&logid=5179920884740494226&ipn=rj&ct' \
                   '=201326592&is=&fp=result&queryWord={' \
                   '}&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=0&hd=&latest=&copyright=&word={' \
                   '}&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&nojc=&pn={' \
                   '}&rn=30&gsm=1e&1635054081427= '
        
        self.directory = "./帅哥/{}"  # 存储目录  这里需要修改为自己希望保存的目录  {}不要丢
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30 '
        }

    # 创建存储文件夹
    def create_directory(self, name):
        self.directory = self.directory.format(name)
        # 如果目录不存在则创建
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.directory += r'\{}'

    # 获取图像链接
    def get_image_link(self, url):
        list_image_link = []
        strhtml = requests.get(url, headers=self.header)  # Get方式获取网页数据
        jsonInfo = json.loads(strhtml.text)
        for index in range(30):
            list_image_link.append(jsonInfo['data'][index]['thumbURL'])
        return list_image_link

    # 下载图片
    def save_image(self, img_link, filename):
        res = requests.get(img_link, headers=self.header)
        if res.status_code == 404:
            print(f"图片{img_link}下载出错------->")
        with open(filename, "wb") as f:
            f.write(res.content)
            print("存储路径：" + filename)

    def create_folder_if_not_exists(self,folder_path):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Folder '{folder_path}' created successfully.")
        else:
            print(f"Folder '{folder_path}' already exists.")

    # 入口函数
    def run(self,searchName):
        # searchName = input("查询内容：")
        searchName_parse = parse.quote(searchName)  # 编码

        self.create_directory(searchName)

        pic_number = 0  # 图像数量
        for index in range(self.json_count):
            pn = (index+1)*30
            request_url = self.url.format(searchName_parse, searchName_parse, str(pn))
            list_image_link = self.get_image_link(request_url)
            for link in list_image_link:
                pic_number += 1
                self.save_image(link, self.directory.format(str(pic_number)+'.jpg'))
                time.sleep(0.2)  # 休眠0.2秒，防止封ip
        print(searchName+"----图像下载完成--------->")

if __name__ == '__main__':
    # name_list = ['陈伟霆','于海','黄子韬','张艺兴','鹿晗','乔振宇','易烊千玺','刘德华','周杰伦','张译','肖战','张鲁一','易烊千玺','刘德华','周杰伦','张译','肖战','张鲁一','杨洋','李易峰','霍建华','王俊凯','胡歌','张国荣','王凯','靳东','李现','王源','王鹤棣','周星驰','王凯','靳东','李现','王源','王鹤棣','周星驰','吴京','蔡徐坤','成龙','乔任梁','王一博','任嘉伦','李晨','于和伟','樊治欣','张若昀','李连杰','熊泽波','李晨','于和伟','樊治欣','张若昀','李连杰','熊泽波','黄景瑜','黄晓明','吴磊','钟汉良','张翰','邓超','张杰','陈赫','刘恺威','王传君','成毅','陈晓','张杰','陈赫','刘恺威','王传君','成毅','陈晓','邓超','李连杰','白敬亭','郑恺','林一','吴奇隆','熊泽波','陈赫','刘恺威','华晨宇','邓伦','丞磊']
    name_list = ['日出风景头像高清']
    for name in name_list:
        spider = BaiduImageSpider()
        spider.json_count = 50   # 定义下载10组图像，也就是三百张
        spider.run(name)


