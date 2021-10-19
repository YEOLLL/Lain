#
# TODO: 歌手页和用户页搜索结果不同，目前只搜索用户，未来将歌手补上
#

import base64
import binascii
import json
import os
import httpx
import asyncio
from Crypto.Cipher import AES
from utils.log import logger
from utils.exception import *
from utils.handle_results import handle_results


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
    params = aes(aes(data, NONCE), secret).decode('utf-8')
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
    def __init__(self, proxies=None):
        self.__user_list = None
        self.__client = httpx.AsyncClient(proxies=proxies)

    def set_user_list(self, netease_music_user_list):
        self.__user_list = netease_music_user_list

    async def __get_user_id(self, nickname):
        logger.info('正在获取userid，用户名：{}', nickname)

        text = {
            "s": nickname,
            "type": 1002,
            "offset": 0,
            "limit": 1
        }
        data = encrypted_request(text)
        print(data)

        response = await self.__client.post(
            'https://music.163.com/weapi/search/get',
            data=data
        )

        if response.status_code != 200:
            raise HttpCodeError(response.status_code)

        response_json = response.json()
        if response_json["code"] != 200:
            raise JsonCodeError(response_json['code'])

        result = response_json["result"]
        if result["userprofileCount"] == 0:
            raise UserNotFound

        user_id = result["userprofiles"][0]["userId"]
        return {nickname: user_id}

    async def __get_followers(self, user_id):
        logger.info("正在获取粉丝，userid：{}", user_id)

        text = {
            "userId": user_id,
            "limit": 999999999,  # 单次获取大小，应该不至于获取不完
        }
        data = encrypted_request(text)
        response = await self.__client.post(
            'https://music.163.com/weapi/user/getfolloweds',
            data=data
        )

        if response.status_code != 200:
            logger.error('获取粉丝失败，userid：{}，HTTP状态码异常：{}', user_id, response.status_code)
            return False

        response_json = response.json()
        if response_json["code"] != 200:
            raise JsonCodeError(response_json['code'])

        followers = []
        result = response_json["followeds"]
        for follower in result:
            followers.append(follower["nickname"])

        return {user_id: followers}

    async def run(self):

        user_dict = {}  # {user_id: nickname}
        user_id_list = []  # user_id, user_id
        followers_dict = {}  # {nickname: [followers]}

        # 获取 userid
        results = await asyncio.gather(
            *[self.__get_user_id(nickname) for nickname in self.__user_list],
            return_exceptions=True
        )
        results = handle_results(results, self.__user_list, '获取userid')  # 处理异常
        for result in results:
            for nickname, user_id in result.items():
                user_dict.update(
                    {user_id: nickname}
                )
                user_id_list.append(user_id)

        # 获取粉丝
        results = await asyncio.gather(
            *[self.__get_followers(user_id) for user_id in user_id_list],
            return_exceptions=True
        )
        results = handle_results(results, user_id_list, '获取粉丝')  # 处理异常
        for result in results:
            for user_id, followers in result.items():
                followers_dict.update(
                    {user_dict[user_id]: followers}
                )

        # 关闭 client
        await self.__client.aclose()

        return followers_dict


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    myapp = NetEaseMusic()
    user_list = ["MiliProject"]
    myapp.set_user_list(user_list)
    print(loop.run_until_complete(myapp.run()))
