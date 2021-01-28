# -*- coding: utf-8 -*-
# @Time    : 2021/1/28 20:15
# @Author  : Haijun

import os
import random
import ssl
import re
import asyncio
from urllib.request import Request, urlopen
from http.cookiejar import LWPCookieJar
from dynaconf import settings
from googleSearch.utils.logger import logger
from googleSearch.parsers.list_detail import CrawlDetail
from parsel import Selector

cookie_jar = LWPCookieJar(os.path.join('.', '.google-cookie'))
try:
    cookie_jar.load()
except Exception:
    pass


class ParseGoogleList(object):
    def __init__(self):
        self.retry_times = 1

    def crawl_google_data(self, init_data):
        url = init_data['search_url']
        page = init_data['page']
        user_agent = random.choice(settings.USER_AGENT)
        request = Request(url)
        request.add_header('User-Agent', user_agent)
        request.add_header('accept',
                           'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
        cookie_jar.add_cookie_header(request)
        context = ssl._create_unverified_context()
        response = urlopen(request, context=context)
        cookie_jar.extract_cookies(response, request)
        res_text = response.read().decode('utf-8')
        response.close()
        try:
            cookie_jar.save()
        except Exception:
            pass

        loop = asyncio.get_event_loop()
        task = loop.create_task(self.parse_actions(init_data, res_text, page))
        loop.run_until_complete(task)
        result = task.result()
        logger.info(result)

    async def parse_actions(self, init_data, res_text, n=0, is_retry=False):
        """
        解析
        :param init_data: 初始数据
        :param res_text: 响应文本
        :param n: 第几页
        :return:
        """
        # 解析google列表
        html = Selector(res_text)
        data_list = html.xpath('//div[@id="rso"]/div[@class="g"]')
        logger.info(f'data_list====={len(data_list)}')
        # 只有本地上传图片的情况下，才不会有title
        title = init_data['title']
        if not title:
            init_data['title'] = await self.title(html)
        if data_list:
            cur_result = await self.parse_google_list(data_list)
            logger.info(f'当前页采集结果========{cur_result}')
            init_data['detail_list'].extend(cur_result)
            return init_data
        else:
            # 如果出现请求错误的情况，需要初始数据重新入redis，重新爬取
            error_msg = await self.error_msg(init_data, data_list, n, res_text)
            if error_msg:
                if self.retry_times < 3:
                    self.retry_times += 1
                    logger.info(f'重试======url:{init_data["search_url"]}')
                    self.crawl_google_data(init_data["search_url"])
            else:
                logger.info(f'重试======url:{init_data["search_url"]}')
                self.crawl_google_data(init_data["search_url"])

        if not is_retry:
            # 下一页,如果是重试，就不取下一页
            next_page = await self.next_page(html)
            logger.info(f'下页======{next_page}')
            # 下一页入库
            if next_page:
                page_url = next_page.get('page_url')
                page = next_page.get('page')
                self.crawl_google_data(page_url)
                # TODO:入库redis
                pass

        return init_data

        # ConstantsConfig.redis_conn.lpush(GOOGLE_SEARCH_RESULT_REDIS_KEY, json.dumps(self.redis_data))

    async def next_page(self, html):
        # 当前总页数
        page_url = html.xpath('//a[@id="pnnext"]/@href').get()
        logger.info(f'next page ====={page_url}')
        if page_url:
            page_no = re.findall(r'start=(\d+)', page_url)[0]
            page_url = f'{settings.BASE_URL}{page_url}'
            page = int(page_no) / 10
            if page <= settings.TOTAL_PAGE:
                return {
                    "page_url": page_url,
                    'page': int(page)
                }
        return False

    async def parse_google_list(self, data_list) -> list:
        """
        获取列表图片和链接
        :param search_data:
        :return:
        """
        search_results = []
        for data in data_list:
            url = data.xpath("./div/div[1]/a/@href").get()
            image = data.xpath('./div/div[2]/div[1]/div/a/@href').get()
            if image:
                _image = re.search(r'/imgres\?imgurl=(.*?)\&', image)
                image = _image if _image else None
            data_dict = {
                "url": url,
                "image": image
            }
            filter_results = await self.filter_url(data_dict)
            if filter_results:
                search_results.append(filter_results)
        return search_results

    async def title(self, html) -> str:
        """
        标题，如果初始数据没有标题，就取google搜索框标题
        :param html:
        :return:
        """
        return html.xpath('//input[@title="Search"]/@value').get()

    async def filter_url(self, url):
        """
        过滤url
        :param url_list:
        :return:
        """
        # 存在黑名单
        del_url = [url for key in settings.EXCLUDE_KEY_WORD if key in url['url']]
        if not del_url:
            _type = self.init_data['type']
            # 如果采集类型为关键字，需要是落地页，如果是以图搜图，不限制
            if _type == 1:
                if '/products/' in url or '/product/' in url or '/collections/' in url:
                    return await CrawlDetail().crawl_product(url)
            elif _type == 2:
                return await CrawlDetail().crawl_product(url)
            return await CrawlDetail().crawl_product(url)
        return None

    async def error_msg(self, init_data, data_list, n, res_text):
        """
        错误回显
        :param data_list:
        :param n: 第几页
        :param res_text:
        :return:
        """
        # 异常
        if not data_list and n == 0:
            logger.error(f'解析为空===={init_data}')
            init_data['error_msg'] = f'解析为空,正在重试,请稍后查看)'
            init_data['code'] = 0
            return True
        # 搜索错误
        if 'Try different keywords' in res_text and n == 0:
            logger.error(f'第一页出现了Try different keywords===={self.init_data}')
            init_data['error_msg'] = '搜索错误,正在重试,请稍后查看)'
            init_data['code'] = 0
            return True
        elif 'The image is too big' in res_text and n == 0:
            logger.error(
                f'第一页出现了The image is too big 或者网络连接异常==={self.init_data}')
            init_data['error_msg'] = '网络连接失败,正在重试,请稍后查看'
            init_data['code'] = 0
            return True
        # 超出页码
        if 'Try different keywords' in res_text and n != 0:
            logger.error(f'第{n}页出现了Try different keywords=={self.init_data}')
            init_data['error_msg'] = '结果太少，未匹配到商品'
            init_data['code'] = 0
            return False
