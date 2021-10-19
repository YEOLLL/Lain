import httpx
import time
import base64
import asyncio
from _md5 import md5
from utils.log import logger
from utils.exception import *
from utils.handle_results import handle_results


# 获取x-app-token算法，来自 https://github.com/PinkD/CoolApkApiTokenGenerator
def base64_encode(data):
    return base64.b64encode(data.encode()).decode()


def md5_hex_digest(data):
    m = md5()
    m.update(data.encode())
    return m.hexdigest()


def get_as(device_id="00000000-0000-0000-0000-000000000000") -> str:
    package_name = "com.coolapk.market"
    token = "token://com.coolapk.market/c67ef5943784d09750dcfbb31020f0ab?"

    timestamp = int(time.time())
    timestamp_md5 = md5_hex_digest(str(timestamp))

    salt = token + timestamp_md5 + "$" + device_id + "&" + package_name

    salt_encoded = base64_encode(salt)
    salt_md5 = md5_hex_digest(salt_encoded)

    return salt_md5 + device_id + f'0x{timestamp:x}'


class Coolapk:
    def __init__(self, proxies=None):
        self.__user_list = None

        self.__client = httpx.AsyncClient(proxies=proxies)
        x_app_token = get_as()
        self.__client.headers = {
            'User-Agent': 'CoolMarket/11.2.6-2106281-universal',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Sdk-Int': '30',
            'X-Sdk-Locale': 'zh-CN',
            'X-App-Id': 'com.coolapk.market',
            'X-App-Token': x_app_token,
            'X-App-Version': '11.2.6',
            'X-App-Code': '2106281',
            'X-Api-Version': '11',
            'X-App-Device': 'AI7MjM3ATMy81Mx8FMwEjMFxEI7ADMxITRMByOzVHbQVmbPByOzVHbQVmbPByOgsDI7AyO',
            'X-Dark-Mode': '0',
            'X-App-Channel': 'coolapk',
            'X-App-Mode': 'universal',
            'Host': 'api.coolapk.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
        }

    def set_user_list(self, coolapk_user_list):
        self.__user_list = coolapk_user_list

    async def __get_uid(self, username):
        logger.info('正在获取uid，用户名：{}', username)

        params = (
            ('type', 'user'),
            ('searchValue', username),
            ('page', '1'),
            ('showAnonymous', '-1'),
        )
        response = await self.__client.get(
            'https://api.coolapk.com/v6/search',
            params=params
        )

        if response.status_code != 200:
            raise HttpCodeError(response.status_code)

        response_json = response.json()

        if len(response_json['data']) == 0:
            raise UserNotFound

        user_data = response_json['data'][0]
        uid = user_data['uid']
        return {username: uid}

    async def __get_followers(self, uid):
        logger.info('正在获取粉丝，uid：{}', uid)

        followers = []
        page = 1

        # 一次 20 个
        while True:
            params = (
                ('uid', uid),
                ('page', str(page)),
            )

            response = await self.__client.get('https://api.coolapk.com/v6/user/fansList', params=params)

            if response.status_code != 200:
                raise HttpCodeError(response.status_code)

            response_json = response.json()
            user_data_list = response_json['data']

            # 获取完毕
            if len(user_data_list) == 0:
                break
            for user_data in user_data_list:
                username = user_data['username']
                followers.append(username)
            page += 1

        return {uid: followers}

    async def run(self):

        user_dict = {}  # {uid: username}
        uid_list = []  # uid, uid, uid
        followers_dict = {}  # {username: [followers]}

        # 获取 UID
        results = await asyncio.gather(
            *[self.__get_uid(user) for user in self.__user_list],
            return_exceptions=True
        )
        results = handle_results(results, self.__user_list, '获取uid')  # 处理异常
        # 将 uid 与用户名对应存进 user_dict
        for result in results:
            for username, uid in result.items():
                user_dict.update(
                    {uid: username}
                )
                uid_list.append(uid)

        # 根据 UID 获取粉丝
        results = await asyncio.gather(
            *[self.__get_followers(uid) for uid in uid_list],
            return_exceptions=True
        )
        results = handle_results(results, uid_list, '获取粉丝')  # 处理异常
        # 通过 uid 获取 user_dict 中对应用户名，将用户名和粉丝对应存至 followers_dict
        for result in results:
            for uid, followers in result.items():
                followers_dict.update(
                    {user_dict[uid]: followers}
                )

        # 关闭 client
        await self.__client.aclose()

        return followers_dict


if __name__ == '__main__':
    myapp = Coolapk()
    myapp.set_user_list(['产品菜鸟吴日天'])
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(myapp.run()))
