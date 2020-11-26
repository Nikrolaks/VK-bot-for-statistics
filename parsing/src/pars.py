import requests
import vk_api
from src.math.time_calculator import ContentTimeComputer


def log_in():
    session = vk_api.VkApi(token='c15b89d7c15b89d7c15b89d75ac12e9b1ccc15bc15b89d79ee1cf4a5977bbe4ff8f6761')
    try:
        session.auth()
    except vk_api.AuthError as error:
        print(error)
    return session.get_api()


class Group:
    def __init__(self, request_owner_id, id, math_professor, remaining_iterations, done_iterations, were_online, now_online):
        self.id = id
        self.math_professor = math_professor
        self.request_owner_id = request_owner_id
        self.remaining_iterations = remaining_iterations
        self.done_iterations = done_iterations
        self.were_online = were_online
        self.now_online = now_online

    def update_lists_of_users(self, online_users_now):
        self.were_online = self.now_online
        self.now_online = online_users_now



def create_group_by_short_name(short_name, iterations):
    a = vk.groups.getById(group_id=short_name, fields='description')[0]
    group = Group(a['id'], iterations, 0, [], [])
    return group


def get_information_about_members_online(vk, group):
    members = vk.groups.getMembers(group_id=group.id, fields='online')
    current_members_online = []
    for member in members['items']:
        if member['online'] == 1:
            current_members_online.append(member['id'])
    return current_members_online


def update_information_for_math_processor(math_processor, iteration, current_members_online):
    how_much_online = len(current_members_online)
    members_online = []
    math_processor.correct_number_of_online(iteration, how_much_online)
    math_processor.correct_income_online(iteration,
                                         members_online,
                                         current_members_online)




