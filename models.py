from main import db

class User(db.Model):
    __tablename__ = "users"
    # user properties (db columns)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chat_id = db.Column(db.Integer)
    first_name = db.Column(db.String())
    tz_delta = db.Column(db.Integer, default=99)

    def __init__(self, chatId, firstName, tzDelta=99):
        self.chat_id = chatId
        self.first_name = firstName
        self.tz_delta = tzDelta


    def __repr__(self):
        return "<id{}>".format(self.id)


class Schedule(db.Model):
    __tablename__ = "schedules"
    # schedule properties (db columns)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chat_id = db.Column(db.Integer)
    coin_symbol = db.Column(db.String())
    coin_name = db.Column(db.String())
    is_daily = db.Column(db.Integer)
    time_daily = db.Column(db.Integer)
    hourly_interval = db.Column(db.Integer)
    last_send = db.Column(db.Integer)


    def __init__(self, chatId, isDaily, coinSymbol, coinName, timeDaily, hourlyInterval, lastSend=0):
        self.chat_id = chatId
        self.coin_symbol = coinSymbol
        self.coin_name = coinName
        self.is_daily = isDaily
        self.time_daily = timeDaily
        self.hourly_interval = hourlyInterval
        self.last_send = lastSend


    def __repr__(self):
        return "<id{}>".format(self.id)


class Alarm(db.Model):
    __tablename__ = "alarms"
    # schedule properties (db columns)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chat_id = db.Column(db.Integer)
    coin_symbol = db.Column(db.String())
    coin_name = db.Column(db.String())
    min_value = db.Column(db.Integer)
    max_value = db.Column(db.Integer)


    def __init__(self, chatId, coinSymbol, coinName, minValue, maxValue):
        self.chat_id = chatId
        self.coin_symbol = coinSymbol
        self.coin_name = coinName
        self.min_value = minValue
        self.max_value = maxValue


    def __repr__(self):
        return "<id{}>".format(self.id)
