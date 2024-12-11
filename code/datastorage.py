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

def get_all_comments(session):
    query = session.query(Comment)
    data = pd.DataFrame([{
        "stock": row.stock,
        "comment_time": row.comment_time,
        "comments": row.comments,
        "sentiment_tag": row.sentiment_tag,
        "influence": row.influence
    } for row in query])
    data = data.drop_duplicates(subset=["stock", "comment_time", "comments", "sentiment_tag", "influence"])
    data = data.reset_index(drop=True)
    return data

class SentimentAnalysis(Base):
    __tablename__ = "sentiment_score"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock = Column(String(50))
    comment_time = Column(TIMESTAMP)
    comments = Column(Text)
    sentiment_tag = Column(String(50)) 
    influence = Column(Integer)  
    sentiment = Column(String(50))
    score = Column(Float)

def save_sentiment(data, session):
    for _, row in data.iterrows():
        sentiment_entry = SentimentAnalysis(
            stock=row["stock"],
            comment_time=row["comment_time"],
            comments=row["comments"],
            sentiment_tag=row["sentiment_tag"],
            influence=row["influence"],
            sentiment = row["sentiment"],
            score = row["score"]
        )
        session.add(sentiment_entry)
    session.commit()
    print("Data successfully saved to database.")

def get_all_sentiments(session):
    query = session.query(SentimentAnalysis)
    data = pd.DataFrame([{
        "stock": row.stock,
        "comment_time": row.comment_time,
        "comments": row.comments,
        "sentiment_tag": row.sentiment_tag,
        "influence": row.influence,
        "sentiment": row.sentiment,
        "score": row.score
    } for row in query])
    return data
