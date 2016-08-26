import battleground
import battleground.entity as entity
import battleground.error as err

import codejail.jail_code
from codejail.languages import python3
from codejail.safe_exec import safe_exec, not_safe_exec


import contextlib
import os
import shutil
import tempfile
import math

import _thread


class ServiceFactory:
    """
    ServiceFactory class keeps the services' instances
    and only one instance of a service is created
    """
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

    @classmethod
    def get_bot_service(cls):
        if not hasattr(cls, "_ServiceFactory__bot_service"):
            cls.__bot_service = BotService()
        return cls.__bot_service

    @classmethod
    def get_battle_service(cls):
        if not hasattr(cls, "_ServiceFactory__battle_service"):
            cls.__battle_service = BattleService()
        return cls.__battle_service

    @classmethod
    def get_matchmaking_service(cls):
        if not hasattr(cls, "_ServiceFactory__matchmaking_service"):
            cls.__matchmaking_service = MatchMakingService()
        return cls.__matchmaking_service


class Service:
    def __init__(self):
        pass

    def update_entity(self, item):
        entity.session.add(item)
        entity.session.commit()

    def _remove(self, query, arg):
        if query.first():
            query.delete()
            entity.session.commit()
        else:
            self._raise_not_found(arg)

    def _get_query(self):
        return entity.session.query(self._get_entity_cls())

    def _get_filtered_query(self, **keywords):
        return self._get_query().filter_by(**keywords)

    def get_logged_user(self):
        user = ServiceFactory.get_user_service().current_user
        if user is None:
            raise err.LogInRequiredError("You need to be logged in "
                                         "to perform this operation")
        return user

    def get_by_id(self, id):
        result = self._get_filtered_query(id=id).first()
        if result is None:
            self._raise_not_found(name)
        return result

    def get_by_name(self, name):
        result = self._get_filtered_query(name=name).first()
        if result is None:
            self._raise_not_found(name)
        return result

    def get_all(self):
        return entity.session.query(self._get_entity_cls()).all()


class GameService(Service):
    """
    Class providing base operatirons on Games
    """

    def add_game(self, name, source):
        """
        Creates a new Game
        Every game's source code should be python3 code and would be executed
        via the exec() build-in. The code receives a global variable bots
        which is the bots modules that the game can import
        Once the game is over the a global variable final_order should be set
        The final_order variable should be sorted
        staring with the winner and finishing with the loser
        If the game is a draw final_order is set to None
        """
        try:
            game = self.get_by_name(name.strip())
            error = "Game with name [%s] already exists" % name
            raise err.GameExistsError(error)
        except err.GameNotExistsError:
            user = self.get_logged_user()
            game = entity.Game(
                name=name.strip(),
                source=source,
                author=user)
            self.update_entity(game)
            return game

    def _get_entity_cls(self):
        return entity.Game

    def remove_game(self, name):
        self.__check_game_rigths(name)
        name = name.strip()
        game_query = self._get_filtered_query(name=name)
        self._remove(game_query, name)

    def __check_game_rigths(self, name):
        user = self.get_logged_user()
        game = self.get_by_name(name.strip())
        if (game.author != user):
            error = "Game with name [%s] is not owned by you" % name
            raise err.RestrictedAccessError(error)

    def update_game(self, name, source):
        self.__check_game_rigths(name)
        game = self.get_by_name(name.strip())
        if not game:
            _raise_not_found(name)
        else:
            game.source = source
            self.update_entity(game)

    def _raise_not_found(self, name):
        error = "Game with name [%s] does not exist" % name
        raise err.GameNotExistsError(error)


class UserRights:
    ADMIN = "ADMIN"
    USER = "USER"


