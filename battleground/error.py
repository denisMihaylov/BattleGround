
class BattleGroundError(Exception):
	pass

class GameExistsError(BattleGroundError):
	pass

class GameNotExistsError(BattleGroundError):
	pass

class UserExistsError(BattleGroundError):
	pass

class UserNotExistsError(BattleGroundError):
	pass

class WrongPasswordError(BattleGroundError):
	pass

class LogInRequiredError(BattleGroundError):
	pass
