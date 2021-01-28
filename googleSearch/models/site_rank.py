# -*- coding: utf-8 -*-
# @Time    : 2020/12/30 17:25
# @Author  : Haijun
import json
import re
import aiohttp
import asyncio
from spiders_utils.proxy import proxy

import requests


class SiteRank(object):
    def __init__(self):
        self.token_url = 'http://www.alexa.cn/rank/'
        self.api = 'http://www.alexa.cn/api/alexa/free'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'
        }
        self.proxy = proxy('HQ86512757H93UVD', '711B84DE972CA59A')

    async def get_token(self, site):
        """
        获取token
        :param site:
        :return:
        """
        token_url = self.token_url + site
        try:
            async with aiohttp.TCPConnector(limit=5, verify_ssl=False) as self.tc:
                async with aiohttp.ClientSession(connector=self.tc) as self.session:
                    async with self.session.get(url=token_url, headers=self.headers, timeout=15,proxy=self.proxy['https']) as req:
                        res_text = await req.text()
        except Exception as e:
            async with self.session.get(url=token_url, headers=self.headers, timeout=15) as req:
                res_text = await req.text()
        token = re.search(r"token : '(.*?)'", res_text).group(1)
        return token

    async def parse(self, site):
        """
        获取排名
        :param site:
        :return:
        """
        site = site.replace('https://', '').replace('http://', '').replace('www.', '').replace('/', '')
        api_url = self.api + f'?token={await self.get_token(site)}&url={site}'
        try:
            async with aiohttp.TCPConnector(limit=5, verify_ssl=False) as self.tc:
                async with aiohttp.ClientSession(connector=self.tc) as self.session:
                    async with self.session.get(url=api_url, headers=self.headers,proxy=self.proxy['https']) as req:
                        res_dict = json.loads(await req.text())
        except Exception as e:
            async with self.session.get(url=api_url, headers=self.headers) as req:
                res_dict = json.loads(await req.text())
        if res_dict.get('status', None) == 0:
            data = res_dict.get('data', '')
            world_rank = data.get('world_rank')
            return world_rank
        return None


if __name__ == '__main__':
    """
        {
        "domain": "baidu.com",
        "world_rank": "4",
        "world_uv_rank": "5",
        "world_delta": "0",
        "country_rank": "2",
        "country_code": "CN",
        "update_time": "1609344676",
        "expire_time": "1609430400",
        "icp_area": "京",
        "flag": "public/flag/CN.png"
        }
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(SiteRank().parse('https://www.baidu.com'))
