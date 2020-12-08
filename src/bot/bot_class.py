# -*- coding: UTF-8 -*-
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType, Event
from vk_api.utils import get_random_id
import time
from collections import deque
from collections import defaultdict
from src.application.basic import Application, GroupNotFoundError, GroupDescription


class UserRepresentative:
    """
    Это класс для представления юзеров в памяти.
    :param bool self.is_in_setting_group: флажок, который говорит о том,
                                          выбирает ли пользователь группу для обработки в данный момент.
    :param list self.processing_groups: список групп, которые отслеживаются по просьбе пользователя.
    """
    def __init__(self):
        self.is_in_setting_group = False
        self.is_selecting_mode = False
        self.setting_group = None
        self.processing_groups = []

    def set_group_to_process(self):
        if self.setting_group is not None:
            self.processing_groups.append(self.setting_group)
            self.revert_changes()

    def revert_changes(self):
        self.is_in_setting_group = False
        self.is_selecting_mode = False
        self.setting_group = None


class ProcessingGroup:
    """
    Это класс для обработки группы.
    :param self.request_owner_id: id пользователя, который запросил статистику группы.
    :param self.group_id: id обрабатываемой группы.
    """
    def __init__(self, request_owner_id: int, group: GroupDescription):
        self.request_owner_id = request_owner_id
        self.group = group


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
        self.processing_users = defaultdict(UserRepresentative)
        self.groups_to_start_process = deque()
        self.exited_processes = deque()
        self.unit_measurement_of_listening = measurement_waiting_intervals
        self.is_work_in_progress = False
        self.is_need_work = True

        self.keys_to_start_talking_with_bot = ['Начать', 'Привет', '!!!Слава Павлу Дурову!!!']
        with open('keyboards\\main_keyboard.json', 'r', encoding='utf-8') as f:
            self.main_keyboard = f.read()
        with open('keyboards\\set_group_to_process_keyboard.json', 'r', encoding='utf-8') as f:
            self.set_group_to_process_keyboard = f.read()
        with open('keyboards\\show_processing_groups_keyboard.json', 'r', encoding='utf-8') as f:
            self.show_processing_groups_keyboard = f.read()

    def delete_exited_processes(self):
        """
        Эта функция вызывается потоком обслуживания запросов пользователей для того,
        чтобы очистить данные об обработанных группах.
        """
        while self.exited_processes.__len__():
            processed_group = self.exited_processes.pop()
            self.processing_users[processed_group.request_owner_id].processing_groups.remove(processed_group.group)

    def send_statistic_to_user(self, group: ProcessingGroup) -> None:
        """
        :param group: пара пользователь - группа, где пользователь - человек, которому нужно
        отправить отчет; группа - о ее статистике отчет формируется.
        """
        # Генерирование отчетов в недалеком будущем, но пока так.
        # listening_result = self.creating_statistic_system.generate_report(group.group_id)
        self.group_representative.messages.send(
            user_id=group.request_owner_id,
            random_id=get_random_id(),
            message='Сбор статистики окончен.\nЯ пока не умею выдавать отчеты, но хотя бы могу сказать, '
                    'что я успешно проследил за твоей группой:333',
            attachment=['photo197313771_457250812'],
            keyboard=self.main_keyboard
        )
        self.exited_processes.append(group)

    def count_statistic(self) -> None:
        """
        Эта функция совершает один цикл обновления данных о группах.
        """
        groups_to_delete = deque()
        groups_to_continue_following = []

        # Обновляем данные о группах
        self.is_work_in_progress = True
        while self.following_groups.__len__():
            group_process = self.following_groups.pop()
            if self.creating_statistic_system.update_information_for_math_processor(group_process.group.group_id):
                groups_to_delete.append(group_process)
            else:
                groups_to_continue_following.append(group_process)

        # Удаляем невалидные процессы и формируем отчеты
        while groups_to_delete.__len__():
            group_process = groups_to_delete.pop()
            self.send_statistic_to_user(group_process)

        self.following_groups = deque(groups_to_continue_following)
        self.is_work_in_progress = False
        groups_to_continue_following.clear()

    def start_counting_statistic(self) -> None:
        """
        Эта функция запускает бесконечный цикл прослушивания групп.
        """
        while self.is_need_work:
            self.count_statistic()
            time.sleep(self.unit_measurement_of_listening)

    def find_out_if_group_is_correct(self, request_owner_id: int, group_short_name: str) -> bool:
        """
        Эта функция получает данные о запрашиваемой группе и спрашивает у пользователя, та ли это группа.
        Если данные о группе получить невозможно (ее не существует), то говорит об этом пользователю.
        :param request_owner_id: id пользователя, пославшего запрос на обработку статистики группы.
        :param group_short_name: короткое имя группы.
        :return: корректное ли имя группы было передано.
        """
        try:
            group = self.creating_statistic_system.get_group_information_by_short_name(group_short_name)
            self.group_representative.messages.send(
                user_id=request_owner_id,
                random_id=get_random_id(),
                message='Я нашел вот такую группу:\n'
                        'Имя: {0}\n'
                        'Ссылка: {1}\n'
                        'Это та самая группа, статистику для которой ты хотел бы получить?'.format(
                    group.name,
                    group.url
                ),
                keyboard=self.set_group_to_process_keyboard
            )
            self.processing_users[request_owner_id].setting_group = group
        except GroupNotFoundError:
            self.processing_users[request_owner_id].is_in_setting_group = False
            self.group_representative.messages.send(
                user_id=request_owner_id,
                random_id=get_random_id(),
                message='Группы с таким коротким именем нет(((',
                keyboard=self.main_keyboard
            )
        return True

    """
    Это большой модуль с функциями, отвечающими на различные сообщения пользователя.
    Каждая из них написана по следующему шаблону:
    :param event: информация как о пользователе, так и о его сообшении.
    :return: надо ли завершить работу программы после этого сообщения.
    """

    def process_messages_say_hello(self, event: Event) -> bool:
        self.group_representative.messages.send(
            user_id=event.user_id,
            message='Привет, рад тебя видеть!',
            random_id=get_random_id(),
            keyboard=self.main_keyboard
        )
        return False

    def process_messages_start_counting_statistic(self, event: Event) -> bool:
        self.processing_users[event.user_id].is_in_setting_group = True
        self.group_representative.messages.send(
            user_id=event.user_id,
            message='Напиши короткое имя группы',
            random_id=get_random_id()
        )
        return False

    def process_messages_get_information_about_groups(self, event: Event) -> bool:
        if not len(self.processing_users[event.user_id].processing_groups):
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
            message += '{0} | {1}\n'.format(counter + 1, group.name)
            counter += 1
        self.group_representative.messages.send(
            user_id=event.user_id,
            message=message,
            random_id=get_random_id(),
            keyboard=self.show_processing_groups_keyboard
        )
        return False

    """
    Небольшой модуль, который нужен для функции process_messages_set_group_to_process 
    """

    def process_messages_accept_request(self, event: Event) -> bool:
        try:
            processing_power = int(event.text.split()[0])
            self.creating_statistic_system.add_group_to_process(
                self.processing_users[event.user_id].setting_group.group_id,
                processing_power
            )
            self.following_groups.append(ProcessingGroup(event.user_id,
                                                         self.processing_users[event.user_id].setting_group))
            self.processing_users[event.user_id].set_group_to_process()
            self.group_representative.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                message='Твой запрос принят',
                keyboard=self.main_keyboard
            )
        except ValueError:
            self.processing_users[event.user_id].revert_changes()
            self.group_representative.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                message='Что-то ты мне не то прислал, брат. Попробуй снова',
                attachment=['photo197313771_457250813'],
                keyboard=self.main_keyboard
            )
        return False

    def process_messages_select_mode(self, event: Event) -> bool:
        processing_powers = self.creating_statistic_system.get_groups_processing_power()
        self.group_representative.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            message=processing_powers + '\nНапиши номер интересующего тебя режима'
        )
        self.processing_users[event.user_id].is_selecting_mode = True
        return False

    """
    Небольшой модуль закончился.
    """

    def process_messages_set_group_to_process(self, event: Event) -> bool:
        if self.processing_users[event.user_id].is_selecting_mode:
            return self.process_messages_accept_request(event)
        elif event.text == 'Да' and self.processing_users[event.user_id].setting_group is not None:
            return self.process_messages_select_mode(event)
        elif event.text == 'Вернуться':
            self.group_representative.messages.send(
                user_id=event.user_id,
                message='Пойдем обратно в главное меню',
                random_id=get_random_id(),
                keyboard=self.main_keyboard
            )
            self.processing_users[event.user_id].revert_changes()
            return False

        group_short_name = event.text
        print(group_short_name)
        if len(group_short_name) == 0:
            self.processing_users[event.user_id].is_in_setting_group = False
            self.group_representative.messages.send(
                user_id=event.user_id,
                message='Ты ничего не отправил :| :| :|',
                random_id=get_random_id(),
                keyboard=self.main_keyboard
            )
            return False
        self.find_out_if_group_is_correct(event.user_id, group_short_name)
        return False

    """
    Большой модуль закончился.
    """

    def process_new_messages(self, event: Event) -> bool:
        """
        Эта функция обрабатывает новые сообщения, пришедшие от пользователей.
        :param event: это информация как о полученном сообщении, так и о его отправителе.
        :return нужно ли завершить работу бота.
        """
        if event.text in self.keys_to_start_talking_with_bot:
            return self.process_messages_say_hello(event)
        elif event.text == 'Начать сбор статистики':
            return self.process_messages_start_counting_statistic(event)
        elif event.text == 'Получить список обрабатываемых групп':
            return self.process_messages_get_information_about_groups(event)
        elif self.processing_users[event.user_id].is_in_setting_group:
            return self.process_messages_set_group_to_process(event)
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
            self.delete_exited_processes()
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text:
                    print(event)
                    if self.process_new_messages(event):
                        self.is_need_work = False
                        return
                else:
                    self.group_representative.messages.send(
                        user_id=event.user_id,
                        random_id=get_random_id(),
                        message='Я не знаю такой команды(((',
                        keyboard=self.main_keyboard
                    )
