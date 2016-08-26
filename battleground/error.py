
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


class BotExistsError(BattleGroundError):
    pass


class BotNotExistsError(BattleGroundError):
    pass


class WrongPasswordError(BattleGroundError):
    pass


class LogInRequiredError(BattleGroundError):
    pass


class AnotherUserLoggedError(BattleGroundError):
    pass


class IncompatibleBotsError(BattleGroundError):
    pass


class RestrictedAccessError(BattleGroundError):
    pass


class NotReadyBotError(BattleGroundError):
    pass


class InvalidBotError(BattleGroundError):
    pass
