import os
import sys
import json
import time
import click
from flask import Flask,request,abort
from flask import jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import Api,Resource,fields,marshal_with,marshal_with_field,reqparse
from flask_login import LoginManager,UserMixin,login_user, logout_user, current_user, login_required
from models import FileNode,UserTable
from extensions import db,login_manager
from utils import generate_token


# apis
class Login(Resource):
	user_fields = {
    	'uid' : fields.Integer,
    	'email' : fields.String,
	}
	@marshal_with(user_fields)
	def serialize_user(self,user):
		return user
	def post(self):
		logout_user()
		if current_user.is_authenticated:
			# TODO
			response = make_response(jsonify(code=32,message = 'already authenticated'))
			return response
		parse = reqparse.RequestParser()
		parse.add_argument('email',type=str,help='邮箱验证不通过',default='beiwang121@163.com')
		parse.add_argument('password',type=str,help='密码验证不通过')
		args = parse.parse_args()

		email = args.get("email")
		password = args.get("password")
		try:
			user = UserTable.query.filter_by(email=email).first()
		except:
			print("{} User query: {} failure......".format(time.strftime("%Y-%m-%d %H:%M:%S"),email))
			response = make_response(jsonify(code = 31,message = 'user not found'))
			return response
		else:
			print("{} User query: {} success...".format(time.strftime("%Y-%m-%d %H:%M:%S"), email))
		finally:
			db.session.close()
		if user and user.varify_password(password):
			login_user(user,remember=True)
			token = generate_token(current_user.uid)
			print('current_user')
			print(current_user)
			response = jsonify(code = 0,message = 'login success',data ={'user': self.serialize_user(user),'token':token})
			response.set_cookie('token',token)
			return response
		else:
			print('in if')
			print("{} User query: {} failure...".format(time.strftime("%Y-%m-%d %H:%M:%S"), email))
			print('user is None or password False')
			response = make_response(jsonify(code = 33,message = 'login fail'))
			return response
		
class Register(Resource):
	user_fields = {
    	'uid' : fields.Integer,
    	'email' : fields.String,
	}
	@marshal_with(user_fields)
	def serialize_user(self,user):
		return user
	def post(self):
		parse = reqparse.RequestParser()
		parse.add_argument('email',type=str,help='email验证不通过',default='beiwang121@163.com')
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
			response = make_response(jsonify(code=34,message = 'user add fail'))
			return response
		else:
			print("{} User add: {} success...".format(time.strftime("%Y-%m-%d %H:%M:%S"), email))
			response = make_response(jsonify(code = 0, message = 'user add success' , data ={'user': self.serialize_user(user)}))
			return response
		finally:
			db.session.close()
class GetCurUserAPI(Resource):
	user_fields = {
    	'uid' : fields.Integer,
    	'email' : fields.String,
	}
	@marshal_with(user_fields)
	def serialize_user(self,user):
		return user
	def get(self):
		if current_user.is_authenticated:
			response = make_response(jsonify(code = 0,message = 'get current_user success',data ={'user':self.serialize_user(current_user)}))
			return response
		else:
			response = make_response(jsonify(code = 35,message = 'get current_user fail'))
			return response

class RefreshTokenAPI(Resource):
	@login_required
	def get(self):
		token = generate_token(current_user.uid)
		response = make_response(jsonify(code=0,message='OK'))
		response.set_cookie('token',token)
		return response

class Logout(Resource):
	user_fields = {
    	'uid' : fields.Integer,
    	'email' : fields.String
	}
	@marshal_with(user_fields)
	def serialize_user(self,user):
		return user

	@login_required
	def logout(self):
		print(current_user)
		print("已退出登录")
		logout_user()
		print(current_user.is_authenticated)
		return True
	def get(self):
		print(11)
		if self.logout():
			response = make_response(jsonify(code = 0,message = 'logout success'))
			response.set_cookie('token','')
			return response
