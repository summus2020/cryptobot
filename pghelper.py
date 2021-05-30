import models


db = models.db


def user_exists(chatId):
    user = db.session.query(models.User).filter(models.User.chat_id==chatId).first()
    db.session.commit()
    if user is not None:
        return True
    else:
        return False


def add_user(chatId, firstName):
    user = models.User(chatId, firstName)
    db.session.add(user)
    db.session.commit()


def get_user_info(chatId):
    user = db.session.query(models.User).filter(models.User.chat_id==chatId).first()
    db.session.commit()
    return user


def set_tz_delta(chatId, tzDelta):
    # user = db.session.query(User).filter(User.chat_id==chatId)
    user = db.session.query(models.User).filter(models.User.chat_id==chatId).update({models.User.tz_delta: tzDelta}, synchronize_session=False)
    db.session.commit()


def timezone_delta_exists(chatId):
    user = db.session.query(models.User).filter(models.User.chat_id==chatId).first()
    if user.tz_delta < 24:
        return True
    else:
        return False


def get_timezone_delta(chatId):
    user = db.session.query(models.User).filter(models.User.chat_id==chatId).first()
    db.session.commit()
    return user.tz_delta


def get_all_users():
    users = models.User.query.all()
    db.session.commit()
    return users

# ======== SCHEDULES ========
def get_schedules(chatId):
    scheds = db.session.query(models.Schedule).filter(models.Schedule.chat_id == chatId)
    db.session.commit()
    if len(scheds.all()) > 0:
        return scheds
    else:
        return None


def add_schedule(chatId, isDaily, coinSymbol, coinName, timeDaily=0, hourlyInterval=0):
    sched = models.Schedule(chatId, isDaily, coinSymbol, coinName, timeDaily, hourlyInterval)
    db.session.add(sched)
    db.session.commit()


def get_schedule_for_coin(chatId, coinSymbol):
    sched = db.session.query(models.Schedule).filter(models.Schedule.chat_id == chatId, models.Schedule.coin_symbol == coinSymbol).first()
    db.session.commit()
    return sched


def delete_schedule(chatId, coinSymbol):
    sched = db.session.query(models.Schedule).filter(models.Schedule.chat_id == chatId, models.Schedule.coin_symbol == coinSymbol).first()
    db.session.delete(sched)
    db.session.commit()


def schedule_exists(chatId, coinSymbol):
    sched = db.session.query(models.Schedule).filter(models.Schedule.chat_id == chatId, models.Schedule.coin_symbol == coinSymbol).first()
    if sched is not None:
        return True
    else:
        return False


def set_scheduled_last_send(chatId, coinSymbol, lastSend):
    sched = db.session.query(models.Schedule).filter(models.Schedule.chat_id==chatId, models.Schedule.coin_symbol==coinSymbol).update({models.Schedule.last_send: lastSend}, synchronize_session=False)
    db.session.commit()


def update_daily_time_with_tz(idIndx, newTime):
    sched = db.session.query(models.Schedule).filter(models.Schedule.id==idIndx).update({models.Schedule.time_daily: newTime}, synchronize_session=False)
    db.session.commit()


def get_alarms(chatId):
    alarms = db.session.query(models.Alarm).filter(models.Alarm.chat_id == chatId)
    db.session.commit()
    if len(alarms.all()) > 0:
        return alarms
    else:
        return None


def add_alarm(chatId, coinSymbol, coinName, minValue, maxValue):
    alarm = models.Alarm(chatId, coinSymbol, coinName, minValue, maxValue)
    db.session.add(alarm)
    db.session.commit()


def get_alarm_for_coin(chatId, coinSymbol):
    alarm = db.session.query(models.Alarm).filter(models.Alarm.chat_id == chatId, models.Alarm.coin_symbol == coinSymbol).first()
    db.session.commit()
    return alarm


def delete_alarm(chatId, coinSymbol):
    alarm = db.session.query(models.Alarm).filter(models.Alarm.chat_id == chatId, models.Alarm.coin_symbol == coinSymbol).first()
    db.session.delete(alarm)
    db.session.commit()


def reset_alarm_min_max(chatId, coinSymbol, for_max):
    if for_max > 0:
        sched = db.session.query(models.Alarm).filter(models.Alarm.chat_id==chatId, models.Alarm.coin_symbol==coinSymbol).update({models.Alarm.max_value: 0}, synchronize_session=False)
    else:
        sched = db.session.query(models.Alarm).filter(models.Alarm.chat_id==chatId, models.Alarm.coin_symbol==coinSymbol).update({models.Alarm.min_value: 0}, synchronize_session=False)
    db.session.commit()
