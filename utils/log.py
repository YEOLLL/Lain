from loguru import logger
from sys import stdout


# 日志
logger.remove()
logger.add(
    stdout,
    colorize=True,
    # format="<level>[{level}]</level> [{time:YYYY-MM-DD HH:mm:ss}] [{extra[module]}] <level>{message}</level>"
    format="<level>[{level}]</level> [{time:YYYY-MM-DD HH:mm:ss}] [{module}] <level>{message}</level>"
)