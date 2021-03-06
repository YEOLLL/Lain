config = {
    # 代理
    'proxies': {
        'https://': 'http://127.0.0.1:7890'
    },

    # 启用的模块
    'modules_enabled': ['CoolAPK'],

    # 推特
    'Twitter': {
        'account': {
            'username': '',
            'password': ''
        },
        'user_list': [''],
        'have_to_login': True,  # 必选
        'use_proxies': True
    },

    # 网易云
    'NetEaseMusic': {
        'user_list': [''],
        'have_to_login': False,  # 不可选
        'use_proxies': False
    },

    # Github
    'Github': {
        'user_list': [''],
        'have_to_login': False,  # 不可选
        'use_proxies': True
    },

    # 豆瓣小组
    'DoubanGroup': {
        'user_list': [''],
        'account': {
            'username': '',
            'password': ''
        },
        'have_to_login': False,  # 可选
        'use_proxies': False
    },

    # 酷安
    'CoolAPK': {
        'user_list': [''],
        'have_to_login': False,  # 不可选
        'use_proxies': False
    },

    # 抖音
    'Douyin': {
        'user_list': [''],
        'have_to_login': False,  # 不可选
        'use_proxies': False
    }
}
