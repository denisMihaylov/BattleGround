from battleground.service import ServiceFactory
user_service = ServiceFactory.get_user_service()
print(user_service.get_all_users()) #no users yet
#user_service.add_user("username", "password")