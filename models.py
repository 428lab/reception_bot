from sqlalchemy import Column, Integer, Text
from sqlalchemy.sql.expression import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import TIMESTAMP as Timestamp
from sqlalchemy.sql.functions import current_timestamp


Base = declarative_base()

class NotificationChannels(Base):
    __tablename__ = 'notification_queue'

    _id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    status = Column(Integer, nullable=False) # 0:disable 1:enable
    server_id = Column(Text, nullable=False)
    channel_id = Column(Text)
    created = Column(Timestamp, server_default=current_timestamp())

    def __init__(self, status=None, server_id=None, channel_id=None):
        self.status = status
        self.server_id = server_id
        self.channel_id = channel_id


class DiscordLog(Base):
    __tablename__ = 'discord_logs'

    _id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    # '0:user join 1:user left 2:chat 3:reaction add 4:reaction remove 5:join vc 6:left vc 7:move vc'
    _type = Column(Integer, nullable=False) 
    server_id = Column(Text, nullable=False)
    channel_id = Column(Text)
    user_id = Column(Integer)
    log1 = Column(Text, nullable=True)
    log2 = Column(Text, nullable=True)
    log3 = Column(Text, nullable=True)
    log4 = Column(Text, nullable=True)
    created = Column(Timestamp, server_default=current_timestamp())

    def __init__(self, _type=None, server_id=None, channel_id=None, user_id=None, log1=None, log2=None, log3=None, log4=None):
        self._type = _type
        self.server_id = server_id
        self.channel_id = channel_id
        self.user_id = user_id
        self.log1 = log1
        self.log1 = log2
        self.log2 = log3
        self.log3 = log4