class UserService(Service):
    """
    UserService class provides base operations to manage users
    """

    def __init__(self):
        super().__init__()
        self.current_user = None

    def add_user(self, name, password, rights=UserRights.USER):
        """
        Creates a new user with user rights
        If the username is taken a UserExistsError is raised
        """
        self._check_for_logged_user()
        name = name.strip()
        try:
            user = self.get_by_name(name)
            error = "User [%s] already registered" % name
            raise err.UserExistsError(error)
        except err.UserNotExistsError:
            password = password.strip()
            user = entity.User(
                name=name,
                password=password,
                rights=rights)
            self.update_entity(user)
            return user

    def _raise_not_found(self, name):
        raise err.UserNotExistsError("User [%s] not registered" % name)

    def _check_for_logged_user(self):
        if self.current_user:
            logged = self.current_user.name
            error = "User [%s] is logged. Logout first" % logged
            raise err.AnotherUserLoggedError(error)

    def _get_entity_cls(self):
        return entity.User

    def make_user(self, name):
        """
        Gives USER rights to user
        """
        self.__change_rights(name, UserRights.USER)

    def make_admin(self, name):
        """
        Gives ADMIN rights to user
        """
        self.__change_rights(name, UserRights.ADMIN)

    def __change_rights(self, name, rights):
        user = self.get_by_name(name)
        user.rights = rights
        self.update_entity(user)

    def remove_user(self, name):
        """
        Removes the user from the system
        """
        self.check_admin_rights()
        name = name.strip()
        user_query = self._get_filtered_query(name=name)
        self._remove(user_query, name)

    def check_admin_rights(self):
        if self.current_user.rights != UserRights.ADMIN:
            error = "Admin rights needed to perform this operation"
            raise err.RestrictedAccess(error)

    def log_in(self, name, password):
        self._check_for_logged_user()
        name = name.strip()
        self.current_user = self.get_by_name(name)
        if not self.current_user:
            self._raise_not_found(name)
        elif self.current_user.password != password.strip():
            self.current_user = None
            error = "Password for user [%s] is wrong." % name
            raise err.WrongPasswordError(error)

    def log_out(self):
        self.current_user is None

    def is_logged(self):
        return self.current_user is not None


class BotReadyState:
    """
    Ready states for the bot
    If a bot is in READY state that means every one can challenge him
    and he can be used in matchmaking
    If a bot is in CHALLENGE state that means it can only be challenged
    If a bot is in NOT_READY state it means that the bot can only
    be played from the BattleService in a single Battle
    """
    READY = "READY"
    CHALLENGE = "CHALLENGE"
    NOT_READY = "NOT_READY"


class BotService(Service):
    """
    BotService class provides base operations to manage bots
    """

    STARTING_BOT_RATING = 1200

    def add_bot(self, bot_name, game_name, source):
        """
        Adds a bot playing the specified game.
        Bots are added per user and one user cannot have two bots
        with the same name but two users can have bots with the same name
        Every bot should provice source which define a Bot class
        which should have a method called get_move
        with the arguments that the Game passes
        """
        user = self.get_logged_user()
        try:
            bot = self.get_by_name(bot_name)
            error = "Bot with name [%s] already exists" % bot_name
            raise err.BotExistsError(error)
        except err.BotNotExistsError:
            game = ServiceFactory.get_game_service().get_by_name(game_name)
            bot = entity.Bot(
                rating=BotService.STARTING_BOT_RATING,
                game_id=game.id,
                author=user,
                source=source,
                name=bot_name,
                version=1,
                ready_state=BotReadyState.NOT_READY)
            self.update_entity(bot)
            return bot

    def update_bot(self, bot_name, source):
        """
        When the user is logged he can update his bot to a newer version
        providing the new source code
        """
        bot = self.get_by_name(bot_name)
        bot.source = source
        bot.version += 1
        self.update_entity(bot)
        return bot

    def remove_bot(self, name):
        name = name.strip()
        bot_query = self._get_filtered_query(
            name=name,
            author=self.get_logged_user())
        self._remove(bot_query, name)

    def get_by_name(self, name):
        bot = self._get_filtered_query(
            name=name,
            author=self.get_logged_user()).first()
        if bot is None:
            self._raise_not_found(name)
        return bot

    def get_bot_for_user(self, user_name, bot_name):
        """
        This operation requires ADMIN rights and can retrieve a bot
        by user_name and bot_name
        """
        user = ServiceFactory.get_user_service().get_by_name(user_name)
        bot = self._get_filtered_query(name=bot_name, author=user).first()
        if bot is None:
            self._raise_not_found(user_name)
        return bot

    def _raise_not_found(self, name):
        raise err.BotNotExistsError("Bot [%s] not registered" % name)

    def _get_entity_cls(self):
        return entity.Bot


class BattleState:
    PREPARED = "PREPARED"
    RUNNING = "THE FIGHT IS ON"
    CONCLUDED = "CONCLUDED"


