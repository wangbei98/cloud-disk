from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from flask_restful import fields,marshal_with


# Models
class FileNode(db.Model):
    # 基本信息
    __tablename__='FileNode'
    id = db.Column(db.Integer,primary_key=True)
    filename = db.Column(db.String(50))
    path_root = db.Column(db.String(200))
    # 默认存到根目录 （-1）
    parent_id = db.Column(db.Integer,default = -1)
    # 默认是文件夹
    type_of_node = db.Column(db.String(20),default='dir')
    size = db.Column(db.Integer,default = 0)
    upload_time = db.Column(db.Integer)
    # 所属用户
    user_id = db.Column(db.Integer,db.ForeignKey('UserTable.uid'))

    is_share = db.Column(db.Boolean, default=False)
    shares = db.relationship('ShareTable')

    # hdfs 相关
    hdfs_path = db.Column(db.String(50))
    hdfs_filename = db.Column(db.String(100))


    file_fields={
        'id':fields.Integer,
        'filename':fields.String,
        'path_root':fields.String,
        'parent_id':fields.Integer,
        'type_of_node':fields.String,
        'size':fields.Integer,
        'upload_time':fields.Integer,
        'user_id':fields.Integer,
        'is_share':fields.Boolean,
        'shares':fields.List(fields.Nested({
            'share_id':fields.Integer,
            'file_id':fields.Integer,
            'share_url':fields.String,
            'share_token':fields.String,
            'share_begin_time':fields.Integer,
            'share_end_time':fields.Integer
            }))
    }
    @marshal_with(file_fields)
    def to_json(self):
        return self

class ShareTable(db.Model):
    __tablename__='ShareTable'
    share_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    file_id = db.Column(db.Integer,db.ForeignKey('FileNode.id'))
    share_url = db.Column(db.String(100),nullable=False)
    share_token = db.Column(db.String(20),default='')
    share_begin_time = db.Column(db.Integer)
    share_end_time = db.Column(db.Integer)

    share_fields = {
        'share_id':fields.Integer,
        'file_id':fields.Integer,
        'share_url':fields.String,
        'share_token':fields.String,
        'share_begin_time':fields.Integer,
        'share_end_time':fields.Integer
    }
    @marshal_with(share_fields)
    def to_json(self):
        return self
class UserTable(UserMixin,db.Model):
    __tablename__ = 'UserTable'
    uid = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(100),unique=True,nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)

    files = db.relationship('FileNode')

    def get_id(self):
        return self.uid
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)
    def varify_password(self,password):
        return check_password_hash(self.password_hash,password)
    def __repr__(self):
        return "<User {}>".format(self.email)