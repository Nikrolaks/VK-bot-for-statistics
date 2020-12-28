# -*- coding: UTF-8 -*-
import vk_api
import time
import math
from src.math.math_diagrams import ContentTimeComputer


class GroupNotFoundError(Exception):
    pass


class GroupIsAlreadyDeleted(Exception):
    pass


class GroupIsDeletedOrPrivate(Exception):
    pass


class GroupIsAlreadyProcessing(Exception):
    pass


class GroupIsTooBig(Exception):
    pass


class GroupDescription:
    """
    :param
        :param group_id: id группы.
        :param url: ссылка на группу.
        :param name: название группы
    """
    def __init__(self, group_id: int, url: str, name: str):
        self.id = group_id
        self.url = url
        self.name = name


class Group:
    """
    Класс для хранения обрабатываемых данных группы.
    :param self.group_id: id группы.
    :param self.time_of_beginning: время начала процессинга.
    :param self.math_processor: созданный для этой группы свой объект класса ContentTimeComputer.
    :param self.done_iterations: сколько раз собиралась информация об участниках онлайн.
    :param processing_power: выбранный режим работы (количество временных промежутков сбора статистики)
    :param self.were_online: список id пользователей, которые были онлайн в момент предпоследнего сбора данных.
    """
    def __init__(self, processing_power: int):
        time_of_beginning = math.ceil(time.time())
        self.time_of_beginning = time_of_beginning
        self.math_processor = ContentTimeComputer(100, processing_power, time_of_beginning)
        self.done_iterations = 0
        self.processing_power = processing_power
        self.were_online = []


class Application:
    """
    Класс, реализующий поиск информации о группах и обработку результатов поиска.
    :param self.application_session: механизм получения сведений о группе от Вконтакте.
    :param self.list_processing_power: список возможных режимов(сколько раз проводить сбор статистики)
    :param self.groups_map: словарь, где по ключу строке user_group_ids хранится свой объект класса Group
    """

    def __init__(self):
        # создаёт сессию, авторизуется с помощью оффлайн-токена приложения
        session = vk_api.VkApi(token='c15b89d7c15b89d7c15b89d75ac12e9b1ccc15bc15b89d79ee1cf4a5977bbe4ff8f6761')
        self.application_session = session.get_api()
        self.list_processing_power = [335]
        self.groups_map = {}

    def get_group_information_by_short_name(self, short_name):
        """
        создаёт объект класса Group description, если группа найдена
        :param short_name: короткое имя или id группы
        :return: объект класса Group description, если верно дано id, или возбуждает исключение
        GroupNotFoundError
        """
        try:
            group = self.application_session.groups.getById(group_id=short_name)[0]
            id = group['id']
            name = group['name']
            url = 'https://vk.com/club' + str(id)
            print(name)
            return GroupDescription(id, url, name)
        except:
            raise GroupNotFoundError()

    def find_time_to_finishing_process(self, user_group_ids):
        """
        позволяет узнать количество часов до конца обработки с погрешностью в полчаса
        :param user_group_ids: строка с id пользователя и группы, которая обрабатывается
        :return: количество часов до конца обработки группы
        """
        remained_iterations = self.groups_map[user_group_ids].processing_power - self.groups_map[user_group_ids].done_iterations
        return remained_iterations/2

    def create_string_user_id_group_id(self, user_id, group_id):
        return str(user_id) + "_" + str(group_id)

    def start_initialization_of_group(self, short_name, request_owner_id):
        """
        отлавливает большинство ошибок на стадии инициализации группы(удалённые, частные, несущетсвующие или
        слишком большие группы(слишком большими для обработки считаем группы, где больше 10000 человек)
        :param short_name: короткое имя или id группы
        :param request_owner_id: id пользователя, сделавшего запрос
        :return: объект класса GroupDescription, если группа корректна
        """
        group = self.get_group_information_by_short_name(short_name)
        try:
            members = self.application_session.groups.getMembers(group_id=short_name)
        except:
            raise GroupIsDeletedOrPrivate()
        if members['count'] > 10000:
            raise GroupIsTooBig()
        if self.create_string_user_id_group_id(request_owner_id, group.id) in self.groups_map:
            raise GroupIsAlreadyProcessing()
        return group

    def finish_initialization_of_group(self, user_group_ids, processing_power_mode: int):
        self.groups_map[user_group_ids] = Group(self.list_processing_power[processing_power_mode-1])

    def get_group_description(self, group_id):
        return self.application_session.groups.getById(group_id=group_id, fields='description')[0]['description']

    def check_selected_mode(self, process_power_id: int):
        """
        проверяет, корректно ли пользователем введён режим работы
        :param process_power_id: выбранный режим работы(в цифрах 1 или 2)
        :return: поднимает ошибку, если не корректно
        """
        if process_power_id > len(self.list_processing_power) and process_power_id <= 0:
            raise ValueError

    def get_groups_processing_power(self):
        text = "Доступен один режим работы:\n" + "1 - статистика за неделю\n"
        return text

    def get_report_with_current_statistics(self, user_group_ids: str):
        """
        завершает обработку группы и делает отчёт
        :param user_group_ids: строка с id пользователя и группы, которая обрабатывается
        :return: отчёт о статистике в виде списка, где первый элемент - время, в которое ползователи были
        наиболее активны, второй - файл с построенной диаграммой
        """
        group = self.groups_map.get(user_group_ids)
        if group is None:
            raise GroupIsAlreadyDeleted()
        else:
            group.math_processor.draw_diagram('diagram.png')
            report = [group.math_processor.calculate_effective_time(), 'diagram.png']
            return report

    def delete_group(self, user_group_ids):
        group = self.groups_map.get(user_group_ids)
        if group is None:
            raise GroupIsAlreadyDeleted()
        else:
            del self.groups_map[user_group_ids]

    def get_information_about_members_online(self, group_id: int) -> list:
        """
        :param group_id: id группы, информацию об участниках онлайн которой мы хотим получить.
        :return: список пользователей онлайн в данный момент.
        """
        members = self.application_session.groups.getMembers(group_id=group_id, fields='online')['count']
        n = members//1000+1
        current_members_online = []
        for x in range(n):
            members = self.application_session.groups.getMembers(group_id=group_id, offset=n*1000, fields='online')
            for member in members['items']:
                if member['online'] == 1:
                    current_members_online.append(member['id'])
        return current_members_online

    def update_information_for_math_processor(self, user_group_ids: str) -> bool:
        """
        Обновляет информацию для статистики, для ContentTimeComputer
        :param user_group_ids: строка с id пользователя и группы, которая обрабатывается
        :return true, если обработка группы должна быть закончена
        """
        group_id = int(user_group_ids.rsplit("_")[1])
        group = self.groups_map[user_group_ids]
        current_members_online = self.get_information_about_members_online(group_id)
        how_much_online = len(current_members_online)
        group.math_processor.correct_number_of_online(how_much_online)
        group.math_processor.correct_income_online(group.were_online, current_members_online)
        group.were_online = current_members_online
        group.done_iterations += 1
        return group.done_iterations == group.processing_power
