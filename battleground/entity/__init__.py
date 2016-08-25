from sqlalchemy import create_engine, UnicodeText, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, VARCHAR, Sequence, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship

db_engine = create_engine('sqlite:///test.db')

Base = declarative_base()

battle_bots = Table("battle_bots", Base.metadata,\
    Column('battle_id', ForeignKey('battles.id'), primary_key=True),\
    Column('bot_id', ForeignKey('bots.id'), primary_key=True))

class Battle(Base):
    __tablename__ = "battles"

    id = Column(Integer, Sequence('battle_id_seq'), primary_key=True)

    bots = relationship("Bot", secondary=battle_bots,\
        back_populates="battles")

class Bot(Base):
    __tablename__ = "bots"

    id = Column(Integer, Sequence('bot_id_seq'), primary_key=True)
    rating = Column(Integer)
    source = Column(UnicodeText())

    game_id = Column(Integer, ForeignKey('games.id'))
    game = relationship("Game", back_populates="bots")

    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="bots")
    
    battles = relationship("Battle", secondary=battle_bots,\
        back_populates="bots")

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, Sequence('game_id_seq'), primary_key=True)
    source = Column(UnicodeText())
    name = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="games")
    bots = relationship("Bot", order_by=Bot.rating, back_populates="game")

    def __repr__(self):
        return "<Game(source='%s')>" % self.source

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    username = Column(String)
    password = Column(String)
    games = relationship("Game", order_by=Game.id, back_populates="author")
    bots = relationship("Bot", order_by=Bot.rating, back_populates="author")

    def __eq(self, other):
        return self.username == other.username

    def __repr__(self):
        return "<User(id='%s', username='%s', password='%s')>" % \
            (self.id, self.username, self.password)

Base.metadata.bind = db_engine
Base.metadata.create_all()

Session = sessionmaker(bind=db_engine)