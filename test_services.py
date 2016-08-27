import unittest
from battleground.service import ServiceFactory, UserRights, BotReadyState
import battleground.error as err
from contextlib import contextmanager
from codejail.exceptions import SafeExecException

@contextmanager
def log_in_user(user_name, password):
    ServiceFactory.get_user_service().log_in(user_name, password)
    yield
    ServiceFactory.get_user_service().log_out()


class TestService:

    def test_availability(self):
        self.assertIsNotNone(self.service)

    def test_all(self, items_count=0):
        items = self.service.get_all()
        self.assertEqual(len(items), items_count)


class TestUserService(TestService, unittest.TestCase):

    def setUp(self):
        self.service = ServiceFactory.get_user_service()

    def test_user_addition(self):
        count = len(self.service.get_all())
        user = self.service.add_user("user1", "password")
        self.assertEqual(user.rights, UserRights.USER)
        self.assertEqual(len(user.games), 0)
        self.assertEqual(len(user.bots), 0)
        self.assertEqual(len(self.service.get_all()), count + 1)

    def test_existing_user(self):
        self.service.add_user("existing_user", "password")
        with self.assertRaises(err.UserExistsError):
            self.service.add_user("existing_user", "password")      

    def test_log_in(self):
        self.service.add_user("login", "password")
        self.assertFalse(self.service.is_logged())
        with log_in_user("login", "password"):
            self.assertTrue(self.service.is_logged())
            self.assertEqual("login", self.service.get_logged_user().name)
        self.assertFalse(self.service.is_logged())


    def test_change_rights(self):
        admin = self.service.add_user("admin", "password", UserRights.ADMIN)
        user = self.service.add_user("user", "password")
        self.assertEqual(UserRights.ADMIN, admin.rights)
        with self.assertRaises(err.LogInRequiredError):
            self.service.make_user("admin")

        with log_in_user("user", "password"):
            with self.assertRaises(err.RestrictedAccessError):
                self.service.make_user("admin")

        with log_in_user("admin", "password"):
            self.service.make_admin("user")
            self.service.make_user("admin")

    def test_remove_user(self):
        admin = self.service.add_user("adm", "password", UserRights.ADMIN)
        remove_user = self.service.add_user("remove", "password")

        with self.assertRaises(err.LogInRequiredError):
            self.service.remove_user("remove")

        with log_in_user("remove", "password"):
            with self.assertRaises(err.RestrictedAccessError):
                self.service.remove_user("remove")
        with log_in_user("adm", "password"):
            self.service.remove_user("remove")
            with self.assertRaises(err.UserNotExistsError):
                self.service.remove_user("remove")



