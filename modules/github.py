import httpx
import asyncio
from lxml import etree
from utils.log import logger
from utils.exception import *
from utils.handle_results import handle_results


class Github:
    def __init__(self, proxies=None):
        self.__client = httpx.AsyncClient(proxies=proxies)
        self.__user_list = None

    def set_user_list(self, github_user_list):
        self.__user_list = github_user_list

    async def __get_followers(self, username):
        logger.info("正在获取粉丝，用户名：{}", username)

        page = 1  # 页面
        followers = []
        while True:
            url = "https://github.com/{}?page={}&tab=followers".format(username, str(page))
            response = await self.__client.get(url)

            if response.status_code != 200:
                raise HttpCodeError(response.status_code)

            html = etree.HTML(response.text)

            # 如果没有数据了，此xpath会定位到的一个提示获取完毕的标签
            if html.xpath('//*[@id="js-pjax-container"]/div[2]/div/div[2]/div[2]/div/p'):
                break  # 获取完毕跳出

            # 获取结果
            result = html.xpath('//*[@id="js-pjax-container"]/div[2]/div/div[2]/div[2]/div/div/div[2]/a/span[2]/text()')
            followers += result
            page += 1

        logger.success("获取粉丝完成，用户名：{}", username)
        return {username: followers}

    async def run(self):
        followers_dict = {}  # {username: [followers]}

        # 获取粉丝
        results = await asyncio.gather(
            *[self.__get_followers(username) for username in self.__user_list],
            return_exceptions=True
        )
        results = handle_results(results, self.__user_list, '获取粉丝')  # 处理异常
        for result in results:
            followers_dict.update(result)

        # 关闭 client
        await self.__client.aclose()

        return followers_dict


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    myapp = Github(proxies={'https://': 'http://127.0.0.1:7890'})
    myapp.set_user_list(["YEOLLL"])
    print(loop.run_until_complete(myapp.run()))
