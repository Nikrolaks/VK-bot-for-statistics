# -*- coding: UTF-8 -*-
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType, Event
from vk_api.utils import get_random_id
import requests
import time

class VkBotForStatistic:
    """
    :param VkLongPoll self.requests_system: система для получения запросов пользователей.
    :param VKApiMethod self.group_representative: система для отправления сообщений пользователям.
    :param bool self.is_work_in_progress: собирается ли сейчас информация о группах или нет.
    :param list self.following_groups: очередь групп, которые находятся на прослушке.
    :param int self.unit_measurement_of_listening: единица времени простоя прослушивания.
    :param bool self.is_need_work: этот флажок нужно установит в False, когда нужно завершить выполнение программы
    :param list self.keys_to_start_talking_with_bot: ключевые фразы, чтобы начать общение с ботом
    """
    def __init__(self, measurement_waiting_intervals: int) -> None:
        """
        :param measurement_waiting_intervals: через какие промежутки времени нужно собирать информацию о группах.
        """
        # Это секретный код доступа к моей группе
        bot_session = vk_api.VkApi(
            token='38848446351cbc8d520eaa7f6340f8533b8d06b0bae7db46bb61428d47571d7565cd642cc98202caccfd6')
        self.requests_system = VkLongPoll(bot_session)
        self.group_representative = bot_session.get_api()
        self.following_groups = []
        self.unit_measurement_of_listening = measurement_waiting_intervals
        self.is_work_in_progress = False
        self.is_need_work = True
        self.keys_to_start_talking_with_bot = ['HELP', 'Привет', '!!!Слава Павлу Дурову!!!']

    def start_counting_statistic_loop(self) -> None:
        """
        Эта функция запускает бесконечный цикл прослушивания групп.
        """
        print('You are in function start_counting_statistic_loop!!!')
        groups_to_delete = []
        while self.is_need_work:
            self.is_work_in_progress = True
            for group in self.following_groups:
                # Обработка группы
                #   а) Обновляю информацию о ее членах
                #   б) Обновляю информацию о прошедшем времени прослушивания (в счетах)
                #   в) Если прослушивание завершено, добавляю группу в список исключаемых
                pass
            for group in groups_to_delete:
                # Удаляю группы из очереди прослушиваемых и
                # отправляю владельцам сообщения о сформированной статистике
                #   а) Вынимаю id пользователя, запросившего сбор статистики
                #   б) Получаю сформированный ответ системы по данным статистики
                #   в) Сообщаю пользователю о том, что сбор статистике окончен и
                #      высылаю ему отчет
                #   г) Удаляю группу из списка прослушиваемых
                self.following_groups.remove(group)
            self.is_work_in_progress = False
            time.sleep(self.unit_measurement_of_listening)

    def accept_request_to_listening(self, group_short_name: str) -> None:
        """
        Эта функция принимает запрос пользователя на сбор статистики.
        :param group_short_name: короткое имя группы.
        """
        # 1) Создание структуры прослушиваемой группы по ее короткому имени
        # 2) Добавление ее в очередь прослушиваемых
        group = None # здесь будет вызываться функция Насти
        while self.is_work_in_progress:
            # жду пока не завершится процесс обработки групп
            pass
        self.following_groups.append(group)

    def process_new_messages(self, event: Event) -> bool:
        """
        Эта функция обрабатывает новые сообщения, пришедшие от пользователей.
        :param event: это информация как о полученном сообщении, так и о его отправителе.
        :return нужно ли завершить работу бота.
        """
        if event.text in self.keys_to_start_talking_with_bot:
            self.group_representative.messages.send(user_id = event.user_id,
                                           message='Привет, рад тебя видеть!',
                                           random_id = get_random_id())
        elif event.text == 'red button' and event.user_id == 197313771:
            return True
        return False

    def start_processing_users_messages(self) -> None:
        """
        Эта функция подключается к серверу серверу Вконтакте и следит за действиями,
        происходящими в группе (по большей части за сообщениями, приходящими в чат с группой)
        """

        for event in self.requests_system.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.text:
                if (self.process_new_messages(event)):
                    self.is_need_work = False
                    return