import os
import sys
import json
import click
import datetime, time
from flask import Flask
from flask import redirect, url_for, abort, render_template, flash,request,send_file
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask import jsonify
from flask_restful import Api,Resource,fields,marshal_with,marshal_with_field
import hdfs

# SQLite URI compatiblec
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)

@app.route('/')
def index():
	return '<h1> hello world </h1>'

# restful api
api = Api(app)

# app.jinja_env.trim_blocks = True
# app.jinja_env.lstrip_blocks = True

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret string')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', prefix + os.path.join(app.root_path, 'disk.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path,'upload')

db = SQLAlchemy(app)
# hdfs client
hdfs_client = hdfs.Client("http://116.62.177.146:50070")

# handlers
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, FileNode=FileNode)


@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
        click.echo('Drop tables')
    db.create_all()
    # 在数据库中存储一个默认根目录 root  id = 0
    root = FileNode(path='',name='root',isFolder=True,children='')
    db.session.add(root)
    db.session.commit()
    click.echo('Initialized database.')


# utils
# 处理文件名
import hashlib
def generate_file_name(path,file_name):
    return hashlib.md5(
                (path + '_' + file_name).encode('utf-8')).hexdigest()

def base36_encode(number):
    assert number >= 0, 'positive integer required'
    if number == 0:
        return '0'
    base36 = []
    while number != 0:
        number, i = divmod(number, 36)
        base36.append('0123456789abcdefghijklmnopqrstuvwxyz'[i])
    return ''.join(reversed(base36))

#TODO 分享相关
# # 生成新的短地址
# import random
# _random = random.SystemRandom()

# def get_random_long_int():
#     return _random.randint(1000000000, 9999999999)
# @app.route('/folders/<folder_name>', methods=['GET','POST', 'DELETE'])
# def generate_url():
#     return base36_encode(get_random_long_int())

# Models
class FileNode(db.Model):
    path = db.Column(db.String(200),primary_key=True,default='')
    name = db.Column(db.String(32),primary_key=True)
    isFolder = db.Column(db.Boolean,default=True)
    children = db.Column(db.Text,default='')

    hdfs_path = db.Column(db.String(50))
    hdfs_filename = db.Column(db.String(100))

# class Folder(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     folder_name = db.Column(db.Text,unique=True)
#     # TODO : 用双亲表示法 表示目录之间的包含关系
#     parent_folder_id = db.Column(db.Integer)
#     files = db.relationship('File',uselist=True,back_populates = 'folder')
#     # optional
#     def __repr__(self):
#         return '<Folder %r>' % self.name

# '''folder 与 folder 之间通过 parent_folder_id 相关联'''
# '''folder 与 file 通过 db.relationship 相关联'''

# class File(db.Model):
#     id = db.Column(db.Integer,primary_key=True)
#     folder_id = db.Column(db.Integer,db.ForeignKey('folder.id'))
#     file_name = db.Column(db.Text)
#     folder = db.relationship('Folder',uselist=False,back_populates='files')

#     # optional
#     def __repr__(self):
#         return '<File %r>' % self.file_name

def get_parent_path(full_path):
    splited_path = full_path.split('/')
    return '/'.join(splited_path[:-2])
def get_parent_folder_name(full_path):
    splited_path = full_path.split('/')
    if len(splited_path) >= 2:
        return splited_path[-2]
    else:
        return ''
def get_path(full_path):
    splited_path = full_path.split('/')
    return '/'.join(splited_path[:-1])
def get_name(full_path):
    splited_path = full_path.split('/')
    if len(splited_path) >= 1:
        return splited_path[-1]
    else:
        return ''

