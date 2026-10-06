import os, datetime as dt
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./edutube.db"), connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()
now = dt.datetime.utcnow

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True); email = Column(String, unique=True, index=True)
    name = Column(String); password_hash = Column(String); level = Column(String, default="Beginner"); interests = Column(String, default="")
class Video(Base):
    __tablename__ = "videos"
    id = Column(String, primary_key=True); title = Column(String); channel = Column(String)
    thumbnail = Column(String); duration = Column(String); views = Column(String)
class WatchHistory(Base):
    __tablename__ = "watch_history"
    id = Column(Integer, primary_key=True); user_id = Column(ForeignKey("users.id")); video_id = Column(ForeignKey("videos.id")); created = Column(DateTime, default=now)
class SavedVideo(Base):
    __tablename__ = "saved_videos"
    id = Column(Integer, primary_key=True); user_id = Column(ForeignKey("users.id")); video_id = Column(ForeignKey("videos.id"))
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True); user_id = Column(ForeignKey("users.id")); video_id = Column(String)
    role = Column(String); content = Column(Text); created = Column(DateTime, default=now)
class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True); user_id = Column(ForeignKey("users.id")); video_id = Column(String); content = Column(Text)
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True); user_id = Column(ForeignKey("users.id")); video_id = Column(String)
    score = Column(Integer); total = Column(Integer); weak = Column(Text, default=""); strong = Column(Text, default=""); created = Column(DateTime, default=now)
Base.metadata.create_all(engine)
class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True); user_id = Column(ForeignKey("users.id")); name = Column(String)
class PlaylistVideo(Base):
    __tablename__ = "playlist_videos"
    id = Column(Integer, primary_key=True); playlist_id = Column(ForeignKey("playlists.id")); video_id = Column(ForeignKey("videos.id"))
Base.metadata.create_all(engine)
