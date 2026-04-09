import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import JobDetail from '../views/JobDetail.vue'
import Login from '../views/Login.vue'
import Profile from '../views/Profile.vue'
import JobsList from '../views/JobsList.vue'
import HistoryJobs from '../views/HistoryJobs.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/job/:jobId',
    name: 'JobDetail',
    component: JobDetail,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/jobs',
    name: 'JobsList',
    component: JobsList,
    meta: { requiresAuth: true }
  },
  {
    path: '/hist',
    name: 'HistoryJobs',
    component: HistoryJobs,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  try {
    const res = await fetch('/api/check-login')
    const data = await res.json()
    const isLoggedIn = data.success
    
    if (to.meta.requiresAuth && !isLoggedIn) {
      next('/login')
    } else if (to.path === '/login' && isLoggedIn) {
      next('/')
    } else {
      next()
    }
  } catch (error) {
    console.error('检查登录状态失败:', error)
    if (to.meta.requiresAuth) {
      next('/login')
    } else {
      next()
    }
  }
})

export default router
