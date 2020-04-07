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
from models import FileNode,UserTable,ShareTable
from extensions import db,login_manager
from utils import generate_token,verify_token,token_required,generate_file_name
from werkzeug.datastructures import FileStorage
from settings import config
from flask import send_file,make_response,send_from_directory,stream_with_context
from PIL import Image
import io
from utils import generate_share_token,generate_url
from flask import session

UPLOAD_FOLDER = config['UPLOAD_FOLDER']
CHUNK_SIZE = config['CHUNK_SIZE']

class UploadAPI(Resource):

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
		# f.close()
		if "/" in f.filename:
			response = make_response(jsonify(code=23,message = 'filename should not has separator'))
			return response
		try:
			cur_file_node = FileNode.query.get(cur_file_id)
		except:
			response = make_response(jsonify(code=11,message='illegal filename'))
			return response
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
				response = make_response(jsonify(code=21,message='file already exist, save fail'))
				return response
			try:
				# 保存文件
				f.save(target_file)
				# print(filename + ' saved')
				fsize = os.path.getsize(target_file)
				filenode = FileNode(filename=filename,path_root = new_path_root,parent_id = cur_file_id,size = fsize,type_of_node=filename.split('.')[-1].lower(),upload_time = d_time,user_id = current_user.uid)
				db.session.add(filenode)
				# print('db added filenode')
				db.session.commit()
				response = make_response(jsonify(code=0,message='OK',data = {'file':filenode.to_json()}))
				return response
			except:
				response = make_response(jsonify(code=12,message='node already exist , add fail'))
				return response
class GetInfoAPI(Resource):
	@login_required
	def get(self):
		parse = reqparse.RequestParser()
		parse.add_argument('id',type=int,help='错误的id',default='0')
		args = parse.parse_args()
		# 获取当前文件夹id
		file_id = args.get('id')
		# TODO：优化，避免全表扫描
		try:
			file_node = FileNode.query.get(file_id)
			child = FileNode.query.filter_by(parent_id=file_id).all()
			num_of_children = len(child)
		except:
			response = make_response(jsonify(code = 11,message='node not exist, query fail'))
			return response
		if file_node == None:
			response = make_response(jsonify(code = 11,message='node not exist, query fail'))
			return response
		# 此文件不属于当前用户
		if file_node.user_id != current_user.uid:
			response = make_response(jsonify(code=25,message='can not access this file'))
			return response
		# 获取信息
		response = make_response(jsonify(code=0,data = {'file':filenode.to_json(),'num_of_children':num_of_children} ))
		return  response
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
			response = make_response(jsonify(code=11,message='node not exist, query fail'))
			return response
		# 无访问权限
		if file_node.user_id != current_user.uid:
			response = make_response(jsonify(code=25,message='can not access this file'))
			return response
		
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
			response = make_response(jsonify(code='22',message='file not exist'))
			return response
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
			response = make_response(jsonify(code = 0,message='OK'))
			return response
		except:
			response = make_response(jsonify(code=20,message='file error'))
			return response
	# 递归修改孩子的路径
	# parent_node 需要修改路径的孩子的父节点
	# new_name 修改后的文件名
	# 当前是第几层
	def changeChildrenPath(self,parent_node,new_name,n):
		try:
			# 获取所有孩子节点
			children = FileNode.query.filter_by(parent_id=parent_node.id).all()
		except:
			response = make_response(jsonify(code = 10,message='database error'))
			return response
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
			response = make_response(jsonify(code=11,message='node not exist, query fail'))
			return response
		if target_file_node.user_id != current_user.uid:
			response = make_response(jsonify(code=25,message='can not access this file'))
			return response
		if target_file_node.type_of_node=='dir':# 如果是要修改目录的名字
			# TODO : 递归修改 path_root
			try:
				target_file_node.filename = new_name# 先修改当前目录的名字
				self.changeChildrenPath(target_file_node,new_name,2)
				db.session.commit()
				response = make_response(jsonify(code=0,message='OK'))
				return response
			except:
				response = make_response(jsonify(code=10,message='database error'))
				return response
		else:# 如果修改的是文件
			return self.reNameFile(target_file_node,new_name)
