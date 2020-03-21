import os
import sys
import json
import time
import datetime
import click
from flask import Flask,request,abort
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import Api,Resource,fields,marshal_with,marshal_with_field,reqparse
from flask_login import LoginManager,UserMixin,login_user, logout_user, current_user, login_required
from models import FileNode,UserTable
from extensions import db,login_manager
from werkzeug.datastructures import FileStorage
from settings import config
from flask import send_file,make_response

UPLOAD_FOLDER = config['UPLOAD_FOLDER']

class UploadAPI(Resource):
	def post(self):
		# print(UPLOAD_FOLDER)
		parse = reqparse.RequestParser()
		parse.add_argument('curId',type=int,help='错误的curId',default='0')
		parse.add_argument('file', type=FileStorage, location='files')
		
		args = parse.parse_args()
		# 获取当前文件夹id
		cur_file_id = args.get('curId')
		f = args['file']
		try:
			cur_file_node = FileNode.query.get(cur_file_id)
		except:
			return jsonify(code=11,message='node not exist, query fail')
		cur_file_path_root = cur_file_node.path_root
		cur_filename = cur_file_node.filename

		# f = request.files['file'] # 获取上传的文件
		# print(f.filename)
		# print(f.filename.split('.')[-1])
		# print(cur_file_path_root)
		# print(cur_filename)
		
		if f:
			filename = f.filename
			new_path_root = cur_file_path_root + '/' + cur_filename
			d_time = int(time.time())
			# 生成文件名的 hash
			actual_filename = generate_file_name(cur_file_id, filename)
			# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
			target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), actual_filename)

			if os.path.exists(target_file):
				return jsonify(code=21,message='file already exist, save fail')
			try:
				# 保存文件
				f.save(target_file)
				# print(filename + ' saved')
				filenode = FileNode(filename=filename,path_root = new_path_root,parent_id = cur_file_id,type_of_node=filename.split('.')[-1],upload_time = d_time)
				db.session.add(filenode)
				# print('db added filenode')
				db.session.commit()
				return jsonify(code=0,message='OK')
			except:
				return jsonify(code=12,message='node already exist , add fail')
class GetInfoAPI(Resource):
	file_fields={
		'id':fields.Integer,
		'filename':fields.String,
		'path_root':fields.String,
		'parent_id':fields.Integer,
		'type_of_node':fields.String,
		'size':fields.Integer,
		'upload_time':fields.Integer,
		'uid':fields.Integer
	}
	@marshal_with(file_fields)
	def serialize_file(self,file):
		return file
	def get(self):
		parse = reqparse.RequestParser()
		parse.add_argument('id',type=int,help='错误的id',default='0')
		args = parse.parse_args()
		# 获取当前文件夹id
		file_id = args.get('id')
		try:
			file_node = FileNode.query.get(file_id)
			child = FileNode.query.filter_by(parent_id=file_id).all()
			num_of_children = len(child)
		except:
			return jsonify(code = 11,message='node not exist, query fail')
		if file_node == None:
			return jsonify(code = 11,message='node not exist, query fail')
		# 获取信息
		return jsonify(code=0,num_of_children= num_of_children, data = self.serialize_file(file_node) ) 

class DownloadFileAPI(Resource):
	def get(self):
		parse = reqparse.RequestParser()
		parse.add_argument('id',type=int,help='错误的id',default='0')
		args = parse.parse_args()
		# 获取当前文件夹id
		file_id = args.get('id')
		try:
			file_node = FileNode.query.get(file_id)
		except:
			return jsonify(code=11,message='node not exist, query fail')
		
		parent_id = file_node.parent_id
		filename = file_node.filename

			# 生成文件名的 hash
		actual_filename = generate_file_name(parent_id, filename)
			# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
		target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), actual_filename)
		if os.path.exists(target_file):
			# print(filename)
			# print(target_file)
			return send_file(target_file,as_attachment=True,attachment_filename=filename)
		else:
			return jsonify(code='22',message='file not exist')

