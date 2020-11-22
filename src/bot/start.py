# -*- coding: UTF-8 -*-
import vk_api
import schedule
import time
from src.math.time_calculator import ContentTimeComputer

def log_in():
    session = vk_api.VkApi(login='login', password='password')
    try:
        session.auth()
    except vk_api.AuthError as error:
        print(error)

    return session.get_api()

def static_var(var_name, value):
    def decorate(func):
        setattr(func, var_name, value)
        return func
    return decorate

@static_var('how_many_times', 1)
@static_var('members_online', [])
def update_information(vk_session, math_processor, group_id):
    members = vk_session.groups.getMembers(group_id=group_id, fields='online')
    current_members_online = []
    print(members['items'])
    for member in members['items']:
        if member['online']:
            current_members_online.append(member['id'])
    how_much_online = len(current_members_online)
    current_members_online.sort()
    math_processor.correct_number_of_online(update_information.how_many_times, how_much_online)
    math_processor.correct_income_online(update_information.how_many_times,
                                         update_information.members_online,
                                         current_members_online)
    if update_information.how_many_times == 47:
        return schedule.CancelJob
    update_information.members_online = current_members_online
    update_information.how_many_times += 1

def start_process():
    math_processor = ContentTimeComputer()
    vk_session = log_in()
    group_information = vk_session.groups.getById(group_id='memkn', fields='description')[0]
    group_id = group_information['id']
    schedule.every(1).seconds.do(update_information,
                                 math_processor=math_processor,
                                 vk_session=vk_session,
                                 group_id=group_id)
    while True:
        print(update_information.how_many_times)
        schedule.run_pending()
        time.sleep(1)
        if update_information.how_many_times > 47:
            break
    print(math_processor.calculate_effective_time())

if __name__ == '__main__':
    start_process()