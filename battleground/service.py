import battleground
import battleground.entity as entity
import battleground.error as err

class ServiceFactory:
    @classmethod
    def get_user_service(cls):
        if not hasattr(cls, "_ServiceFactory__user_service"):
            cls.__user_service = UserService()
        return cls.__user_service

    @classmethod
    def get_game_service(cls):
        if not hasattr(cls, "_ServiceFactory__game_service"):
            cls.__game_service = GameService()
        return cls.__game_service

class Service:
    def __init__(self):
        self._session = entity.Session()

    def update_entity(self, entity):
        self._session.add(entity)
        self._session.commit()

    def _remove(self, query, arg):
        if query.first():
            query.delete()
            self._session.commit()
        else:
            self._raise_not_found(arg)

    def _get_query(self):
        return self._session.query(self._get_entity_cls())

    def _get_filtered_query(self, **keywords):
        return self._get_query().filter_by(**keywords)

    def get_logged_user(self):
        user = ServiceFactory.get_user_service().current_user
        if user == None:
            raise err.LogInRequiredError("You need to be logged in "
                                         "to perform this operation")
        return user

class BattleService(Service):
    pass


class GameService(Service):

    def add_game(self, name, source):
        game = self.get_game(name=name.strip())
        if game:
            raise err.GameExistsError("Game with name [%s] already exists" %\
                name)
        else:
            game = entity.Game(name=name.strip(), source=source)
            user = self.get_logged_user()
            user.games.append(game)
            self.update_entity(user)

    def _get_entity_cls(self):
        return entity.Game

    def get_game(self, **keywords):
        return self._get_filtered_query(**keywords).first()

    def remove_game(self, name):
        name = name.strip()
        game_query = self._get_filtered_query(name=name)
        self._remove(game_query, name)

    def update_game(self, name, source):
        game = self.get_game(name=name.strip())
        if not game:
            _raise_not_found(name)
        else:
            game.source = source
            self.update_entity(game)

    def _raise_not_found(self, name):
        raise err.GameNotExistsError("Game with name [%s] does not exist" %\
            name)

class UserService(Service):
    def __init__(self):
        super().__init__()
        self.current_user = None

    def add_user(self, username, password):
        self._check_for_logged_user()
        username = username.strip()
        user = self.get_user(username=username)
        if user:
            raise err.UserExistsError("User [%s] already registered" %\
                username)
        else:
            password = password.strip()
            user = entity.User(username=username, password=password)
            self.update_entity(user)
            return user

    def _raise_not_found(self, username):
        raise err.UserNotExistsError("User [%s] not registered" % username)

    def _check_for_logged_user(self):
        if self.current_user:
            raise err.AnotherUserLogged("User [%s] is logged. Logout first" %\
                self.current_user)

    def _get_entity_cls(self):
        return entity.User

    def remove_user(self, username):
        username = username.strip()
        user_query = self._get_filtered_query(username=username)
        self._remove(user_query, username)

    def get_user(self, **keywords):
        return self._get_filtered_query(**keywords).first()

    def get_all_users(self):
        return self._session.query(entity.User).all()

    def log_in(self, username, password):
        self._check_for_logged_user()
        username = username.strip()
        self.current_user = self.get_user(username=username)
        if not self.current_user:
            self._raise_not_found(username)
        elif self.current_user.password != password.strip():
            self.current_user = None
            raise err.WrongPasswordError("Password for user [%s] is wrong." %\
                username)

    def log_out(self):
        self.current_user = None

    def is_logged(self):
        return self.current_user != None

class BotService(Service):

    def add_bot(self, game_id, source):
        user = ServiceFactory.get_user_service().current_user


    def get_bot(self, )