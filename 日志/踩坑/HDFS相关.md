

1. 往HDFS上传文件

```
>>> import hdfs
>>> hdfs_client = hdfs.Client("http://127.0.0.1:50070")
>>> f = open('test.py')
>>> hdfs_client.write('/user/hadoop',f)
```

```
$ hdfs dfs -ls /user/hadoop
20/02/26 18:56:45 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
Found 1 items
-rwxr-xr-x   1 dr.who supergroup          0 2020-02-26 18:56 /user/hadoop/test1.py
```

1. hdfs.util.HdfsError: Permission denied:

```
$ hdfs_client.write('/user/hadoop/test1.py',f)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/local/python3/lib/python3.6/site-packages/hdfs/client.py", line 477, in write
    consumer(data)
  File "/usr/local/python3/lib/python3.6/site-packages/hdfs/client.py", line 472, in consumer
    raise _to_error(res)
hdfs.util.HdfsError: Permission denied: user=dr.who, access=WRITE, inode="/user/hadoop":root:supergroup:drwxr-xr-x
        at org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.check(FSPermissionChecker.java:307)
       ....
```

解决方法：修改目标文件夹的权限

```
hdfs dfs -chmod 777 /user/hadoop
```