class NewFolderAPI(Resource):
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
			response = make_response(jsonify(code=11,message='node not exist, query fail'))
			return response
		if cur_file_node == None:
			response = make_response(jsonify(code=11,message='node not exist, query fail'))
			return response
		cur_file_path_root = cur_file_node.path_root
		cur_filename = cur_file_node.filename

		new_path_root = cur_file_path_root + cur_filename + '/'
		d_time = int(time.time())
		try:
			print(current_user.uid)
			filenode = FileNode(filename=filename,path_root = new_path_root,parent_id = cur_file_id,upload_time = d_time,user_id = current_user.uid)
			db.session.add(filenode)
			db.session.commit()
			response = make_response(jsonify(code=0,message='OK',data = {'file':filenode.to_json()}))
			return response
		except:
			response = make_response(jsonify(code = 12,message='node already exist , add fail'))
			return response
class GetAllAPI(Resource):

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
			response = make_response(jsonify(code = 0,data={'files':[ file.to_json() for file in file_nodes]}))
			return response
		except :
			response = make_response(jsonify(code=10,message='database error'))
			return response
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
			response = make_response(jsonify(code = 0,message='OK'))
			return response
		except:
			response = make_response(jsonify(code=20,message='file error'))
			return response
	def deleteChildren(self,parent_node):
		try:
			# 获取所有孩子节点
			children = FileNode.query.filter_by(parent_id=parent_node.id).all()
		except:
			response = make_response(jsonify(code = 10,message='database error'))
			return response
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
			response = make_response(jsonify(message='error'))
			return response

		if file_node.user_id != current_user.uid:
			response = make_response(jsonify(code=25,message='can not access this file'))
			return response
		if file_node.type_of_node == 'dir':# 如果删除的是文件夹
			try:
				self.deleteChildren(file_node)
				db.session.delete(file_node)
				db.session.commit()
				response = make_response(jsonify(code=0,message='OK'))
				return response
			except:
				response = make_response(jsonify(code=10,message='database error'))
				return response
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
			response = make_response(jsonify(code=38,message='wrong token'))
			return response
		try:
			file_node = FileNode.query.get(file_id)
		except:
			response = make_response(jsonify(code = 11,message='node not exist, query fail'))
			return response
		if file_node.user_id != user.uid:
			response = make_response(jsonify(code=38,message='wrong token'))
			return response
		if file_node == None:
			response = make_response(jsonify(code = 11,message='node not exist, query fail'))
			return response
		if file_node.type_of_node in config['IMG_TYPE']:
			parent_id = file_node.parent_id
			filename = file_node.filename
			node_type = file_node.type_of_node
				# 生成文件名的 hash
			actual_filename = generate_file_name(parent_id, filename)
				# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
			target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), actual_filename)
			if os.path.exists(target_file):
				try:
					with Image.open(target_file,mode='r') as img_data:
					# img_data = Image.open(target_file)
						img_data.thumbnail((width,height))

						fp = io.BytesIO()
						format = Image.registered_extensions()['.'+node_type]
						img_data.save(fp, format)

						response = make_response(fp.getvalue())
						response.headers['Content-Type'] = 'image/' + node_type
						return response
				except:
					response = make_response(jsonify(code = 24,message='preview not allowed'))
					return response
			else:
				response = make_response(jsonify(code=22,message='file not exist'))
				return response
		else:
			response = make_response(jsonify(code = 24,message='preview not allowed'))
			return response

'''
文件分享
'''

class ShareAPI(Resource):
	@login_required
	def post(self):
		parse = reqparse.RequestParser()
		parse.add_argument('id',type=int,help='错误的id',default='0')
		parse.add_argument('token_required',type=int,default='0')
		parse.add_argument('day',type=int,default=1095)
		args = parse.parse_args()
		file_id = args.get('id')
		token_required = args.get('token_required')
		day = args.get('day')
		fileobj = FileNode.query.filter_by(id=file_id, user_id=current_user.uid).first()
		if fileobj is None:
			response = make_response(jsonify(code = 11,message='node not exist, query fail'))
			return response
		if fileobj.is_share == False:
			fileobj.is_share=True
		share_url = generate_url()
		if token_required == 1:
			share_token = generate_share_token()
		else:
			share_token = ''
		shareobj = ShareTable(file_id = file_id,share_url = share_url,share_token = share_token,share_begin_time=int(time.time()),share_end_time = int(time.time()) + day*24*3600)
		try:
			db.session.add(shareobj)
			db.session.commit()
			response = make_response(jsonify(code=0,message='OK',data = {'share':shareobj.to_json()}))
			return response
		except Exception as e:
			# app.logger.exception(e)
			response = make_response(jsonify(code=12,message='node already exist , add fail'))
			return response

