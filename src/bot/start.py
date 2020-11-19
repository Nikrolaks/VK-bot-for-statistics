import requests
import vk_api

session = requests.Session()
login, password = 'secret', 'super_secret'
vk_session = vk_api.VkApi(login, password)
try:
    vk_session.auth(token_only=True)
except vk_api.AuthError as error:
    print(error)

vk = vk_session.get_api()
a = vk.groups.getById(group_id='stickertime', fields='description')[0]
super_id = a['id']
members = vk.groups.getMembers(group_id=super_id, fields='online')
online = 0
for member in members['items']:
    # print(member)
    online += member['online']
print(online)