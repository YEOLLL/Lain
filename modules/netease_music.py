import base64
import binascii
import json
import os
import requests

from Crypto.Cipher import AES


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

    def set_proxies(self, netease_music_proxies):
        self.__session.proxies = netease_music_proxies

    def set_user_list(self, netease_music_user_list):
        self.__user_list = netease_music_user_list

    def __get_user_id(self, nickname):
        text = {
            "s": nickname,
            "type": 1002,
            "offset": 0,
            "limit": 30
        }
        data = encrypted_request(text)
        response = self.__session.post('https://music.163.com/weapi/search/get', data=data)
        user_id = response.json()["result"]["userprofiles"][0]["userId"]
        return user_id

    def __get_followers(self, nickname):
        user_id = self.__get_user_id(nickname)
        text = {
            "userId": user_id,
            "limit": 999999999,
        }
        data = encrypted_request(text)
        response = self.__session.post('https://music.163.com/weapi/user/getfolloweds', data=data)

        followers = response.json()["followeds"]
        user_set = set()
        for follower in followers:
            user_set.add(follower["nickname"])

        return user_set

    def get_all_followers(self):
        follower_pool = {}
        for user in self.__user_list:
            followers = self.__get_followers(user)
            follower_pool[user] = followers
        return follower_pool


if __name__ == "__main__":
    myapp = NetEaseMusic()
    user_list = [""]
    myapp.set_user_list(user_list)
    print(myapp.get_all_followers())
