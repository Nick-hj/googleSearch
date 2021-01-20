# -*- coding: utf-8 -*-
# @Time    : 2021/1/19 14:55
# @Author  : Haijun

import random
import requests
import re
from dynaconf import settings


def google_sbi(image_url: str) -> str:
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
    response = requests.get(url=url, headers=headers, verify=False)
    if response.status_code == 302:
        fetch_url = response.headers.get('Location')
        return fetch_url


if __name__ == '__main__':
    google_sbi(
        'https://ae01.alicdn.com/kf/H906419260898432088dfe4aeeb832491o/Mini-IP-Camera-1080P-Sensor-Night-Vision-Camcorder-Motion-DVR-Micro-Camera-Sport-DV-Video-small.jpg')
