from loguru_extra import logger, add_file_logger, traceable

add_file_logger("log.log")


@traceable
def main():
    logger.info("START")


if __name__ == '__main__':
    logger.info("pp")
    main()
