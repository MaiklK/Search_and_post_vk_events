import logging

# включение логирования
logger = logging.getLogger("Search_and_post_vk_events")
logger.setLevel(logging.ERROR)
fl = logging.FileHandler("log.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fl.setFormatter(formatter)
logger.addHandler(fl)


def log(message):
    """Пишет ошибку в лог с датой

    :param message: сообщение записываемое в лог
    """
    logger.error(message)