'''RESTful API'''
class FoldersView(Resource):
    folder_fields = {
        'name':fields.String,
        'isFolder':fields.Boolean,
        'children':fields.String
    }
    @marshal_with(folder_fields)
    def serialize_folder(self,folder):
        return folder

    def __init__(self):
        self.req = request.args
        self.query = request.args['query']
    ## GET 获取文件夹信息 http://xxxxx/a/b/c
    ## GET 删除文件夹 http://xxxx/a/b/c
    def get(self,full_path):
        print('folderView -> get')
        path = get_path(full_path)
        folder_name = get_name(full_path)
        print('full_path: ' + full_path)
        print('path: ' + path)
        print('folder_name: ' + folder_name)
        # 获取当前folder对象
        try:
            folder = FileNode.query.filter(FileNode.path == path,FileNode.name == folder_name).first()
            print(folder)
        except Exception as e:
            return jsonify(message='error',code=404)
        # 获取当前文件夹信息
        if self.query == 'getInfo':
            print('folderView -> get -> getInfo')
            return self.serialize_folder(folder)
        # 删除当前文件夹
        elif self.query == 'delete':
            # 获得 父目录
            parent_path = get_parent_path(full_path)
            parent_folder_name = get_parent_folder_name(full_path)
            try:
                # 删除当前文件夹在父目录中的内容
                parent_folder = FileNode.query.filter(FileNode.path == parent_path,FileNode.name == parent_folder_name).first()
                children = parent_folder.children.split(',')
                print('before: ')
                print(children)
                children.remove(folder_name)
                parent_folder.children = ','.join(children)
                print('after: ')
                print(children)
                # 删除当前文件夹的子文件
                itsChildren = folder.children.split(',')[1:]
                print('its children: ')
                print(itsChildren)
                for child_name in itsChildren:
                    if len(child_name) > 0:
                        print(full_path)
                        print(child_name)
                        child = FileNode.query.filter(FileNode.path == full_path,FileNode.name == child_name).first()
                        db.session.delete(child)
                # 删除当前文件夹
                db.session.delete(folder)
                db.session.commit()

            except Exception as e:
                return jsonify(message='error',code=409)
            return jsonify(message='OK')
    # POST 添加文件夹  http://xxxxa/b/c
    # POST 修改文件名 http://xxxxx/a/b/c
    def post(self,full_path):
        if self.query == 'add':
            path = get_path(full_path)
            folder_name = get_name(full_path)
            name = self.req['name']
            print('full_path: ' + full_path)
            print('path: ' + path)
            print('folder_name: ' + folder_name)
            print('name: ' + name)
            try:
                # 父文件夹对象
                parent_folder = FileNode.query.filter(FileNode.path == path,FileNode.name == folder_name).first()
                print(parent_folder)
                # 新文件夹对象
                new_folder = FileNode(path=full_path,name=name,isFolder=True)
                # 修改父目录对象的children
                parent_folder.children = parent_folder.children + ',' + name
                db.session.add(new_folder)
                db.session.commit()
                return jsonify(message='OK')
            except Exception as e:
                return jsonify(message='error')
        elif self.query == 'reName':
            path = get_path(full_path)
            folder_name = get_name(full_path)
            parent_path = get_parent_path(full_path)
            parent_folder_name = get_parent_folder_name(full_path)
            new_name = self.req['newName']
            print('full_path: ' + full_path)
            print('path: ' + path)
            print('folder_name: ' + folder_name)
            print('parent_path: ' + parent_path)
            print('parent_folder_name: ' + parent_folder_name)
            print('new_name: ' + new_name)
            # 获取当前folder对象
            try:
                folder = FileNode.query.filter(FileNode.path == path,FileNode.name == folder_name).first()
                print(folder)
            except Exception as e:
                return jsonify(message='error',code=404)
            try:

                # 修改当前文件夹的子文件的路径
                itsChildren = folder.children.split(',')[1:]
                print('its children: ')
                print(itsChildren)
                for child_name in itsChildren:
                    if len(child_name) > 0:
                        child = FileNode.query.filter(FileNode.path == full_path,FileNode.name == child_name).first()
                        child_path = child.path.split('/')
                        child_path[-1] = new_name
                        child.path = '/'.join(child_path)
                        db.session.delete(child)

                # 修改父目录中的children
                parent_folder = FileNode.query.filter(FileNode.path == parent_path,FileNode.name == parent_folder_name).first()
                print(parent_folder)
                children = parent_folder.children.split(',')
                print('old_children: ' + parent_folder.children)
                print(children)
                # children = children.replace(folder_name,new_name)# 就是这一句有问题
                children = [new_name if e == folder_name else e for e in children]
                print('new_children: ')
                print(children)
                parent_folder.children = ','.join(children)
                

                # 修改当前目录的名字
                folder = FileNode.query.filter(FileNode.path == path,FileNode.name == folder_name).first()
                print(folder)
                folder.name = new_name
                db.session.commit()
                return jsonify(message='OK')
            except Exception as e:
                return jsonify(message='error') 
api.add_resource(FoldersView,'/folders/<path:full_path>')

