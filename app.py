from flask import Flask, request, jsonify, render_template, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from data.data_functions import *
from simulation.simulation_models import *
from optimization.optimization import *
import itertools
from datetime import time, timedelta
import warnings
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

warnings.filterwarnings("ignore")


db = SQLAlchemy()
# flask db init
# flask db migrate
# flask db upgrade

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")


    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///./bemanningslanternenDB.db'
    app.secret_key = 'KPMGs Bemanningslanterne'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)


    from models import User
    
    @login_manager.user_loader
    def load_user(uid):
        return User.query.get(uid)
    
    @login_manager.unauthorized_handler
    def unauth_callback():
        return "You are not logged in, please do so before proceeding"


    bcrypt = Bcrypt()


    from routes import register_routes
    register_routes(app,db)

    migrate = Migrate(app,db)
    
    return app

