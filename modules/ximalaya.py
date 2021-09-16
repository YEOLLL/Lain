"""
    废弃
    最大只能获取66*30=1980个粉丝
"""

import requests


class Ximalaya:
    def __init__(self, ximalaya_proxies=None, ximalaya_user_list=None):
        self.__proxies = ximalaya_proxies
        self.__user_list = ximalaya_user_list

        self.__session = requests.Session()
        self.__session.proxies = ximalaya_proxies
        self.__session.headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90"',
            'DNT': '1',
            'xm-sign': '3ea9690718bf1dfce18e436fd6bfa486(43)1631599717057(19)1631599434486',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.21 (KHTML, like Gecko) konqueror/4.14.10 Safari/537.21',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://www.ximalaya.com/search/',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def __get_user_id(self, username):

        params = (
            ('kw', username),
            ('page', '1'),
            ('spellchecker', 'true'),
            ('condition', 'relation'),
            ('rows', '1'),
            ('core', 'user'),
            ('device', 'iPhone'),
        )

        response = self.__session.get('https://www.ximalaya.com/revision/search/main', params=params)
        uid = response.json()["data"]["user"]["docs"][0]["uid"]
        return str(uid)

    def get_followers(self, user_id):

        followers = []
        params = (
            ('page', '66'),  # 最大66
            ('pageSize', '30'),  # 最大30
            ('keyWord', ''),
            ('uid', user_id),
            ('orderType', ''),
        )
        response = self.__session.get('https://www.ximalaya.com/revision/user/fans', params=params)

        fans_page_info = response.json()["data"]["fansPageInfo"]
        for follower in fans_page_info:
            anchor_nickname = follower["anchorNickName"]
            followers.append(anchor_nickname)

        return followers


if __name__ == '__main__':
    myapp = Ximalaya()