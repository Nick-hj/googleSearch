# -*- coding: utf-8 -*-
# @Time    : 2021/1/19 14:54
# @Author  : Haijun

import requests
from google_search.utils.config import DatabaseConnection
from dynaconf import settings
from google_search.utils.logger import logger

Image_path = "testing.jpg"  # Your File With PATH HERE


def sbi_via_upload_image(file_path: str) -> str:
    """
    上传本地图片获取sbi
    :param file_path: 图片路径
    :return:
    """
    upload_url = settings.BASE_URL + 'searchbyimage/upload'
    multi_part = {
        'encoded_image': (file_path, open(file_path, 'rb')),
        'image_content': ''
    }
    response = requests.post(upload_url, files=multi_part, allow_redirects=False)
    if response.status_code == 302:
        fetch_url = response.headers.get('Location')
        logger.info(f"上传本地土地图片获取sbi,存入链接{fetch_url}")
        return fetch_url
    return ''


if __name__ == '__main__':
    sbi_via_upload_image('C:\\Users\\haiju\\Desktop\\女装-out.jpg')
