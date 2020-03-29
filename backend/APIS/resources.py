import os
import sys
import json
import time
import datetime
import click
from flask import Flask,request,abort
from flask import jsonify,Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import Api,Resource,fields,marshal_with,marshal_with_field,reqparse
from flask_login import LoginManager,UserMixin,login_user, logout_user, current_user, login_required
from models import FileNode,UserTable
from extensions import db,login_manager
from utils import generate_token,verify_token,token_required
from werkzeug.datastructures import FileStorage
from settings import config
from flask import send_file,make_response,send_from_directory,stream_with_context
from PIL import Image
import io


UPLOAD_FOLDER = config['UPLOAD_FOLDER']
CHUNK_SIZE = config['CHUNK_SIZE']

class UploadAPI(Resource):
	file_fields={
		'id':fields.Integer,
		'filename':fields.String,
		'path_root':fields.String,
		'parent_id':fields.Integer,
		'type_of_node':fields.String,
		'size':fields.Integer,
		'upload_time':fields.Integer,
		'user_id':fields.Integer
	}
	@marshal_with(file_fields)
	def serialize_file(self,file):
		return file

	@login_required
	def post(self):
		# print(UPLOAD_FOLDER)
		parse = reqparse.RequestParser()
		parse.add_argument('curId',type=int,help='错误的curId',default='0')
		parse.add_argument('file', type=FileStorage, location='files')
		
		args = parse.parse_args()
		# 获取当前文件夹id
		cur_file_id = args.get('curId')
		f = args['file']
		if "/" in f.filename:
			return jsonify(code=23,message = 'filename should not has separator')
		try:
			cur_file_node = FileNode.query.get(cur_file_id)
		except:
			return jsonify(code=11,message='illegal filename')
		cur_file_path_root = cur_file_node.path_root
		cur_filename = cur_file_node.filename
		
		if f:
			filename = f.filename
			# print('\"' in filename)
			# print('"' in filename)
			# print(filename[:-1])
			if '\"' in filename:
				filename = filename[:-1]
			new_path_root = cur_file_path_root  + cur_filename + '/'
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
				filenode = FileNode(filename=filename,path_root = new_path_root,parent_id = cur_file_id,type_of_node=filename.split('.')[-1].lower(),upload_time = d_time,user_id = current_user.uid)
				db.session.add(filenode)
				# print('db added filenode')
				db.session.commit()
				return jsonify(code=0,message='OK',data = self.serialize_file(filenode))
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
		'user_id':fields.Integer
	}
	@marshal_with(file_fields)
	def serialize_file(self,file):
		return file
	@login_required
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
	def generate(self,path):
		with open(path, 'rb') as fd:
			while 1:
				buf = fd.read(CHUNK_SIZE)
				if buf:
					yield buf
				else:
					break
	@login_required
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
			return send_file(target_file,as_attachment=True,attachment_filename=filename,cache_timeout=3600)
			# return send_from_directory(UPLOAD_FOLDER,actual_filename,as_attachment=True)
			# response =  Response(stream_with_context(self.generate(target_file)),content_type='application/octet-stream')
			# response.headers["Content-disposition"] = "attachment; filename={}".format(filename.encode().decode('latin-1'))
			# return response
		else:
			return jsonify(code='22',message='file not exist')
class ReNameAPI(Resource):
	# 重命名文件
	def reNameFile(self,target_file_node,new_name):
		# node 是要重命名的结点
		print('0')
		try:
				# 修改文件名
			print('1')
			old_actual_filename = generate_file_name(target_file_node.parent_id, target_file_node.filename)
			# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
			target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), old_actual_filename)
			print('2')
			new_actual_filename = generate_file_name(target_file_node.parent_id,new_name)
			new_target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), new_actual_filename)
			# 本地文件重命名
			print(target_file)
			if os.path.exists(target_file):
				print('3')
				os.rename(target_file,new_target_file)
			# 修改数据库中的文件名
			target_file_node.filename = new_name# 修改当前文件的名字
			print('4')
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
		if children == None:
			return
		for child in children:
			if child.type_of_node == 'dir':
				# 递归修改孩子
				self.changeChildrenPath(child,new_name,n+1)
				# 修改孩子的path
			old_path_root = child.path_root.split('/')
			old_path_root[pos] = new_name
			new_path_root = '/'.join(old_path_root)
			child.path_root = new_path_root
	@login_required
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
				self.changeChildrenPath(target_file_node,new_name,2)
				db.session.commit()
				return jsonify(code=0,message='OK')
			except:
				return jsonify(code=10,message='database error')
		else:# 如果修改的是文件
			return self.reNameFile(target_file_node,new_name)
