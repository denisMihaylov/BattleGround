from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

db_engine = create_engine('sqlite:///test.db')

Base = declarative_base()

class User(Base):
	__tablename__ = "Users"

	Id = Column(Integer, primary_key=True)
	Username = Column(String)
	Pass = Column(String)


Base.metadata.bind = db_engine
Base.metadata.create_all()

Session = sessionmaker(bind=eng)
ses = Session()