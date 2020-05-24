<template>
    <!-- 公共侧边栏组件 -->
    <div class="sidebar">
    <!-- default-active：当前激活菜单的 index；
         collapse：是否折叠收起菜单；
         unique-opened：是否只保持一个子菜单的展开，默认为false；
         router：是否使用 vue-router 的模式，启用该模式会在激活导航时以 index 作为 path 进行路由跳转，默认值为false； -->
        <el-menu
            class="sidebar-el-menu"
            background-color="#324157"
            text-color="#bfcbd9"
            active-text-color="#20a0ff"
            unique-opened
        >
        <!-- 对items进行遍历 -->
            <el-menu-item-group>
              <el-menu-item @click='goAllFiles'>
                <i class="el-icon-files"></i>
                <span slot="title">全部</span>
              </el-menu-item>
              <el-menu-item @click='goDocs'>
                <i class="el-icon-document"></i>
                文档</el-menu-item>
              <el-menu-item @click='goImgs'>
                <i class="el-icon-picture"></i>
                图片</el-menu-item>
              <el-menu-item @click='goMusics'>
                <i class="el-icon-headset"></i>
                音乐</el-menu-item>
              <el-menu-item @click='goVideos'>
                <i class="el-icon-video-camera-solid"></i>
                视频</el-menu-item>
              <el-menu-item @click='goTrash'>
                <i class="el-icon-files"></i>
                回收站</el-menu-item>
              <el-menu-item @click='goDemo'>
                <i class="el-icon-files"></i>
                demo</el-menu-item>
              <!-- <el-menu-item @click='goTrash'>
                <el-progress type="circle" :percentage="20"></el-progress>
                容量：2G/10G
              </el-menu-item> -->
              
            </el-menu-item-group>
        </el-menu>
    </div>
</template>

<script>
    export default {
        data() {
            return {

            };
        },
        computed: {
        },
        created() {
        },
        methods:{
          goAllFiles(){
            this.$router.push('/home/files')
          },
          goDocs(){
            this.$router.push('/home/doc')
          },
          goImgs(){
            this.$router.push('/home/img')
          },
          goMusics(){
            this.$router.push('/home/music')
          },
          goVideos(){
            this.$router.push('/home/video')
          },
          goTrash(){
            this.$router.push('/home')
          },
          goDemo(){
            this.$router.push('/home/demo')
          }
        }
    };
</script>

<!-- CSS样式 -->
<style scoped>
    .sidebar {
        display: block;
        position: absolute;
        left: 0;
        top: 70px;
        bottom: 0;
        overflow-y: scroll;
    }
    .sidebar::-webkit-scrollbar {
        width: 0;
    }
    .sidebar-el-menu:not(.el-menu--collapse) {
        width: 250px;
    }
    .sidebar > ul {
        height: 100%;
    }
</style>
