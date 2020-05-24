<template>
  <div>
    <v-head></v-head>
    <b-container>
      <b-row align-h="center" class="mt-5">
        <b-col cols="5">
          <b-card v-if="file!=null" class="p-3">
            <h3 class="mb-4">获取文件</h3>
            <div>
              <p>{{file.filename}}</p>
            </div>
            <br>
            <el-row>
              <el-col :span="12">
                <el-input placeholder="请输入密码" v-model="shareToken" show-password></el-input>
              </el-col>
              <el-col :span="12">
                <el-button type="primary" plain @click='handleDownloadShare'>下载</el-button>
              </el-col>
            </el-row>
          </b-card>
          <b-card v-else class="p-3">
            <h4 class="mb-4">该分享链接已失效</h4>
          </b-card>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
  // import NavHeader from '../common/NavHeader.vue'
  import vHead from '../common/Header.vue'
  export default{
    name:'home',
    props:{
      shareUrl:{
        type:String,
        required:true
      }
    },
    components:{
      vHead
    },
    data() {
      return {
        file:null,
        shareToken:''
      };
    },
    created(){
      this.$store.dispatch('getShareFileInfo',this.shareUrl)
      .then(res=>{
        console.log('mounted -> getShareFileInfo -> res')
        console.log(res)
        this.file = res.data.data.file
        console.log('this.file:')
        console.log(this.file)
      }).catch(err=>{
        console.log(err)
      })
    },
    methods:{
      handleDownloadShare(){
        //仿照文件下载的方法
        this.$store.dispatch('downloadShare',{
          shareUrl:this.shareUrl,
          shareToken:this.shareToken
        })
        .then(res=>{
          console.log('in handleDownloadShare -> res:')
          console.log(res)
          if (res.data.type === "application/json") {
            this.$message({
              type: "error",
              message: "下载失败，文件不存在或权限不足"
            });
          } else {
            if (window.navigator.msSaveOrOpenBlob) {
              navigator.msSaveBlob(blob, this.file.fileName);
            } else {
              let url = window.URL.createObjectURL(new Blob([res.data]))
              let link = document.createElement('a')
              link.style.display = 'none'
              link.href = url
              link.setAttribute('download', this.file.filename)

              document.body.appendChild(link)
              link.click()
            }
          }
          this.$message({
            message: '下载成功',
            type: 'success'
          })
        })
        .catch(err=>{
          console.log(err)
          this.$message.error('下载失败，请刷新后重试');
        })
      }
    }
  }
</script>

<style>
  body {
    background: #eef1f4;
  }
</style>