class CancelShareAPI(Resource):
	@login_required
	def post(self):
		parse = reqparse.RequestParser()
		parse.add_argument('share_id',type=int,help='错误的share_id',default='0')
		args = parse.parse_args()
		share_id = args.get('share_id')
		try:
			shareobj = ShareTable.query.get(share_id)
			file_id = shareobj.file_id
			db.session.delete(shareobj)
			fileobj = FileNode.query.get(file_id)
			print(len(fileobj.shares))
			if len(fileobj.shares) == 0:
				fileobj.is_share=False
			db.session.commit()
			response = make_response(jsonify(code=0,message = 'OK'))
			return response
		except:
			response = make_response(jsonify(code=10,message = 'database error'))
			return response
class DownloadShareAPI(Resource):
	def post(self,url):
		parse = reqparse.RequestParser()
		parse.add_argument('share_token',type=str,default='')
		args = parse.parse_args()
		# 获取当前文件夹id
		share_token = args.get('share_token')

		shareobj = ShareTable.query.filter_by(share_url=url).first()
		if shareobj is None:
			response = make_response(jsonify(code = 11,message='node not exist, query fail'))
			return response
		file_node = FileNode.query.filter_by(id = shareobj.file_id).first()
		if file_node is None:
			response = make_response(jsonify(code = 11,message='node not exist, query fail'))
			return response
		if shareobj.share_token == '' or share_token == shareobj.share_token:
			if shareobj.share_end_time < int(time.time()):
				print(shareobj.share_end_time)
				print(int(time.time()))
				response = make_response(jsonify(code=42,message='out of date'))
				return response
			parent_id = file_node.parent_id
			filename = file_node.filename
				# 生成文件名的 hash
			actual_filename = generate_file_name(parent_id, filename)
				# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
			target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), actual_filename)
			if os.path.exists(target_file):
				return send_file(target_file,as_attachment=True,attachment_filename=filename,cache_timeout=3600)
			else:
				response = make_response(jsonify(code=22,message='file not exist'))
				return response
		else:
			response = make_response(jsonify(code=41,message='wrong share_token'))
			return response

class PreviewShareAPI(Resource):
	def post(self,url):
		parse = reqparse.RequestParser()
		parse.add_argument('width',type=int,help='wrong width',default=300)
		parse.add_argument('height',type=int,help='wrong height',default=300)
		parse.add_argument('share_token',type=str,default='')
		args = parse.parse_args()
		# 获取当前文件夹id
		width = args.get('width')
		height = args.get('height')
		share_token = args.get('share_token')

		shareobj = ShareTable.query.filter_by(share_url=url).first_or_404()
		file_node = FileNode.query.filter_by(id = shareobj.file_id).first_or_404()
		if shareobj.share_token == '' or share_token == shareobj.share_token:
			if shareobj.share_end_time < int(time.time()):
				response = make_response(jsonify(code=42,message='out of date'))
				return response
			if file_node.type_of_node in config['IMG_TYPE']:
				parent_id = file_node.parent_id
				filename = file_node.filename
				node_type = file_node.type_of_node
					# 生成文件名的 hash
				actual_filename = generate_file_name(parent_id, filename)
					# 结合 UPLOAD_FOLDER 得到最终文件的存储路径
				target_file = os.path.join(os.path.expanduser(UPLOAD_FOLDER), actual_filename)
				if os.path.exists(target_file):
					try:
						with Image.open(target_file,mode='r') as img_data:
						# img_data = Image.open(target_file)
							img_data.thumbnail((width,height))

							fp = io.BytesIO()
							format = Image.registered_extensions()['.'+node_type]
							img_data.save(fp, format)

							response = make_response(fp.getvalue())
							response.headers['Content-Type'] = 'image/' + node_type
							return response
					except:
						response = make_response(jsonify(code = 24,message='preview not allowed'))
						return response
				else:
					response = make_response(jsonify(code=22,message='file not exist'))
					return response
			else:
				response = make_response(jsonify(code = 24,message='preview not allowed'))
				return response
		else:
			response = make_response(jsonify(code=41,message='wrong share_token'))
			return response