class TestGameService(TestService, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        user_service = ServiceFactory.get_user_service()
        user_service.add_user("game_user1", "a", UserRights.ADMIN)


    def setUp(self):
        self.service = ServiceFactory.get_game_service()
        self.user_service = ServiceFactory.get_user_service()

    @classmethod
    def tearDownClass(cls):
        user_service = ServiceFactory.get_user_service()
        with log_in_user("game_user1", "a"):
            user_service.remove_user("game_user1")


    def test_game_addition(self):
        with self.assertRaises(err.LogInRequiredError):
            self.service.add_game("game_name", "source code", "2")
        with log_in_user("game_user1", "a"):
            game = self.service.add_game("game_name", "source code", "2")
            with self.assertRaises(err.GameExistsError):
                self.service.add_game("game_name", "source code", "2")


    def test_game_update(self):
        with log_in_user("game_user1", "a"):
            game = self.service.add_game("game_name1", "source", "2")
            game = self.service.update_game("game_name1", "new source")
            self.assertEqual(game.source, "new source")

    def test_remove_game(self):
        with log_in_user("game_user1", "a"):
            self.service.add_game("game_name2", "source", "2")
            self.service.remove_game("game_name2")
            with self.assertRaises(err.GameNotExistsError):
                self.service.remove_game("game_name2")


class TestBotService(TestService, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        user_service = ServiceFactory.get_user_service()
        user_service.add_user("bot_user1", "a", UserRights.ADMIN)
        user_service.add_user("bot_user2", "a")
        with log_in_user("bot_user1", "a"):
            game_service = ServiceFactory.get_game_service()
            game_service.add_game("game1", "source", "2")

    @classmethod
    def tearDownClass(cls):
        user_service = ServiceFactory.get_user_service()
        with log_in_user("bot_user1", "a"):
            game_service = ServiceFactory.get_game_service()
            game_service.remove_game("game1")
            user_service.remove_user("bot_user2")
            user_service.remove_user("bot_user1")


    def setUp(self):
        self.service = ServiceFactory.get_bot_service()
        self.user_service = ServiceFactory.get_user_service()


    def test_logged_error(self):
        with self.assertRaises(err.LogInRequiredError):
            self.service.add_bot("bot_name", "game1", "source")

    def test_bot_exists(self):
        with log_in_user("bot_user1", "a"):
            self.service.add_bot("bot_name", "game1", "source")
            with self.assertRaises(err.BotExistsError):
                self.service.add_bot("bot_name", "game1", "source")


    def test_bot_additions(self):
        with log_in_user("bot_user1", "a"):
            bot = self.service.add_bot("bot_name1", "game1", "source")
            self.assertEqual("game1", bot.game.name)
            self.assertEqual("bot_user1", bot.author.name)
            self.assertEqual(1200, bot.rating)
            self.assertEqual(1, bot.version)
            self.assertEqual(BotReadyState.NOT_READY, bot.ready_state)

    def test_update_ready_state(self):
        with log_in_user("bot_user1", "a"):
            self.service.add_bot("bot_name2", "game1", "source")
            bot = self.service.update_ready_state("bot_name2", BotReadyState.READY)
            self.assertEqual(BotReadyState.READY, bot.ready_state)

    def update_bot(self):
        with log_in_user("bot_user1", "a"):
            self.service.add_bot("bot_name3", "game1", "source")
            bot = self.service.update_bot("bot_name3", "new source")
            self.assertEqual(bot.source, "new source")
            self.assertEqual(bot.version, 2)

    def test_get_bot_for_user(self):
        with log_in_user("bot_user1", "a"):
            bot = self.service.add_bot("bot_name5", "game1", "source")
        self.service.get_bot_for_user("bot_user1", "bot_name5")

    def test_multiple_bot_with_same_name(self):
        with log_in_user("bot_user1", "a"):
            self.service.add_bot("bot_name4", "game1", "source")

        with log_in_user("bot_user2", "a"):
            self.service.add_bot("bot_name4", "game1", "source")


@contextmanager
def reloaded_bots():
    bot_service = ServiceFactory.get_bot_service()
    bot1 = bot_service.get_bot_for_user("battle_user1", "battle_bot")
    bot2 = bot_service.get_bot_for_user("battle_user2", "battle_bot")
    yield [bot1, bot2]


class TestBattleService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        user_service = ServiceFactory.get_user_service()
        game_service = ServiceFactory.get_game_service()
        bot_service = ServiceFactory.get_bot_service()

        user_service.add_user("battle_user1", "a", UserRights.ADMIN)
        user_service.add_user("battle_user2", "a")

        with log_in_user("battle_user1", "a"):
            game_service.add_game("error_game", "1/0", "2")
            game_service.add_game("battle_game", "final_order = [0, 1]", "2")
            bot_service.add_bot("battle_bot", "battle_game", "")
            bot_service.add_bot("battle_bot1", "error_game", "")

        with log_in_user("battle_user2", "a"):
            bot_service.add_bot("battle_bot", "battle_game", "")
            bot_service.add_bot("battle_bot1", "error_game", "")

    @classmethod
    def tearDownClass(cls):
        user_service = ServiceFactory.get_user_service()
        game_service = ServiceFactory.get_game_service()
        bot_service = ServiceFactory.get_bot_service()

        with log_in_user("battle_user2", "a"):
            bot_service.remove_bot("battle_bot")
            bot_service.remove_bot("battle_bot1")

        with log_in_user("battle_user1", "a"):
            bot_service.remove_bot("battle_bot")
            bot_service.remove_bot("battle_bot1")
            game_service.remove_game("battle_game")
            game_service.remove_game("error_game")
            user_service.remove_user("battle_user2")
            user_service.remove_user("battle_user1")


    def setUp(self):
        self.service = ServiceFactory.get_battle_service()
        self.user_service = ServiceFactory.get_user_service()
        self.bot_service = ServiceFactory.get_bot_service()
        self.game_service = ServiceFactory.get_game_service()

    def test_battle_bots_not_ranked(self):
        with reloaded_bots() as bots:
            ratings = sorted([bot.rating for bot in bots])
            self.service.battle_bots(*bots)

        with reloaded_bots() as bots:
            self.assertEqual(bots[0].rating, ratings[0])
            self.assertEqual(bots[1].rating, ratings[1])

    def test_battle_ranked(self):
        with reloaded_bots() as bots:
            ratings = sorted([bot.rating for bot in bots])
            self.service.battle_bots(*bots, ranked=True)

        with reloaded_bots() as bots:
            self.assertGreater(bots[0].rating, ratings[0])
            self.assertLess(bots[1].rating, ratings[1])

    def test_battle_bots_error(self):
        bot1 = self.bot_service.get_bot_for_user("battle_user1", "battle_bot1")
        bot2 = self.bot_service.get_bot_for_user("battle_user2", "battle_bot1")
        with self.assertRaises(SafeExecException):
            self.service.battle_bots(bot1, bot2)

      
if __name__ == '__main__':
    unittest.main()