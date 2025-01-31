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



    from routes import register_routes
    register_routes(app,db)

    migrate = Migrate(app,db)
    
    return app



# if __name__ == '__main__':
#     # app.run(debug=True)
#     from werkzeug.serving import run_simple
#     run_simple('localhost', 5000, app)
