[TOC]

## APIs (Api.js)

## api设计



### 总体

```js
const Api = {
    BASE_API :'http://localhost:5000',
    //...
}
```

### 登录相关

### 文件夹

```
http://localhost:5000/folders/
```

* 添加文件夹

```
# http://localhost:5000/folders/<path:full_path>?query=add
# POST {name:name}
# 在 full_path 下建立名为name 的文件夹
```

```
eg. curl -X POST -H "content-type: application/json" --data '{"name":"folder1"}' http://localhost:5000/folders/root?query=add
```

* 重命名文件夹（TODO）

```
# http://localhost:5000/folders/<path:full_path>?query=reName
# POST {newName:newName}
```

```
curl -X POST -H "content-type: application/json" --data '{"newName":"new_folder1"}' http://localhost:5000/folders/root/folder1?query=reName
```

* 获取文件夹信息

```
# http://localhost:5000/folders/<path:full_path>?query=getInfo
# GET 
# 此函数返回 full_path 的信息和所包含的所有 folder 和 file
```

```
# 获得文件夹c的信息和 所包含的所有 folder 和 file
eg. curl http://localhost:5000/folders/root/folder1?query=getInfo
```

* 删除文件夹

```
# http://localhost:5000/folders/<full_path>?query=delete
# GET
```

```
eg. curl -v -X DELETE http://localhost:5000/folders/root/folder1?query=delete
```

### 文件

```python
http://localhost:5000/files/
```

* 上传

```
# http://localhost:5000/files/<path:full_path>?query=upload
# POST 
# 此函数向当前文件夹path下上传 'file'
```

```
eg. curl -X POST -F file=@test.py http://localhost:5000/files/root/folder1?query=upload
```

* 重命名

```
# http://localhost:5000/files/<path:full_path>?query=reName
# POST {newName:newName}
```

```
curl -X POST -H "content-type: application/json" --data '{"newName":"new_test.py"} 'http://localhost:5000/files/root/folder1/test.py?query=reName
```

* 获取文件信息/下载

```
# http://localhost:5000/files/<path:full_path>?query=getInfo
# GET
```

```
eg. curl http://localhost:5000/files/root/folder1/test.py?query=getInfo
```

下载

```
# http://localhost:5000/files/<path:full_path>?query=download
# GET
```

```
eg. curl http://localhost:5000/files/root/folder1/test.py?query=download
```



* 删除

```
# http://localhost:5000/files/<path:full_path>?query=delete
# GET
```

```
eg. eg. curl -v -X DELETE http://localhost:5000/files/root/folder1/test.py/query=delete
```

### 分享



## RESTful

```js
const Api = {
    BASE_API :'http://localhost:5000',
    //...
    // //获取所有文件夹
    // // eg. curl http://localhost:5000/folders/  
    // getFolders() {
    //     return fetch(this.BASE_API + "/folders", {
    //         method: 'GET',
    //         headers: {
    //             'Accept': 'application/json',
    //         },
    //     });
    // },
    
    // 添加文件夹
    // selected_folder_id 当前选中目录 默认为 0（根目录）
    // eg. curl -X POST -H "content-type: application/json" --data '{"name": "111","selected_folder_id":0}' http://localhost:5000/folders

    addFolder(name) {
        return fetch(this.BASE_API + "/folders", {
            method: 'POST',
            body: JSON.stringify({name: name,selected_folder_id:selected_folder_id}),
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
        });
    },
    //获得指定文件夹
    // eg. curl http://localhost:5000/folders/111
    getFolder(name) {
        return fetch(this.BASE_API + "/folders/" + name, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
        });
    },
    //删除指定文件夹
    // eg. curl -v -X DELETE http://localhost:5000/folders/111
    deleteFolder(name) {
        return fetch(this.BASE_API + "/folders/" + name, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json',
            },
        });
    }
    // 上传文件 post
    // eg. curl -X POST -F file=@test.py http://localhost:5000/folders/111
    uploadFile(folder,file){
    	var data = new FormData();
    	data.append('file',file);
    	return fetch(this.BASE_API + "/folders/" + folder,{
    		method:'POST',
    		body:data,
    		headers:{
    			Accept:'application/json',
    		},
    	});
    },
    //获取文件信息
    //eg. curl http://localhost:5000/folders/111/test.py?query=info


    //删除文件 delete
    //eg. eg. curl -v -X DELETE http://localhost:5000/folders/111/test.py
    deleteFile(folder,filename){
    	return fetch(this.BASE_API + "/folders/" + folder + "/" + filename,{
    		method:'DELETE',
    		headers:{
    			'Accept':'application/json',
    		}
    	});
    },
}
```



### 说明

* url 最后一个 没有 ‘/ ’