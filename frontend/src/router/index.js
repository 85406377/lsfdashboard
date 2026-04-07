import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import JobsList from '../views/JobsList.vue'
import JobDetail from '../views/JobDetail.vue'
import AdminLayout from '../views/AdminLayout.vue'
import AdminProfile from '../views/AdminProfile.vue'
import HistoryList from '../views/HistoryList.vue'
import HistoryDetail from '../views/HistoryDetail.vue'
import Login from '../views/Login.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/jobs',
    name: 'JobsList',
    component: JobsList
  },
  {
    path: '/hist',
    name: 'HistoryList',
    component: HistoryList
  },
  {
    path: '/hist/:bid',
    name: 'HistoryDetail',
    component: HistoryDetail
  },
  {
    path: '/job/:jobId',
    name: 'JobDetail',
    component: JobDetail
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminLayout,
    redirect: '/admin/profile',
    children: [
      {
        path: 'profile',
        name: 'AdminProfile',
        component: AdminProfile
      },
      {
        path: 'history',
        name: 'HistoryList',
        component: HistoryList
      },
      {
        path: 'history/:bid',
        name: 'HistoryDetail',
        component: HistoryDetail
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/auth',
    name: 'Auth',
    component: Login
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 路由守卫 - 所有路由都需要认证（除了 login）
router.beforeEach((to, from, next) => {
  if (to.path === '/login') {
    next()
  } else {
    // 检查 localStorage 中的登录状态
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true'
    
    if (!isLoggedIn) {
      // 未登录，重定向到登录页，并保存原路径
      next({
        path: '/login',
        query: { next: to.fullPath }
      })
    } else {
      next()
    }
  }
})

export default router
