# -*- coding: UTF-8 -*-
import vk_api
from src.math.statistic_calculator import ContentTimeComputer


class Group:
    """
    Класс для хранения обрабатываемых данных группы.
    :param self.request_owner_id: идентификатор, куда уходят данные.
    :param self.group_id: id группы.
    :param self.math_processor: созданный для этой группы свой объект класса ContentTimeComputer.
    :param self.count_of_iterations: сколько раз нужно собрать информацию об участниках онлайн.
    :param self.done_iterations: сколько раз собиралась информация об участниках онлайн.
    :param self.were_online: список id пользователей, которые были онлайн в момент предпоследнего сбора данных.
    """
    def __init__(self, request_owner_id: int, group_id: int, math_processor: ContentTimeComputer,
                 count_of_iterations, done_iterations, were_online: list):
        self.id = group_id
        self.math_processor = math_processor
        self.request_owner_id = request_owner_id
        self.count_of_iterations = count_of_iterations
        self.done_iterations = done_iterations
        self.were_online = were_online


class Application:
    """
    Класс, реализующий поиск информации о группах и обработку результатов поиска.
    :param self.application_session: механизм получения сведений о группе от Вконтакте.
    """
    def __init__(self):
        # создаёт сессию, авторизуется с помощью оффлайн-токена приложения
        session = vk_api.VkApi(token='c15b89d7c15b89d7c15b89d75ac12e9b1ccc15bc15b89d79ee1cf4a5977bbe4ff8f6761')
        self.application_session = session.get_api()

    def find_group_by_short_name(self, request_owner_id, short_name, iterations) -> {None, Group}:
        """
        :param request_owner_id: идентификатор, куда уходят данные.
        :param short_name: короткое имя группы или id, если у группы нет короткого имени.
        :param iterations: сколько раз нужно получить количество пользователей онлайн для составления статистики.
        :return: объект класса Group, если группа была найдена, иначе - None.
        """
        print(short_name)
        try:
            finding_results = self.application_session.groups.getById(group_id=short_name, fields='description')
        except:
            return None
        # а нужна ли эта проверка - пока не знаю. Скорее всего, в функцию сверху надо отправлять
        # не group_id, а одноэлементный group_ids
        if len(finding_results) == 0:
            return None
        group = finding_results[0]
        return Group(request_owner_id, group['id'], ContentTimeComputer(), iterations, 0, [])

    def get_information_about_members_online(self, group: Group) -> list:
        """
        :param group: группа, информацию об участниках онлайн которой мы хотим получить.
        :return: список пользователей онлайн в данный момент.
        """
        members = self.application_session.groups.getMembers(group_id=group.id, fields='online')
        current_members_online = []
        for member in members['items']:
            if member['online'] == 1:
                current_members_online.append(member['id'])
        return current_members_online

    def update_information_for_math_processor(self, group: Group):
        """
        :param group: группа, информацию о которой обрабатываем.
        """
        current_members_online = self.get_information_about_members_online(group)
        how_much_online = len(current_members_online)
        group.math_processor.correct_number_of_online(group.done_iterations-1, how_much_online)
        group.math_processor.correct_income_online(group.done_iterations-1,
                                                   group.were_online,
                                                   current_members_online)
        group.were_online = current_members_online
