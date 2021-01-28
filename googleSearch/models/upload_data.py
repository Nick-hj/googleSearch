# -*- coding: utf-8 -*-
# @Time    : 2021/1/28 17:34
# @Author  : Haijun


import os
import random
import ssl
import requests
from urllib.request import Request
from urllib import request
import urllib.request
import urllib.parse
from http.cookiejar import LWPCookieJar
from dynaconf import settings
from googleSearch.utils.logger import logger
from requests_toolbelt.multipart.encoder import MultipartEncoder


home_folder = os.getenv('HOME')
if not home_folder:
    home_folder = os.getenv('USERHOME')
    if not home_folder:
        home_folder = '.'  # Use the current folder on error.
cookie_jar = LWPCookieJar(os.path.join(home_folder, '.google-cookie'))
try:
    cookie_jar.load()
except Exception:
    pass

class NoRedirHandler(request.HTTPRedirectHandler):
    # 禁止302跳转
    def http_error_302(self, req, fp, code, msg, headers):
        return fp

    http_error_301 = http_error_302


class UploadDataForSbi(object):
    def __init__(self):
        self.user_agent = random.choice(settings.USER_AGENT)

    def upload_image_url(self, image_url, verify_ssl=True):
        url = f'https://www.google.com/searchbyimage?image_url={image_url}&btnG=Search+by+image&encoded_image=&image_content=&filename=&hl=en'
        logger.info(url)
        request = Request(url)
        """
        accept:
        accept-encoding: gzip, deflate, br
        accept-language: zh-CN,zh;q=0.9,en;q=0.8
        referer: https://www.google.com/
        """
        request.add_header('User-Agent', self.user_agent)
        # request.add_header('accept',
        #                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
        # request.add_header('accept-encoding', 'gzip, deflate, br')
        # request.add_header('accept-language', 'zh-CN,zh;q=0.9,en;q=0.8')
        # request.add_header('referer', 'https://www.google.com/')
        # request.add_header('sec-fetch-mode', 'navigate')
        # request.add_header('Host', 'www.google.com')
        cookie_jar.add_cookie_header(request)
        # if verify_ssl:
        #     response = urlopen(request)
        # else:
        #     # 在浏览器中访问该网站时会弹出证书不受信任，但是忽略仍可继续访问
        opener = urllib.request.build_opener(NoRedirHandler)
        context = ssl._create_unverified_context()
        response = opener.open(request)
        cookie_jar.extract_cookies(response, request)
        url_with_sbi = response.headers.get('Location')
        logger.info(f'通过图片链接获取sbi===={url_with_sbi}')
        response.close()
        try:
            cookie_jar.save()
        except Exception:
            logger.error('cookiejar保持失败')
            pass

    def upload_local_image(self, image_url, verify_ssl=True):
        """
                通过上传本地图片获取sbi
                :param file_path: 图片本地路径
                :return:
                """
        # 目标url
        # file_path = init_data.get('image')
        upload_url = settings.BASE_URL + '/searchbyimage/upload'
        # 打开图片
        fp = open(image_url, 'rb')
        m = MultipartEncoder(
            {'encoded_image': (fp.name, fp, 'image/jpeg'), 'image_url': None, 'image_content': None, 'filename': None,
             'btnG': None})
        # 此处需要禁止跳转
        response = requests.post(upload_url, data=m,
                                 headers={'Content-Type': m.content_type, 'User-Agent': self.user_agent},
                                 allow_redirects=False)
        if response.status_code == 302:
            url_with_sbi = response.headers.get('Location')
            logger.info(url_with_sbi)

            # init_data['url'] = url_with_sbi
            # logger.info(f"上传本地土地图片获取sbi,存入链接{url_with_sbi}")
            # # 入库redis
            # init_data['sbi_url'] = url_with_sbi
            # # TODO
        else:
            logger.info(f'获取sbi失败')
            # 失败后返回redis
            # TODO
            pass
