import re
import json
import requests
import random
import binascii
from modules.log import logger
from json import JSONDecodeError
from functools import reduce


# token生成，修改自 https://github.com/CharlesPikachu/DecryptLogin/blob/master/DecryptLogin/core/twitter.py
def generate_token(size=16):
    token = random.getrandbits(size * 8).to_bytes(size, 'big')
    return binascii.hexlify(token).decode()


# 登录代码，修改自 https://github.com/CharlesPikachu/DecryptLogin/blob/master/DecryptLogin/core/twitter.py
def twitter_login(twitter_username, twitter_password, twitter_proxies):
    logger.info("正在登录")
    session = requests.Session()
    session.headers = {
        'user-agent': 'Opera/9.80 (J2ME/MIDP; Opera Mini/7.1.32052/29.3417; U; en) Presto/2.8.119 Version/11.10',
        'origin': 'https://mobile.twitter.com',
        'referer': 'https://mobile.twitter.com/login'
    }

    login_url = 'https://twitter.com/login'
    sessions_url = 'https://twitter.com/sessions'

    session.proxies = twitter_proxies

    # 获得authenticity_token
    authenticity_token = generate_token()
    session.cookies.clear()
    session.get(login_url)

    # 模拟登录
    cookies = {'_mb_tk': authenticity_token}
    data = {
        'redirect_after_login': '/',
        'remember_me': '1',
        'authenticity_token': authenticity_token,
        'wfa': '1',
        'ui_metrics': '{}',
        'session[username_or_email]': twitter_username,
        'session[password]': twitter_password,
    }
    try:
        response = session.post(sessions_url, cookies=cookies, data=data)
    except requests.RequestException as e:
        logger.error("登录失败，请求失败：{}", e)
        return False

    if response.status_code != 200:
        logger.error("登录失败，HTTP状态码异常：{}", response.status_code)
        return False

    if response.cookies.get("twid") is None:
        logger.error("登录失败，未能正确获取Cookies，请检查配置文件中的账户")
        return False

    return session


