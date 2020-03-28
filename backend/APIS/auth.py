import os
import sys
import json
import time
import click
from flask import Flask,request,abort
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import Api,Resource,fields,marshal_with,marshal_with_field,reqparse
from flask_login import LoginManager,UserMixin,login_user, logout_user, current_user, login_required
from models import FileNode,UserTable
from extensions import db,login_manager


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
		if current_user.is_authenticated:
			# TODO
			return jsonify(code=32,message = 'user already authenticated')
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
			return jsonify(code = 31,message = 'user not found')
		else:
			print("{} User query: {} success...".format(time.strftime("%Y-%m-%d %H:%M:%S"), email))
		finally:
			db.session.close()
		if user and user.varify_password(password):
			login_user(user)
			print('current_user')
			print(current_user)
			return jsonify(code = 0,message = 'user login success',data = self.serialize_user(user))
		else:
			print('in if')
			print("{} User query: {} failure...".format(time.strftime("%Y-%m-%d %H:%M:%S"), email))
			print('user is None or password False')
			return jsonify(code = 33,message = 'user login fail')
		
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
			return jsonify(code=34,message = 'user add fail')
		else:
			print("{} User add: {} success...".format(time.strftime("%Y-%m-%d %H:%M:%S"), email))
			return jsonify(code = 0, message = 'user add success' , data = self.serialize_user(user))
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
			return jsonify(code = 0,message = 'get current_user success',data = self.serialize_user(current_user))
		else:
			return jsonify(code = 35,message = 'get current_user fail')
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
			return jsonify(code = 0,message = 'logout success')
