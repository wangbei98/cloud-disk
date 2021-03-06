
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_restful import reqparse
from flask import jsonify
from settings import config
from models import UserTable

import functools

# utils
# 处理文件名
import hashlib
def generate_file_name(parent_id,filename):
	return hashlib.md5(
				(str(parent_id) + '_' + filename).encode('utf-8')).hexdigest()


# 根据用户id生成token
def generate_token(uid):
	s = Serializer(config['SECRET_KEY'],config['EXPIRES_TIME'])
	token = s.dumps({"uid":uid}).decode("ascii")
	return token

# 验证token，如果验证通过，则返回token代表的用户，如果不通过，则返回None
def verify_token(token):
	s = Serializer(config['SECRET_KEY'])
	try:
		data = s.loads(token)
	except Exception:
		return None
	try:
		user = UserTable.query.get(data['uid'])
	except:
		return None
	if user:
		return user
	else:
		return None

# 写一个装饰器
def token_required(view_func):
	@functools.wraps(view_func)
	def verify_token(*args,**kwargs):
		parse = reqparse.RequestParser()
		parse.add_argument('token',type=str,help='wrong token')
		args = parse.parse_args()

		token = args.get('token')
		
		s = Serializer(config['SECRET_KEY'])
		try:
			s.loads(token)
		except Exception:
			return jsonify(code = 38,msg = "wrong token")

		return view_func(*args,**kwargs)

	return verify_token



import random

_random = random.SystemRandom()

def base36_encode(number):
	assert number >= 0, 'positive integer required'
	if number == 0:
		return '0'
	base36 = []
	while number != 0:
		number, i = divmod(number, 36)
		base36.append('0123456789abcdefghijklmnopqrstuvwxyz'[i])
	return ''.join(reversed(base36))

# 用于生成短地址
def generate_url():
	return base36_encode(get_random_long_int())


def get_random_long_int():
	return _random.randint(1000000000, 9999999999)


def get_random_short_int():
    return _random.randint(100000, 999999)


def generate_share_token():
    return base36_encode(get_random_short_int())
