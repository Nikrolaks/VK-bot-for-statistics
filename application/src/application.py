import requests
import vk_api
from src.math.time_calculator import ContentTimeComputer


def log_in():
    """создаёт сессию, авторизуется с помощью оффлайн-токена приложения"""
    session = vk_api.VkApi(token='c15b89d7c15b89d7c15b89d75ac12e9b1ccc15bc15b89d79ee1cf4a5977bbe4ff8f6761')
    try:
        session.auth()
    except vk_api.AuthError as error:
        print(error)
    return session.get_api()


class Group:
    def __init__(self, request_owner_id, id, math_professor: ContentTimeComputer, remaining_iterations, done_iterations, were_online: list, now_online: list):
        """
        Класс "Группа"
    :param request_owner_id: идентификатор, куда уходят данные
    :param id: id группы(число)
    :param math_professor: созданный для этой группы свой объект класса ContentTimeComputer
    :param remaining_iterations: сколько ещё раз нужно собрать информацию об участниках онлайн
    :param done_iterations: сколько раз собиралась информация об участниках онлайн
    :param were_online: список id пользователей, которые были онлайн в предпоследний сбор данных
    :param now_online:  список id пользователей, которые онлайн на момент последнего сбора данных"""
        self.id = id
        self.math_professor = math_professor
        self.request_owner_id = request_owner_id
        self.remaining_iterations = remaining_iterations
        self.done_iterations = done_iterations
        self.were_online = were_online
        self.now_online = now_online

    def update_lists_of_users(self, online_users_now: list):
        self.were_online = self.now_online
        self.now_online = online_users_now


def create_group_by_short_name(request_owner_id, short_name, iterations, vk):
    """

    :param request_owner_id: идентификатор, куда уходят данные
    :param short_name: короткое имя группы или id, если у группы нет короткого имени
    :param iterations: сколько раз нужно получить количество пользователей онлайн для получения статистик
    :param vk: сессия vk, с которой произошла авторизация
    :return: объект класса Group
    """
    math_professor = ContentTimeComputer()
    a = vk.groups.getById(group_id=short_name, fields='description')[0]
    group = Group(request_owner_id, a['id'], math_professor, iterations, 0, [], [])
    return group


def get_information_about_members_online(vk, group: Group):
    """

    :param vk: сессия vk, с которой произошла авторизация
    :param group: объект класса Group, группа, информацию об участниках онлайн которой мы хотим получить
    :return: список пользователей онлайн в данный момент
    """
    members = vk.groups.getMembers(group_id=group.id, fields='online')
    current_members_online = []
    for member in members['items']:
        if member['online'] == 1:
            current_members_online.append(member['id'])
    return current_members_online


def update_information_for_math_processor(math_processor, iteration, current_members_online):
    """

    :param math_processor:
    :param iteration:
    :param current_members_online:
    :return:
    """
    how_much_online = len(current_members_online)
    members_online = []
    math_processor.correct_number_of_online(iteration, how_much_online)
    math_processor.correct_income_online(iteration,
                                         members_online,
                                         current_members_online)




