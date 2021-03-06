import re
import json
import httpx
import asyncio
import random
import binascii
from utils.log import logger
from utils.exception import *
from utils.handle_results import handle_results


# token生成，修改自 https://github.com/CharlesPikachu/DecryptLogin/blob/master/DecryptLogin/core/twitter.py
def generate_token(size=16):
    token = random.getrandbits(size * 8).to_bytes(size, 'big')
    return binascii.hexlify(token).decode()


# 登录代码，修改自 https://github.com/CharlesPikachu/DecryptLogin/blob/master/DecryptLogin/core/twitter.py
async def twitter_login(twitter_username, twitter_password, twitter_proxies):
    logger.info("正在登录")

    client = httpx.AsyncClient(proxies=twitter_proxies)
    client.headers = {
        'user-agent': 'Opera/9.80 (J2ME/MIDP; Opera Mini/7.1.32052/29.3417; U; en) Presto/2.8.119 Version/11.10',
        'origin': 'https://mobile.twitter.com',
        'referer': 'https://mobile.twitter.com/login'
    }

    login_url = 'https://twitter.com/login'
    sessions_url = 'https://twitter.com/sessions'

    # 获得authenticity_token
    authenticity_token = generate_token()
    client.cookies.clear()
    await client.get(login_url)

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
    response = await client.post(sessions_url, cookies=cookies, data=data)

    if response.status_code != 200:
        raise HttpCodeError(response.status_code)

    if response.cookies.get("twid") is None:
        raise LoginError

    return client


class Twitter:
    def __init__(self, proxies=None):
        self.__client = None
        self.__username = None
        self.__password = None
        self.__proxies = proxies
        self.__user_list = None

    def set_user_list(self, twitter_user_list):
        self.__user_list = twitter_user_list

    def set_login_username(self, twitter_username):
        self.__username = twitter_username

    def set_login_password(self, twitter_password):
        self.__password = twitter_password

    async def __create_session(self):
        logger.info("正在创建Session")

        # 登录
        client = await twitter_login(self.__username, self.__password, self.__proxies)

        response = await client.get("https://abs.twimg.com/responsive-web/client-web/main.e1a20265.js")

        if response.status_code != 200:
            logger.error('创建Session出错，HTTP状态码异常：{}', response.status_code)
            return False

        content = response.text

        if (result := re.findall(r'c="auth_token",l="(.*?)",d="', content)) is None:
            logger.error("创建Session出错，无法从返回中取出AuthToken")
            return False
        else:
            auth_token = 'Bearer ' + result[0]
            x_csrf_token = client.cookies.get("ct0")

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
        client.headers = headers
        return client

    async def __get_user_id(self, screen_name):
        logger.info("正在获取userid，用户名：{}", screen_name)

        variables = {
            "screen_name": screen_name,
            "withSafetyModeUserFields": True,
            "withSuperFollowsUserFields": True
        }
        params = {
            "variables": json.dumps(variables)
        }

        response = await self.__client.get(
            'https://twitter.com/i/api/graphql/B-dCk4ph5BZ0UReWK590tw/UserByScreenName',
            params=params
        )

        if response.status_code != 200:
            raise HttpCodeError(response.status_code)

        user_id = response.json()["data"]["user"]["result"]["rest_id"]
        return {screen_name: user_id}

    async def __get_followers(self, user_id):
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
            response = await self.__client.get(
                'https://twitter.com/i/api/graphql/mqh0QWUpZWoiKdylGa69Jg/Followers',
                params=params
            )

            if response.status_code != 200:
                raise HttpCodeError(response.status_code)

            instructions = response.json()["data"]["user"]["result"]["timeline"]["timeline"]["instructions"]

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

        return {user_id: followers}

    async def run(self):
        # 创建 Session
        result = await asyncio.gather(
            self.__create_session()
        )
        result = handle_results(result, [self.__username], '创建Session')
        self.__client = result[0] if result else httpx.AsyncClient(proxies=self.__proxies)

        user_dict = {}  # {user_id: screen_name}
        user_id_list = []  # user_id, user_id
        followers_dict = {}  # {screen_name: [followers]}

        # 获取 userid
        results = await asyncio.gather(
            *[self.__get_user_id(screen_name) for screen_name in self.__user_list],
            return_exceptions=True
        )
        results = handle_results(results, self.__user_list, '获取userid')
        for result in results:
            for screen_name, user_id in result.items():
                user_dict.update(
                    {user_id: screen_name}
                )
                user_id_list.append(user_id)

        # 获取粉丝
        results = await asyncio.gather(
            *[self.__get_followers(user_id) for user_id in user_id_list],
            return_exceptions=True
        )
        results = handle_results(results, user_id_list, '获取粉丝')
        for result in results:
            for user_id, followers in result.items():
                followers_dict.update(
                    {user_dict[user_id]: followers}
                )

        await self.__client.aclose()

        return followers_dict


if __name__ == "__main__":
    username = ""
    password = ""

    proxies = {"https://": "http://127.0.0.1:7890"}

    user_list = [""]

    myapp = Twitter(proxies)
    myapp.set_login_username(username)
    myapp.set_login_password(password)
    myapp.set_user_list(user_list)

    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(myapp.run()))
