from flask import Flask,g,request,jsonify
import mysql.connector
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
from project.paypal import paypal_bp
from project.sms import sms_bp

app = Flask(__name__)

@app.before_request
def before_request():
    g.db=mysql.connector.connect(
        user = os.environ['MYSQL_USER'],
        password = os.environ['MYSQL_PASSWORD'],
        host = os.environ['MYSQL_HOST'],
        database = os.environ['MYSQL_DB']
    )

@app.after_request
def after_request(response):
    g.db.close()
    return response

app.config['JWT_SECRET_KEY']=os.environ['JWT_SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES']=timedelta(days=1)    

jwt = JWTManager(app)

app.register_blueprint(paypal_bp,url_prefix="/v1/paypal/")
app.register_blueprint(sms_bp,url_prefix="/v1/sms/")