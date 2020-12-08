# -*- coding: UTF-8 -*-
import vk_api
import time
from collections import defaultdict
from src.math.statistic_calculator import ContentTimeComputer


class GroupNotFoundError(Exception):
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
    :param self.count_of_iterations: сколько раз нужно собрать информацию об участниках онлайн.
    :param self.done_iterations: сколько раз собиралась информация об участниках онлайн.
    :param self.were_online: список id пользователей, которые были онлайн в момент предпоследнего сбора данных.
    """
    def __init__(self, group_id: int, math_processor: ContentTimeComputer):
        self.id = group_id
        time_of_beginning = time.gmtime(time.time())
        self.time_of_beginning = time_of_beginning
        self.math_processor = math_processor
        self.done_iterations = 0
        self.were_online = []


class Application:
    """
    Класс, реализующий поиск информации о группах и обработку результатов поиска.
    :param self.application_session: механизм получения сведений о группе от Вконтакте.
    :param self.list_processing_power: список возможных режимов(сколько раз проводить сбор статистики)
    """
    def __init__(self):
        # создаёт сессию, авторизуется с помощью оффлайн-токена приложения
        session = vk_api.VkApi(token='c15b89d7c15b89d7c15b89d75ac12e9b1ccc15bc15b89d79ee1cf4a5977bbe4ff8f6761')
        self.application_session = session.get_api()
        self.list_processing_power = [47, 168, 328, 671]
        self.groups_processing_power = {}
        self.groups_map = defaultdict(Group)

    def get_group_information_by_short_name(self, short_name):
        """
        создаёт объект класса Group description, если это возможно
        :param short_name: короткое имя или id группы
        :return: объект класса Group description, если верно дано id, или возбуждает исключение
        GroupNotFoundError
        """
        try:
            group = self.application_session.groups.getById(group_id=short_name)[0]
            id = group['id']
            name = group['name']
            url = 'https://vk.com/' + short_name
            print(name)
            return GroupDescription(id, url, short_name)
        except:
            raise GroupNotFoundError()

    def add_group_to_process(self, group_id: int, process_power_id: int):
        if process_power_id > len(self.list_processing_power):
            raise ValueError
        else:
            self.groups_processing_power[group_id] = self.list_processing_power[process_power_id-1]

    def get_groups_processing_power(self):
        text = "Доступно три режима работы:\n"+ "1 - статистика за сутки\n" "2 - статистика за неделю\n" \
               "3 - статистика за две недели"
        return text

    def end_group_processing(self, group_id: int):
        del self.groups_processing_power[group_id]
        del self.groups_map[group_id]

    def get_information_about_members_online(self, group: Group) -> list:
        """
        :param group: группа, информацию об участниках онлайн которой мы хотим получить.
        :return: список пользователей онлайн в данный момент.
        """
        members = self.application_session.groups.getMembers(group_id=group.id, fields='online')['count']
        n = members//1000+1
        current_members_online = []
        for x in range(n):
            members = self.application_session.groups.getMembers(group_id=group.id, offset=n*1000, fields='online')
            for member in members['items']:
                if member['online'] == 1:
                    current_members_online.append(member['id'])
        return current_members_online

    def update_information_for_math_processor(self, group_id: int) -> bool:
        """
        Обновляет информацию для статистики, для ContentTimeComputer
        :param group_id: группа, информацию о которой обрабатываем.
        :return true, если обработка группы должна быть закончена
        """
        group = self.groups_map[group_id]
        group_processing_mode = self.groups_processing_power[group_id]
        current_members_online = self.get_information_about_members_online(group)
        how_much_online = len(current_members_online)
        group.math_processor.correct_number_of_online(group.done_iterations, how_much_online)
        group.math_processor.correct_income_online(group.done_iterations,
                                                   group.were_online,
                                                   current_members_online)
        group.were_online = current_members_online
        group.done_iterations += 1
        return group.done_iterations == group_processing_mode
