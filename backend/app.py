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
login = LoginManager(app)

# app.jinja_env.trim_blocks = True
# app.jinja_env.lstrip_blocks = True

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret string')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', prefix + os.path.join(app.root_path, 'disk.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path,'upload')

db = SQLAlchemy(app)
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
    root_of_default_user = FileNode(id = 0,filename='root',path_root='',parent_id=-1,type_of_node='dir')
    # 创建 管理员
    default_user = UserTable(uid=0, email='beiwang121@163.com',password_hash = generate_password_hash('123456'))
    db.session.add(root_of_default_user)
    db.session.add(default_user)
    db.session.commit()
    click.echo('Initialized database.')
# utils
# 处理文件名
import hashlib
def generate_file_name(parent_id,filename):
    return hashlib.md5(
                (str(parent_id) + '_' + filename).encode('utf-8')).hexdigest()

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
    # 基本信息
    id = db.Column(db.Integer,primary_key=True)
    filename = db.Column(db.String(50))
    path_root = db.Column(db.String(200))
    parent_id = db.Column(db.Integer,default = 0)
    type_of_node = db.Column(db.String(20),default='dir')
    size = db.Column(db.Integer,default = 0)
    upload_time = db.Column(db.DateTime)
    # 所属用户
    user_id = db.Column(db.Integer,db.ForeignKey('UserTable.uid'),default=0)

    # hdfs 相关
    hdfs_path = db.Column(db.String(50))
    hdfs_filename = db.Column(db.String(100))

class UserTable(UserMixin,db.Model):
    __tablename__ = 'UserTable'
    uid = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(100),unique=True,nullable=True)
    password_hash = db.Column(db.String(100), nullable=False)

    files = db.relationship('FileNode')

    def get_id(self):
        return self.user_id
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
'''
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
'''

'''RESTful API'''
class FilesView(Resource):
    file_fields={
        'id':fields.Integer,
        'filename':fields.String,
        'path_root':fields.String,
        'parent_id':fields.Integer,
        'type_of_node':fields.String,
        'size':fields.Integer,
        'upload_time':fields.DateTime,
        'uid':fields.Integer
    }
    @marshal_with(file_fields)
    def serialize_file(self,file):
        return file
    def __init__(self):
        self.req = request.args
        self.query = request.args['query']
    def post(self):
        if self.query == 'upload':# 上传文件
            cur_file_id = self.req['curId']# 获取当前文件夹id

            try:
                cur_file_node = FileNode.query.get(cur_file_id)
            except Exception as e:
                return jsonify(message='cur_file_node error')
            cur_file_path_root = cur_file_node.path_root
            cur_filename = cur_file_node.filename

            f = request.files['file'] # 获取上传的文件
            
            if f:
                filename = f.filename
                new_path_root = cur_file_path_root + '/' + cur_filename
                time = datetime.datetime.now()
                # 生成文件名的 hash
                actual_filename = generate_file_name(cur_file_id, filename)
                # 结合 UPLOAD_FOLDER 得到最终文件的存储路径
                target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), actual_filename)

                if os.path.exists(target_file):
                    return jsonify(message='error',code=409)
                try:
                    # 保存文件
                    f.save(target_file)
                    print(filename + 'saved')
                    filenode = FileNode(filename=filename,path_root = new_path_root,parent_id = cur_file_id,upload_time = time)
                    db.session.add(filename)
                    print('db added filenode')
                    db.session.commit()
                    return jsonify(message='OK')
                except Exception as e:
                    return jsonify(message='error')

        elif (self.query == 'addFolder'):# 新建文件夹
            cur_file_id = self.req['curId']# 获取当前文件夹id
            filename = self.req['foldername']# 获取新建文件夹的名称

            cur_file_node = FileNode.query.get(cur_file_id)
            cur_file_path_root = cur_file_node.path_root
            cur_filename = cur_file_node.filename

            new_path_root = cur_file_path_root + '/' + cur_filename
            time = datetime.datetime.now()
            try:
                filenode = FileNode(filename=filename,path_root = new_path_root,parent_id = cur_file_id,upload_time = time)
                db.session.add(filenode)
                db.session.commit()
                return jsonify(message='OK')
            except Exception as e:
                return jsonify(message='error')

        else:# 改名
            cur_file_id = self.req['curId']
            new_name = self.req['newName']
            try:
                target_file_node = FileNode.query.get(cur_file_id)
            except Exception as e:
                return jsonify(message='error')
            if target_file_node.type_of_node=='dir':# 如果是要修改目录的名字
                try:
                    target_file_node.filename = new_name# 先修改当前目录的名字
                    children = FileNode.query.filter_by(parent_id=cur_file_id)
                    # 循环修改孩子结点的path_root
                    for child in children:
                        old_path_root = child.path_root
                        prefix = old_path_root.split('/')[:-1]
                        child.path_root = '/'.join(prefix) + '/' + new_name
                    db.session.commit()
                    return jsonify(message='OK')
                except Exception as e:
                    return jsonify(message='error')
            else:# 如果修改的是文件
                try:
                    # 修改文件名
                    old_actual_filename = generate_file_name(cur_file_id, target_file_node.filename)
                    # 结合 UPLOAD_FOLDER 得到最终文件的存储路径
                    old_target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), old_actual_filename)

                    new_actual_filename = generate_file_name(cur_file_id, target_file_node.filename)
                    # 结合 UPLOAD_FOLDER 得到最终文件的存储路径
                    new_target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), old_actual_filename)
                    # 本地文件重命名
                    if os.path.exists(old_target_file):
                        os.rename(old_target_file,new_actual_filename)
                    # 修改数据库中的文件名
                    target_file_node.filename = new_name# 修改当前文件的名字
                    db.session.commit()
                except Exception as e:
                    return jsonify(message='error')

    def get(self):
        cur_file_id = self.req['curId']
        try:
            file_node = FileNode.query.get(cur_file_id)
        except Exception as e:
            return jsonify(message='error')
        
        if self.query == 'getInfo': # 获取信息
            return self.serialize_file(file_node)
        elif self.query == 'download': #下载
            filename = file_node.filename
            # 生成文件名的 hash
            actual_filename = generate_file_name(cur_file_id, filename)
            # 结合 UPLOAD_FOLDER 得到最终文件的存储路径
            target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), actual_filename)
            if os.path.exists(target_file):
                return send_file(target_file)
            else:
                return jsonify(message='error',code='404')
        elif self.query == 'getAll': # 获取该用户的所有文件信息
            cur_uid = self.req['curUid']
            try:
                file_nodes = FileNode.query.filter_by(user_id=cur_uid)
                return jsonify(data=[ serialize(file) for file in file_nodes])
            except Exception as e:
                return jsonify(message='error')
        else: # delete
            if file_node.type_of_node == 'dir':# 如果删除的是文件夹
                children = FileNode.query.filter_by(parent_id=cur_file_id)
                # 循环删除
                for child in children:
                    delete_node(child)
                delete_node(file_node)
                return jsonify('LOOP delete OK')
            else: # 如果是删除文件
                delete_node(file_node)
                return jsonify('delete file OK')
