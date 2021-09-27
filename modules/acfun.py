"""
    Acfun
    已废弃：上限2000条
"""

import requests
import re
from lxml import etree


class Acfun:
    def __init__(self, acfun_proxies=None, acfun_user_list=None):
        self.__proxies = acfun_proxies
        self.__user_list = acfun_user_list

        self.__session = requests.Session()
        self.__session.proxies = self.__proxies
        self.__session.headers = {
            'authority': 'www.acfun.cn',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="92"',
            'dnt': '1',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Opera/9.80 (J2ME/MIDP; Opera Mini/7.1.32052/29.3417; U; en) Presto/2.8.119 Version/11.10',
            'accept': '*/*',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.acfun.cn/u/',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def get_user(self, acfun_username):

        params = (
            ('type', 'user'),
            ('keyword', acfun_username),
        )

        response = self.__session.get('https://www.acfun.cn/search', params=params)
        response_text = response.text
        user_id = re.search(r'\\"up_id\\":(.*?),\\"is_on_live\\"', response_text).group(1)
        return user_id

    def get_followers(self, user_id):

        followers = []
        page = 1

        while True:
            params = (
                ('quickViewId', 'ac-space-followed-user-list'),
                ('reqID', '2'),
                ('ajaxpipe', '1'),
                ('type', 'followed'),
                ('page', str(page)),
                ('pageSize', '100'),  # 最大100
                ('t', '1631782336786'),
            )

            response = self.__session.get('https://www.acfun.cn/u/'+user_id, params=params)
            response_html = etree.HTML(response.text[:-25])
            followers_html = response_html.xpath('//ul/li')

            if len(followers_html) == 0:
                break

            for item in followers_html:
                follower = item.xpath('div[2]/a/text()')[0]
                followers.append(follower)
            page += 1
        print(len(followers))


if __name__ == '__main__':
    myapp = Acfun()