class Twitter:
    def __init__(self, twitter_username=None, twitter_password=None, twitter_proxies=None, twitter_user_list=None):
        self.__username = twitter_username
        self.__password = twitter_password
        self.__proxies = twitter_proxies
        self.__user_list = twitter_user_list
        self.__session = None
        self.__something_wrong = False

    def set_proxies(self, twitter_proxies):
        self.__proxies = twitter_proxies

    def set_user_list(self, twitter_user_list):
        self.__user_list = twitter_user_list

    def set_login_username(self, twitter_username):
        self.__username = twitter_username

    def set_login_password(self, twitter_password):
        self.__password = twitter_password

    def __create_session(self):
        logger.info("正在获取Session")

        # 登录
        if not (session := twitter_login(self.__username, self.__password, self.__proxies)):
            logger.error("创建Session出错，登录失败")
            return False

        try:
            response = session.get("https://abs.twimg.com/responsive-web/client-web/main.e1a20265.js")
        except requests.RequestException as e:
            logger.error("创建Session出错，请求失败：{}", e)
            return False

        if response.status_code != 200:
            logger.error('创建Session出错，HTTP状态码异常：{}', response.status_code)
            return False

        content = response.text

        if (result := re.findall(r'c="auth_token",l="(.*?)",d="', content)) is None:
            logger.error("创建Session出错，无法从返回中取出AuthToken")
            return False
        else:
            auth_token = 'Bearer ' + result[0]
            x_csrf_token = session.cookies.get("ct0")

        headers = {
            'authority': 'twitter.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90"',
            'dnt': '1',
            'x-twitter-client-language': 'zh-cn',
            'x-csrf-token': x_csrf_token,
            'sec-ch-ua-mobile': '?0',
            'authorization': auth_token,
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
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

    def __get_user_id(self, screen_name):
        logger.info("正在获取userid，用户名：{}", screen_name)

        variables = {
            "screen_name": screen_name,
            "withSafetyModeUserFields": True,
            "withSuperFollowsUserFields": True
        }
        params = {
            "variables": json.dumps(variables)
        }
        try:
            response = self.__session.get(
                'https://twitter.com/i/api/graphql/B-dCk4ph5BZ0UReWK590tw/UserByScreenName',
                params=params
            )
        except requests.RequestException as e:
            logger.error("获取userid失败，用户名：{}，请求失败：{}", screen_name, e)
            return False

        if response.status_code != 200:
            logger.error("获取userid失败，用户名：{}，HTTP状态码异常：{}", screen_name, response.status_code)
            return False

        try:
            return response.json()["data"]["user"]["result"]["rest_id"]
        except JSONDecodeError:
            logger.error("获取userid失败，用户名：{}，Json解析失败", screen_name)
            return False

    def __get_followers(self, user_id):
        logger.info("正在获取粉丝，userid：{}", user_id)

        followers = []
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
            try:
                response = self.__session.get(
                    'https://twitter.com/i/api/graphql/mqh0QWUpZWoiKdylGa69Jg/Followers',
                    params=params
                )
            except requests.RequestException as e:
                logger.error("获取粉丝失败，userid：{}，请求失败：{}", user_id, e)
                return False

            if response.status_code != 200:
                logger.error('获取粉丝失败，userid：{}，HTTP状态码异常：{}', user_id, response.status_code)
                return False

            try:
                instructions = response.json()["data"]["user"]["result"]["timeline"]["timeline"]["instructions"]
            except JSONDecodeError:
                logger.error('获取粉丝失败：userid：{}，Json解析失败', user_id)
                return False

            timeline_add_entries = [item for item in instructions if item["type"] == "TimelineAddEntries"][0]
            entries = timeline_add_entries["entries"]
            for entry in entries[:-2]:
                result = entry["content"]["itemContent"]["user_results"]["result"]
                # 有封禁账户？ "__typename": "UserUnavailable", "reason": "Protected"
                if result["__typename"] == "User":
                    screen_name = result["legacy"]["screen_name"]
                    followers.append(screen_name)

            cursor = entries[-2:-1][0]["content"]["value"]

            # 获取完了结束
            if cursor.split("|")[0] == "0":
                break

        logger.success("获取粉丝完成，userid：{}", user_id)
        return followers

    def get_all_followers(self):
        # 创建 Session
        self.__session = self.__create_session()
        if not self.__session:
            logger.error("获取各帐号粉丝失败，创建Session出错")
            return False

        follower_pool = {}
        for user in self.__user_list:

            if not (user_id := self.__get_user_id(user)):
                self.__something_wrong = True
                logger.warning("获取userid出错，执行跳过")
                continue

            if not (followers := self.__get_followers(user_id)):
                self.__something_wrong = True
                logger.warning("获取粉丝出错，执行跳过")
                continue

            follower_pool[user] = followers

        if self.__something_wrong:
            logger.warning("各帐号粉丝获取完成，发生了一些错误")
        else:
            logger.success("各帐号粉丝获取完成")

        return follower_pool

    # def get_user_name(self, screen_name):
    #     variables = {
    #         "screen_name": screen_name,
    #         "withSafetyModeUserFields": True,
    #         "withSuperFollowsUserFields": True
    #     }
    #     params = {"variables": json.dumps(variables)}
    #     response = self.__session.get(
    #         'https://twitter.com/i/api/graphql/B-dCk4ph5BZ0UReWK590tw/UserByScreenName',
    #         params=params
    #     )
    #     return response.json()["data"]["user"]["result"]["legacy"]["name"]

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

    proxies = {"https": "http://127.0.0.1:7890"}

    user_list = [""]

    myapp = Twitter(username, password, proxies)
    myapp.set_user_list(user_list)
    print(myapp.get_all_followers())
