from sqlalchemy import create_engine, UnicodeText, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, VARCHAR, Sequence, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship

db_engine = create_engine('sqlite:///test1.db')

Base = declarative_base()


class Fighter(Base):
    __tablename__ = "fighters"

    id = Column(Integer, Sequence('fighter_id_seq'), primary_key=True)
    bot_version = Column(Integer)
    battle_place = Column(Integer)

    bot_id = Column(Integer, ForeignKey('bots.id'))
    bot = relationship("Bot", back_populates="fighters")

    battle_id = Column(Integer, ForeignKey('battles.id'))
    battle = relationship("Battle", back_populates="fighters")


class Battle(Base):
    __tablename__ = "battles"

    id = Column(Integer, Sequence('battle_id_seq'), primary_key=True)
    state = Column(String)

    fighters = relationship("Fighter", back_populates="battle")


class Bot(Base):
    __tablename__ = "bots"

    id = Column(Integer, Sequence('bot_id_seq'), primary_key=True)

    version = Column(Integer)
    name = Column(String)
    rating = Column(Integer)
    source = Column(UnicodeText())

    game_id = Column(Integer, ForeignKey('games.id'))
    game = relationship("Game", back_populates="bots")

    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="bots")

    fighters = relationship("Fighter", back_populates="bot")

    def to_fighter(self, battle):
        return Fighter(
            bot_version=self.version,
            battle_place=-1,
            bot=self,
            battle=battle)

    def __eq__(self, other):
        return self.name == other.name and self.author_id == other.author_id

    def __repr__(self):
        return "<Bot(name=[%s], author=[%s], source=[%s], version=[%s]"\
            ", rating=[%s])>" % \
            (self.name, self.author, self.source, self.version, self.rating)


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, Sequence('game_id_seq'), primary_key=True)
    source = Column(UnicodeText())
    name = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="games")

    bots = relationship("Bot", order_by=Bot.rating)

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return "<Game(name=[%s], author=[%s], source=[%s])>" % \
            (self.name, self.author, self.source)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    rights = Column(String)
    name = Column(String)
    password = Column(String)
    games = relationship("Game", order_by=Game.id)
    bots = relationship("Bot", order_by=Bot.rating)

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return "<User(id='%s', name=[%s], password=[********])>" % \
            (self.id, self.name)

Base.metadata.bind = db_engine
Base.metadata.create_all()

session = sessionmaker(bind=db_engine)()
