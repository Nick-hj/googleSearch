# -*- coding: utf-8 -*-
# @Time    : 2021/1/19 17:23
# @Author  : Haijun

import requests
import random
from typing import Dict
from google_search.utils.logger import logger
from dynaconf import settings
from google_search.parsers.google import GoogleParser


class SearchGoogle(object):
    """
    Google搜索列表
    """

    def __init__(self, init_data: Dict[any]):
        self.init_data = init_data
        self.user_agent = random.choice(settings.USER_AGEN)

    def _parse_action(self):
        url = self.init_data.get('url')
        headers = {
            'user-agent': self.user_agent
        }
        response = requests.get(url=url, headers=headers, verify=False)
        logger.info(response.status_code)
        res_text = response.text
        GoogleParser(res_text).parse_actions()
