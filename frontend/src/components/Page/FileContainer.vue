<template>
  <div class="file-container">
    <!-- <b-breadcrumb>
      <b-breadcrumb-item v-for="pathItem in pathItems"
      @click='changeCurFileID(pathItem.to.id,pathItem.to.path)'
      :key='pathItem.to.id'
      :text="pathItem.text">
      </b-breadcrumb-item>
    </b-breadcrumb> -->
    <div>
      <b-card title="Card Title" no-body>
        <b-card-header header-tag="nav">
          <b-nav card-header tabs>
            <b-nav-item :active="newFolderTab"
            @click='clickNewFolderTab'>新建文件夹</b-nav-item>
            <b-nav-item :active="uploadTab"
            @click='clickUploadTab'>上传文件</b-nav-item>
          </b-nav>
        </b-card-header>

        <b-card-body class="text-center">
          <div v-if="newFolderTab">
            <!-- v-model="newFolderSuccessAlert" -->
            <!-- <b-alert :show="dismissCountDown"
             dismissible
            @dismissed="dismissCountDown=0"
            @dismiss-count-down="countDownChanged">
              add success
            </b-alert> -->
            <b-button-toolbar aria-label="Toolbar with button groups and input groups">
              &nbsp;
              <b-input-group size="sm">
                <b-form-input
                 placeholder="新建文件夹" class="text-right"
                 v-model="newFile"
                ></b-form-input>
              </b-input-group>
              &nbsp;
              <b-button-group size="sm" class="mr-1">
                <b-button @click='commitNew'
                @keyup.enter="commitNew" >Commit</b-button>
                &nbsp;
                <b-button @click='cancelNew'
                @keyup.esc="cancelNew">Cancel</b-button>
              </b-button-group>
            </b-button-toolbar>
          </div>
          <div v-if="uploadTab">
            <!-- <b-alert v-model="uploadSuccessAlert" dismissible>
              upload success</b>
            </b-alert> -->
            <!-- <b-alert
            :show="dismissCountDown"
             dismissible
            @dismissed="dismissCountDown=0"
            @dismiss-count-down="countDownChanged">
              upload success
            </b-alert> -->
            <div>
              <b-form-file
                    v-model="file"
                    :state="Boolean(file)"
                    placeholder="Choose a file or drop it here..."
                    drop-placeholder="Drop file here..."
                  ></b-form-file>
              <div class="mt-3">Selected file: {{ file ? file.name : '' }}</div>
            </div>
            <b-button variant="primary"
             @click="submitUpload">上传</b-button>
          </div>

        </b-card-body>
      </b-card>
    </div>
    <br>
    <!-- <div>
       <b-form-checkbox
         :checked="!anyRemaining"
         @change='allChecked'
       >
         Check All
       </b-form-checkbox>
    </div> -->
    <!-- <div>
      {{selectedLength}} items selected
    </div> -->
    <!-- <b-row>
      <file-item v-for="(file,index) in curFileList"
      :key="file.id" :file='file'
      :checkAll = '!anyRemaining'
      @addSelect = 'addSelect'
      @deleteSelect = 'deleteSelect'
      @emptyChecked='emptyChecked'
      >
      </file-item>
    </b-row> -->


    <el-container style="height: 500px; border: 1px solid #eee">
      <el-aside width="200px" style="background-color: rgb(238, 241, 246)">
        <el-menu :default-openeds="['1', '3']">

          <el-submenu index="1">
            <el-menu-item-group>
              <el-menu-item index="3-1">全部</el-menu-item>
              <el-menu-item index="3-2">文档</el-menu-item>
              <el-menu-item index="3-3">视频</el-menu-item>
              <el-menu-item index="3-4">图片</el-menu-item>
              <el-menu-item index="3-5">音乐</el-menu-item>
              <el-menu-item index="3-6">回收站</el-menu-item>
            </el-menu-item-group>
          </el-submenu>
        </el-menu>
      </el-aside>

      <el-container>
        <b-breadcrumb>
          <b-breadcrumb-item v-for="pathItem in pathItems"
          @click='changeCurFileID(pathItem.to.id,pathItem.to.path)'
          :key='pathItem.to.id'
          :text="pathItem.text">
          </b-breadcrumb-item>
        </b-breadcrumb>
        <el-header style="text-align: right; font-size: 12px">
          <!-- <el-dropdown>
            <i class="el-icon-setting" style="margin-right: 15px"></i>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item>查看</el-dropdown-item>
              <el-dropdown-item>新增</el-dropdown-item>
              <el-dropdown-item>删除</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
          <!-- <el-tooltip v-if="selectedLength>0" placement="top"> -->
           <!-- <el-button type="text" v-if="selectedLength>0"
            @click='handleDownload'>下载</el-button> -->
          <!-- </el-tooltip> -->
          <!-- <el-tooltip v-if="selectedLength>0" placement="top"> -->
           <!-- <el-button type="text" v-if="selectedLength>0"
            @click='handleDelete'>删除</el-button> -->
          <!-- </el-tooltip> -->
          <!-- <el-tooltip placement="top"> -->
           <!-- <span>{{selectedLength}} items selected</span> -->
          <!-- </el-tooltip> -->
          <el-row type="flex" class="row-bg" justify="end">
            <el-col :span="6"><el-button type="text" v-if="selectedLength>0"
            @click='handleShowShare'>查看分享链接</el-button></el-col>
            <el-col :span="6"><el-button type="text" v-if="selectedLength>0"
            @click='handleShare'>分享</el-button></el-col>
            <el-col :span="6"><el-button type="text" v-if="selectedLength>0"
            @click='handleDownload'>下载</el-button></el-col>
            <el-col :span="6"><el-button type="text" v-if="selectedLength>0"
            @click='handleDelete'>删除</el-button></el-col>
            <el-col :span="6">
              <el-checkbox :indeterminate="isIndeterminate" v-model="checkAll" @change="handleCheckAllChange">全选</el-checkbox>
            </el-col>
            <el-col :span="6"><span style="font-size: 15px;">{{selectedLength}} items selected</span></el-col>
          </el-row>
        </el-header>

        <el-main>
          <el-checkbox-group v-model="selected"
          @change="handleSelectedChange">
            <el-checkbox v-for="file in curFileList" :label="file" :key="file.id">
              <file-item :file='file'></file-item>
            </el-checkbox>
          </el-checkbox-group>

        </el-main>
      </el-container>
    </el-container>

    <el-dialog title="分享文件" :visible.sync="dialogFormVisible">
      <el-form :model="shareForm">
        <el-form-item label="是否需要密码" :label-width="formLabelWidth">
          <!-- <el-input v-model="shareForm.token_required" autocomplete="off"></el-input> -->
          <el-radio v-model="shareForm.token_required" label="0">不需要</el-radio>
          <el-radio v-model="shareForm.token_required" label="1">需要</el-radio>
        </el-form-item>
        <el-form-item label="失效时间" :label-width="formLabelWidth">
          <el-input v-model="shareForm.day" autocomplete="off"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible = false">取 消</el-button>
        <el-button type="primary" @click="newShare">确 定</el-button>
      </div>
    </el-dialog>
    <el-dialog width="70%" title="已经分享的链接" :visible.sync="dialogTableVisible">
      <el-table :data="shares"
      ref="multipleTable"
       max-height="400"
      :default-sort = "{prop: 'share_begin_time', order: 'descending'}"
      @selection-change="handleSelectionChange">
        <el-table-column
          type="selection"
          width="55">
        </el-table-column>
        <el-table-column sortable property="share_begin_time" label="开始日期" :formatter="beginTimeFormatter" width="150"></el-table-column>
        <el-table-column sortable property="share_end_time" label="失效日期" :formatter="endTimeFormatter" width="150"></el-table-column>
        <el-table-column property="share_url" label="链接" :formatter="URLFormatter" width="400"></el-table-column>
        <el-table-column property="share_token" label="密钥"></el-table-column>
      </el-table>
      <div style="margin-top: 20px">
        <el-button @click="toggleSelection()">取消选择</el-button>
        <el-button @click="handleDeleteShare()">删除链接</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
  import FileItem from '../common/FileItem.vue'
  export default {
    name:'file-container',
    props:{
      id:{
        type:String,
        required:true
      }
    },
    inject:['reload'],
    data(){
      return{
        newFile:'',
        // newFolderSuccessAlert:false,
        // uploadSuccessAlert:false,
        // dismissSecs: 5,
        // dismissCountDown: 0,
        file: null,
        checkAll:false,
        isIndeterminate: true,
        newFolderTab:true,
        uploadTab:false,
        selected:[],
        shareForm:{
          id:-1,
          token_required:0,
          day:1
        },
        dialogFormVisible: false,
        dialogTableVisible: false,
        formLabelWidth: '120px',
        shares:[],
        multipleSelection: [],// 选中的分享链接
      }
    },
    components:{
      FileItem
    },
    created(){
      console.log('created FileContainer')
      this.$store.dispatch('getAllFiles')
      console.log('this.id',this.id)
      // console.log('$route.query.id',this.$route.query.id)
      this.$store.dispatch('changeCurFileID',this.id)
      // this.$store.dispatch('changePathItems',this.id)
    },
    computed:{
      curFileList(){
        return this.$store.getters.curFileList
      },
      pathItems(){
        console.log('computed pathItems')
        console.log(this.$store.getters.curPathItems)
        return this.$store.getters.curPathItems
      },
      anyRemaining(){
        return this.$store.getters.anyRemaining
      },
      selectedLength(){
        return this.selected.length
      },
    },
    methods:{
      changeCurFileID(id,path){
        this.$store.dispatch('changeCurFileID',id)
        this.$store.dispatch('changePathItems',id)
        this.$router.push(path).catch(err => {})
        //晴空所有复选框
        this.emptyChecked()
      },
      // 提交新建文件夹
      commitNew(){
        this.$store.dispatch('commitNew',{
          curID:this.id,
          newFile:this.newFile
        }).then(response => {
          //成功后提示
          // this.shownewFolderSuccessAlert()
          this.$message({
            message: '新建成功',
            type: 'success'
          })
          // 刷新页面
          this.reload()
        })
        // 刷新数据
        this.$store.dispatch('getAllFiles')
      },
      cancelNew(){
        this.newFile = ''
      },
      // shownewFolderSuccessAlert(){
      //   // this.newFolderSuccessAlert = true
      //   this.dismissCountDown = this.dismissSecs
      // },
      // showuploadSuccessAlert(){
      //   this.dismissCountDown = this.dismissSecs
      // },
      // countDownChanged(dismissCountDown) {
      //   this.dismissCountDown = dismissCountDown
      // },

      clickNewFolderTab(){
        this.newFolderTab = true
        this.uploadTab = false
      },
      clickUploadTab(){
        this.newFolderTab = false
        this.uploadTab = true
      },
      //提交上传
      submitUpload(){
        if(!this.file){
          return
        }
        console.log('submitUpload:')
        console.log(this.id)
        console.log(this.file)
        this.$store.dispatch('submitUpload',{
          curID:this.id,
          file:this.file,
        }).then(response => {
          //成功后提示
          // this.showuploadSuccessAlert()
          this.$message({
            message: '上传成功',
            type: 'success'
          })
          // 刷新页面
          this.reload()
        }).toLocaleString(err => {})
        // 刷新数据
        // this.$store.dispatch('getAllFiles')
      },
      // allChecked(){
      //   // this.$store.state.todos.forEach((todo) => todo.completed = event.target.checked)
      //   // 将 checkAll 按钮的值存下来
      //   console.log('click check all')
      //   const length = this.curFileList.length
      //   console.log('--> current FileList len:',length)
      //   console.log(event.target.checked)
      //   this.$store.dispatch('checkAll',{
      //     checked:event.target.checked,
      //     len:length
      //   })
      //   //如果点击全选
      //   if(event.target.checked){
      //     this.selected = this.curFileList.map(item => item.id);
      //     console.log('点击全选后的select数组')
      //     console.log(this.selected)
      //   }else{
      //     this.selected = []
      //   }
      // },
      handleCheckAllChange(val){
        this.selected = val ? this.curFileList : [];
        this.isIndeterminate = false;
      },
      handleSelectedChange(value) {
        let checkedCount = value.length;
        this.checkAll = checkedCount === this.curFileList.length;
        this.isIndeterminate = checkedCount > 0 && checkedCount < this.curFileList.length;
      },
      // addSelect(id){
      //   this.selected.push(id)
      //   console.log('after push select is ')
      //   console.log(this.selected)
      // },
      // deleteSelect(id){
      //   const index = this.selected.findIndex(item => item ==id)
      //   this.selected.splice(index,1)
      //   // console.log(index)

      //   console.log('after delete select is ')
      //   console.log(this.selected)
      // },
      // FileITem 发生点击事件时，清空当前select 和 remaining=len
      // emptyChecked(){
      //   this.selected = []
      //   console.log('method:emptyChecked')
      //   console.log(this.selected)
      //   this.$store.dispatch('emptyChecked',this.curFileList.length)
      // },
      handleDownload(){
        console.log('in handleDownload')
        this.selected.forEach(file => this.$store.dispatch('downloadFile',file.id)
        .then(res => {
          console.log('in handleDownload -> res:')
          console.log(res)
          if (res.data.type === "application/json") {
            this.$message({
              type: "error",
              message: "下载失败，文件不存在或权限不足"
            });
          } else {
            if (window.navigator.msSaveOrOpenBlob) {
              navigator.msSaveBlob(blob, file.fileName);
            } else {
              let url = window.URL.createObjectURL(new Blob([res.data]))
              let link = document.createElement('a')
              link.style.display = 'none'
              link.href = url
              link.setAttribute('download', file.filename)

              document.body.appendChild(link)
              link.click()
            }
          }
          this.$message({
            message: '下载成功',
            type: 'success'
          })
        })
        .catch(err => {
          console.log(err)
          this.$message.error('下载失败，请刷新后重试');
        }))

      },
      handleDelete(){
        console.log('in handleDelete')
        this.selected.forEach(file => this.$store.dispatch('deleteFile',file.id)
        .then(response => {
          this.$message({
            message: '删除成功',
            type: 'success'
          })
          // 刷新页面
          this.reload()
        })
        .catch(err => {
          this.$message.error('删除失败，请刷新后重试');
        }))
      },
      handleShare(){
        if(this.selected.length >1){
          this.$message.error('只能选中一个')
          return
        }
        var file = this.selected[0]
        if(file.type_of_node == 'dir'){
          this.$message.error('暂时不支持分享目录')
        }else{
        // 设置当前id
        this.shareForm.id = file.id
        // 显示对话框
        this.dialogFormVisible = true
        }
      },
      newShare(){
        this.dialogFormVisible = false
        this.$store.dispatch('shareFile',this.shareForm)
        .then(res => {
          console.log('new share success -> res: ')
          console.log(res)
          const shareURL = res.data.data.share.share_url
          const shareToken = res.data.data.share.share_token
          console.log(shareURL)
          console.log(shareToken)
          this.$message({
            message:'分享成功',
            type:'sucess'
          })
          // 刷新页面
          this.reload()
        }).catch(err =>{
          this.$message.error('分享失败')
        })
      },
      handleShowShare(){
        if(this.selected.length >1){
          this.$message.error('只能选中一个')
          return
        }
        var file = this.selected[0]
        if(file == 'dir'){
          this.$message.error('暂时不支持分享目录')
        }else{
          var shares = file.shares
          this.shares = shares
          console.log('method : handleShowShare -> this.shares: ')
          console.log(this.shares)
          this.dialogTableVisible = true
        }
      },
      // 操作shares
      toggleSelection(rows) {
        if (rows) {
          console.log('in toggleSelection -> rows')
          console.log(rows)
          rows.forEach(row => {
            this.$refs.multipleTable.toggleRowSelection(row);
          });
        } else {
          console.log('in toggleSelection -> not rows')
          console.log(rows)
          this.$refs.multipleTable.clearSelection();
        }
      },
      handleSelectionChange(val) {
        this.multipleSelection = val;
      },
      handleDeleteShare(){
        console.log(this.multipleSelection)
        this.multipleSelection.forEach(item =>
          this.$store.dispatch('deleteShare',item.share_id)
          .then(res => {
            this.$message({
              message:'删除成功',
              type:'sucess'
            })
            // 刷新页面
            this.reload()
          })
          .catch(err => {
            this.$message.error('删除失败')
          }))
      },
      //时间戳转string
      beginTimeFormatter(row,col){
        return new Date(parseInt(row.share_begin_time) * 1000).toLocaleString().replace(/:\d{1,2}$/,' ');
      },
      endTimeFormatter(row,col){
        return new Date(parseInt(row.share_end_time) * 1000).toLocaleString().replace(/:\d{1,2}$/,' ');
      },
      // 补全share_url
      URLFormatter(row,col){
        return this.$store.getters.targetHost + '/share/' + row.share_url
      }
    }
  }
</script>

<style>
  .file-container{
    margin-left: 10%;
    margin-right: 10%;
    padding-top: 30px;
  }


  .el-header {
    /* background-color: #E9ECF0; */
    color: #333;
    line-height: 20px;
  }

  .el-aside {
    color: #333;
  }
  .el-row {
    margin-bottom: 0px;
    &:last-child {
      margin-bottom: 0;
    }
  }
  .el-col {
    border-radius: 4px;
  }
  .bg-purple-dark {
    background: #ffffff;
  }
  .bg-purple {
    background: #ffffff;
  }
  .bg-purple-light {
    background: #ffffff;
  }
  .grid-content {
    border-radius: 4px;
    min-height: 20px;
  }
  .row-bg {
    padding:  0;
    background-color: #ffffff;
  }
</style>