class BattleService(Service):
    """
    BattleService class provides base battle operations
    """

    ENV_PATH = '/home/denis/university/python/sandbox_virtualenv/bin/python'

    def battle_bots(self, *bots, ranked=False):
        """
        Battles multiple bots which play the same game
        This is only one battle.
        """
        game = bots[0].game
        for bot in bots:
            if bot.game_id != game.id:
                error = "Not all bots play the same game"
                raise err.IncompatibleBotsError(error)
        battle = self.__create_battle(bots)
        self.__start_battle(battle, game, bots, ranked)

    def __create_battle(self, bots):
        """
        Stores a battle in prepared state and returns it
        """
        battle = entity.Battle(state=BattleState.PREPARED)
        entity.session.add(battle)
        [entity.session.add(bot.to_fighter(battle)) for bot in bots]
        entity.session.commit()
        return battle

    def __start_battle(self, battle, game, bots, ranked):
        """
        Starts an async thred that executes the battle
        The battle changes its state from running to concluded and
        when it finishes it updates the fighters final positions
        and then updated the bot rating based on the elo system
        """

        # update battle state to RUNNING
        battle.state = BattleState.RUNNING
        self.update_entity(battle)

        def execute_battle(bots, game, battle):
            # configure codejail
            codejail.jail_code.configure(
                'python',
                BattleService.ENV_PATH,
                lang=python3)

            # sort bots by rating so the weakest start first
            bots = sorted(bots, key=lambda bot: bot.rating, reverse=True)

            # work with a temporary directory where
            # the sources are stored as modules
            with self.__temp_directory() as temp_dir:
                # create .py files with the bots source code
                modules = self.__create_fighter_files(bots, temp_dir)

                # workaround because of using chess implementations
                # that require third-party modules
                self.__copy_chess_files(temp_dir)

                # creating the namespace of the game
                game_globals = {"final_order": [], "bots": modules}

                # Executing the game in safe mode
                safe_exec(game.source, game_globals, python_path=[temp_dir])

            final_order = game_globals['final_order']

            # conclude the battle
            battle.state = BattleState.CONCLUDED
            entity.session.add(battle)

            # update the battle place of the fighter
            if final_order is not None:
                for i, fighter in enumerate(battle.fighters):
                    fighter.battle_place = final_order.index(i)
                    entity.session.add(fighter)

            # update the bots rating
            if ranked:
                if final_order is None:
                    for i in range(len(battle.fighters) / 2):
                        stronger = battle.fighters[-i - 1]
                        weaker = battle.fighters[i]
                        rating_diff = stronger - weaker
                        rating_diff = round(rating_diff / 50)
                        stronger.bot.rating -= rating_diff
                        weaker.bot.rating += rating_diff
                else:
                    self.__update_bots_elo(battle.fighters, final_order)

            # save all changes
            entity.session.commit()

            return final_order

        # start the battle in another thread
        args = (bots, game, battle)
        _thread.start_new_thread(execute_battle, args)

    def __create_fighter_files(self, bots, temp_dir):
        """
        Copying the bot sources to the temporary folder so that
        the Game can use them as modules
        """
        bot_modules = []
        for bot in bots:
            module_name = bot.author.name + bot.name
            bot_modules.append(module_name)
            file_name = os.path.join(temp_dir, module_name + ".py")
            with open(file_name, "w") as module_file:
                module_file.write(bot.source)
        return bot_modules

    def __copy_chess_files(self, temp_dir):
        """
        Workaraund for chess to enable unsave exec for debuging
        """
        tools_path = '/home/denis/university/python/BattleGround/'\
            'battleground/tools.py'
        sunfish_path = '/home/denis/university/python/BattleGround/'\
            'battleground/sunfish.py'
        shutil.copy(tools_path, temp_dir)
        shutil.copy(sunfish_path, temp_dir)

    @contextlib.contextmanager
    def __temp_directory(self):
        """
        A context manager to make and use a temp directory.
        The directory will be removed when done.
        """
        temp_dir = tempfile.mkdtemp(prefix="battle-")
        try:
            yield temp_dir
        finally:
            # if this errors, something is genuinely wrong,
            # so don't ignore errors.
            shutil.rmtree(temp_dir)

    def __update_bots_elo(self, fighters, final_order):
        """
        Calculates the updated ELO points and updates the bots
        Based on the algorithm / code presented here
        http://elo-norsak.rhcloud.com/index.php
        """
        K = 32 / (len(fighters) - 1)

        for i, fighter in enumerate(fighters):
            current_place = final_order.index(i) + 1
            current_elo = fighter.bot.rating
            elo_change = 0

            for j, opponent in enumerate(fighters):
                if i != j:
                    opponent_place = final_order.index(j) + 1
                    opponent_elo = opponent.bot.rating

                    # work out S
                    if current_place < opponent_place:
                        S = 1.0
                    elif current_place == opponent_place:
                        S = 0.5
                    else:
                        S = 0.0

                    # work out EA
                    diff = (opponent_elo - current_elo)
                    EA = 1 / (1.0 + math.pow(10.0, diff / 400.0))

                    # calculate ELO change vs this one opponent,
                    # add it to our change bucket
                    elo_change += K * (S - EA)

            # add accumulated change to initial ELO for final ELO
            fighter.bot.rating += round(elo_change)
            entity.session.add(fighter.bot)


class MatchMakingService:
    pass