import requests
import json
from functools import reduce
from DecryptLogin import login


class Twitter:
    def __init__(self, twitter_username, twitter_password, twitter_proxies=None, twitter_user_list=None):
        self.__username = twitter_username
        self.__password = twitter_password
        self.__proxies = twitter_proxies
        self.__user_list = twitter_user_list
        self.__session = None

    def set_proxies(self, twitter_proxies):
        self.__proxies = twitter_proxies

    def set_user_list(self, twitter_user_list):
        self.__user_list = twitter_user_list

    def __create_session(self):
        lg = login.Login()
        _, session = lg.twitter(self.__username, self.__password, proxies=self.__proxies)
        response = session.get("https://abs.twimg.com/responsive-web/client-web/main.e1a20265.js")
        content = response.text

        character_begin = "c=\"auth_token\",l=\""
        character_length = 18
        auth_token_length = 104
        index_begin = content.find(character_begin) + character_length
        index_end = index_begin + auth_token_length

        auth_token = "Bearer " + content[index_begin:index_end]
        x_csrf_token = session.cookies.get("ct0")

        headers = {
            'authority': 'twitter.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="92"',
            'dnt': '1',
            'x-twitter-client-language': 'zh-cn',
            'x-csrf-token': x_csrf_token,
            'sec-ch-ua-mobile': '?0',
            'authorization': auth_token,
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.21 (KHTML, like Gecko) konqueror/4.14.10 Safari/537.21',
            'x-twitter-auth-type': 'OAuth2Session',
            'x-twitter-active-user': 'yes',
            'accept': '*/*',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://twitter.com/',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        session.headers = headers
        return session

    def __get_followers(self, user_id):
        user_set = set()
        cursor = ""  # 分页游标，不填写从第一开始
        count = 1000  # 单次获取数量，最大到7500， 太大可能503

        while True:
            variables = {
                "userId": user_id,
                "count": count,
                "cursor": cursor,
                "withTweetQuoteCount": False,
                "includePromotedContent": False,
                "withSuperFollowsUserFields": True,
                "withUserResults": True,
                "withBirdwatchPivots": False,
                "withReactionsMetadata": True,
                "withReactionsPerspective": True,
                "withSuperFollowsTweetFields": True
            }
            params = {"variables": json.dumps(variables)}
            response = self.__session.get(
                'https://twitter.com/i/api/graphql/mqh0QWUpZWoiKdylGa69Jg/Followers',
                params=params
            )

            instructions = response.json()["data"]["user"]["result"]["timeline"]["timeline"]["instructions"]
            for item in instructions:
                if item["type"] == "TimelineAddEntries":
                    entries = item["entries"]

            for entry in entries[:-2]:
                result = entry["content"]["itemContent"]["user_results"]["result"]
                # 有封禁账户？ "__typename": "UserUnavailable", "reason": "Protected"
                if result["__typename"] == "User":
                    screen_name = result["legacy"]["screen_name"]
                    user_set.add(screen_name)

            cursor = entries[-2:-1][0]["content"]["value"]

            # 获取完了结束
            if cursor.split("|")[0] == "0":
                break
        return user_set

    def __get_user_id(self, screen_name):
        variables = {
            "screen_name": screen_name,
            "withSafetyModeUserFields": True,
            "withSuperFollowsUserFields": True
        }
        params = {"variables": json.dumps(variables)}
        response = self.__session.get(
            'https://twitter.com/i/api/graphql/B-dCk4ph5BZ0UReWK590tw/UserByScreenName',
            params=params
        )
        return response.json()["data"]["user"]["result"]["rest_id"]

    def get_user_name(self, screen_name):
        variables = {
            "screen_name": screen_name,
            "withSafetyModeUserFields": True,
            "withSuperFollowsUserFields": True
        }
        params = {"variables": json.dumps(variables)}
        response = self.__session.get(
            'https://twitter.com/i/api/graphql/B-dCk4ph5BZ0UReWK590tw/UserByScreenName',
            params=params
        )
        return response.json()["data"]["user"]["result"]["legacy"]["name"]

    def get_all_followers(self):
        if self.__session is None:
            self.__session = self.__create_session()
        follower_pool = {}
        for user in self.__user_list:
            user_id = self.__get_user_id(user)
            followers = self.__get_followers(user_id)
            follower_pool[user] = followers
        return follower_pool

    # def both_follow_all(self, user_list):
    #     follower_pool = []
    #     for user in user_list:
    #         user_id = self._get_user_id(user)
    #         print("正在获取粉丝列表 >> " + user)
    #         followers = self._get_followers(user_id)
    #         follower_pool.append(followers)
    #     target = reduce(lambda a, b: a.intersection(b), follower_pool)  # 取交集
    #     print(target)
    #     print(len(target))

    # def both_follow_most(self, user_list):
    #     from collections import Counter

    #     follower_pool = []
    #     counts = Counter()
    #     for user in user_list:
    #         user_id = self._get_user_id(user)
    #         followers = self._get_followers(user_id)
    #         counts += Counter(followers)
    #     print(counts.most_common())


if __name__ == "__main__":
    username = ""
    password = ""

    proxies = {"https": "http://xxx.xxx.xxx.xxx:xxxx"}

    user_list = ["ProjectMili", "sanapri", "And.....?"]

    myapp = Twitter(username, password, proxies)
