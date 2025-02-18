from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

URL_DATABASE = 'sqlite:///ecommerce.db'

engine = create_engine(URL_DATABASE, connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Produto( Base ):

    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    preco = Column(Float)
    estoque = Column(Integer)

#class Pedido( Base ):
#
#    __tablename__ = 'pedidos'
#
#    id = Column(Integer, primary_key=True, index=True)
#    produtos = Column(String, nullable=False)
#    total = Column(Float, nullable=False)
#    status = Column(String)
#