class ReNameAPI(Resource):
	# 重命名文件
	def reNameFile(self,target_file_node,new_name):
		# node 是要重命名的结点
		try:
				# 修改文件名
			old_actual_filename = generate_file_name(target_file_node.parent_id, target_file_node.filename)
			# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
			target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), old_actual_filename)

			new_actual_filename = generate_file_name(target_file_node.parent_id,new_name)
			# 本地文件重命名
			if os.path.exists(old_target_file):
				os.rename(target_file,new_actual_filename)
			# 修改数据库中的文件名
			target_file_node.filename = new_name# 修改当前文件的名字
			db.session.commit()
			return jsonify(code = 0,message='OK')
		except:
			return jsonify(code=20,message='file error')
	# 递归修改孩子的路径
	# parent_node 需要修改路径的孩子的父节点
	# new_name 修改后的文件名
	# 当前是第几层
	def changeChildrenPath(self,parent_node,new_name,n):
		try:
			# 获取所有孩子节点
			children = FileNode.query.filter_by(parent_id=parent_node.id).all()
		except:
			return jsonify(code = 10,message='database error')
		pos = n * (-1)
		for child in children:
			if child.type_of_node == 'dir':
				# 递归修改孩子
				self.changeChildrenPath(child,new_name,n+1)
				# 修改孩子的path
			old_path_root = child.path_root.split('/')
			old_path_root[pos] = new_name
			new_path_root = '/'.join(old_path_root)
			child.path_root = new_path_root
	def post(self):
		parse = reqparse.RequestParser()
		parse.add_argument('id',type=int,help='错误的id',default='0')
		parse.add_argument('newName',type=str,help='错误的newName',default='default_name')
		args = parse.parse_args()
		# 获取当前文件夹id
		file_id = args.get('id')
		new_name = args.get('newName')
		try:
			target_file_node = FileNode.query.get(file_id)
		except Exception as e:
			return jsonify(code=11,message='node not exist, query fail')
		if target_file_node.type_of_node=='dir':# 如果是要修改目录的名字
			# TODO : 递归修改 path_root
			try:
				target_file_node.filename = new_name# 先修改当前目录的名字
				self.changeChildrenPath(target_file_node,new_name,1)
				db.session.commit()
				return jsonify(code=0,message='OK')
			except:
				return jsonify(code=10,message='database error')
		else:# 如果修改的是文件
			self.reNameFile(target_file_node,new_name)
class NewFolderAPI(Resource):
	file_fields={
		'id':fields.Integer,
		'filename':fields.String,
		'path_root':fields.String,
		'parent_id':fields.Integer,
		'type_of_node':fields.String,
		'size':fields.Integer,
		'upload_time':fields.Integer,
		'uid':fields.Integer
	}
	@marshal_with(file_fields)
	def serialize_file(self,file):
		return file
	def post(self):
		parse = reqparse.RequestParser()
		parse.add_argument('curId',type=int,help='错误的curId',default='0')
		parse.add_argument('foldername',type=str,help='错误的filename',default='default_name')
		args = parse.parse_args()
		# 获取当前文件夹id
		cur_file_id = args.get('curId')# 获取当前文件夹id
		filename = args.get('foldername')# 获取新建文件夹的名称

		cur_file_node = FileNode.query.get(cur_file_id)
		cur_file_path_root = cur_file_node.path_root
		cur_filename = cur_file_node.filename

		new_path_root = cur_file_path_root + '/' + cur_filename
		d_time = int(time.time())
		try:
			filenode = FileNode(filename=filename,path_root = new_path_root,parent_id = cur_file_id,upload_time = d_time)
			db.session.add(filenode)
			db.session.commit()
			return jsonify(code=0,message='OK',data = self.serialize_file(filenode))
		except:
			return jsonify(code = 12,message='node already exist , add fail')
class GetAllAPI(Resource):
	file_fields={
		'id':fields.Integer,
		'filename':fields.String,
		'path_root':fields.String,
		'parent_id':fields.Integer,
		'type_of_node':fields.String,
		'size':fields.Integer,
		'upload_time':fields.Integer,
		'uid':fields.Integer
	}
	@marshal_with(file_fields)
	def serialize_file(self,file):
		return file

	def get(self):
		parse = reqparse.RequestParser()
		parse.add_argument('curUid',type=int,help='错误的curId',default='0')
		args = parse.parse_args()
		# 获取当前文件夹id
		cur_uid = args.get('curUid')# 获取当前文件夹id
		try:
			file_nodes = FileNode.query.filter_by(user_id=cur_uid)
			return jsonify(code = 0,data=[ self.serialize_file(file) for file in file_nodes])
		except :
			return jsonify(code=10,message='database error')
class DeleteAPI(Resource):
	def get(self):
		parse = reqparse.RequestParser()
		parse.add_argument('id',type=int,help='错误的id',default='0')
		args = parse.parse_args()
		# 获取当前文件夹id
		file_id = args.get('id')
		try:
			file_node = FileNode.query.get(file_id)
		except Exception as e:
			return jsonify(message='error')

		if file_node.type_of_node == 'dir':# 如果删除的是文件夹
			children = FileNode.query.filter_by(parent_id=file_id)
			# 循环删除
			for child in children:
				delete_node(child)
			delete_node(file_node)
			return jsonify('LOOP delete OK')
		else: # 如果是删除文件
			delete_node(file_node)
			return jsonify('delete file OK')
# 辅助函数
# 删除结点

# utils
# 处理文件名
import hashlib
def generate_file_name(parent_id,filename):
	return hashlib.md5(
				(str(parent_id) + '_' + filename).encode('utf-8')).hexdigest()

def delete_node(file_nde):
	# print('in func delete_node')
	# TODO 递归删除	# 此结点从数据库中删除
	try:
		db.session.delete(file_node)
		db.session.commit()
		returnjsoify(message='delete success')
	except Exception as e:
		return jsonify(message='error')
	# 如果删除的是文件，则先把文件从系统中删除
	if file_node.type_of_node != 'dir':
		filename = file_node.filename
		# 生成文件名的 hash
		actual_filename = generate_file_name(cur_file_id, filename)
		# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
		target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), actual_filename)
		if os.path.exists(target_file):
			os.remove(target_file)

