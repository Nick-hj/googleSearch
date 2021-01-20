# -*- coding: utf-8 -*-
# @Time    : 2020/12/2 12:02
# @Author  : ''
# google 以图搜图
import os
import sys
import os
import random
import time
import ssl
import threading
import requests
import json
import re
import iso8601
from urllib.request import Request, urlopen
from urllib.error import URLError
from retrying import retry
from http.cookiejar import LWPCookieJar
from parsel import Selector

ssl._create_default_https_context = ssl._create_unverified_context
sys.path.append(os.getcwd())

from crawl_conf import EXCLUDE_KEY_WORD, SOURCE_KEY_WORD, \
    GOOGLE_SEARCH_RESULT_REDIS_KEY, DOMAIN, USER_AGENT, ConstantsConfig, logger, email_exists
from site_rank import SiteRank

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


def delete_repeat(old_list):
    """
    列表里嵌套字典按起重一个value去重
    :param old_list:
    :return:
    """
    new_list = []
    new_list.append(old_list[0])
    for dict in old_list:
        k = 0
        for item in new_list:
            # print 'item'
            if dict['host'] != item['host']:
                k = k + 1
                # continue
            else:
                break
            if k == len(new_list):
                new_list.append(dict)
    return new_list


def proxies():
    proxy_host = "proxy.crawlera.com"
    proxy_port = "8010"
    proxy_auth = "78cd6d363f6044bf9fd8747e967408bd:"  # Make sure to include ':' at the end
    proxies = {
        "https": "https://{}@{}:{}/".format(proxy_auth, proxy_host, proxy_port),
        "http": "http://{}@{}:{}/".format(proxy_auth, proxy_host, proxy_port)
    }
    return proxies


def retry_if_error(exception):
    """
    重试异常条件
    :param exception:
    :return:
    """
    logger.info(f'url解析错误，重试')
    return isinstance(exception, URLError)


def retry_if_result_empty(result):
    """
    重试条件，如果返货空就重试
    :param self:
    :param result:
    :return:
    """
    return len(result) == 0


