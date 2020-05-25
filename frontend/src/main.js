// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import VueCookies from 'vue-cookies'
import VueCookie from 'vue-cookie'

import { BootstrapVue, IconsPlugin } from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

// // 引入ant design https://www.antdv.com/docs/vue/getting-started-cn/
// import Antd from 'ant-design-vue';
// import 'ant-design-vue/dist/antd.css';
// Vue.use(Antd);

// 引入 element ui
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';
Vue.use(ElementUI);



import {store} from './store/store.js'


// import AxiosPlugin from 'vue-axios-cors';
// Vue.use(AxiosPlugin)

// Install BootstrapVue
Vue.use(BootstrapVue)
// Optionally install the BootstrapVue icon components plugin
Vue.use(IconsPlugin)

Vue.use(VueCookies)
Vue.use(VueCookie)
Vue.use(router)

Vue.config.productionTip = false

router.beforeEach((to,from,next) => {
  if(to.matched.some(record => record.meta.requiresAuth)){
    if(! store.getters.loggedIn){//如果当前没登录，则需要跳转到登录页
      console.log('requiresAuth -> not login')
      next({
        path:'/login',
        query:{redirect:to.fullPath}
      })
    }else{//如果登录过
      console.log('requiresAuth -> logined')
      next()
    }
  }else if(to.matched.some(record => record.meta.requiresVisitor)){
    if(store.getters.loggedIn){//如果当前登录了
      console.log('requiresVisiter -> logined')
      next({
        path:'/files/-1',
        query:{redirect:to.fullPath}
      })
    }else{//如果没登录
      console.log('requiresVisiter ->  not logined')
      next()
    }
  }else{
    next()
  }
})


/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  components: { App },
  template: '<App/>'
})
