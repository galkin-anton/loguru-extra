from loguru_extra import logger, add_file_logger

add_file_logger("log.log")

if __name__ == '__main__':
    logger.info("START")
