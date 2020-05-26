import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

Vue.use(Vuex);

//生产环境
axios.defaults.baseURL = '//116.62.177.146/api'
//开发环境
// axios.defaults.baseURL = '/api'


// Vue.use(axios)
// Vue.prototype.$ajax = axios

export const store = new Vuex.Store({
  state:{
    email: localStorage.getItem('email') || null,
    files:[],
    token: localStorage.getItem('token') || '',//用来预览图片
    curFileID:-1,
    curPathItems:[
      {
        text:'/root',
        to:{
          name:'FileContainer',
          path:'/home/files/-1',
          id:'-1'
        }
      },
    ],
    //没有被选中的Item的数量
    // remainingCount:0
  },
  getters:{
    loggedIn(state){
      return state.email !== null
    },
    curFileList(state){
      //每次获取/更新curFileList 的时候重新计算 remainingCount
      const fileList = state.files.filter(file => file.parent_id == state.curFileID)
      state.remainingCount = fileList.length
      return fileList
    },
    curPathItems(state){
      console.log('get curPathItems')
      console.log(state.curPathItems)
      return state.curPathItems
    },
    // anyRemaining(state){
    //   //当存在「没有被选中的」 返回true
    //   return state.remainingCount != 0
    // },
    curEmail(state){
      return state.email
    },
    token(state){
      return state.token
    },
    targetHost(state){
      return 'http://116.62.177.146'
    }
  },
  mutations:{
    refreshEmail(state,email){
      state.email = email
    },
    deleteEmail(state){
      state.email = null
    },
    refreshFiles(state,files){
      state.files = files
    },
    refreshToken(state,token){
      state.token = token
    },
    deleteToken(state){
      state.token = ''
    },
    changeCurFileID(state,id){
      state.curFileID = id
    },
    changePathItems(state,id){
      console.log('in changePathItems')
      console.log(id)
      //如果当前路径有这个id，则删除这个id后面的对象
      if(state.curPathItems.findIndex(pathItem => pathItem.to.id == id) != -1){
        console.log('in if')
        // console.log(state.curPathItems.findIndex(pathItem => pathItem.to.query.id == id))
        const index = state.curPathItems.findIndex(pathItem => pathItem.to.id == id)
        state.curPathItems.splice(index+1)
      }else{//如果没有，则将这个id对应的路径push进去
        console.log('in else :')
        console.log(id)
        const newFile = state.files.filter(file => file.id == id)[0] // 找到对应的file对象
        const filename = newFile.filename
        const newPathItem = {
          text:filename,
          to:{
            name:'FileContainer',
            path:'/home/files/' + id ,
            id:id
          }
        }
        // state.curPathItems.splice(state.curPathItems.length-1,0,newPathItem)
        state.curPathItems.push(newPathItem)
      }
    },
    // checkAll(state,data){
    //   if(data.checked){//如果全选
    //     state.remainingCount = 0
    //   }else{//如果全不选，则初始化 remaining
    //     state.remainingCount=data.len
    //   }
    // },
    // addRemainingCount(state){
    //   state.remainingCount++
    // },
    // reduceRemainingCount(state){
    //   state.remainingCount--
    // },
    // emptyChecked(state,len){
    //   state.remainingCount = len
    // }
  },
  actions:{
    login(context,credentials){
      // 将axios封装为Promise请求
      return new Promise((resolve,reject) => {
        axios.post('/login',{
          email:credentials.email,
          password:credentials.password
        }).then(response => {
          console.log(response)
          const email = response.data.data.user.email
          context.commit('refreshEmail',email)
          localStorage.setItem('email',email)
          resolve(response)
        }).catch(err => {
          console.log(err)
          reject(err)
        })
      })
    },
    logout(context){
      if(context.getters.loggedIn){
        return new Promise((resolve,reject) => {
          axios.get('/logout')
          .then(response => {
            localStorage.removeItem('email')
            context.commit('deleteEmail')
            context.commit('deleteToken')
            localStorage.removeItem('token')
            resolve(response)
          }).catch(err => {
            localStorage.removeItem('email')
            context.commit('deleteEmail')
            reject(err)
          })
        })
      }
    },
    register(context,data){
      // 将axios封装为Promise请求
      return new Promise((resolve,reject) => {
        axios.post('/register',{
          email:data.email,
          password:data.password
        }).then(response => {
          alert('success')
          resolve(response)
        }).catch(err => {
          reject(err)
        })
      })
    },
    saveToken(context,token){
      localStorage.setItem('token',token)
      context.commit('refreshToken',token)
    },
    getAllFiles(context){
      return new Promise((resolve,reject) => {
        axios.get('/file/all')
        .then(response=>{
          const files = response.data.data.files
          context.commit('refreshFiles',files)
          resolve(response)
        }).catch(err => {
          console.log(err)
          reject(err)
        })
      })
    },
    changeCurFileID(context,id){//更改当前curFileID
      console.log('context commit changecurfileid',id)
      context.commit('changeCurFileID',id)
    },
    changePathItems(context,id){
      console.log('context commit changePathItems',id)
      context.commit('changePathItems',id)
    },
    finishedEdit(context,data){
      return new Promise((resolve,reject) => {
        axios.post('/file/reName',{
          id:data.id,
          newName:data.newName
        })
        .then(response=>{
          // context.commit('reNameFile',data)
          resolve(response)
        }).catch(err => {
          console.log(err)
          reject(err)
        })
      })
    },
    // 新建folder
    commitNew(context,data){
      return new Promise((resolve,reject) => {
        axios.post('/file/newFolder',{
          curId:data.curID,
          foldername:data.newFile
        })
        .then(response=>{
          // context.commit('reNameFile',data)
          resolve(response)
        }).catch(err => {
          console.log(err)
          reject(err)
        })
      })
    },
    submitUpload(context,data){

      let config = {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
      console.log('action: submit upload')
      console.log(data.file)
      let formData = new FormData();
      formData.append('curId',data.curID)
      formData.append('file',data.file)
      console.log('action: submit upload')
      console.log(formData)
      return new Promise((resolve,reject) => {
        axios.post('/file/upload',formData,config)
        .then(response=>{
          // context.commit('reNameFile',data)
          resolve(response)
        }).catch(err => {
          console.log(err)
          reject(err)
        })
      })
    },
    // //将 checkAll 按钮的值传入 本地checkAll
    // checkAll(context,data){
    //   console.log('action -> checkAll',data.len)
    //   console.log(data.checked)
    //   context.commit('checkAll',data)
    // },
    // addRemainingCount(context){
    //   console.log('action addRemainingCount')
    //   context.commit('addRemainingCount')
    // },
    // reduceRemainingCount(context){
    //   console.log('action reduceRemainingCount')
    //   context.commit('reduceRemainingCount')
    // },
    //  清空复选框 ，让remaining 为 len
    // emptyChecked(context,len){
    //   console.log('action emptyRemainingCount')
    //   context.commit('emptyChecked',len)
    // },
    deleteFile(context,id){
      return new Promise((resolve,reject) => {
        axios.get('/file/delete?id='+id)
        .then(response=>{
          resolve(response)
        }).catch(err => {
          console.log(err)
          reject(err)
        })
      })
    },
    downloadFile(context,id){
      return new Promise((resolve,reject) => {
        console.log('action: downloadFile')
        axios.get('/file/download?id='+id,{
          responseType: 'blob'
        })
        .then(response =>{
          resolve(response)
        }).catch(err => {
          console.log(err)
          reject(err)
        })
      })
    },
    shareFile(context,params){
      return new Promise((resolve,reject) => {
        console.log('action: shareFile')
        axios.post('/file/share',{
          id:params.id,
          token_required:params.token_required,
          day:params.day
        }).then(response =>{
          resolve(response)
        }).catch(err =>{
          reject(err)
        })
      })
    },
    deleteShare(context,share_id){
      return new Promise((resolve,reject) => {
        console.log('action: shareFile')
        axios.post('file/share/cancel',{
          share_id:share_id
        }).then(response =>{
          resolve(response)
        }).catch(err =>{
          reject(err)
        })
      })
    },
    //获取被分享文件的信息
    getShareFileInfo(context,shareUrl){
      return new Promise((resolve,reject) => {
        console.log('action: getShareFileInfo')
        axios.get('file/share/info/'+shareUrl).then(response =>{
          resolve(response)
        }).catch(err =>{
          reject(err)
        })
      })
    },
    downloadShare(context,data){
      return new Promise((resolve,reject) => {
        console.log('action: downloadShare')
        axios.get('/file/share/download/'+data.shareUrl + '?share_token=' + data.shareToken,{
          responseType: 'blob'
        })
        .then(response =>{
          resolve(response)
        }).catch(err => {
          console.log(err)
          reject(err)
        })
      })
    }
  }
})
