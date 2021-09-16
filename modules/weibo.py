"""
    接口来自Weibo微信小程序，最大获取5000个粉丝
    本文件已被放弃
"""

import requests
from time import sleep


class Weibo:
    def __init__(self, weibo_proxies=None, weibo_user_list=None):
        self.__user_list = weibo_user_list

        self.__session = requests.Session()
        self.__session.proxies = weibo_proxies
        self.__session.headers = {
            'Host': 'api.weibo.cn',
            'Connection': 'keep-alive',
            'charset': 'utf-8',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.21 (KHTML, like Gecko) konqueror/4.14.10 Safari/537.21',
            'x-sessionid': '',
            'content-type': 'application/json',
            'Accept-Encoding': 'gzip,compress,br,deflate',
            'Referer': 'https://servicewechat.com/',
        }

    def __get_user_id(self, screen_name):
        params = (
            ('count', '12'),  # 返回数量，只返回一个，节省带宽
            ('containerid', '100103type=3&t=3&q=' + screen_name),
            ('page', '1'),
        )

        response = self.__session.get('https://api.weibo.cn/2/guest/cardlist', params=params)
        user_id = response.json()["cards"][1]["card_group"][0]["user"]["id"]
        return str(user_id)

    def get_followers(self, screen_name):
        user_id = self.__get_user_id(screen_name)
        print(user_id)
        since_id = 1
        followers = []

        while True:
            params = (
                ('containerid', '231051_-_fans_-_' + user_id),
                ('since_id', str(since_id)),  # 从哪儿起始
                ('count', '20'),  # 数量固定，存疑
                ('wm', '123456'),
                ('from', '123456'),
                ('uid', '123456'),
                ('c', 'weixinminiprogram'),
                ('gsid', "_123456")
            )
            response = self.__session.get('https://api.weibo.cn/2/guest/cardlist', params=params)
            response_json = response.json()

            n = 0  # 计数器，记录无数据返回次数
            # 访问过快可能导致不返回数据，延迟几秒后重试
            if response_json["cards"] is None:
                n += 1
                if n == 5:  # 如果连续五次无数据，则认为达到获取上限
                    break
                else:
                    sleep(3)
                    continue
            else:
                n = 0  # 计数器清零

            card_group = response_json["cards"][0]["card_group"]
            for card in card_group:
                follower = card["user"]["screen_name"]
                followers.append(follower)
            if response_json["cardlistInfo"].get("since_id") is None:
                break
            else:
                since_id = response_json["cardlistInfo"]["since_id"]

        return followers


if __name__ == '__main__':
    myapp = Weibo()
    followers = myapp.get_followers("")
    print(followers)
    # print(len(followers))
