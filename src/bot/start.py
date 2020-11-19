import requests
import vk_api

vk_session = vk_api.VkApi(token='38848446351cbc8d520eaa7f6340f8533b8d06b0bae7db46bb61428d47571d7565cd642cc98202caccfd6')

from vk_api.longpoll import VkLongPoll, VkEventType
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
        if event.text == 'Привет!!!':
            if event.from_user:
                vk.messages.send(user_id=event.user_id, message='Привет, брат, хоть я и бот!',
                                 random_id='12345', peer_id=event.user_id)