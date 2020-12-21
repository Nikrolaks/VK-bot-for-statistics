# -*- coding: UTF-8 -*-
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
        print('testestest1')
        self.bot.start_counting_statistic()
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
        print('testestest2')
        self.bot.start_processing_users_messages()
        print('this is the end of running thread for accept orders')


if __name__ == '__main__':
    super_puper_bot = VkBotForStatistic(1)
    thread1 = ThreadAcceptOrders(super_puper_bot)
    thread2 = ThreadListeningChannel(super_puper_bot)
    thread1.start()
    thread2.start()
