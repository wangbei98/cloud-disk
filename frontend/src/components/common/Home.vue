<template>
<!-- 公共Home组件 -->
    <div class="wrapper">
        <!-- 头部组件 -->
        <v-head></v-head>
        <!-- <nav-header></nav-header> -->
        <!-- 侧边栏组件 -->
        <v-sidebar></v-sidebar>
        <div class="content-box" >
          <router-view></router-view>
        </div>
    </div>
</template>

<script>
    import NavHeader from './NavHeader.vue';
    import vHead from './Header.vue'
    import vSidebar from './Sidebar.vue';
    export default {
        components: {
            vHead,
            NavHeader,
            vSidebar,
        },
        created() {
        }
    };
</script>
