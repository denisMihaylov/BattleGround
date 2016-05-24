from sqlalchemy import create_engine, UnicodeText
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, VARCHAR, Sequence, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship

db_engine = create_engine('sqlite:///test.db')

Base = declarative_base()

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, Sequence('game_id_seq'), primary_key=True)
    source = Column(UnicodeText())
    name = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="games")

    def __repr__(self):
        return "<Game(source='%s')>" % self.source

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    username = Column(String)
    password = Column(String)
    games = relationship("Game", order_by=Game.id, back_populates="author")

    def __eq(self, other):
        return self.username == other.username

    def __repr__(self):
        return "<User(id='%s', username='%s', password='%s')>" % \
            (self.id, self.username, self.password)


Base.metadata.bind = db_engine
Base.metadata.create_all()

Session = sessionmaker(bind=db_engine)