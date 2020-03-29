import os

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

config={
	'UPLOAD_FOLDER':os.path.join(basedir,'backend/upload'),
	'CHUNK_SIZE':1024,
	'PHOTO_TYPES':['png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF'],
	'SECRET_KEY':'wangbei',
	'EXPIRES_TIME':86400,
	'IMG_TYPE':['jpeg','jpg','png','PNG','JPG','JPEG','GIF','gif']
}