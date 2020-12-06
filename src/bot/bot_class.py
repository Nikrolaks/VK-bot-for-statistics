# -*- coding: UTF-8 -*-
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType, Event
from vk_api.utils import get_random_id
import time, re
from collections import deque
from src.application.basic import Application


class VkBotForStatistic:
    """
    :param VkLongPoll self.requests_system: система для получения запросов пользователей.
    :param VKApiMethod self.group_representative: система для отправления сообщений пользователям.
    :param Application self.creating_statistic_system: система для сбора и обработки информации.
    :param bool self.is_work_in_progress: собирается ли сейчас информация о группах или нет.
    :param deque self.following_groups: стек групп, которые находятся на прослушке.
    :param int self.unit_measurement_of_listening: единица времени простоя прослушивания.
    :param bool self.is_need_work: этот флажок нужно установит в False, когда нужно завершить выполнение программы.
    :param list self.keys_to_start_talking_with_bot: ключевые фразы, чтобы начать общение с ботом.
    """
    def __init__(self, measurement_waiting_intervals: int) -> None:
        """
        :param measurement_waiting_intervals: через какие промежутки времени нужно собирать информацию о группах.
        """
        bot_session = vk_api.VkApi(
            token='38848446351cbc8d520eaa7f6340f8533b8d06b0bae7db46bb61428d47571d7565cd642cc98202caccfd6')
        # Это секретный код доступа к моей группе
        self.requests_system = VkLongPoll(bot_session)
        self.group_representative = bot_session.get_api()
        self.creating_statistic_system = Application()
        self.following_groups = deque()
        self.unit_measurement_of_listening = measurement_waiting_intervals
        self.is_work_in_progress = False
        self.is_need_work = True
        self.keys_to_start_talking_with_bot = ['HELP', 'Привет', '!!!Слава Павлу Дурову!!!']
        self.iterations = 47  # Костыль пока Слава не исправит код

    def start_counting_statistic_loop(self) -> None:
        """
        Эта функция запускает бесконечный цикл прослушивания групп.
        """
        groups_to_delete = []
        groups_to_continue_following = []
        while self.is_need_work:
            self.is_work_in_progress = True
            while self.following_groups.__len__():
                # Обработка группы
                #   а) Обновляю информацию о прошедшем времени прослушивания (в счетах)
                #   б) Обновляю информацию о ее членах
                #   в) Если прослушивание завершено, добавляю группу в список исключаемых
                group = self.following_groups.pop()
                group.done_iterations += 1
                print('{0}| До конца исследования осталось {1}'.format(group.id, 47-group.done_iterations))
                self.creating_statistic_system.update_information_for_math_processor(group)
                if group.done_iterations == group.count_of_iterations:
                    groups_to_delete.append(group)
                else:
                    groups_to_continue_following.append(group)
            for group in groups_to_delete:
                # Удаляю группы из очереди прослушиваемых и
                # отправляю владельцам сообщения о сформированной статистике
                #   а) Вынимаю id пользователя, запросившего сбор статистики
                #   б) Получаю сформированный ответ системы по данным статистики
                #   в) Сообщаю пользователю о том, что сбор статистике окончен и
                #      высылаю ему отчет
                user_id = group.request_owner_id
                listening_result = group.math_processor.calculate_effective_time()
                self.group_representative.messages.send(
                    user_id=user_id, random_id=get_random_id(),
                    message='Сбор статистики окончен.\nТебе стоит выкладывать посты в {0}'.format(listening_result))
            self.following_groups = deque(groups_to_continue_following)
            self.is_work_in_progress = False
            groups_to_delete.clear()
            groups_to_continue_following.clear()
            time.sleep(self.unit_measurement_of_listening)

    def accept_request_to_listening(self, request_owner_id: int, group_short_name: str) -> bool:
        """
        Эта функция принимает запрос пользователя на сбор статистики.
        :param request_owner_id: id пользователя, пославшего запрос на обработку статистики группы.
        :param group_short_name: короткое имя группы.
        :return был ли принят запрос.
        """
        group = self.creating_statistic_system.find_group_by_short_name(request_owner_id,
                                                                        group_short_name,
                                                                        self.iterations)
        if group is None:
            return False
        while self.is_work_in_progress:
            # жду пока не завершится процесс обработки групп
            pass
        self.following_groups.append(group)
        return True

    def process_new_messages(self, event: Event) -> bool:
        """
        Эта функция обрабатывает новые сообщения, пришедшие от пользователей.
        :param event: это информация как о полученном сообщении, так и о его отправителе.
        :return нужно ли завершить работу бота.
        """
        if event.text in self.keys_to_start_talking_with_bot:
            self.group_representative.messages.send(
                user_id = event.user_id,
                message='Привет, рад тебя видеть!',
                random_id = get_random_id()
            )
        elif 'статистика:' in event.text:
            group_short_name = event.text[len('статистика:'):].split()
            print(group_short_name)
            if len(group_short_name) == 0:
                self.group_representative.messages.send(
                    user_id=event.user_id,
                    message='Ты неправильно отправил запрос\nПопробуй снова в формате:\n'
                            '"статистика: __group__short__name__"',
                    random_id=get_random_id()
                )
                return False
            group_short_name = group_short_name[0]
            if self.accept_request_to_listening(event.user_id, group_short_name):
                self.group_representative.messages.send(
                    user_id=event.user_id,
                    message='Запрос принят. Информация о статистике придет через примерно 47 секунд',
                    random_id=get_random_id()
                )
            else:
                self.group_representative.messages.send(
                    user_id=event.user_id,
                    message='Группы с таким коротким именем (или идентификатором) не существует\nПопробуй снова',
                    random_id = get_random_id()
                )
        elif event.text == 'red button' and event.user_id == 197313771:
            return True
        return False

    def start_processing_users_messages(self) -> None:
        """
        Эта функция подключается к серверу серверу Вконтакте и следит за действиями,
        происходящими в группе (по большей части за сообщениями, приходящими в чат с группой)
        """

        for event in self.requests_system.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
                if (self.process_new_messages(event)):
                    self.is_need_work = False
                    return