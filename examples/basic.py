from loguru_extra import add_file_logger, logger, setup, trace, traceable

setup()
add_file_logger("log.log", rotation="10 MB")


@traceable
def handle_request():
    logger.info("handling request")


if __name__ == '__main__':
    logger.info("outside of a trace")
    handle_request()
    handle_request()
    with trace("external-request-id"):
        logger.info("trace id from an incoming header")
