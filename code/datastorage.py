from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Float
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import dotenv
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock = Column(String(50))
    comment_time = Column(TIMESTAMP)
    comments = Column(Text)
    sentiment_tag = Column(String(50))
    influence = Column(Integer)

def save_to_database(data, session):
    for _, row in data.iterrows():
        comment = Comment(
            stock=row["stock"],
            comment_time=row["comment_time"],
            comments=row["comments"],
            sentiment_tag=row["sentiment_tag"],
            influence=row["influence"]
        )
        session.add(comment)
    session.commit()
    print("Data successfully saved to database.")
