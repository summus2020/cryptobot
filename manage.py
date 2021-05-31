from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import app
from models import db

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://xlhvqyldvmigns:93709ec366f14884dd2f666a007bf463a1f125c0696b3cd7f301230a85753a2a@ec2-18-214-195-34.compute-1.amazonaws.com:5432/d966buti312f0r" # "postgresql://postgres:postgres@localhost:5432/alex" #
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()