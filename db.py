from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.dialects.mysql import TIMESTAMP as Timestamp
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy import desc, asc

from sqlalchemy import create_engine

from models import Base, NotificationChannels, DiscordLog

from contextlib import contextmanager

import socket
import time


url = 'sqlite:///reception.db'
engine = create_engine(url, echo=False)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        import sys
        import traceback
        import datetime
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_text = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        sys.stderr.write(err_text)
        print(err_text)
        session.rollback()
        raise
    finally:
        session.close()


def add_notify_channel(server_id, channel_id):
    with session_scope() as session:
        notificationChannel = session.query(NotificationChannels).filter(NotificationChannels.server_id==server_id)\
                    .filter(NotificationChannels.channel_id==channel_id)\
                    .one_or_none()
        if notificationChannel is None:
            notificationChannel = NotificationChannels(status=1, server_id=server_id, channel_id=channel_id)
            session.add(notificationChannel)
            session.commit()
        else:
            if notificationChannel.status == 0:
                notificationChannel.status = 1
            session.commit()


def remove_notify_channel(server_id, channel_id):
    with session_scope() as session:
        notificationChannel = session.query(NotificationChannels).filter(NotificationChannels.server_id==server_id)\
                    .filter(NotificationChannels.channel_id==channel_id)\
                    .one_or_none()
        if notificationChannel:
            if notificationChannel.status != 0:
                notificationChannel.status = 0
            session.commit()


def get_notify_channels(server_id, status):
    with session_scope() as session:
        notificationChannels = session.query(NotificationChannels).filter(NotificationChannels.server_id==server_id)\
                    .filter(NotificationChannels.status==status)\
                    .all()
        channels = []
        for notificationChannel in notificationChannels:
            channel = {}
            channel["server_id"] = notificationChannel.server_id
            channel["channel_id"] = notificationChannel.channel_id
            channels.append(channel)
        return channels


def discord_log(_type=None, server_id=None, channel_id=None, user_id=None, log1=None, log2=None, log3=None, log4=None):
    with session_scope() as session:
        discord_log = DiscordLog(_type, server_id, channel_id, user_id, log1, log2, log3, log4)
        session.add(discord_log)
        session.commit()


def discord_log_join(server_id=None, user_id=None, name=None, nick=None):
    discord_log(0, server_id, -1, user_id, log1=name, log2=nick)


def discord_log_left(server_id=None, user_id=None):
    discord_log(1, server_id, -1, user_id, log1=name, log2=nick)


def discord_log_chat(server_id=None, channel_id=None, user_id=None, text=None):
    discord_log(2, server_id, channel_id, user_id, text)


def discord_log_reaction_add(server_id=None, channel_id=None, user_id=None, message_id=None, reaction=None):
    discord_log(3, server_id, channel_id, user_id, log1=message_id, log2=reaction)


def discord_log_reaction_remove(server_id=None, channel_id=None, user_id=None, message_id=None, reaction=None):
    discord_log(4, server_id, channel_id, user_id, log1=message_id, log2=reaction)


def discord_log_join_vc(server_id=None, channel_id=None, user_id=None):
    discord_log(5, server_id, channel_id, user_id)


def discord_log_left_vc(server_id=None, channel_id=None, user_id=None):
    discord_log(6, server_id, channel_id, user_id)


def discord_log_left_vc(server_id=None, channel_id=None, user_id=None, target_channel=None):
    discord_log(7, server_id, channel_id, user_id, log1=target_channel)

