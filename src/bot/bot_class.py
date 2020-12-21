# -*- coding: UTF-8 -*-
import vk_api
import requests
from vk_api.longpoll import VkLongPoll, VkEventType, Event
from vk_api.utils import get_random_id
import time
import json
from collections import deque
from collections import defaultdict
from src.application.basic import Application, GroupDescription
from src.application.basic import GroupIsAlreadyDeleted, GroupNotFoundError,\
                                  GroupIsDeletedOrPrivate, GroupIsTooBig, GroupIsAlreadyProcessing


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
        self.is_in_viewing_processing_groups = False
        self.is_in_deleting_group = False
        self.is_in_getting_time_to_end = False
        self.setting_group = None
        self.processing_groups = []
        self.processed_group = []

    def set_group_to_process(self):
        if self.setting_group is not None:
            self.processing_groups.append(self.setting_group)
            self.clear_status()

    def clear_status(self):
        self.is_in_setting_group = False
        self.is_selecting_mode = False
        self.is_in_viewing_processing_groups = False
        self.is_in_deleting_group = False
        self.is_in_getting_time_to_end = False
        self.setting_group = None


class ProcessingGroup:
    """
    Это класс для обработки группы.
    :param self.request_owner_id: id пользователя, который запросил статистику группы.
    :param self.group: представление в памяти обрабатываемой группы.
    """
    def __init__(self, request_owner_id: int, group: GroupDescription, processing_power_mode):
        self.request_owner_id = request_owner_id
        self.group = group
        self.processing_power_mode = processing_power_mode
        self.marked_as_new = True
        self.marked_as_deleted = False
        self.marked_as_processing = False

    def __eq__(self, other):
        # c импортированием лажа, что делать - не знаю!!!!!
        # if not isinstance(other, ProcessingGroup):
        #    return False
        return self.group == other.group and self.request_owner_id == other.request_owner_id


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
        # Это секретный код доступа к моей группе
        bot_session = vk_api.VkApi(
            token='38848446351cbc8d520eaa7f6340f8533b8d06b0bae7db46bb61428d47571d7565cd642cc98202caccfd6')

        self.requests_system = VkLongPoll(bot_session)
        self.group_representative = bot_session.get_api()
        self.group_id = 200455000
        self.creating_statistic_system = Application()
        self.url_and_album_for_upload_photos =\
            self.group_representative.photos.getMessagesUploadServer(peer_id=0)

        self.following_groups = deque()
        self.processing_users = defaultdict(UserRepresentative)
        self.groups_to_start_process = deque()
        self.groups_to_delete = deque()
        self.exited_processes = deque()

        self.questions_and_reviews = []

        self.unit_measurement_of_listening = measurement_waiting_intervals
        self.is_work_in_progress = False
        self.is_need_work = True

        with open('src/bot/keyboards/main_keyboard.json', 'r', encoding='utf-8') as f:
            self.main_keyboard = f.read()
        with open('src/bot/keyboards/set_group_to_process_keyboard.json', 'r', encoding='utf-8') as f:
            self.set_group_to_process_keyboard = f.read()
        with open('src/bot/keyboards/show_processing_groups_keyboard.json', 'r', encoding='utf-8') as f:
            self.show_processing_groups_keyboard = f.read()
        with open('src/bot/keyboards/show_groups_with_complete_statistics_keyboard.json', 'r', encoding='utf-8') as f:
            self.show_groups_with_complete_statistics_keyboard = f.read()
        with open('src/bot/keyboards/show_group_complete_statistics.json', 'r', encoding='utf-8') as f:
            self.show_group_complete_statistics = f.read()

        self.keys_to_start_talking_with_bot = ['Начать', 'Привет', '!!!Слава Павлу Дурову!!!']

        # Фразы, которые обрабатываются в главном меню
        self.start_counting_statistic_phrase = 'Начать сбор статистики'
        self.get_processing_groups_phrase = 'Группы в процессе'
        self.get_complete_statistics_phrase = 'Готовые отчеты'
        self.get_help_phrase = 'Помощь'
        self.send_review_or_question_phrase = 'Отзыв'

        # Фразы, которые обрабатываются из меню обрабатываемых групп
        self.get_time_to_end_phrase = 'Сколько осталось до конца обработки'
        self.delete_group_from_processing_phrase = 'Убрать группу'

        # Фразы, которые обрабатываются из меню групп с готовыми статистиками
        self.get_statistics_list_phrase = 'Меню статистик'

        # Фразы, которые обрабатываются из меню статистик группы
        self.get_complete_statistic_phrase = 'Получить статистику'

        # Базовые командные фразы
        self.go_back_to_menu_phrase = 'Вернуться'

        # Админские командные фразы
        self.admin_exit_phrase = 'red button'
        self.admin_get_questions_and_reviews_phrase = 'get reviews'

        self.admin_ids = [197313771, 388775481]  # Соня Копейкина и Настя Хоробрых <--- верховный шаман нашего сервера

    def send_statistic_to_user(self, group_process: ProcessingGroup) -> None:
        """
        Эта функция формирует отчет о статистике и посылает его пользователю.
        :param group_process: пара пользователь - группа, где пользователь - человек, которому нужно
                              отправить отчет; группа - о ее статистике отчет формируется.
        """
        try:
            group_process_id = self.creating_statistic_system.create_string_user_id_group_id(
                user_id=group_process.request_owner_id,
                group_id=group_process.group.id
            )
            listening_result = self.creating_statistic_system.end_group_processing(group_process_id)
            # Потом нужно выделить в отдельную функцию
            response = requests.post(
                self.url_and_album_for_upload_photos['upload_url'],
                files={
                    "file1" : open(listening_result[1], 'rb')
                }
            ).json()
            result = self.group_representative.photos.saveMessagesPhoto(
                photo=response['photo'],
                server=response['server'],
                hash=response['hash']
            )
            # Потом нужно выделить в отдельную функцию
            self.group_representative.messages.send(
                user_id=group_process.request_owner_id,
                random_id=get_random_id(),
                message='(⊃｡•́‿•̀｡)⊃:｡･:*:･ﾟ’★,｡･:*:･ﾟ’☆\n'
                        'Cбор статистики окончен.\nТебе стоит выкладывать посты в {}'.format(listening_result[0]),
                attachments=[result['id']]
            )
        except GroupIsAlreadyDeleted:
            return

    def count_statistic(self) -> None:
        """
        Эта функция совершает один цикл обновления данных о группах.
        """
        groups_to_continue_following = []

        # Обновляем данные о группах
        self.is_work_in_progress = True
        while self.groups_to_start_process.__len__():
            group_process = self.groups_to_start_process.pop()
            self.creating_statistic_system.finish_initialization_of_group(
                user_group_ids=self.creating_statistic_system.create_string_user_id_group_id(
                    user_id=group_process.request_owner_id,
                    group_id=group_process.group.id
                ),
                processing_power_mode=group_process.processing_power_mode
            )
            self.following_groups.append(group_process)
        while self.following_groups.__len__():
            group_process = self.following_groups.pop()
            group_process_id = self.creating_statistic_system.create_string_user_id_group_id(
                user_id=group_process.request_owner_id,
                group_id=group_process.group.id
            )
            if self.creating_statistic_system.update_information_for_math_processor(group_process_id):
                self.groups_to_delete.append(group_process)
                self.send_statistic_to_user(group_process)
            else:
                groups_to_continue_following.append(group_process)

        # Удаляем невалидные процессы
        while self.groups_to_delete.__len__():
            group_process = self.groups_to_delete.pop()
            if group_process in groups_to_continue_following:
                groups_to_continue_following.remove(group_process)
            self.exited_processes.append(group_process)

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
            group = self.creating_statistic_system.start_initialization_of_group(group_short_name, request_owner_id)
            self.group_representative.messages.send(
                user_id=request_owner_id,
                random_id=get_random_id(),
                message='┬┴┬┴┤( ͡° ͜ʖ├┬┴┬┴\n'
                        'Я нашел вот такую группу:\n'
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
            self.processing_users[request_owner_id].clear_status()
            self.group_representative.messages.send(
                user_id=request_owner_id,
                random_id=get_random_id(),
                message='ヽ｀ヽ｀、ヽ(ノ＞＜)ノ ｀、ヽ｀☂ヽ｀\n'
                        'Группы с таким коротким именем нет(((',
                keyboard=self.main_keyboard
            )
        except GroupIsDeletedOrPrivate:
            self.processing_users[request_owner_id].clear_status()
            self.group_representative.messages.send(
                user_id=request_owner_id,
                random_id=get_random_id(),
                message='ヽ｀ヽ｀、ヽ(ノ＞＜)ノ ｀、ヽ｀☂ヽ｀\n'
                        'Я не могу собрать статистику этой группы. Скорее всего, она была удалена или заблокирована',
                keyboard=self.main_keyboard
            )
        except GroupIsTooBig:
            self.processing_users[request_owner_id].clear_status()
            self.group_representative.messages.send(
                user_id=request_owner_id,
                random_id=get_random_id(),
                message='ヽ｀ヽ｀、ヽ(ノ＞＜)ノ ｀、ヽ｀☂ヽ｀\n'
                        'Эта группа слишком тяжела для меня(( ',
                keyboard = self.main_keyboard
            )
        except GroupIsAlreadyProcessing:
            self.processing_users[request_owner_id].clear_status()
            self.group_representative.messages.send(
                user_id=request_owner_id,
                random_id=get_random_id(),
                message='ヽ｀ヽ｀、ヽ(ノ＞＜)ノ ｀、ヽ｀☂ヽ｀\n'
                        'Ты уже запустил обработку этой группы(( ',
                keyboard=self.main_keyboard

            )
        return True

    """
    Это большой модуль с функциями, отвечающими на различные сообщения пользователя.
    Каждая из них написана по следующему шаблону:
    Имя функции начинается с process_messages_
    Аргументы:
    :param event: информация как о пользователе, так и о его сообшении.
    :return: надо ли завершить работу программы после этого сообщения.
    """

    def process_messages_say_hello(self, event: Event) -> bool:
        user = self.group_representative.users.get(user_ids=[event.user_id])[0]
        user_name = user['first_name'] + ' ' + user['last_name']
        self.group_representative.messages.send(
            user_id=event.user_id,
            message='(＠＾◡＾) Привет, рад тебя видеть, {}!'.format(user_name),
            random_id=get_random_id(),
            keyboard=self.main_keyboard
        )
        return False

    def process_messages_go_back_to_menu(self, event: Event) -> bool:
        self.processing_users[event.user_id].clear_status()
        self.group_representative.messages.send(
            user_id=event.user_id,
            message='Σ(°△°|||)︴ Пойдем обратно в главное меню',
            random_id=get_random_id(),
            keyboard=self.main_keyboard
        )
        return False

    def process_messages_return_unknown_command(self, event: Event) -> bool:
        self.processing_users[event.user_id].clear_status()
        self.group_representative.messages.send(
            user_id=event.user_id,
            message='( : ౦ ‸ ౦ : )\n'
                    'Я не знаю такой команды(((',
            random_id=get_random_id(),
            keyboard=self.main_keyboard
        )
        return False

    def process_messages_return_exception(self, event: Event) -> bool:
        self.processing_users[event.user_id].clear_status()
        self.group_representative.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            message='Что-то ты мне не то прислал, брат. Попробуй снова︻デ═一',
            attachment=['photo197313771_457250813'],
            keyboard=self.main_keyboard
        )
        return False

    def process_messages_start_counting_statistic(self, event: Event) -> bool:
        self.processing_users[event.user_id].is_in_setting_group = True
        self.group_representative.messages.send(
            user_id=event.user_id,
            message='☆*:.｡.o(≧▽≦)o.｡.:*☆\n'
                    'Напиши короткое имя группы',
            random_id=get_random_id()
        )
        return False

    """
    Небольшой модуль, который нужен для функции process_messages_set_group_to_process 
    """

    def process_messages_accept_request(self, event: Event) -> bool:
        try:
            processing_power = int(event.text.split()[0])

            self.creating_statistic_system.check_selected_mode(processing_power)
            group_process = ProcessingGroup(event.user_id,
                                            self.processing_users[event.user_id].setting_group, processing_power)
            self.groups_to_start_process.append(group_process)

            self.processing_users[event.user_id].set_group_to_process()
            self.group_representative.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                message='ε=ε=ε=ε=┌(;￣▽￣)┘\n'
                        'Твой запрос принят',
                keyboard=self.main_keyboard
            )
        except ValueError:
            self.processing_users[event.user_id].clear_status()
            self.process_messages_return_exception(event)

        return False

    def process_messages_select_mode(self, event: Event) -> bool:
        processing_powers = self.creating_statistic_system.get_groups_processing_power()
        self.group_representative.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            message=processing_powers + '\n⊂(￣▽￣)⊃ Напиши номер интересующего тебя режима'
        )
        self.processing_users[event.user_id].is_selecting_mode = True
        return False

    """
    Небольшой модуль закончился.
    """

    def process_messages_set_group_to_process(self, event: Event) -> bool:
        # Если перст указующий уже пал на какую-то группу:
        if self.processing_users[event.user_id].is_selecting_mode:
            return self.process_messages_accept_request(event)
        elif event.text == 'Да' and self.processing_users[event.user_id].setting_group is not None:
            return self.process_messages_select_mode(event)

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
    Небольшой модуль, который нужен для функции process_messages_view_processing_group 
    """

    def process_messages_ask_for_group_number(self, event: Event) -> bool:
        self.group_representative.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            message='ᕕ( ᐛ )ᕗ Введи номер группы'
        )
        return False

    def process_messages_get_time_to_end(self, event: Event) -> bool:
        if not self.processing_users[event.user_id].is_in_getting_time_to_end:
            self.process_messages_ask_for_group_number(event)
            self.processing_users[event.user_id].is_in_getting_time_to_end = True
            return False

        try:
            selected_group_number = int(event.text.split()[0])
            if selected_group_number <= 0:
                raise IndexError

            selected_group = self.processing_users[event.user_id].processing_groups[selected_group_number - 1]
            group_processing_id = self.creating_statistic_system.create_string_user_id_group_id(
                user_id=event.user_id,
                group_id=selected_group.id
            )
            time_to_end = self.creating_statistic_system.find_time_to_finishing_process(group_processing_id)
            self.group_representative.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                message="౦０o ｡ (‾́。‾́ )y~~ Осталось " + str(time_to_end) + " часов",
                keyboard=self.main_keyboard
            )
        except ValueError:
            self.process_messages_return_exception(event)
        except IndexError:
            self.process_messages_return_exception(event)

        self.processing_users[event.user_id].clear_status()
        return False

    def process_messages_delete_group(self, event: Event) -> bool:
        if not self.processing_users[event.user_id].is_in_deleting_group:
            self.process_messages_ask_for_group_number(event)
            self.processing_users[event.user_id].is_in_deleting_group = True
            return False

        try:
            selected_group_number = int(event.text.split()[0])
            if selected_group_number <= 0:
                raise IndexError
            selected_group = self.processing_users[event.user_id].processing_groups[selected_group_number - 1]
            self.groups_to_delete.append(ProcessingGroup(event.user_id, selected_group, 0))
            self.group_representative.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                message='__〆(．．;) Группа будет удалена. Учти, отчет по собираемой статистике не придет'
                        ' (он придет только если сейчас заканчивается сбор информации о группе)',
                keyboard=self.main_keyboard
            )
        except ValueError:
            self.process_messages_return_exception(event)
        except IndexError:
            self.process_messages_return_exception(event)

        self.processing_users[event.user_id].clear_status()
        return False

    """
    Небольшой модуль закончился.
    """

    def process_messages_view_processing_group(self, event: Event) -> bool:
        if event.text == self.get_time_to_end_phrase or\
                self.processing_users[event.user_id].is_in_getting_time_to_end:
            return self.process_messages_get_time_to_end(event)
        elif event.text == self.delete_group_from_processing_phrase or\
                self.processing_users[event.user_id].is_in_deleting_group:
            return self.process_messages_delete_group(event)
        else:
            return self.process_messages_return_unknown_command(event)

    def process_messages_get_processing_groups_list(self, event: Event) -> bool:
        if not len(self.processing_users[event.user_id].processing_groups):
            self.group_representative.messages.send(
                user_id=event.user_id,
                message='╮(￣ω￣;)╭ У тебя не обрабатываются группы',
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
        self.processing_users[event.user_id].is_in_viewing_processing_groups = True
        return False

    def process_messages_get_help(self, event: Event):
        help_message_intro = 'Привет!\n' \
                             'Наш бот умеет считать статистику твоей группы (если она не слишком большая ;) )\n' \
                             'P.s ограничение по количеству участников группы - 10К\n' \
                             'В главном меню есть три кнопки. Давай разберу по полочкам:\n'
        help_message_first_button_first = '&#9997; Начать сбор статистики &#9997;\n' \
                                          'Для начала тебе предложат написать короткое имя твоей группы\n ' \
                                          'Это либо цифры, которые в ссылке идут после слова club:\n' \
                                          'Например, у такой ссылки\n' \
                                          '---> https://vk.com/club1 <---\n' \
                                          'короткое имя - 1\n' \
                                          'Либо короткая фраза:\n' \
                                          'Например, у такой ссылки\n' \
                                          '---> https://vk.com/memkn <---\n' \
                                          'короткое имя - memkn'
        help_message_first_button_second = '&#10067; Бот покажет тебе некоторую информацию о группе ' \
                                           'и спросит, ту ли группу ты имел в виду.\n' \
                                           'Подтверди или вернись в главное меню'
        help_message_first_button_third = '&#128195; Далее тебе будет предложено несколько режимов обработки\n' \
                                          'Просто выбери нужный.\n' \
                                          'На этом форма ввода группы для просчета статистики окончена.'
        help_message_second_button_first = '&#128269; Группы в процессе:\n' \
                                           'Бот покажет, какие группы ты поставил на подсчет статистики\n' \
                                           'С группами в этом списке можно проводить следующие действия:\n' \
                                           '&#9200; Узнать, сколько осталось до конца обработки\n' \
                                           '&#128683; Удалить группу из списка - учти, что при этом отчет ' \
                                           'о собранной статистике скорее всего не придет: ' \
                                           'он придет, только если сейчас заканчивается обработка группы'
        help_message_third_button_first = '&#128202; Готовые отчеты\n' \
                                          'Здесь хранятся уже собранные данные о группах\n' \
                                          'Сначала ты попадешь в меню обработанных групп\n' \
                                          'На клавиатуре будет кнопка: меню статистик. ' \
                                          'При нажатии на нее тебе предложат указать номер группы в списке\n' \
                                          'Далее будет выведено меню собранных статистик этой группы\n' \
                                          'Можно выбрать конкретный отчет и посмотреть подробную информацию по нему\n'
        help_message_epilogue = '&#9881; Если ты найдешь какие-нибудь ошибки ' \
                                'или если у тебя остались вопросы, то можешь воспользоваться кнопкой "Отзыв"\n' \
                                '&#128583; А за сим откланяюсь. Твои покорные слуги и постфактум создатели:\n' \
                                '&#128101; Копейкина Софья - -  бот\n' \
                                '&#128101; Хоробрых Анастасия - сервер\n' \
                                '&#128101; Безруков Вячеслав -  математика\n' \
                                '&#128139;&#128139;&#128139;&#128139;&#128139;&#128139;&#128139;&#128139;&#128139;'
        messages = [help_message_intro, help_message_first_button_first, help_message_first_button_second,
                    help_message_first_button_third, help_message_second_button_first, help_message_third_button_first,
                    help_message_epilogue]
        for message in messages:
            self.group_representative.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                message=message,
                keyboard=self.main_keyboard
            )
        return False

    def process_messages_send_question_or_review(self, event: Event) -> bool:
        user = self.group_representative.users.get(user_ids=[event.user_id])[0]
        user_information = user['first_name'] + ' ' + user['last_name'] + ' https://vk.com/id{}'.format(event.user_id)
        message = 'Отзыв от пользователя: {}\n' \
                  '(￣▽￣)/♫•*¨*•.¸¸♪\n'.format(user_information) + event.text
        self.questions_and_reviews.append(message)
        self.group_representative.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            message='(￣▽￣)/♫•*¨*•.¸¸♪ Твой отзыв был успешно отправлен',
            keyboard=self.main_keyboard
        )
        return False

    def process_messages_get_questions_and_reviews(self, event: Event) -> bool:
        for review in self.questions_and_reviews:
            self.group_representative.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                message=review,
                keyboard=self.main_keyboard
            )
        return False

    def process_messages_exit(self, event: Event) -> bool:
        message = 'Я ухожу, но обещаю вернуться вновь'.format(event.user_id)
        self.group_representative.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            message=message
        )
        return True

    """
    Большой модуль закончился.
    """

    def delete_exited_processes(self):
        """
        Эта функция вызывается потоком обслуживания запросов пользователей для того,
        чтобы очистить данные об обработанных группах.
        """
        while self.exited_processes.__len__():
            processed_group = self.exited_processes.pop()
            if processed_group.group in\
                    self.processing_users[processed_group.request_owner_id].processing_groups:
                self.processing_users[processed_group.request_owner_id].processing_groups.remove(processed_group.group)

    def process_new_messages(self, event: Event) -> bool:
        """
        Эта функция обрабатывает новые сообщения, пришедшие от пользователей.
        :param event: это информация как о полученном сообщении, так и о его отправителе.
        :return нужно ли завершить работу бота.
        """
        if event.text == self.go_back_to_menu_phrase:
            return self.process_messages_go_back_to_menu(event)
        elif event.text == self.start_counting_statistic_phrase:
            return self.process_messages_start_counting_statistic(event)
        elif event.text == self.get_processing_groups_phrase:
            return self.process_messages_get_processing_groups_list(event)
        elif self.processing_users[event.user_id].is_in_setting_group:
            return self.process_messages_set_group_to_process(event)
        elif self.processing_users[event.user_id].is_in_viewing_processing_groups:
            return self.process_messages_view_processing_group(event)
        elif event.text in self.keys_to_start_talking_with_bot:
            return self.process_messages_say_hello(event)
        elif event.text == self.get_help_phrase:
            return self.process_messages_get_help(event)
        elif event.text == self.send_review_or_question_phrase:
            return self.process_messages_send_question_or_review(event)
        elif event.text == self.admin_get_questions_and_reviews_phrase and event.user_id in self.admin_ids:
            return self.process_messages_get_questions_and_reviews(event)
        elif event.text == self.admin_exit_phrase and event.user_id in self.admin_ids:
            return self.process_messages_exit(event)
        else:
            return self.process_messages_return_unknown_command(event)

    def start_processing_users_messages(self) -> None:
        """
        Эта функция подключается к серверу серверу Вконтакте и следит за действиями,
        происходящими в группе (по большей части за сообщениями, приходящими в чат с группой)
        """
        try:
            for event in self.requests_system.listen():
                self.delete_exited_processes()
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if event.text:
                        print(event)
                        if self.process_new_messages(event):
                            self.is_need_work = False
                            return
                    else:
                        self.process_messages_return_unknown_command(event)
        except requests.exceptions.ReadTimeout:
            print('Переподключение к серверам ВК')
            time.sleep(3)
