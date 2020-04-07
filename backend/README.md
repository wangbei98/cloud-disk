[TOC]

# 文档

## 数据库设计

在设计数据库时，并不是通过维护一个嵌套的对象，而是将所有的数据都放入到一维数组，父子关系通过`parId`字段来维护，根目录到当前所在目录通过`path_root`字段来维护。只考虑相邻的两级关系，不考虑所有的层级关系，优势如下：

1. 存入数据时，只需要将`parent_id`设为当前目录的Id，`path_root`设为根目录到当前目录的路径。而不是通过递归对象将数据放到对应的节点上。
2. 修改当前文件或者目录名称时，只需要根据当前数据的Id去数据库匹配然后修改。如果修改的是目录名称(假如nameA修改为nameB)，会影响该目录下所有子目录和子文件的`path_root`字段，那么只需要匹配所有满足`path_root`字段里面包含nameA的数据，然后替换成nameB就可以了。
3. 移动文件或目录时，所有的子目录或者文件也会跟着变化。修改当前文件或目录的`parent_id`字段，指向新的目录Id，同样也要修改所有子目录或者子文件的`path_root`字段，同上。
4. 删除文件或目录时，根据当前的Id去数据库匹配删除。如果删除的目录里面有子目录或者文件(假如删除的是目录folderA)，那么只需要匹配所有满足`path_root`字段里面包含folderA的数据，然后全部删除。最后记得也要删除磁盘文件，不然内存消耗太大(如果有回收站保留30天，则设置最后保留时间，超时后再去删磁盘文件)。



UserTable

|               |              |        |
| ------------- | ------------ | ------ |
| uid           | 用户ID       | 默认 0 |
| email         | 邮箱         |        |
| password_hash | 密码的hash值 |        |

FileNode

|               |                          |                                        |
| ------------- | ------------------------ | -------------------------------------- |
| id            | 唯一id                   | 主键                                   |
| filename      | 文件名                   |                                        |
| path_root     | 从根目录到当前目录到路径 | ‘/’ 分割                               |
| parent_id     | 父目录id                 |                                        |
| type_of_node  | 类型                     | （dir , .py , .csv ） 'dir' 表示是目录 |
| size          | 大小                     |                                        |
| upload_time   | 上传时间                 |                                        |
| user_id       | 所属用户                 | 外键，默认0                            |
| hdfs_path     |                          |                                        |
| hdfs_filename |                          |                                        |



## api设计

| 资源                     | URL                       | 实现方法/对应功能              |
| ------------------------ | ------------------------- | ------------------------------ |
| 登录                     | /api/login                | POST(email,password)           |
| 注册                     | /api/register             | POST(emil,password)            |
| 登出                     | /api/logout               | GET                            |
|                          |                           |                                |
| 上传文件                 | /api/file/upload          | POST(curId=xxx&file=xx)        |
| 获取文件信息（目录）     | /api/file/getInfo?id=xxx  | GET                            |
| 下载文件                 | /api/file/download?id=xxx | GET                            |
| 重命名文件（目录）       | /api/file/reName          | POST(id=xxx&newName=xxx)       |
| 新建文件夹               | /api/file/newFolder       | POST(curId=xxx&foldername=xxx) |
| 获取当前用户所有文件信息 | /api/file/all             | GET                            |
| 删除文件（目录）         | /api/file/delete?id=xxx   | GET                            |



## 返回值协议

* 0-9 ：
* 10-19: 数据库
* 20-29: 文件

| code | Message                        | Data | 说明                       |
| ---- | ------------------------------ | ---- | -------------------------- |
| 0    |                                |      | 成功                       |
| 10   | database error                 |      | 未知数据库错误             |
| 11   | node not exist, query fail     |      | 当前结点在数据库中不存在   |
| 12   | node already exist , add fail  |      | 目标结点已经存在，插入失败 |
|      |                                |      |                            |
| 20   | File error                     |      | 未知文件错误               |
| 21   | file already exist, save fail  |      | 文件已存在，保存失败       |
| 22   | file not exist                 |      | 目标文件不存在             |
| 23   | illegal filename               |      | 文件名不合格               |
| 24   | preview not allowed            |      | 文件不支持预览             |
| 25   | can not access this file       |      | 无访问权限                 |
|      |                                |      |                            |
| 30   | user error                     |      | 用户相关错误               |
| 31   | user not found                 |      | 用户不存在                 |
| 32   | already authenticated          |      | 用户已经登录               |
| 33   | login fail                     |      | 登录失败                   |
| 34   | user add fail                  |      |                            |
| 35   | get current_user fail          |      |                            |
| 36   | user unauthorized,please login |      | 用户未登录                 |
| 37   | token out of date              |      | token 过期                 |
| 38   | Wrong token                    |      | token 错误                 |
|      |                                |      |                            |
|      |                                |      |                            |
| 分享 |                                |      |                            |
|      |                                |      |                            |
| 41   | wrong share_token              |      |                            |
| 42   | out of date                    |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |
|      |                                |      |                            |



## 设计规约

* id = -1 是根目录
* uid = -1 是管理员账号