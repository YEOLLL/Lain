from modules import *
from config import *

from os import mkdir, path


class MainApp:
    def __init__(self, output_path="./output"):
        self.modules = {
            "Twitter": Twitter,
            "NetEaseMusic": NetEaseMusic
        }
        for k, v in self.modules.items():
            setattr(self, k, v)
        self.output_path = output_path


if __name__ == "__main__":

    # And you don't seem to understand
    # A shame you seemed an honest man
    # And all the fears you hold so dear
    # Will turn to whisper in your ear
    # And you know what they say might hurt you
    # And you know that it means so much
    # And you don't even feel a thing

    main_app = MainApp()
    for module_name in main_app.modules.keys():

        # 每个模块的结果存储到各自的文件夹
        module_output_path = path.join(main_app.output_path, module_name)
        if not path.exists(module_output_path):
            mkdir(module_output_path)

        # 获取模块
        attr = getattr(main_app, module_name)

        # 需要登录则传入配置中的账户
        if config[module_name]["have_to_login"]:
            module = attr(
                config[module_name]["account"]["username"],
                config[module_name]["account"]["password"],
            )
        else:
            module = attr()

        # 设置代理，如果配置了的话
        if config[module_name]["use_proxies"]:
            module.set_proxies(config["proxies"])

        # 设置用户列表
        module.set_user_list(config[module_name]["user_list"])

        # 获取全部粉丝
        followers_dict = module.get_all_followers()
        for user, followers in followers_dict.items():
            # 为每个用户创建单独的文件
            user_path = path.join(module_output_path, f"{user}.txt")
            with open(user_path, 'w') as f:
                f.write(str(followers))
