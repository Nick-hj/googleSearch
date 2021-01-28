# -*- coding: utf-8 -*-
# @Time    : 2021/1/28 17:38
# @Author  : Haijun
from googleSearch.utils.settings import load_or_create_settings

load_or_create_settings('')

from googleSearch.models.upload_data import UploadDataForSbi
from googleSearch.parsers.googleList import ParseGoogleList

if __name__ == '__main__':
    data = {
        "page": 0,  # 当前页
        "type": 2,  # 搜索类型，1关键字，2以图搜图
        "title": "",
        "key_word": "",
        "search_url": 'https://www.google.com/searchbyimage?image_url=https://ae01.alicdn.com/kf/Hfff23dde0ad6417d8e3732065376003cc.jpg?width=1476&height=1920&hash=3396&btnG=Search+by+image&encoded_image=&image_content=&filename=&hl=en',
        'detail_list': []
    }
    ParseGoogleList().crawl_google_data(data.get('url'))
    # UploadDataForSbi().upload_image_url('https://ae01.alicdn.com/kf/Hfff23dde0ad6417d8e3732065376003cc.jpg?width=1476&height=1920&hash=3396')
    # UploadDataForSbi().upload_local_image('C:\\Users\\haiju\\Desktop\\kfbuy1610421141811.jpg')
