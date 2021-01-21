# -*- coding: utf-8 -*-
# @Time    : 2021/1/19 14:54
# @Author  : Haijun


import requests
import time
from requests_toolbelt.multipart.encoder import MultipartEncoder
from google_search.utils.config import DatabaseConnection
from dynaconf import settings
from google_search.utils.logger import logger


def sbi_via_upload_image(file_path: str) -> None:
    """
    上传本地图片获取sbi
    :param file_path: 图片路径
    :return:
    """
    # 目标url
    upload_url = settings.BASE_URL + 'searchbyimage/upload'
    # 打开图片
    fp = open(file_path, 'rb')
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36'
    m = MultipartEncoder(
        {'encoded_image': (fp.name, fp, 'image/jpeg'), 'image_url': None, 'image_content': None, 'filename': None,
         'btnG': None})
    # 此处需要禁止跳转
    r = requests.post(upload_url, data=m,
                      headers={'Content-Type': m.content_type, 'User-Agent': user_agent}, allow_redirects=False)
    if r.status_code == 302:
        url_with_sbi = r.headers.get('Location')
        logger.info(f"上传本地土地图片获取sbi,存入链接{url_with_sbi}")
    else:
        # 失败后重新获取
        time.sleep(4)
        sbi_via_upload_image(file_path)



if __name__ == '__main__':
    sbi_via_upload_image('C:\\Users\\haiju\\Desktop\\女装-out.jpg')
