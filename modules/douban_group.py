import asyncio
import httpx
import re
from lxml import etree
from utils.log import logger
from utils.exception import *
from utils.handle_results import handle_results


class DoubanGroup:
    def __init__(self, proxies=None):
        self.__username = None
        self.__password = None
        self.__group_list = None
        self.__username_closed = '[已注销]'
        self.__client = httpx.AsyncClient(proxies=proxies)

    def set_login_username(self, douban_username):
        self.__username = douban_username

    def set_login_password(self, douban_password):
        self.__password = douban_password

    def set_user_list(self, douban_group_list):
        self.__group_list = douban_group_list

    async def __create_session(self):
        logger.info('正在创建Session')

        # 登录代码，修改自 https://github.com/CharlesPikachu/DecryptLogin/blob/master/DecryptLogin/core/douban.py
        logger.info('正在登录')

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36',
            'Host': 'accounts.douban.com',
            'Origin': 'https://accounts.douban.com',
            'Referer': 'https://accounts.douban.com/passport/login_popup?login_source=anony'
        }

        home_url = 'https://www.douban.com/'
        cookies = httpx.get(
            home_url, headers=headers, proxies=self.__proxies
        ).cookies  # 初始化 cookies

        login_url = 'https://accounts.douban.com/j/mobile/login/basic'
        data = {
            'ck': '',
            'name': self.__username,
            'password': self.__password,
            'remember': 'true',
            'ticket': ''
        }
        login_request = httpx.Request('POST', login_url, headers=headers, data=data, cookies=cookies)

        client = httpx.AsyncClient(proxies=self.__proxies)
        response = await client.send(login_request)  # 模拟登录

        if response.status_code != 200:
            raise HttpCodeError(response.status_code)

        response_json = response.json()
        # 登录成功
        if response_json['status'] == 'success':
            client.headers = {
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90"',
                'sec-ch-ua-mobile': '?0',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.21 (KHTML, like Gecko) konqueror/4.14.10 Safari/537.21',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Referer': 'https://www.douban.com/group/',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            return client
        # 账号或密码错误
        elif response_json['status'] == 'failed' and response_json['message'] == 'unmatch_name_password':
            raise LoginError('用户名或密码错误')
        # 其他错误
        else:
            raise LoginError(response_json.get('description'))

    async def __get_group_id(self, group_name):
        logger.info("正在获取小组id，小组名：{}", group_name)

        params = (
            ('cat ', '1019'),  # 分类代码，1019为小组
            ('q', group_name)
        )

        response = await self.__client.get("https://www.douban.com/search", params=params)

        if response.status_code != 200:
            if response.status_code == 403:
                raise NeedLogin
            else:
                raise HttpCodeError(response.status_code)

        html = etree.HTML(response.text)

        # 没有搜索结果，或者结果符合项不匹配
        if len(html.xpath('//*[@id="content"]/div/div[1]/div[3]/p[@class="no-result"]')) != 0 or \
                group_name != html.xpath('//*[@id="content"]/div/div[1]/div[3]/div[2]/div/div[2]/div/h3/a/text()'[0]):
            raise UserNotFound

        group_href = html.xpath('//*[@id="content"]/div/div[1]/div[3]/div[2]/div/div[2]/div/h3/a/@href')[0]
        return re.findall("group%2F(.*?)%2F&query", group_href)[0]

    async def __get_members(self, group_id):
        logger.info("正在获取小组成员，小组id：{}", group_id)

        group_members = []  # 成员列表

        # 获取成员总数
        response = await self.__client.get(f'https://www.douban.com/group/{group_id}/members')

        if response.status_code != 200:
            raise HttpCodeError(response.status_code)

        html = etree.HTML(response.text)
        count = html.xpath('//*[@id="g-side-info"]/div[2]/div/div/i/text()')[0]
        count = int(count)

        # offset偏移值，从0开始，网页一次会固定返回35条
        for offset in range(0, count, 35):
            params = (
                ('start', offset),
            )
            response = await self.__client.get(f'https://www.douban.com/group/{group_id}/members', params=params)

            if response.status_code != 200:
                logger.error('获取小组成员失败，小组id：{}，HTTP状态码异常：{}', group_id, response.status_code)
                return False

            html = etree.HTML(response.text)
            div_mod = html.xpath('//*[@class="mod"]')  # 用户分组， 第一个是组长，第二个是管理员，第三个是成员, 第四个为空。 组长、管理员也在成员内
            member_list = div_mod[-2].xpath('./div[@class="member-list"]/ul/*[@class="member-item"]')  # 取出成员列表

            for member_item in member_list:
                name = member_item.xpath('./*[@class="name"]/a/text()')[0]
                # 判断注销用户
                if name != self.__username_closed:
                    group_members.append(name)

        return group_members

    def get_all_followers(self):
        loop = asyncio.get_event_loop()

        # 如果配置了用户名密码，先登录获取Session
        if self.__username:
            self.__client = loop.run_until_complete(self.__create_session())
            if not self.__client:
                logger.error('获取各帐号粉丝出错，登录失败')
                return False

        # 获取小组id
        task1 = [self.__get_group_id(group) for group in self.__group_list]
        results = loop.run_until_complete(
            asyncio.gather(*task1, return_exceptions=True)
        )
        results = handle_results(results, self.__group_list, '获取小组id')
        group_id_dict = {k: v for result in results for k, v in result.items()}

        # 获取小组成员
        task2 = [self.__get_members(group_id) for group_id in group_id_dict.values()]
        results = loop.run_until_complete(
            asyncio.gather(*task2)
        )
        results = handle_results(results, group_id_dict.values(), '获取小组成员')
        member_dict = {k: v for result in results for k, v in result.items()}

        loop.run_until_complete(self.__client.aclose())

        return member_dict


if __name__ == '__main__':
    myapp = DoubanGroup()
    group_list = ["帮军人及恋军女孩儿找对象"]
    myapp.set_user_list(group_list)
    print(myapp.get_all_followers())
