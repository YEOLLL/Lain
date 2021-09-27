import requests
import re
from lxml import etree
from modules.log import logger
from json import JSONDecodeError


# 登录代码，修改自 https://github.com/CharlesPikachu/DecryptLogin/blob/master/DecryptLogin/core/douban.py
def douban_login(douban_username, douban_password, douban_proxies):
    logger.info('正在登录')

    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36',
        'Host': 'accounts.douban.com',
        'Origin': 'https://accounts.douban.com',
        'Referer': 'https://accounts.douban.com/passport/login_popup?login_source=anony'
    }
    home_url = 'https://www.douban.com/'
    login_url = 'https://accounts.douban.com/j/mobile/login/basic'
    session.headers.update(headers)

    # 设置代理
    session.proxies = douban_proxies
    # 初始化cookie
    session.get(home_url)
    # 模拟登录
    data = {
        'ck': '',
        'name': douban_username,
        'password': douban_password,
        'remember': 'true',
        'ticket': ''
    }
    try:
        response = session.post(login_url, data=data)
    except requests.RequestException as e:
        logger.error("登录失败，请求失败：{}", e)
        return False

    if response.status_code != 200:
        logger.error("登录失败，HTTP状态码异常：{}", response.status_code)
        return False

    try:
        response_json = response.json()
        # 登录成功
        if response_json['status'] == 'success':
            return session
        # 账号或密码错误
        elif response_json['status'] == 'failed' and response_json['message'] == 'unmatch_name_password':
            logger.error('登录失败，用户名或密码错误，请检查配置文件')
            return False
        # 其他错误
        else:
            logger.error('登录失败，其他错误：{}', response_json.get('description'))
            return False

    except JSONDecodeError:
        logger.error('登录失败，Json解析错误')
        return False


class DoubanGroup:
    def __init__(self, douban_username=None, douban_password=None, douban_group_proxies=None, douban_group_list=None):
        self.__username = None
        self.__password = None
        self.__proxies = douban_group_proxies
        self.__group_list = douban_group_list
        self.__username_closed = '[已注销]'

        self.__session = requests.Session()
        self.__session.proxies = douban_group_proxies
        self.__session.headers = {
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

        self.__something_wrong = False

    def set_login_username(self, douban_username):
        self.__username = douban_username

    def set_login_password(self, douban_password):
        self.__password = douban_password

    def set_proxies(self, douban_group_proxies):
        self.__session.proxies = douban_group_proxies

    def set_user_list(self, douban_group_list):
        self.__group_list = douban_group_list

    def __create_session(self):
        logger.info('正在创建Session')

        # 登录，由于我没有可用于测试的豆瓣帐号，此功能不保证可用
        if not (session := douban_login(self.__username, self.__password, self.__proxies)):
            logger.error("创建Session出错，登录失败")
            return False

        session.proxies = self.__proxies
        session.headers = {
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
        return session

    def __get_group_id(self, group_name):
        logger.info("正在获取小组id，小组名：{}", group_name)

        params = (
            ('cat ', '1019'),  # 分类代码，1019为小组
            ('q', group_name)
        )
        try:
            response = self.__session.get("https://www.douban.com/search", params=params)
        except requests.RequestException as e:
            logger.error("获取小组id失败，小组名：{}，请求失败：{}", group_name, e)
            return False

        if response.status_code != 200:
            if response.status_code == 403:
                logger.error('获取小组id失败，小组名：{}，登录跳转：请尝试配置登录账户', group_name)
            else:
                logger.error('获取小组id失败，小组名：{}，HTTP状态码异常：{}', group_name, response.status_code)
            return False

        html = etree.HTML(response.text)

        # 没有搜索结果，或者结果符合项不匹配
        if len(html.xpath('//*[@id="content"]/div/div[1]/div[3]/p[@class="no-result"]')) != 0 or \
                group_name != html.xpath('//*[@id="content"]/div/div[1]/div[3]/div[2]/div/div[2]/div/h3/a/text()'[0]):
            logger.error('获取小组id失败，小组名：{}，未找到该小组', group_name)
            return False

        group_href = html.xpath('//*[@id="content"]/div/div[1]/div[3]/div[2]/div/div[2]/div/h3/a/@href')[0]
        return re.findall("group%2F(.*?)%2F&query", group_href)[0]

    def __get_members(self, group_id):
        logger.info("正在获取小组成员，小组id：{}", group_id)

        group_members = []  # 成员列表

        try:
            # 获取成员总数
            response = self.__session.get(f'https://www.douban.com/group/{group_id}/members')
        except requests.RequestException as e:
            logger.error("获取小组成员总数失败，小组id：{}，请求失败：{}", group_id, e)
            return False

        if response.status_code != 200:
            logger.error('获取小组成员总数失败，小组id：{}，HTTP状态码异常：{}', group_id, response.status_code)
            return False

        html = etree.HTML(response.text)
        count = html.xpath('//*[@id="g-side-info"]/div[2]/div/div/i/text()')[0]
        count = int(count)

        # offset偏移值，从0开始，网页一次会固定返回35条
        for offset in range(0, count, 35):
            params = (
                ('start', offset),
            )
            try:
                response = self.__session.get(f'https://www.douban.com/group/{group_id}/members', params=params)
            except requests.RequestException as e:
                logger.error("获取小组成员失败，小组id：{}，请求失败：{}", group_id, e)
                return False

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

        logger.success("获取小组成员完成，小组id：{}", group_id)
        return group_members

    def get_all_followers(self):
        # 如果配置了用户名密码，先登录获取Session
        if self.__username is not None:
            self.__session = self.__create_session()
            if not self.__session:
                logger.error('获取各帐号粉丝出错，登录失败')
                return False

        members_pool = {}
        for group in self.__group_list:

            if not (group_id := self.__get_group_id(group)):
                self.__something_wrong = True
                logger.warning("获取小组id出错，执行跳过")
                continue
            if not (members := self.__get_members(group_id)):
                self.__something_wrong = True
                logger.warning("获取小组成员出错，执行跳过")
                continue
            members_pool[group] = members

        if self.__something_wrong:
            logger.warning("各帐号粉丝获取完成，发生了一些错误")
        else:
            logger.success("各帐号粉丝获取完成")

        return members_pool


if __name__ == '__main__':
    myapp = DoubanGroup()
    group_list = ["帮军人及恋军女孩儿找对象"]
    myapp.set_user_list(group_list)
    print(myapp.get_all_followers())
