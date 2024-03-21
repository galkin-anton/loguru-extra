import sys

from loguru import logger

FILE_NAME = None
FORMAT = ("<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
          "<r>|</r> <le><b>{extra}</b></le> "
          "<r>|</r> {thread.id} <r>|</r> <y><b>{thread.name: ^12}</b></y> "
          "<r>|</r> <level>{level: <8}</level> "
          "<r>|</r> <cyan>{name}</cyan><r>:</r><cyan>{function}</cyan><r>:</r><cyan>{line}</cyan> "
          "<r>-</r> <level>{message}</level>")

logger.remove()
logger.add(sys.stdout, level="INFO", format=FORMAT,
           filter=None, colorize=None, serialize=False, backtrace=True, diagnose=True, enqueue=False, context=None, catch=True)


def add_file_logger(file_name: str) -> None:
    logger.add(file_name, level="INFO", format=FORMAT,
               filter=None, colorize=None, serialize=False, backtrace=True, diagnose=True, enqueue=False, context=None, catch=True)
