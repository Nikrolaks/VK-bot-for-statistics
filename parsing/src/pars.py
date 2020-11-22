import requests
import vk_api


session = requests.Session()
vk_session = vk_api.VkApi(token='849146c0bb4431fd001894813703ac671902d38ba156a841440da630aad9c695e6e40413411f6360d9666')

try:
    vk_session.auth(token_only=True)
except vk_api.AuthError as error:
    print(error)

vk = vk_session.get_api()
a = vk.groups.getById(group_id='memkn', fields='description')[0]
super_id = a['id']
members = vk.groups.getMembers(group_id=super_id, fields='online')
online = 0
for member in members['items']:
    print(member)
    online += member['online']
print(online)