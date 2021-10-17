from json import JSONDecodeError
from httpx import HTTPError


class NotAllowToGet(Exception):
    pass


class UserNotFound(Exception):
    pass


class HttpCodeError(Exception):
    pass


class NeedLogin(Exception):
    pass


class LoginError(Exception):
    pass
