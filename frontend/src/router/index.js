import Vue from 'vue'
import Router from 'vue-router'
import Home from '../components/common/Home.vue'
import Login from '../components/Auth/Login.vue'
import Logout from '../components/Auth/Logout.vue'
import Register from '../components/Auth/Register.vue'
import Share from '../components/Page/Share.vue'

import FileContainer from '../components/Page/FileContainer.vue'
// import Docs from '../components/Page/Docs.vue'
// import Imgs from '../components/Page/Imgs.vue'
// import Musics from '../components/Page/Musics.vue'
// import Videos from '../components/Page/Videos.vue'
import AllFiles from '../components/Page/AllFiles.vue'
import Filter from '../components/Page/Filter.vue'
import NotFoundComponent from '../components/Page/NotFoundComponent.vue'
Vue.use(Router)

export default new Router({
	mode: 'history',
  routes: [
    { path: '*', component: NotFoundComponent },
    {
        path: '/',
        redirect: '/home/files/-1'
    },
    {
      path: '/home',
      name: 'Home',
      component: Home,
      meta:{
        requiresAuth:true,
      },
      children:[
        {
          path:'files',
          redirect:'/home/files/-1'
        },
        {
          path:':nodeType',
          name:'Filter',
          component:Filter,
          props: true,
          meta:{
            requiresAuth:true
          },
        },
        {
          path:'demo/:id',
          name:'FileContainer',
          component:FileContainer,
          props: true,
          meta:{
            requiresAuth:true
          },
        },
        {
          path:'files/:id',
          name:'AllFiles',
          component:AllFiles,
          props: true,
          meta:{
            requiresAuth:true
          },
        },
        {
          path:'demo',
          redirect:'/home/demo/-1'
        }
      ]
    },
    {
      path:'/share/:shareUrl',
      name:'Share',
      component:Share,
      props:true
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta:{
        requiresVisitor:true
      }
    },
    {
      path: '/register',
      name: 'Register',
      component: Register,
      meta:{
        requiresVisitor:true
      }
    },
    {
      path: '/logout',
      name: 'Logout',
      component: Logout,
      meta:{
        requiresAuth:true
      }
    }
  ]
})
