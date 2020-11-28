# -*- coding: UTF-8 -*-
import time
from threading import Thread
from src.bot.bot_class import VkBotForStatistic


class ThreadListeningChannel(Thread):
    def __init__(self, bot: VkBotForStatistic):
        """
        :param bot: это бот, процессы которого мы запускаем.
        """
        Thread.__init__(self)
        self.bot = bot

    def run(self) -> None:
        """
        Эта функция запускает цикл наблюдения за группами.
        """
        self.bot.start_counting_statistic_loop()
        print('this is the end of running thread for listening channel')


class ThreadAcceptOrders(Thread):
    def __init__(self, bot: VkBotForStatistic):
        """
        :param bot: это бот, процессы которого мы запускаем.
        """
        Thread.__init__(self)
        self.bot = bot

    def run(self):
        """
        Эта функция запускает цикл обработки сообщений пользователей.
        """
        self.bot.start_processing_users_messages()
        print('this is the end of running thread for accept orders')


if __name__ == '__main__':
    super_puper_bot = VkBotForStatistic(20)
    thread1 = ThreadAcceptOrders(super_puper_bot)
    thread2 = ThreadListeningChannel(super_puper_bot)
    thread1.start()
    thread2.start()