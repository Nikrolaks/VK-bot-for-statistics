# -*- coding: UTF-8 -*-
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType, Event
from vk_api.utils import get_random_id
import time
from collections import deque
from src.application.basic import Application


class UserRepresentative:
    def __init__(self):
        self.is_in_setting_group = False
        self.processing_groups = []


class VkBotForStatistic:
    """
    :param VkLongPoll self.requests_system: система для получения запросов пользователей.
    :param VKApiMethod self.group_representative: система для отправления сообщений пользователям.
    :param Application self.creating_statistic_system: система для сбора и обработки информации.
    :param bool self.is_work_in_progress: собирается ли сейчас информация о группах или нет.
    :param deque self.following_groups: стек групп, которые находятся на прослушке.
    :param deque self.groups_to_delete: стек групп, обработка которых закончена.
    :param int self.unit_measurement_of_listening: единица времени простоя прослушивания.
    :param bool self.is_need_work: этот флажок нужно установит в False, когда нужно завершить выполнение программы.
    :param list self.keys_to_start_talking_with_bot: ключевые фразы, чтобы начать общение с ботом.
    :param dict self.main_keyboard: главная клавиатура, как бы меню бота.
    :param dict self.set_group_to_process_keyboard: клавиатура, которая встраивается в сообщение с информацией о группе.
    :param dict self.show_processing_groups_keyboard: клавиатура для режима работы с обрабатываемыми группами.
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
        self.groups_to_delete = deque()
        self.unit_measurement_of_listening = measurement_waiting_intervals
        self.is_work_in_progress = False
        self.is_need_work = True
        self.keys_to_start_talking_with_bot = ['Начать', 'Привет', '!!!Слава Павлу Дурову!!!']
        self.iterations = 47  # Костыль пока Слава не исправит код
        with open('keyboards\\main_keyboard.json', 'r', encoding='utf-8') as f:
            self.main_keyboard = f.read()
        with open('keyboards\\set_group_to_process_keyboard.json', 'r', encoding='utf-8') as f:
            self.set_group_to_process_keyboard = f.read()
        with open('keyboards\\show_processing_groups_keyboard.json', 'r', encoding='utf-8') as f:
            self.show_processing_groups_keyboard = f.read()
        self.test_groups_to_add = deque()
        self.processing_users = {}
        self.test_processing_groups = deque()
        self.test_groups_to_delete = deque()

    def start_counting_statistic_loop(self) -> None:
        """
        Эта функция запускает бесконечный цикл прослушивания групп.
        """
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
                    self.groups_to_delete.append(group)
                else:
                    groups_to_continue_following.append(group)
            while self.groups_to_delete.__len__():
                # Удаляю группы из очереди прослушиваемых и
                # отправляю владельцам сообщения о сформированной статистике
                #   а) Вынимаю id пользователя, запросившего сбор статистики
                #   б) Получаю сформированный ответ системы по данным статистики
                #   в) Сообщаю пользователю о том, что сбор статистике окончен и
                #      высылаю ему отчет
                group = self.groups_to_delete.pop()
                user_id = group.request_owner_id
                listening_result = group.math_processor.calculate_effective_time()
                self.group_representative.messages.send(
                    user_id=user_id, random_id=get_random_id(),
                    message='Сбор статистики окончен.\nТебе стоит выкладывать посты в {0}'.format(listening_result))
            self.following_groups = deque(groups_to_continue_following)
            self.is_work_in_progress = False
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
        self.processing_users[request_owner_id].processing_groups.append(group.id)
        return True

    def process_new_messages(self, event: Event) -> bool:
        """
        Эта функция обрабатывает новые сообщения, пришедшие от пользователей.
        :param event: это информация как о полученном сообщении, так и о его отправителе.
        :return нужно ли завершить работу бота.
        """
        if event.text in self.keys_to_start_talking_with_bot:
            self.group_representative.messages.send(
                user_id=event.user_id,
                message='Привет, рад тебя видеть!',
                random_id=get_random_id(),
                keyboard=self.main_keyboard
            )
        elif event.text == 'Начать сбор статистики':
            if event.user_id not in self.processing_users:
                self.processing_users[event.user_id] = UserRepresentative()
            self.processing_users[event.user_id].is_in_setting_group = True
            self.group_representative.messages.send(
                user_id=event.user_id,
                message='Напиши короткое имя группы',
                random_id=get_random_id()
            )
        elif event.text == 'Получить список обрабатываемых групп':
            if event.user_id not in self.processing_users or not len(
                    self.processing_users[event.user_id].processing_groups):
                self.group_representative.messages.send(
                    user_id=event.user_id,
                    message='У тебя не обрабатываются группы',
                    random_id=get_random_id(),
                    keyboard=self.main_keyboard
                )
                return False
            message = ''
            counter = 0
            for group in self.processing_users[event.user_id].processing_groups:
                message += '{0}| {1}\n'.format(counter+1, group)
                counter += 1
            self.group_representative.messages.send(
                user_id=event.user_id,
                message=message,
                random_id=get_random_id(),
                keyboard=self.show_processing_groups_keyboard
            )
        elif event.user_id in self.processing_users and self.processing_users[event.user_id].is_in_setting_group:
            if event.text == 'Да' or event.text == 'Вернуться':
                self.group_representative.messages.send(
                    user_id=event.user_id,
                    message='Пойдем обратно в главное меню',
                    random_id=get_random_id(),
                    keyboard=self.main_keyboard
                )
                self.processing_users[event.user_id].is_in_setting_group = False
                return False
            group_short_name = event.text
            print(group_short_name)
            if len(group_short_name) == 0:
                self.processing_users[event.user_id].is_in_setting_group = False
                self.group_representative.messages.send(
                    user_id=event.user_id,
                    message='Ты неправильно отправил запрос',
                    random_id=get_random_id(),
                    keyboard=self.main_keyboard
                )
                return False
            if self.accept_request_to_listening(event.user_id, group_short_name):
                self.group_representative.messages.send(
                    user_id=event.user_id,
                    message='Запрос принят. Информация о статистике придет через примерно 47 секунд',
                    random_id=get_random_id(),
                    keyboard=self.set_group_to_process_keyboard
                )
            else:
                self.processing_users[event.user_id].is_in_setting_group = False
                self.group_representative.messages.send(
                    user_id=event.user_id,
                    message='Группы с таким коротким именем (или идентификатором) не существует\nПопробуй снова',
                    random_id = get_random_id(),
                    keyboard=self.main_keyboard
                )
        elif event.text == 'Вернуться':
            self.group_representative.messages.send(
                user_id=event.user_id,
                message='Пойдем обратно в главное меню',
                random_id=get_random_id(),
                keyboard=self.main_keyboard
            )
        elif event.text == 'red button' and event.user_id == 197313771:
            return True
        else:
            self.group_representative.messages.send(
                user_id=event.user_id,
                message='Я не знаю такой команды(((',
                random_id=get_random_id(),
                keyboard=self.main_keyboard
            )
        return False

    def start_processing_users_messages(self) -> None:
        """
        Эта функция подключается к серверу серверу Вконтакте и следит за действиями,
        происходящими в группе (по большей части за сообщениями, приходящими в чат с группой)
        """

        for event in self.requests_system.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text:
                    print(event)
                    if (self.process_new_messages(event)):
                        self.is_need_work = False
                        return
                else:
                    self.group_representative.messages.send(
                        user_id=event.user_id,
                        random_id=get_random_id(),
                        message='Я не знаю такой команды(((',
                        keyboard=self.main_keyboard
                    )