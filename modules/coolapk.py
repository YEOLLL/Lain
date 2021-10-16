import requests
import time
import base64
from _md5 import md5
from json import JSONDecodeError
from utils.log import logger


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
    def __init__(self, coolapk_proxies=None, coolapk_user_list=None):
        self.__user_list = coolapk_user_list
        self.__something_wrong = False

        self.__session = requests.Session()
        x_app_token = get_as()
        self.__session.headers = {
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
        self.__session.proxies = coolapk_proxies

    def set_proxies(self, coolapk_proxies):
        self.__session.proxies = coolapk_proxies

    def set_user_list(self, coolapk_user_list):
        self.__user_list = coolapk_user_list

    def __get_user_id(self, username):
        logger.info('正在获取userid，用户名：{}', username)

        params = (
            ('type', 'user'),
            ('searchValue', username),
            ('page', '1'),
            ('showAnonymous', '-1'),
        )
        try:
            response = self.__session.get('https://api.coolapk.com/v6/search', params=params)
        except requests.RequestException as e:
            logger.error('获取userid出错，用户名：{}，请求失败：{}', username, e)
            return False

        if response.status_code != 200:
            logger.error('获取userid出错，用户名：{}，HTTP状态码异常：{]', username, response.status_code)
            return False

        try:
            response_json = response.json()
            if len(response_json['data']) == 0:
                logger.error('获取userid出错，用户名：{}，未查找到该用户', username)
                return False
        except JSONDecodeError:
            logger.error('获取userid出错，用户名：{}，返回json解析失败', username)
            return False

        user_data = response_json['data'][0]
        uid = user_data['uid']
        return uid

    def __get_followers(self, user_id):
        logger.info('正在获取粉丝，userid：{}', user_id)

        followers = []
        page = 1

        while True:
            params = (
                ('uid', user_id),
                ('page', str(page)),
            )

            try:
                response = self.__session.get('https://api.coolapk.com/v6/user/fansList', params=params)
            except requests.RequestException as e:
                logger.error("获取粉丝失败，userid：{}，请求失败：{}", user_id, e)
                return False

            if response.status_code != 200:
                logger.error('获取粉丝失败，userid：{}，HTTP状态码异常：{}', user_id, response.status_code)
                return False

            try:
                response_json = response.json()
                user_data_list = response_json['data']
            except JSONDecodeError:
                logger.error('获取粉丝失败，userid：{}，返回json解析失败', user_id)
                return False

            # 获取完毕
            if len(user_data_list) == 0:
                break

            for user_data in user_data_list:
                username = user_data['username']
                followers.append(username)
            page += 1

        return followers

    def get_all_followers(self):
        followers_pool = {}
        for user in self.__user_list:
            if not (user_id := self.__get_user_id(user)):
                self.__something_wrong = True
                logger.warning("获取UserId出错，执行跳过")
                continue
            if not (followers := self.__get_followers(user_id)):
                self.__something_wrong = True
                logger.warning("获取粉丝出错，执行跳过")
                continue
            followers_pool[user] = followers

        if self.__something_wrong:
            logger.warning("各帐号粉丝获取完成，发生了一些错误")
        else:
            logger.success("各帐号粉丝获取完成")

        return followers_pool


if __name__ == '__main__':
    myapp = Coolapk()
    myapp.set_user_list(['产品菜鸟吴日天'])
    print(myapp.get_all_followers())