class NewFolderAPI(Resource):
	file_fields={
		'id':fields.Integer,
		'filename':fields.String,
		'path_root':fields.String,
		'parent_id':fields.Integer,
		'type_of_node':fields.String,
		'size':fields.Integer,
		'upload_time':fields.Integer,
		'user_id':fields.Integer
	}
	@marshal_with(file_fields)
	def serialize_file(self,file):
		return file
	@login_required
	def post(self):
		parse = reqparse.RequestParser()
		parse.add_argument('curId',type=int,help='错误的curId',default='0')
		parse.add_argument('foldername',type=str,help='错误的filename',default='default_name')
		args = parse.parse_args()
		# 获取当前文件夹id
		cur_file_id = args.get('curId')# 获取当前文件夹id
		filename = args.get('foldername')# 获取新建文件夹的名称
		try:
			cur_file_node = FileNode.query.get(cur_file_id)
		except:
			return jsonify(code=11,message='node not exist, query fail')
		cur_file_path_root = cur_file_node.path_root
		cur_filename = cur_file_node.filename

		new_path_root = cur_file_path_root + cur_filename + '/'
		d_time = int(time.time())
		try:
			print(current_user.uid)
			filenode = FileNode(filename=filename,path_root = new_path_root,parent_id = cur_file_id,upload_time = d_time,user_id = current_user.uid)
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
		'user_id':fields.Integer
	}
	@marshal_with(file_fields)
	def serialize_file(self,file):
		return file

	@login_required
	def get(self):
		# parse = reqparse.RequestParser()
		# parse.add_argument('curUid',type=int,help='错误的curId',default='0')
		# args = parse.parse_args()
		# 获取当前文件夹id
		# cur_uid = args.get('curUid')# 获取当前文件夹id
		try:
			# file_nodes = FileNode.query.filter_by(user_id=cur_uid)
			file_nodes = current_user.files
			return jsonify(code = 0,data=[ self.serialize_file(file) for file in file_nodes])
		except :
			return jsonify(code=10,message='database error')
class DeleteAPI(Resource):
	def deleteFile(self,target_file_node):
		try:
			filename = target_file_node.filename
			parent_id = target_file_node.parent_id
			actual_filename = generate_file_name(parent_id, filename)
			# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
			target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), actual_filename)
			# 本地删除
			if os.path.exists(target_file):
				os.remove(target_file)
			# 修改数据库中的文件名
			db.session.delete(target_file_node)
			db.session.commit()
			return jsonify(code = 0,message='OK')
		except:
			return jsonify(code=20,message='file error')
	def deleteChildren(self,parent_node):
		try:
			# 获取所有孩子节点
			children = FileNode.query.filter_by(parent_id=parent_node.id).all()
		except:
			return jsonify(code = 10,message='database error')
		if children == None:
			return
		for child in children:
			if child.type_of_node == 'dir':
				# 递归修改孩子
				self.deleteChildren(child)
				# 修改孩子的path
			else:
				self.deleteFile(child)
			db.session.delete(child)
	@login_required
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
			try:
				self.deleteChildren(file_node)
				db.session.delete(file_node)
				db.session.commit()
				return jsonify(code=0,message='OK')
			except:
				return jsonify(code=10,message='database error')
		else: # 如果是删除文件
			return	self.deleteFile(file_node)
class PreviewAPI(Resource):
	@token_required
	def get(self):
		parse = reqparse.RequestParser()
		parse.add_argument('id',type=int,help='错误的id',default='0')
		parse.add_argument('width',type=int,help='wrong width',default=300)
		parse.add_argument('height',type=int,help='wrong height',default=300)
		parse.add_argument('token',type=str,help='wrong token')
		args = parse.parse_args()
		# 获取当前文件夹id
		file_id = args.get('id')
		width = args.get('width')
		height = args.get('height')
		token = args.get('token')
		try:
			user = verify_token(token)
		except:
			jsonify(code=38,message='wront token')
		try:
			file_node = FileNode.query.get(file_id)
		except:
			return jsonify(code = 11,message='node not exist, query fail')
		if file_node.user_id != user.uid:
			return jsonify(code=38,message='wrong')
		if file_node == None:
			return jsonify(code = 11,message='node not exist, query fail')
		if file_node.type_of_node in config['IMG_TYPE']:
			parent_id = file_node.parent_id
			filename = file_node.filename
			node_type = file_node.type_of_node
				# 生成文件名的 hash
			actual_filename = generate_file_name(parent_id, filename)
				# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
			target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), actual_filename)
			if os.path.exists(target_file):
				img_data = Image.open(target_file)
				img_data.thumbnail((width,height))

				fp = io.BytesIO()
				format = Image.registered_extensions()['.'+node_type]
				img_data.save(fp, format)

				response = make_response(fp.getvalue())
				response.headers['Content-Type'] = 'image/' + node_type
				return response
			else:
				return jsonify(code=22,message='file not exist')
		else:
			return jsonify(code = 24,message='preview not allowed')


# 辅助函数
# 删除结点

# utils
# 处理文件名
import hashlib
def generate_file_name(parent_id,filename):
	return hashlib.md5(
				(str(parent_id) + '_' + filename).encode('utf-8')).hexdigest()


