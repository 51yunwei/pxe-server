# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True)
    mac = Column(String(17), unique=True)
    status = Column(String(20))  # discovered, deploying, success, failed
    progress = Column(Integer)   # 0-100
    image = Column(String(100))
    ip = Column(String(15))
    last_seen = Column(DateTime, default=datetime.now)
    duration = Column(Integer)   # in seconds

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    message = Column(Text)

class Database:
    def __init__(self, db_uri='sqlite:///pxe.db'):
        self.engine = create_engine(db_uri)
        self.Session = sessionmaker(bind=self.engine)
    
    def init_db(self):
        Base.metadata.create_all(self.engine)
    
    def add_device(self, mac, status, progress, image, ip, duration=0):
        session = self.Session()
        device = Device(
            mac=mac,
            status=status,
            progress=progress,
            image=image,
            ip=ip,
            duration=duration
        )
        session.add(device)
        session.commit()
        return device.id
    
    def update_device(self, device_id, **kwargs):
        session = self.Session()
        device = session.query(Device).get(device_id)
        if device:
            for key, value in kwargs.items():
                setattr(device, key, value)
            device.last_seen = datetime.now()
            session.commit()
    
    def get_devices(self):
        session = self.Session()
        return session.query(Device).order_by(Device.last_seen.desc()).all()
    
    def log_event(self, message):
        session = self.Session()
        event = Event(message=message)
        session.add(event)
        session.commit()
    
    def get_events(self, limit=10):
        session = self.Session()
        return session.query(Event).order_by(Event.timestamp.desc()).limit(limit).all()
