from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # 累計數據
    total_guesses = Column(Integer, default=0)
    correct_guesses = Column(Integer, default=0)
    total_disclosures = Column(Integer, default=0)
    recognized_disclosures = Column(Integer, default=0)  # 被猜中的次數

class Room(Base):
    __tablename__ = "rooms"

    id = Column(String, primary_key=True, index=True)  # 使用 6 位數房間碼
    current_phase = Column(String, default="WAITING")
    captain_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("rooms.id"))
    question_text = Column(String)
    level = Column(Integer)
    captain_name = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"))
    player_name = Column(String)
    content = Column(String)

class Guess(Base):
    __tablename__ = "guesses"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"))
    guesser_name = Column(String)
    target_name = Column(String)
    is_correct = Column(Boolean)
