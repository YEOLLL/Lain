from json import JSONDecodeError
from httpx import HTTPError


class NotAllowToGet(Exception):
    pass
