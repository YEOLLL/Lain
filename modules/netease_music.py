import base64
import binascii
import json
import os
import requests
from Crypto.Cipher import AES
from modules.log import logger
from json import JSONDecodeError

# From https://github.com/nnnewb/NEMCore/blob/master/nemcore/encrypt.py
MODULUS = (
    "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7"
    "b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280"
    "104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932"
    "575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b"
    "3ece0462db0a22b8e7"
)
PUBKEY = "010001"
NONCE = b"0CoJUm6Qyw8W8jud"


# 登录加密算法, 基于https://github.com/stkevintan/nw_musicbox
def encrypted_request(text):
    data = json.dumps(text).encode("utf-8")
    secret = create_key(16)
    params = aes(aes(data, NONCE), secret)
    enc_sec_key = rsa(secret, PUBKEY, MODULUS)
    return {"params": params, "encSecKey": enc_sec_key}


def aes(text, key):
    pad = 16 - len(text) % 16
    text = text + bytearray([pad] * pad)
    encryptor = AES.new(key, 2, b"0102030405060708")
    ciphertext = encryptor.encrypt(text)
    return base64.b64encode(ciphertext)


def rsa(text, pubkey, modulus):
    text = text[::-1]
    rs = pow(int(binascii.hexlify(text), 16), int(pubkey, 16), int(modulus, 16))
    return format(rs, "x").zfill(256)


def create_key(size):
    return binascii.hexlify(os.urandom(size))[:16]


class NetEaseMusic:
    def __init__(self, netease_music_proxies=None, netease_music_user_list=None):
        self.__user_list = netease_music_user_list
        self.__session = requests.Session()
        self.__session.proxies = netease_music_proxies
        self.__something_wrong = False

    def set_proxies(self, netease_music_proxies):
        self.__session.proxies = netease_music_proxies

    def set_user_list(self, netease_music_user_list):
        self.__user_list = netease_music_user_list

    def __get_user_id(self, nickname):
        logger.info('正在获取userid，用户名：{}', nickname)

        text = {
            "s": nickname,
            "type": 1002,
            "offset": 0,
            "limit": 1
        }
        data = encrypted_request(text)

        try:
            response = self.__session.post('https://music.163.com/weapi/search/get', data=data)
        except requests.RequestException as e:
            logger.error('获取userid失败，用户名：{}，请求失败：{}', nickname, e)
            return False

        if response.status_code != 200:
            logger.error('获取userid失败，用户名：{}，HTTP状态码异常：{}', nickname, response.status_code)
            return False

        try:
            response_json = response.json()
            if response_json["code"] != 200:
                logger.error('获取userid失败，用户名：{}，Json状态码异常：{}', nickname, response_json["code"])
                return False
        except JSONDecodeError:
            logger.error('获取userid失败，用户名：{}，Json解析异常', nickname)
            return False

        result = response_json["result"]
        if result["userprofileCount"] == 0:
            logger.warning('获取userid失败，用户名：{}，未找到此用户', nickname)
            return False

        user_id = result["userprofiles"][0]["userId"]
        return user_id

    def __get_followers(self, user_id):
        logger.info("正在获取粉丝，userid：{}", user_id)

        text = {
            "userId": user_id,
            "limit": 999999999,  # 单次获取大小，应该不至于获取不完
        }
        data = encrypted_request(text)
        try:
            response = self.__session.post('https://music.163.com/weapi/user/getfolloweds', data=data)
        except requests.RequestException as e:
            logger.error('获取粉丝失败，userid：{}，请求失败：{}', user_id, e)
            return False

        if response.status_code != 200:
            logger.error('获取粉丝失败，userid：{}，HTTP状态码异常：{}', user_id, response.status_code)
            return False

        try:
            response_json = response.json()
            if response_json["code"] != 200:
                logger.error('获取粉丝失败，userid：{}，Json状态码异常：{}', user_id, response_json["code"])
                return False
        except JSONDecodeError:
            logger.error('获取粉丝失败，userid：{}，Json解析异常', user_id)
            return False

        followers = []
        result = response_json["followeds"]
        for follower in result:
            followers.append(follower["nickname"])

        logger.success("获取粉丝完成，userid：{}", user_id)
        return followers

    def get_all_followers(self):

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


if __name__ == "__main__":
    myapp = NetEaseMusic()
    user_list = [""]
    myapp.set_user_list(user_list)
    print(myapp.get_all_followers())
