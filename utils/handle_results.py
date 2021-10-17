from utils.log import logger
from utils.exception import *


def handle_results(results, account, msg):
    has_error = False
    error_account = []
    return_results = []
    for index, value in enumerate(results):
        if isinstance(value, KeyError):
            logger.error('{}错误，KeyError：{}，Account：{}', msg, value, account[index])
            has_error = True
            error_account.append(account[index])

        elif isinstance(value, HTTPError):
            logger.error('{}错误，请求失败：{}，Account：{}', msg, value, account[index])
            has_error = True
            error_account.append(account[index])

        elif isinstance(value, JSONDecodeError):
            logger.error('{}错误，Json解析失败：{}，Account：{}', msg, value, account[index])
            has_error = True
            error_account.append(account[index])

        elif isinstance(value, NotAllowToGet):
            logger.error('{}错误，由于该用户隐私设置，粉丝列表不可见，Account：{}', msg, account[index])
            has_error = True
            error_account.append(account[index])

        elif isinstance(value, UserNotFound):
            logger.error('{}错误，未查找到该用户，Account：{}', msg, account[index])
            has_error = True
            error_account.append(account[index])

        elif isinstance(value, HttpCodeError):
            logger.error('{}错误，HTTP状态码异常：{}，Account：{}', msg, value, account[index])
            has_error = True
            error_account.append(account[index])

        else:
            return_results.append(value)

    if has_error:
        logger.warning(
            '{}完毕，共 {} 个账户，其中 {} 个账户发生了错误，ErrorAccount：{}',
            msg, len(account), len(error_account), error_account
        )
    else:
        logger.success(
            '{}完毕，共 {} 个账户',
            msg, len(account)
        )

    return return_results
