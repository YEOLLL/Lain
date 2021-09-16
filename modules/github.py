import requests
from lxml import etree
from modules.log import logger


class Github:
    def __init__(self, github_proxies=None, github_user_list=None):
        self.__session = requests.Session()
        self.__session.proxies = github_proxies
        self.__user_list = github_user_list
        self.__something_wrong = False

    def set_proxies(self, github_proxies):
        self.__session.proxies = github_proxies

    def set_user_list(self, github_user_list):
        self.__user_list = github_user_list

    def __get_followers(self, username):
        logger.info("正在获取粉丝，用户名：{}", username)

        page = 1  # 页面
        followers = []
        while True:
            url = "https://github.com/{}?&page={}&tab=followers".format(username, str(page))
            try:
                response = self.__session.get(url)
            except requests.RequestException as e:
                logger.error("获取粉丝失败，用户名：{}，请求失败：{}", username, e)
                return None

            if response.status_code != 200:
                logger.error('获取粉丝失败，用户名：{}，HTTP状态码异常：{}', username, response.status_code)
                return None

            html = etree.HTML(response.text)

            # 如果没有数据了，此xpath会定位到的一个提示获取完毕的标签
            if html.xpath('//*[@id="js-pjax-container"]/div[2]/div/div[2]/div[2]/div/p'):
                break  # 获取完毕跳出

            # 获取结果
            result = html.xpath('//*[@id="js-pjax-container"]/div[2]/div/div[2]/div[2]/div/div/div[2]/a/span[2]/text()')
            followers += result
            page += 1

        logger.success("获取粉丝完成，用户名：{}", username)
        return followers

    def get_all_followers(self):
        if self.__user_list is None:
            logger.error("未设置用户列表")
            return None

        followers_poll = {}
        for user in self.__user_list:

            if (followers := self.__get_followers(user)) is None:
                self.__something_wrong = True
                logger.warning("获取粉丝出错，执行跳过")
                continue

            followers_poll[user] = followers

        if self.__something_wrong:
            logger.warning("各帐号粉丝获取完成，发生了一些错误")
        else:
            logger.success("各帐号粉丝获取完成")

        return followers_poll


if __name__ == "__main__":
    myapp = Github()
    myapp.set_proxies({"https": ""})
    myapp.set_user_list([""])
    print(myapp.get_all_followers())
