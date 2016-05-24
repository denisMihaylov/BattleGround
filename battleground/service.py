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

	def _remove(self, query, arg):
		if query.first():
			query.delete()
			self._session.commit()
		else:
			self._raise_not_found(arg)

class UserAwareService(Service):
	def __init__(self):
		super().__init__()
		self._user_service = ServiceFactory.get_user_service()

	def _raise_login_error(self):
		raise err.LogInRequiredError("You need to be logged in "
									 "to perform this operation")

class BattleService(UserAwareService):
	pass


class GameService(UserAwareService):

	def add_game(self, name, source):
		game = self.get_game(name=name.strip())
		if game:
			raise err.GameExistsError("Game with name [%s] already exists" %\
				name)
		else:
			game = entity.Game(name=name.strip(), source=source)
			user = self._user_service.current_user
			if not user:
				self._raise_login_error()
			user.games.append(game)
			self._user_service.update_user(user)

	def get_game_query(self, **keywords):
		return self._session.query(entity.Game).filter_by(**keywords)

	def get_game(self, **keywords):
		return self.get_game_query(**keywords).first()

	def remove_game(self, name):
		name = name.strip()
		game = self.get_game_query(name=name)
		self._remove(game, name)

	def update_game(self, name, source):
		game = self.get_game(name=name.strip())
		if not game:
			_raise_not_found(name)
		else:
			game.source = source
			self._session.add(game)
			self._session.commit()

	def _raise_not_found(self, name):
		raise err.GameNotExistsError("Game with name [%s] does not exist" %\
			name)

class UserService(Service):
	def __init__(self):
		super().__init__()
		self.current_user = None

	def add_user(self, username, password):
		username = username.strip()
		user = self.get_user(username=username)
		if user:
			raise err.UserExistsError("User [%s] already registered" %\
				username)
		else:
			password = password.strip()
			user = entity.User(username=username, password=password)
			self._session.add(user)
			self._session.commit()
			return user

	def _raise_not_found(self, username):
		raise err.UserNotExistsError("User [%s] not registered" % username)

	def remove_user(self, username):
		username = username.strip()
		user = self.get_user_query(username=username)
		self._remove(user, username)

	def get_user_query(self, **keywords):
		return self._session.query(entity.User).filter_by(**keywords)

	def get_user(self, **keywords):
		return self.get_user_query(**keywords).first()

	def log_in(self, username, password):
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

	def update_user(self, user):
		self._session.add(user)
		self._session.commit()