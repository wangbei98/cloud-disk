## 处理 flask_sqlalchemy 查询结果转json

参考：

[RESTful. API 文档](http://www.pythondoc.com/Flask-RESTful/api.html)

[SQLAlchemy+Flask-RESTful使用(一)](https://www.cnblogs.com/chnmig/p/10538149.html)

[flask-restful & marshal_with](https://www.cnblogs.com/guyuyun/p/11318801.html)

[flask-restful扩展](https://github.com/anjianshi/flask-restful-extend)

[Flask 实现 Rest API (02) - 查询结果转换为 json 字符串](https://www.jianshu.com/p/07c1bb9f6848)

[flask 实现 RESTful API(04)-基于flask_sqlalchemy](https://www.jianshu.com/p/053904f5073b)

### 方法零：给每个模型类写一个简单的 to_json()函数

```python
# 用户表
class User(db.Model):
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('user_username', db.String(100), index=True, unique=True, nullable=True)
    password = db.Column('user_password', db.String(120), nullable=True)
    create_time = db.Column('user_time', db.Integer, default=Date.now())

    def __repr__(self):
        return '<User %s>' % self.username

    def to_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'time': Date.unix_to_human(self.create_time),
        }
```

### 方法一：设计一个基类

```python
class EntityBase(object):
    def to_json(self):
        fields = self.__dict__
        if "_sa_instance_state" in fields:
            del fields["_sa_instance_state"]
        
        return fields
```

让模型类继承它

```python
class Folder(db.Model,EntityBase):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)

    # optional
    def __repr__(self):
        return '<Folder %r>' % self.name
```

转换查询结果

```python
folders = Folder.query.all()
if len(folders)>0:
    return jsonify(message='OK', data=[folder.to_json() for folder in folders])
```

缺点：只能把单个的实例序列化，当多个表有一对多，多对多等关系时，就不能序列化了

### 方法二：使用flask-restful 和 marshal_with

使用 marshal_with 对视图类中得到的查询结果进行统一化和规范化

对于使用marshal_with装饰器装饰的函数，它的return对象会json化为字典，作为最后的返回值，其字典数据格式需要提前设定。return对象中有多余的key项是不会添加到返回的字典中的。

```python
from flask-restful import fields,marshal_with
class FoldersView(Resource):
    def post(self):
        pass
    def get(self):
        # 查询所有结果 --> list
        folders = Folder.query.all()
        if len(folders)>0:
        	# 设置返回值字典格式
            resource_fields = {
                'id':fields.Integer(attribute='id'),
                'name':fields.String(attribute='name'),
                'files':fields.List(fields.Nested({
                    'id':fields.Integer,
                    'filename':fields.String,
                    'folder_id':fields.Integer
                }))
            }
            # 此函数用来把folder对象 转成 json
            @marshal_with(resource_fields)
            def marshalObj(obj):
                return obj
            # 返回被转成json的对象列表
            return jsonify(data=[marshalObj(folder) for folder in folders])
        else:
            return jsonify(message='OK')
# flask-restful : 添加api
api.add_resource(FoldersView,'/folders')
```

### 方法三：将方法一和方法二结合 (TODO)

定义一个基类，基类中用marshal_with实现转json算法

并在每一个model类中实现 resource_fields = { }

* 利用 \_\_dict\_\_ 

```python
__dict__属性总结
1.类__dict__属性中包括类属性，类方法（非系统默认的，修改过的__init__()等，自己写的静态非静态方法），包括它实例化对象的方法
2.对象的属性就是__init__方法中带有的属性，子类默认继承父类__init__时候，子类创建对象的属性与父类一致，取决于你是否重写__init__属性，你可以尝试在子类重写__init__方法，并修改属性
3.可以通过操作对象__dict__属性来获取对象的属性。有时候会用到
来自：https://blog.csdn.net/Dage_Python/article/details/88047751
```

```python
from flask-restful import fields,marshal_with
class BaseModel(object):
    def __init__(self):
        self.resource_fields = {}
    def to_json(self):
        @marshal_with(self.resource_fields)
        def marshal_obj(ojb):
            return obj
        return marshal_obj(self)
# 用户表
class User(db.Model):
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('user_username', db.String(100), index=True, unique=True, nullable=True)
    password = db.Column('user_password', db.String(120), nullable=True)
    create_time = db.Column('user_time', db.Integer, default=Date.now())

    self.resource_fields = {
        'id',fields.Integer,
        ...
    }
```