class FilesView(Resource):
    file_fields = {
        'name':fields.String,
    }
    @marshal_with(file_fields)
    def serialize_file(self,file):
        return file

    def __init__(self):
        self.req = request.args
        self.query = request.args['query']
    
    def get(self,full_path):# full_path = a/b/c/test.py
        path = get_path(full_path) # path = a/b/c
        file_name = get_name(full_path) # file_name = test.py
        # 生成文件名的 hash
        actual_filename = generate_file_name(path,file_name)
        # 结合 UPLOAD_FOLDER 得到最终文件的存储路径
        # target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), actual_filename)
        try:
            # 获得当前 文件对象
            file = FileNode.query.filter(FileNode.path == path,FileNode.name == file_name).first()
            hdfs_path = file.hdfs_path
        except Exception as e:
            return jsonify(message='error')
        
        ## 分类处理
        if self.query == 'getInfo':
            return self.serialize_file(file)
        elif self.query == 'download':
            # if os.path.exists(target_file):
            #     return send_file(target_file)
            # else:
            #     return jsonify(message='error',code='404')
            with hdfs_client.read(hdfs_path+file_name) as reader:
                buf = reader.read()
                return send_file(buf)
        elif self.query == 'delete':
            # 获得 父目录
            parent_path = get_parent_path(full_path) # parent_path = a/b
            parent_folder_name = get_parent_folder_name(full_path) # parent_folder_name = c
            if os.path.exists(target_file):
                try:
                    # 在hdfs中删除
                    hdfs_client.delete(hdfs_path+file_name)

                    # 删除当前文件在父目录中的内容
                    parent_folder = FileNode.query.filter(FileNode.path == parent_path,FileNode.name == parent_folder_name).first() # c
                    children = parent_folder.children.split(',')
                    children.remove(file_name)
                    parent_folder.children = ','.join(children)
                    # 删除文件以及文件在数据库中的记录
                    db.session.delete(file)
                    db.session.commit()
                    os.remove(target_file)
                    return jsonify(message='OK')
                except Exception as e:
                    app.logger.exception(e)
                    return jsonify(message='error',code=500)
            else:
                return jsonify(message='error',code=404)
    def post(self,full_path):
        
        if self.query == 'upload':# a/b/c
            path = get_path(full_path)# path = a/b
            folder_name = get_name(full_path) # folder_name = c
            print(path)
            print(folder_name)
            try:
                # 获得当前文件夹
                parent_folder = FileNode.query.filter(FileNode.path == path,FileNode.name == folder_name).first() # c
                print(parent_folder)
            except Exception as e:
                return jsonify(message='error')
            f = request.files['file']
            if f:
                # 生成文件名的 hash
                actual_filename = generate_file_name(full_path, f.filename)
                # actual_filename = f.filename
                # 结合 UPLOAD_FOLDER 得到最终文件的存储路径
                # target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), actual_filename)
            
                hdfs_path = '/user/hadoop' + datetime.date.today().strftime("/%Y/%m/%d/")
                # hdfs_path = '/user/hadoop/'
                hdfs_filename = actual_filename
                data = f.read()

                if os.path.exists(target_file):
                    return jsonify(message='error',code=409)
                print('after data ')
                try:
                    # 保存文件
                    # f.save(target_file)
                    # print(hdfs_path+hdfs_filename)
                    # print(data)
                    hdfs_client.write(hdfs_path + hdfs_filename, data=data)
                    # print(hdfs_client.list('/user/hadoop'))
                    # hdfs_client.write(hdfs_path + hdfs_filename,data)
                    # print(target_file)
                    # hdfs_client.upload(hdfs_path+hdfs_filename,target_file,overwriten=True)
                    print('hdfs saved')
                    f2 = FileNode(path = full_path,name = f.filename,isFolder=False,hdfs_path=hdfs_path, hdfs_filename=hdfs_filename)
                    print('create f2')
                    db.session.add(f2)
                    print('db add f2')
                    parent_folder.children = parent_folder.children + ',' + f.filename
                    db.session.commit()
                    return jsonify(message='OK')
                except Exception as e:
                    return jsonify(message='error')
        elif self.query == 'reName': # a/b/c/test.py
            path = get_path(full_path)# path = a/b/c
            file_name = get_name(full_path) # folder_name = test.py
            parent_path = get_parent_path(full_path) # parent_path = a/b
            parent_folder_name = get_parent_folder_name(full_path) # parent_folder_name = c
            new_name = self.req['newName']
            try:
                # 在hdfs重命名
                file = FileNode.query.filter(FileNode.path == path,FileNode.name == file_name).first()
                hdfs_path = file.hdfs_path
                old_name = generate_file_name(path,file_name)
                new_name = generate_file_name(path,new_name)
                hdfs_client.rename(hdfs_path+old_name,hdfs_path+new_name)

                # 修改父目录中的children
                parent_folder = FileNode.query.filter(FileNode.path == parent_path,FileNode.name == parent_folder_name).first() # c
                print(parent_folder)
                children = parent_folder.children.split(',')
                print('before children : ')
                print(children)
                # children.replace(folder_name,new_name)
                children = [new_name if e == file_name else e for e in children]
                print('after children : ')
                print(children)
                parent_folder.children = ','.join(children)
                print('after parent_folder')
                print(parent_folder)
                # 修改当前目录的名字
                folder = FileNode.query.filter(FileNode.path == path,FileNode.name == file_name).first() # test.py
                folder.name = new_name
                db.session.commit()
                return jsonify(message='OK')
            except Exception as e:
                return jsonify(message='error') 
            
api.add_resource(FilesView,'/files/<path:full_path>')

if __name__ == '__main__':
	app.run()
