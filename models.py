from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate

db = SQLAlchemy()

def create_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://xlhvqyldvmigns:93709ec366f14884dd2f666a007bf463a1f125c0696b3cd7f301230a85753a2a@ec2-18-214-195-34.compute-1.amazonaws.com:5432/d966buti312f0r" # "postgresql://postgres:postgres@localhost:5432/postgres"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    # migrate = Migrate(app, db)


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
