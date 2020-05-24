<template>
  <div style="width: 80px; margin: 20px;">
      <slot></slot>
      <b-col l="4">

        <!-- 如果是文件夹 -->
        <div style="font-size: 60px;"
        v-if="type=='dir'"
        @click="clickInto(id,type_of_node)">
          <i class="el-icon-folder-opened"
          style="color: #324157; "
          ></i>
        </div>
        <!-- 如果是图片 -->
        <div style="font-size: 60px;"
         v-else-if="type=='img'">
            <el-image
              style="width: 60px; height: 60px"
              :src="previewURL"
              :preview-src-list="[previewSRC]"
              fit="contain"></el-image>
        </div>

        <!-- 如果是视频 -->
        <div style="font-size: 60px;"
        v-else-if="type=='video'"
        @click="clickInto(id,type_of_node)">
          <i class="el-icon-video-camera"
          style="color: #324157; "
          ></i>
        </div>
        <!-- 如果是音乐 -->
        <div style="font-size: 60px;"
        v-else-if="type=='music'"
        @click="clickInto(id,type_of_node)">
          <i class="el-icon-headset"
          style="color: #324157; "
          ></i>
        </div>
        <!-- 如果是文档 -->
        <div style="font-size: 60px;"
        v-else-if="type=='doc'"
        @click="clickInto(id,type_of_node)">
          <i class="el-icon-document"
          style="color: #324157; "
          ></i>
        </div>

        <div v-if="!editing"
         @dblclick="editFilename"
         style="width: 60px;text-align: center;">
          {{filename | cutString(4)}}
        </div>
        <input v-else class="todo-item-edit" type="text"
         v-model="filename" @blur="doneEdit"
         @keyup.enter="doneEdit" @keyup.esc="cancelEdit"
         v-focus>
      </b-col>
  </div>
</template>

<script>
  export default{
    name:'file-item',
    props:{
      file:{
        type:Object,
        required:true
      },
      // checkAll:{
      //   type:Boolean,
      //   required:true
      // }
    },
    data(){
      return {
        "filename": this.file.filename,
        "id": this.file.id,
        "parent_id": this.file.parent_id,
        "path_root": this.file.path_root,
        "size": this.file.size,
        "type_of_node": this.file.type_of_node,
        "upload_time": this.file.upload_time,
        'editing':false,
        'beforeEditCache':'',
        // 'checked':false,
        // 'preChecked':false //存储上一次的状态
      }
    },
    // watch:{
    //   checkAll(){
    //     console.log('watch: checkAll: ')
    //     console.log(this.checkAll)
    //     this.checked = this.checkAll? true:this.preChecked
    //     console.log('after change:')
    //     console.log(this.checked)
    //   }
    // },
    // 每次只能有一个元素focus
    directives:{
      focus:{
        inserted:function(el){
          el.focus()
        }
      }
    },
    computed:{
      type(){
        if (this.type_of_node == 'JPG' ||
                this.type_of_node == 'jpg' ||
                this.type_of_node == 'JPEG' ||
                this.type_of_node == 'jpeg' ||
                this.type_of_node == 'PNG' ||
                this.type_of_node == 'png' ||
                this.type_of_node == 'GIF' ||
                this.type_of_node == 'gif')return 'img'
        else if(this.type_of_node == 'mp3' ||
                this.type_of_node == 'wav' ||
                this.type_of_node == 'wma' ||
                this.type_of_node == 'rm'  ||
                this.type_of_node == 'm4a') return 'music'
        else if(this.type_of_node == 'flv' ||
                this.type_of_node == 'avi' ||
                this.type_of_node == 'mov' ||
                this.type_of_node == 'mp4' ||
                this.type_of_node == 'wmv') return 'video'
        else if(this.type_of_node=='dir')return 'dir'
        else return 'doc'
      },
      //缩略图
      previewURL(){
        return this.$store.getters.targetHost + '/api/file/preview?id=' + this.id +  '&width=50&height=50&token=' + this.$store.getters.token
      },
      //预览图
      previewSRC(){
        return this.$store.getters.targetHost + '/api/file/preview?id=' + this.id +  '&width=800&height=800&token=' + this.$store.getters.token
      }
    },
    methods:{
      clickInto(id,type){
        //如果点击，就要取消所有的checked
        console.log(id,type)
        if(type == 'dir'){//如果是文件夹，则进入文件夹
          console.log('dispath to changecurfileid',id)
          this.$router.push({
            path:'/home/files/' + id,
          })
          this.$store.dispatch('changeCurFileID',id)
          this.$store.dispatch('changePathItems',id)
        }else{
          console.log('预览文件' , id)
        }
      },
      editFilename(){
        // 先把编辑之前的值暂存
        this.beforeEditCache = this.filename
        this.editing = true
      },
      doneEdit(){
        if(this.filename.trim().length == 0){
          this.filename = this.beforeEditCache
          return;
        }
        this.editing = false
        this.$store.dispatch('finishedEdit',{
          id:this.id,
          newName:this.filename
        })
        // 刷新
        this.$store.dispatch('getAllFiles')
        console.log('done edit')
      },
      cancelEdit(){
        this.filename = this.beforeEditCache
        this.editing = false
      },
      // changeChecked(){
      //   this.preChecked = this.checked
      //   console.log(event.target.value)
      //   const id = event.target.value
      //   const res = event.target.checked
      //   if(res){//如果 ☑️
      //     // 1. 向父类告知，修改select
      //     this.$emit('addSelect',id)
      //     // 2. 向vuex告知，使count--
      //     this.$store.dispatch('reduceRemainingCount')
      //     console.log(res)
      //   }else{//如果 not ☑️
      //     // 1. 向父类告知，修改select
      //     this.$emit('deleteSelect',id)
      //     // 2. 向vuex告知，使count++
      //     this.$store.dispatch('addRemainingCount')
      //     console.log(res)
      //   }
      // }
    },
    filters:{
      cutString(str,len){
        var reg = /[\u4e00-\u9fa5]/g,    //专业匹配中文
          slice = str.substring(0, len),
          chineseCharNum = (~~(slice.match(reg) && slice.match(reg).length)),
          realen = slice.length*2 - chineseCharNum;
        return str.substr(0, realen) + (realen < str.length ? "..." : "");
      }
    }
  }
</script>

<style>
</style>
