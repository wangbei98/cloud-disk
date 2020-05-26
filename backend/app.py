import os
import sys
import json
import click
import datetime, time
from flask import Flask
from flask import redirect, url_for, abort, render_template, flash,request,send_file,abort,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask import jsonify
import hdfs
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import Api,Resource,fields,marshal_with,marshal_with_field,reqparse
from flask_login import LoginManager,UserMixin,login_user, logout_user, current_user, login_required
from extensions import db,login_manager
from APIS.auth import Login,Register,Logout,GetCurUserAPI,RefreshTokenAPI
from APIS.resources import UploadAPI,GetInfoAPI,DownloadFileAPI,ReNameAPI,NewFolderAPI,GetAllAPI,DeleteAPI,PreviewAPI
from APIS.resources import ShareAPI,CancelShareAPI,DownloadShareAPI,PreviewShareAPI
from APIS.resources import ShareInfoAPI
from models import UserTable,FileNode
from settings import config
import logging
from logging.handlers import RotatingFileHandler

from flask_cors import CORS
from flask import request

# SQLite URI compatiblec
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)

# app.jinja_env.trim_blocks = True
# app.jinja_env.lstrip_blocks = True

app.config['SECRET_KEY'] = config['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', prefix + os.path.join(app.root_path, 'disk.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path,'upload')

# restful api
api = Api(app)
login = LoginManager(app)
db.init_app(app)
login_manager.init_app(app)

config = {
  'ORIGINS': [
    'http://localhost:8080',  # React
    'http://127.0.0.1:8080',  # React
  ],

  'SECRET_KEY': '...'
}
# CORS(app,resources={r"/api/*": {"origins": config['ORIGINS']}},support_credentials=True)
CORS(app, resources={ r'/api/*': {'origins': config['ORIGINS']}}, supports_credentials=True)
# logging
app.logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(astime)s - %(name)s - %(levelname)s - %(message)s ')
file_handler = RotatingFileHandler('logs/cloud-disk.log',maxBytes=10*1024*1024,backupCount=10)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
if not app.debug:
    app.logger.addHandler(file_handler)


@app.route('/')
def index():
    return '<h1>index<h1>'

# hdfs client
# hdfs_client = hdfs.Client("http://116.62.177.146:50070")

# handlers
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, FileNode=FileNode,UserTable=UserTable)   

@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
        click.echo('Drop tables')
    db.create_all()
    # 在数据库中存储一个默认根目录 root  id = 0
    root_of_default_user = FileNode(id = -1,filename='',path_root='',parent_id=-2,type_of_node='dir')
    # 创建 管理员
    default_user = UserTable(uid=-1, email='beiwang121@163.com',password_hash = generate_password_hash('123456'))
    db.session.add(root_of_default_user)
    db.session.add(default_user)
    db.session.commit()
    click.echo('Initialized database.')


#TODO 分享相关
# # 生成新的短地址
# import random
# _random = random.SystemRandom()

# def get_random_long_int():
#     return _random.randint(1000000000, 9999999999)
# @app.route('/folders/<folder_name>', methods=['GET','POST', 'DELETE'])
# def generate_url():
#     return base36_encode(get_random_long_int())



api.add_resource(Login, '/api/login', endpoint='login')
api.add_resource(Register, '/api/register', endpoint='register')
api.add_resource(Logout,'/api/logout',endpoint='logout')

api.add_resource(RefreshTokenAPI,'/api/user/refreshtoken',endpoint='refreshtoken')
api.add_resource(GetCurUserAPI,'/api/user/getcur',endpoint = 'getcur')

api.add_resource(UploadAPI,'/api/file/upload',endpoint='upload')
api.add_resource(GetInfoAPI,'/api/file/getInfo',endpoint='getInfo')
api.add_resource(DownloadFileAPI,'/api/file/download',endpoint='download')
api.add_resource(ReNameAPI,'/api/file/reName',endpoint='reName')
api.add_resource(NewFolderAPI,'/api/file/newFolder',endpoint='newFolder')
api.add_resource(GetAllAPI,'/api/file/all',endpoint='all')
api.add_resource(DeleteAPI,'/api/file/delete',endpoint='delete')
api.add_resource(PreviewAPI,'/api/file/preview',endpoint='preview')

api.add_resource(ShareAPI,'/api/file/share',endpoint='share')
api.add_resource(CancelShareAPI,'/api/file/share/cancel',endpoint='cancel')

api.add_resource(DownloadShareAPI,'/api/file/share/download/<url>',endpoint='downloadshare')
api.add_resource(PreviewShareAPI,'/api/file/share/preview/<url>',endpoint='previewshare')
api.add_resource(ShareInfoAPI,'/api/file/share/info/<url>',endpoint='shareinfo')

if __name__ == '__main__':
	app.run()
