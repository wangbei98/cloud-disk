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
		print(UPLOAD_FOLDER)
		parse = reqparse.RequestParser()
		parse.add_argument('curId',type=int,help='错误的curId',default='0')
		parse.add_argument('file', type=FileStorage, location='files')
		
		args = parse.parse_args()
		# 获取当前文件夹id
		cur_file_id = args.get('curId')
		f = args['file']
		try:
			cur_file_node = FileNode.query.get(cur_file_id)
		except Exception as e:
			return jsonify(message='cur_file_node error')
		cur_file_path_root = cur_file_node.path_root
		cur_filename = cur_file_node.filename

		# f = request.files['file'] # 获取上传的文件
		print(f.filename)
		print(f.filename.split('.')[-1])
		print(cur_file_path_root)
		print(cur_filename)
		
		if f:
			filename = f.filename
			new_path_root = cur_file_path_root + '/' + cur_filename
			d_time = int(time.time())
			# 生成文件名的 hash
			actual_filename = generate_file_name(cur_file_id, filename)
			# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
			target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), actual_filename)

			if os.path.exists(target_file):
				return jsonify(message='error',code=409)
			try:
				# 保存文件
				f.save(target_file)
				print(filename + ' saved')
				filenode = FileNode(filename=filename,path_root = new_path_root,parent_id = cur_file_id,type_of_node=filename.split('.')[-1],upload_time = d_time)
				db.session.add(filenode)
				print('db added filenode')
				db.session.commit()
				return jsonify(message='OK')
			except Exception as e:
				return jsonify(message='error')
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
			return jsonify(message='error')
		if file_node == None:
			return jsonify('no sucn node')
		# 获取信息
		return jsonify(num_of_children= num_of_children, data = self.serialize_file(file_node) ) 

class DownloadFileAPI(Resource):
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
		
		parent_id = file_node.parent_id
		filename = file_node.filename

			# 生成文件名的 hash
		actual_filename = generate_file_name(parent_id, filename)
			# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
		target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), actual_filename)
		if os.path.exists(target_file):
			print(filename)
			print(target_file)
			return send_file(target_file,as_attachment=True,attachment_filename=filename)
		else:
			return jsonify(message='error',code='404')

class ReNameAPI(Resource):
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
			return jsonify(message='error')
		if target_file_node.type_of_node=='dir':# 如果是要修改目录的名字
			# TODO : 递归修改 path_root
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
				old_target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), old_actual_filename)

				new_actual_filename = generate_file_name(cur_file_id, target_file_node.filename)
				# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
				new_target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), old_actual_filename)
				# 本地文件重命名
				if os.path.exists(old_target_file):
					os.rename(old_target_file,new_actual_filename)
				# 修改数据库中的文件名
				target_file_node.filename = new_name# 修改当前文件的名字
				db.session.commit()
			except Exception as e:
				return jsonify(message='error')
class NewFolderAPI(Resource):
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
			return jsonify(message='OK')
		except Exception as e:
			return jsonify(message='error')
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
			return jsonify(data=[ self.serialize_file(file) for file in file_nodes])
		except Exception as e:
			return jsonify(message='error')
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
	print('in func delete_node')
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