class GoogleSearchByImage(object):
    def __init__(self):
        self.redis_data = dict()
        self.crawl_data = list()
        self.f_num = 1
        self.retry_sbi = True
        self.is_success_code = None
        self.is_success_message = None

    @logger.catch()
    def get_redis_data(self, data):
        """
        需要搜索的redis原数据
        data = {
            'url': goods_url,  # 本网址商品链接
            'title': title,
            'image': main_image,
            'product_id': product_id,
            "product_url": link,
            'orders': orders,
            'third_orders': likes,
            'source': 2,
            'user': 0  # 默认值
        }
        :return:
        """
        image = data.get('image')
        self.redis_data = data
        self.google_sbi(image)

    @logger.catch()
    @retry(stop_max_attempt_number=5, stop_max_delay=3000, wait_fixed=3000)
    def google_sbi(self, image_url, verify_ssl=True):
        user_agent = random.choice(USER_AGENT)
        url = f'https://www.google.com/searchbyimage?image_url={image_url}&btnG=Search+by+image&encoded_image=&image_content=&filename=&hl=en'
        request = Request(url)
        """
        accept: 
        accept-encoding: gzip, deflate, br
        accept-language: zh-CN,zh;q=0.9,en;q=0.8
        referer: https://www.google.com/
        """
        request.add_header('User-Agent', user_agent)
        request.add_header('accept',
                           'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
        request.add_header('accept-encoding', 'gzip, deflate, br')
        request.add_header('accept-language', 'zh-CN,zh;q=0.9,en;q=0.8')
        request.add_header('referer', 'https://www.google.com/')
        request.add_header('sec-fetch-mode', 'navigate')
        request.add_header('Host', 'www.google.com')
        cookie_jar.add_cookie_header(request)
        # if verify_ssl:
        #     response = urlopen(request)
        # else:
        #     # 在浏览器中访问该网站时会弹出证书不受信任，但是忽略仍可继续访问

        context = ssl._create_unverified_context()
        response = urlopen(request, context=context)
        cookie_jar.extract_cookies(response, request)
        res_url = response.url
        _sbi = re.findall(r'tbs=sbi:(.*?)&', res_url)
        sbi = _sbi[0] if len(_sbi) > 0 else ''
        self.url_via_google(sbi)
        response.close()
        try:
            cookie_jar.save()
        except Exception:
            logger.error('cookiejar保持失败')
            pass

    @logger.catch()
    def url_via_google(self, sbi):
        """
        获取google 列表链接
        :param sbi:
        :param n: 分页
        :return: False
        """
        # domain = random.choice(DOMAIN)  # 随机google子域名
        for n in range(0, 11):
            time.sleep(random.randint(3, 6))
            logger.info(f'睡眠3-6秒')
            path = f'/search?tbs=sbi:{sbi}&btnG=Search%20by%20image&hl=en-US&start={10 * n}'
            url = f'https://www.google.com{path}'
            logger.info(f'搜索链接==========={url}')
            try:
                res_data = self.crawl_google_data(url, n)
                if res_data:
                    self.filter_url(res_data)
                else:
                    logger.error(f'爬取失败，结束,跳出循环====image:{self.redis_data.get("image",None)}======url: {url}')
                    break
            except AssertionError as e:
                logger.info(f'{e.args},跳出循环')
                break
            except Exception as e:
                logger.error(f'出错了,跳出本次循环url:=======image:{self.redis_data.get("image",None)}====={url}=========原因：{e}')
                continue
        logger.info(f'爬取结果================{self.crawl_data}')
        self.redis_data['detail_list'] = self.crawl_data
        # code 成功1，失败0
        if self.redis_data['detail_list']:
            self.redis_data['code'] = 1
        elif not self.redis_data['detail_list'] and self.is_success_code == -1:
            self.redis_data['code'] = 0
            self.redis_data['error_msg'] = self.is_success_message
        else:
            self.redis_data['code'] = 0
            self.redis_data['error_msg'] = '未匹配到有效商品'
        logger.info(f'爬取结果入redis================{self.redis_data}')
        ConstantsConfig.redis_conn.lpush(GOOGLE_SEARCH_RESULT_REDIS_KEY, json.dumps(self.redis_data))

    @retry(stop_max_attempt_number=5, stop_max_delay=3000, wait_fixed=3000)
    @logger.catch()
    def crawl_google_data(self, url, n):
        user_agent = random.choice(USER_AGENT)
        request = Request(url)
        request.add_header('User-Agent', user_agent)
        request.add_header('accept',
                           'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
        # request.add_header('accept-encoding', 'gzip, deflate, br')
        # request.add_header('accept-language', 'zh-CN,zh;q=0.9,en;q=0.8')
        # request.add_header('referer', 'https://www.google.com/')
        # request.add_header('sec-fetch-mode', 'navigate')
        # request.add_header('Host', 'www.google.com')
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
        html = Selector(text=res_text)
        if not self.redis_data.get('title', ''):
            self.redis_data['title'] = html.xpath('//input[@title="Search"]/@value').get()
        url_images = html.xpath('//div[@id="rso"]/div[@class="g"]')
        if not url_images and n == 0:
            logger.error(f'解析为空====rul:{url}=====image: {self.redis_data.get("image",None)}')
            self.is_success_code = -1
            self.is_success_message = '解析为空,请重试)'
            return False
        # 搜索错误
        if 'Try different keywords' in res_text and n == 0:
            logger.error(f'第一页出现了Try different keywords====rul:{url}=====image: {self.redis_data.get("image",None)}')
            self.is_success_code = -1
            self.is_success_message = 'Try different keywords,搜索错误，请重试(上传本地图片或图片连接)'
            return False
        elif 'The image is too big' in res_text and n == 0:
            logger.error(f'第一页出现了The image is too big 或者网络连接异常===rul:{url}=====image: {self.redis_data.get("image",None)}')
            self.is_success_code = -1
            self.is_success_message = '网络连接失败，请重试(上传本地图片或图片连接)'
        elif 'Try different keywords' in res_text and n != 0:
            logger.error(f'第{n}页出现了Try different keywords==rul:{url}=====image: {self.redis_data.get("image",None)}')
            self.is_success_code = -1
            self.is_success_message = '结果太少，未匹配到商品'
            return False

        url_image_list = self.parse_google_data(url_images)
        return url_image_list

    def parse_google_data(self, url_images):
        url_image_list = []
        for url_image in url_images:
            url = url_image.xpath("./div/div[1]/a/@href").get()
            _image = url_image.xpath('./div/div[2]/div[1]/div/a/@href').get()
            if _image:
                image = re.search(r'/imgres\?imgurl=(.*?)\&', _image).group(1)
                url_image_dict = {
                    "url": url,
                    "image": image
                }
                url_image_list.append(url_image_dict)
        return url_image_list

    def filter_url(self, url_list):
        """
        过滤url
        :param url_list:
        :return:
        """
        # 过滤关键字
        del_url = [url for url in url_list for key in EXCLUDE_KEY_WORD if key in url['url']]
        # # 去重
        # del_url = deleteDuplicate(_del_url)
        # 删除重复的
        expected_url = [json.loads(k) for k in
                        list(set([json.dumps(j) for j in url_list]) - set([json.dumps(i) for i in del_url]))]
        self.product_callback(expected_url)

    def product_callback(self, expected_url):
        """
        多线程爬取
        :param expected_url:
        :return:
        """
        if expected_url:
            try:
                self.thread_crawl(expected_url)
            except Exception as e:
                logger.error(f'爬取商品失败，url:{expected_url}')
                pass
            # for url in expected_url:
            #     self.crawl_product(url)

    @logger.catch()
    @retry(stop_max_attempt_number=2, stop_max_delay=3000, wait_fixed=3000)
    def crawl_product(self, url, image):
        """
        获取最终的产品链接和店铺链接
        :param url:
        :return:
        """
        # try:
        #     host = re.findall(r'https://(.*?/)', url)[0]
        # except IndexError as e:
        #     host = re.findall(r'http://(.*?/)', url)[0]
        # headers = spider_header(host)
        user_agent = random.choice(USER_AGENT)
        headers = {
            'user-agent': user_agent,
            'referer': 'https://www.google.com/'
        }
        try:
            logger.info(f'开始爬取详情数据url==============={url}')
            response = requests.get(url=url, headers=headers, verify=False, timeout=15)
            res_text = response.text
            res_url = response.url
            domain = re.findall(r'(.*?://.*?/)', res_url)[0]
            # 匹配商品上架时间
            _published_time = list()
            if 'Shopify.shop' in res_text or 'Shopify.theme' in res_text or \
                    'Shopify.cdnHost' in res_text or 'Powered by Shopify' in res_text:
                if 'published_at":"' in res_text:
                    p_at = re.findall(r'published_at":"(.*?)"', res_text)
                    _published_time.extend(p_at)
                # elif 'created_at":"' in res_text:
                #     p_at = re.findall(r'created_at":"(.*?)"', res_text)
                #     _published_time.extend(p_at)
                elif 'created_at&quot;:&quot;' in res_text:
                    p_at = re.findall(r'created_at&quot;:&quot;(.*?)&quot', res_text)
                    _published_time.extend(p_at)
                elif '"datePublished":"' in res_text:
                    p_at = re.findall(r'datePublished":"(.*?)"', res_text)
                    _published_time.extend(p_at)
                published_time = self.create_time(_published_time)
                self.source_filter_key(res_text, domain, image, res_url, 'shopify', published_time)
            elif 'content="WooCommerce' in res_text or 'woocommerce_params' in res_text or \
                    'woocommerce-product-gallery' in res_text:
                if 'datePublished":"' in res_text:
                    p_at = re.findall(r'datePublished":"(.*?)"', res_text)
                    _published_time.extend(p_at)
                if 'modified_time" content="' in res_text:
                    p_at = re.findall(r'modified_time" content="(.*?)"', res_text)
                    _published_time.extend(p_at)
                if '"dateModified":"' in res_text:
                    p_at = re.findall(r'"dateModified":"(.*?)"', res_text)
                    _published_time.extend(p_at)
                published_time = self.create_time(_published_time)
                self.source_filter_key(res_text, domain, image, res_url, 'woocommerce', published_time)
        except Exception as e:
            logger.error(f'爬取详情数据失败==============={url}===={e}')
            pass

    def create_time(self, p_time):
        published_time = None
        if p_time:
            # 2020-06-05T15:01:50-04:00 时间转换 iso8601
            published_time = p_time[0]
            t = iso8601.parse_date(published_time)
            published_time = t.strftime("%Y-%m-%d %H:%M:%S")
        return published_time

    def source_filter_key(self, res_text, domain, image, res_url, source_key, published_time):
        try:
            expected_mail = []
            for mail in email_exists:
                if mail in res_text:
                    o_m = re.findall(r'(%s[a-z0-9]*[-_]?[a-z0-9]*[\.][a-z]{2,3}[\.]?[a-z]{0,2})' % mail, res_text)
                    expected_mail.extend(o_m)
            # if not expected_mail:
            #     o_m = re.search(
            #         r'[a-z]([a-z0-9]*[-_]?[a-z0-9]+)*@([a-z0-9]*[-_]?[a-z0-9]+)+[\.][a-z]{2,3}([\.][a-z]{2})?',
            #         res_text)
            #     expected_mail.append(o_m)
            #     o_m = re.findall(r'([a-z][a-z0-9]*[-_]?[a-z0-9]*@[a-z0-9]*[-_]?[a-z0-9]*[\.][a-z]{2,3}[\.]?[a-z]{0,2})',res_text)
            #     expected_mail.extend(o_m)
            if expected_mail:
                expected_mail = list(
                    set([i.strip() for i in expected_mail if 'png' not in i and len(i) < 50]))
                expected_mail = list(
                    set([i.strip() for i in expected_mail if 'jpg' not in i and len(i) < 50]))
            rank_data = SiteRank().parse(domain) or None
            url_dict = {
                'host': domain,
                'image': image,
                'product_url': res_url,
                'tool_name': source_key,
                'email': expected_mail,
                'world_rank': rank_data,
                'published_time': published_time
            }
            self.crawl_data.append(url_dict)
            logger.info(f'过滤后爬取数据结束============={self.crawl_data}')
        except Exception as e:
            pass

    def thread_crawl(self, url_list):
        t_list = []
        for data in url_list:
            t = threading.Thread(target=self.crawl_product, args=(data['url'], data['image']))
            logger.info(f'多线程爬取========{threading.current_thread().name}====={data}')
            t_list.append(t)
            t.start()
        for t in t_list:
            t.join()


def google_search(data):
    GoogleSearchByImage().get_redis_data(data)


if __name__ == '__main__':
    GoogleSearchByImage().google_sbi('https://ae01.alicdn.com/kf/HTB1zNpxlbPpK1RjSZFFq6y5PpXaJ.jpg')