api.add_resource(FilesView,'/file')


# 辅助函数
# 删除结点
def delete_node(file_node):
    # 把此结点从数据库中删除
    try:
        db.session.delete(file_node)
        db.session.commit()
        return jsonify(message='delete success')
    except Exception as e:
        return jsonify(message='error')
    # 如果删除的是文件，则先把文件从系统中删除
    if file_node.type_of_node != 'dir':
        filename = file_node.filename
        # 生成文件名的 hash
        actual_filename = generate_file_name(cur_file_id, filename)
        # 结合 UPLOAD_FOLDER 得到最终文件的存储路径
        target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), actual_filename)
        if os.path.exists(target_file):
            os.remove(target_file)
    


'''
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
        target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), actual_filename)
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
            if os.path.exists(target_file):
                return send_file(target_file)
            else:
                return jsonify(message='error',code='404')
            # with hdfs_client.read(hdfs_path+file_name) as reader:
            #     buf = reader.read()
            #     return send_file(buf)
        elif self.query == 'delete':
            # 获得 父目录
            parent_path = get_parent_path(full_path) # parent_path = a/b
            parent_folder_name = get_parent_folder_name(full_path) # parent_folder_name = c
            if os.path.exists(target_file):
                try:
                    # 在hdfs中删除
                    # hdfs_client.delete(hdfs_path+file_name)

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
                # 结合 UPLOAD_FOLDER 得到最终文件的存储路径
                target_file = os.path.join(os.path.expanduser(app.config['UPLOAD_FOLDER']), actual_filename)
            
                # hdfs_path = '/user/hadoop' + datetime.date.today().strftime("/%Y/%m/%d/")
                # hdfs_path = '/user/hadoop/'
                # hdfs_filename = actual_filename
                # data = f.read()

                if os.path.exists(target_file):
                    return jsonify(message='error',code=409)
                print('after data ')
                try:
                    # 保存文件
                    f.save(target_file)
                    # hdfs_client.write(hdfs_path + hdfs_filename, data=data)
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
'''
@login.user_loader
def load_user(id):
	return UserTable.query.get(int(id))

# apis
class Login(Resource):
	def post(self):
		if current_user.is_authenticated:
			# TODO
			return jsonify('already authenticated')
		parse = reqparse.RequestParser()
		parse.add_argument('email',type=int,help='邮箱验证不通过',default='beiwang121@163.com')
		parse.add_argument('password',type=str,help='密码验证不通过')
		args = parse.parse_args()

		email = args.get("email")
		password = args.get("password")
		try:
			user = UserTable.query.filter(email==email).first()
		except Exception:
			print("{} User query: {} failure......".format(time.strftime("%Y-%m-%d %H:%M:%S"),email))
			return jsonify('user not found')
		else:
			print("{} User query: {} success...".format(time.strftime("%Y-%m-%d %H:%M:%S"), email))
		finally:
			db.session.close()
		if user and user.varify_password(password):
			login_user(user)
			print(current_user)
			return jsonify('login success')
		else:
			print('in if')
			print("{} User query: {} failure...".format(time.strftime("%Y-%m-%d %H:%M:%S"), email))
			print('user is None or password False')
			return jsonify('login fail')
		
class Register(Resource):
	def post(self):
		parse = reqparse.RequestParser()
		parse.add_argument('email',type=int,help='email验证不通过',default='beiwang121@163.com')
		parse.add_argument('password',type=str,help='密码验证不通过')
		args = parse.parse_args()

		email = args.get('email')
		password = args.get('password')
		password_hash = generate_password_hash(password)
		try:
			user = UserTable(email = email,password_hash =password_hash)
			db.session.add(user)
			db.session.commit()
		except:
			print("{} User add: {} failure...".format(time.strftime("%Y-%m-%d %H:%M:%S"), email))
			db.session.rollback()
			return jsonify('user add fail')
		else:
			print("{} User add: {} success...".format(time.strftime("%Y-%m-%d %H:%M:%S"), email))
			return jsonify('user add success')
		finally:
			db.session.close()
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Register, '/register', endpoint='register')

class LoginOut(Resource):
	@login_required
	def get():
	    logout_user()
	    flash("已退出登录")
	    return jsonify('loginout success')
api.add_resource(LoginOut,'/loginout',endpoint='loginout')

if __name__ == '__main__':
	app.run()
