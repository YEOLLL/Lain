# Lain  
该说什么呢……不知道。  
可悲的人们拼了命地联结。  
互相汲取着对方的负面情绪。  
以此作为关系的养料。  
我不明白。  
对不起。

# 介绍

一个社会工程学工具，去寻找目标在另一个网络平台的账号。

# 使用场景

已知目标在平台A的帐号，通过其帐号的发布信息得知喜好，如：喜爱歌手、画师、明星、游戏、任何可能关注的帐号（如亲友帐号），在平台B找到对应的账户（歌手、画师、亲友账户等），目标在平台B的账户很可能在这些账户粉丝的交集中。

只是个辅助工具，为了更快得找到目标另一个平台的账户，扩大攻击面。

# 程序原理

1. 配置一个或多个可能被目标关注的账户		

2. 爬取这些账户的粉丝列表

3. 查找用户交集(权重)

# 支持与不支持的平台

## 支持的平台

| 平台中文名 | 平台英文名 | 平台网址                             | 获取关注者账户类别 | 限制条件 | 单次获取粉丝数量(一定程度反应速度) | 备注                                     |
| ---------- | ---------- | ------------------------------------ | ------------------ | -------- | ---------------------------------- | ---------------------------------------- |
| 酷安       | CoolAPK    | https://www.coolapk.com/             | 所有账户           | 无       | 20                                 |                                          |
| 豆瓣小组   | Douban     | https://www.douban.com/group/explore | 所有小组           | 无       | 36                                 | 不稳定，很可能需要登录（未测试登录功能） |

## 不支持的平台

| 平台中文名 | 平台英文名 | 平台网址                  | 原因                   | 备注             |
| ---------- | ---------- | ------------------------- | ---------------------- | ---------------- |
| B站        | Bilibili   | https://bilibili.com/     | 最大只能获取1000个粉丝 | 正序500、逆序500 |
| A站        | AcFun      | https://www.acfun.cn/     | 最大只能获取2000个粉丝 |                  |
| 微博       | Weibo      | https://weibo.com/        | 最大只能获取5000个粉丝 |                  |
| 喜马拉雅   | ximalaya   | https://www.ximalaya.com/ | 最大只能获取1980个粉丝 |                  |

## 待确定的平台

| 平台中文名 | 平台英文名 | 平台网址                 |      |
| ---------- | ---------- | ------------------------ | ---- |
| 油管       | YouTube    | https://www.youtube.com/ | 0.1% |

