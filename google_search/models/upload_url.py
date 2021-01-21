# -*- coding: utf-8 -*-
# @Time    : 2021/1/19 14:55
# @Author  : Haijun

import random
import requests
from dynaconf import settings
from google_search.utils.logger import logger

def google_sbi_via_url(image_url: str) -> bool:
    user_agent = random.choice(settings.USER_AGENT)
    url = f'{settings.BASE_URL}searchbyimage?image_url={image_url}&btnG=Search+by+image&encoded_image=&image_content=&filename=&hl=en'
    headers = {
        'User-Agent': user_agent,
        # 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        # 'accept-encoding': 'gzip, deflate, br',
        # 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        # 'referer': settings.BASE_URL,
        # 'sec-fetch-mode': 'navigate'
    }
    response = requests.get(url=url, headers=headers, verify=False,allow_redirects=False)
    if response.status_code == 302:
        fetch_url = response.headers.get('Location')
        logger.info(fetch_url)
        return True
    return False


if __name__ == '__main__':
    google_sbi_via_url(
        'https://ae01.alicdn.com/kf/H906419260898432088dfe4aeeb832491o/Mini-IP-Camera-1080P-Sensor-Night-Vision-Camcorder-Motion-DVR-Micro-Camera-Sport-DV-Video-small.jpg')
