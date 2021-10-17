import httpx
import json
import asyncio
from utils.log import logger
from utils.handle_results import handle_results
from utils.exception import *


class Douyin:
    def __init__(self, douyin_proxies=None):
        self.__user_list = None
        self.__client = httpx.AsyncClient(http2=True, verify=False, proxies=douyin_proxies)

    def set_user_list(self, douyin_user_list):
        self.__user_list = douyin_user_list

    async def __get_uid_and_sec_uid(self, user_number):
        logger.info('正在获取uid和sec_uid，抖音号：{}', user_number)

        headers = {
            'Host': 'search100-search-quic-lf.amemv.com',
            'cookie': 'odin_tt=34634f362add90317e0f2d677fb314f9dca620c26538310d256a43b5cb6166c6ee4f48065b61f5b40b65f8a302ecd9064286952ce00245644004243ed0958ac1',
            'x-tt-dt': 'AAA2QEHJS2TYTZVB65ENXXDBUM34DJSVRXDAAB74I654JKXIOFSXNH43TT6VY6B4ZYUF2RUNKUO5AFYY65KNBTIRNZUDMEGKL5KAQQDY6ZZNRLPWN6NLSL5PUV4MMCGHYA7BLTK65EV5GMHHBXSU7KA',
            'activity_now_client': '1633336353034',
            'sdk-version': '2',
            'passport-sdk-version': '20356',
            'x-ss-req-ticket': '1633336351791',
            'x-vc-bdturing-sdk-version': '2.2.0.cn',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-ss-stub': '4176100896239509FC2A4D9AE1E0CE86',
            'x-tt-request-tag': 's=-1;p=0',
            'x-ss-dp': '1128',
            'x-tt-trace-id': '00-4a6eddb80dc0863ea34164e054530468-4a6eddb80dc0863e-01',
            'user-agent': 'com.ss.android.ugc.aweme/170601 (Linux; U; Android 11; Build/RKQ1.201112.002; Cronet/TTNetVersion:04953992 2021-07-30 QuicVersion:82e20c3d 2021-06-11)',
            'accept-encoding': 'gzip, deflate, br',
            'x-argus': 'L+vhvex7ziwGEHT3zAxccCzm9Af26Gm9o//mqSWMOpffrVL4MY6Mx45DmmrWYecfxLza7JM6N8lRYW1RXZ9pHAID43jNZNRe2qU/n5lUdpn7aM5j6bNvAZJ5gpwn+ZUoX6/eiiAUdk++4mhCOOQ7LdlNCm+k3uW2l3Dti/RhEVxAnvbN6XJyUehvBjkm6486hHab95eYKsJP2amaECyaeXaDFX1fxai87DTHJyGHQPHoVJxOhLCnzLT4gLwx3QOPtx4Lc/IKNMGXwl32h8B22OaNOz/jvZRygocpNDqWcdGSgQ==',
            'x-gorgon': '0404c0b300007524e4a6df11c115f20ada5874d2b084bf29dd30',
            'x-khronos': '1633336350',
            'x-ladon': 'OoCITMbWwnXXjNJH7rl2XSfzxd9wtnmJ5KiMoJqPn2M8Tbn7',
            'x-common-params-v2': 'ac=4g&aid=1128&appTheme=light&app_name=aweme&app_type=normal&cdid=845606cf-f90d-4399-a42e-6a98e08ddb3d&channel=douyin_huitou_and171&cpu_support64=true&device_brand=OnePlus&device_id=3386924944594510&device_platform=android&device_type=LE2100&dpi=450&host_abi=armeabi-v7a&iid=994387652514414&is_android_pad=0&is_guest_mode=0&language=zh&manifest_version_code=170601&minor_status=0&openudid=f30472c7d58e8ad8&os=android&os_api=30&os_version=11&package=com.ss.android.ugc.aweme&resolution=1080*2252&ssmix=a&update_version_code=17609900&version_code=170600&version_name=17.6.0',
        }

        params = (
            ('_rticket', '1633336351790'),
            ('mcc_mnc', '46011'),
            ('need_personal_recommend', '1'),
            ('ts', '1633336352'),
        )

        data = {
            'cursor': '0',
            'enter_from': 'homepage_fresh_2',
            'count': '10',
            'secret': '5LuF6ZmQ5pCc57Si5LuT5bqT5YaF5L2/55SoLjE2MTA1MDMxMjkuMTYzMzMzNjM1MTc4OQ==\n',
            'type': '1',
            'is_pull_refresh': '0',
            'query_correct_type': '1',
            'search_source': 'normal_search',
            'hot_search': '0',
            'search_id': '',
            'token': 'search',
            'address_book_access': '2',
            'location_access': '2',
            'keyword': user_number  # 1610503129
        }

        response = await self.__client.post(
            url='https://search100-search-quic-lf.amemv.com/aweme/v1/discover/search/',
            headers=headers,
            params=params,
            data=data
        )

        raw_data = response.json()['user_list'][0]['dynamic_patch']['raw_data']
        json_data = json.loads(raw_data)
        uid = json_data['user_info']['uid']
        sec_id = json_data['user_info']['sec_uid']

        return {user_number: (uid, sec_id)}

    async def __get_followers(self, uid, sec_uid):
        logger.info('正在获取粉丝，uid：{}', uid)

        headers = {
            'Host': 'api3-normal-c-lf.amemv.com',
            'cookie': 'odin_tt=ebaf4812c8f2376a97e743192ef9bc7c74ae8ed693570d6bb7fac01c72cbbf7d140d1b1d527b36d95cc656a6319e74e1a6c2ab33bd7d0ea7be92160247adf310;install_id=994387652514414;ttreq=1$d38ca2d17cea09c53748c352d1a5ad379e8e0767',
            'x-tt-dt': 'AAA23MLVFKXI2NVWMPSE7AJQJHLGKMTNZ7B77WNKFXSYYCSBF3PWPXAYEP36TKB5SAQCDIG3FPLWSP4V7SBUD5NISIYRNDTLKLJ4ANKWNLA456NMNJKF4OZ3T5XDSCY4LXHV5AVLELEPPLNRWTOUGYA',
            'activity_now_client': '1633253611293',
            'sdk-version': '2',
            'passport-sdk-version': '20356',
            'x-ss-req-ticket': '1633253611675',
            'x-vc-bdturing-sdk-version': '2.2.0.cn',
            'x-tt-request-tag': 's=1;p=0',
            'x-ss-dp': '1128',
            'x-tt-trace-id': '00-45805a190dc0863ea34164ea04500468-45805a190dc0863e-01',
            'user-agent': 'com.ss.android.ugc.aweme/170601 (Linux; U; Android 11; Build/RKQ1.201112.002; Cronet/TTNetVersion:04953992 2021-07-30 QuicVersion:82e20c3d 2021-06-11)',
            'accept-encoding': 'gzip, deflate, br',
            'x-argus': '/uS4BbuTuwZlq7m3qfgKFSC0W2O7S2KZOEEAIe3hYXCEL1D4RxevoXrjhzOmca9yP+ADyWfWq8NaEN+4xQRNfTyB/l8JtbqzqMAutaYWQntBCEwJ9/Gnesp0ym5zEQInnVNsXuaNhNktQMb/+d6c+CD1BCOzvq798kAEqQTj+2m7ngFfNuGgdx+lf7dwM6WZE59pUruUfyM1TScC8I1+AKTE74kcwJzzQurqq3olUVafDbjHIw6aiWiXnfw5zxQ3E+o6UCjjgErvsRjHzGzNuyEbOcxQ/tPcg7LJbFg2aS035g==',
            'x-gorgon': '0404102700002321bd327b25e823573c1b74f83d4c6fa7e24868',
            'x-khronos': '1633253612',
            'x-ladon': 'K1uAUE90KDRvgB8gzzeJtNb2Jd49B6yNmh3bLgbWsDM1PBtM',
            'x-common-params-v2': 'ac=4g&aid=1128&appTheme=light&app_name=aweme&app_type=normal&cdid=cdda65e1-8a09-4314-89ed-45be715066f0&channel=douyin_huitou_and171&cpu_support64=true&device_brand=OnePlus&device_id=3386924944594510&device_platform=android&device_type=LE2100&dpi=450&host_abi=armeabi-v7a&iid=994387652514414&is_android_pad=0&is_guest_mode=0&language=zh&manifest_version_code=170601&minor_status=0&openudid=f30472c7d58e8ad8&os=android&os_api=30&os_version=11&package=com.ss.android.ugc.aweme&resolution=1080*2252&ssmix=a&update_version_code=17609900&version_code=170600&version_name=17.6.0',
        }

        followers = []
        min_time = 0
        source_type = '2'
        has_more = True
        while has_more:
            params = (
                ('user_id', uid),
                ('sec_user_id', sec_uid),
                ('max_time', min_time),  # 使用返回 json 的 min_time
                ('count', '60'),  # 最大 60
                ('offset', '0'),
                ('source_type', source_type),  # 先使用2获取第一次的min_time，之后使用1获取数据
                ('address_book_access', '2'),
                ('gps_access', '2'),
                ('vcd_count', '0'),
                ('_rticket', '1633253611674'),
                ('mcc_mnc', '46011'),
                ('need_personal_recommend', '1'),
                ('ts', '1633253610'),
            )

            response = await self.__client.get(
                url='https://api3-normal-c-lf.amemv.com/aweme/v1/user/follower/list/',
                headers=headers,
                params=params
            )

            source_type = '1'  # 先使用2获取第一次的min_time，之后使用1获取数据
            response_json = response.json()
            if response_json['status_code'] == 2096:
                raise NotAllowToGet
            has_more = response_json['has_more']
            min_time = response_json['min_time']
            followers += [follower['short_id'] for follower in response_json['followers']]

        return {(uid, sec_uid): followers}

    def get_all_followers(self):
        loop = asyncio.get_event_loop()

        # 任务一，获取uid和sec_uid
        tasks1 = [self.__get_uid_and_sec_uid(user) for user in self.__user_list]
        # results --> [ {user_number: (uid, sec_id)}, {user_number: (uid, sec_id)} ]
        results = loop.run_until_complete(
            asyncio.gather(*tasks1, return_exceptions=True),
        )

        results = handle_results(results, self.__user_list, '获取uid和sec_uid')

        # uid_and_sec_uid --> { user_number: (uid, sec_id), user_number: (uid, sec_uid) }
        uid_and_sec_uid = {k: v for result in results for k, v in result.items()}

        # 任务二，获取粉丝
        tasks2 = [self.__get_followers(uid, sec_uid) for uid, sec_uid in uid_and_sec_uid.values()]
        # results --> [ {(uid, sec_uid): followers}, {(uid, sec_uid): followers} ]
        results = loop.run_until_complete(
            asyncio.gather(*tasks2, return_exceptions=True)
        )
        results = handle_results(results, list(uid_and_sec_uid.values()), '获取粉丝')
        # followers --> { (uid, sec_id): [uid], (uid, sec_uid): [uid] }
        followers = {k: v for result in results for k, v in result.items()}

        # 关闭 client
        loop.run_until_complete(self.__client.aclose())

        # 可读性为 0
        return {k2: v1 for k1, v1 in followers.items() for k2, v2 in uid_and_sec_uid.items() if k1 == v2}


if __name__ == '__main__':
    myapp = Douyin()
    myapp.set_user_list(['1610503127', 'chuanchuan5055'])
    print(myapp.get_all_followers())
