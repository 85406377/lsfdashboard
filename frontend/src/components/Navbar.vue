<template>
  <nav class="navbar">
    <div class="navbar-container">
      <router-link to="/" class="navbar-logo">
        <span class="logo-icon">🚀</span>
        <span class="logo-text">LSF Dashboard</span>
      </router-link>

      <!-- 导航菜单 -->
      <div class="navbar-menu">
        <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
          首页
        </router-link>
        <router-link to="/jobs" class="nav-link" :class="{ active: $route.path === '/jobs' }">
          Run 列表
        </router-link>
        <router-link to="/hist" class="nav-link" :class="{ active: $route.path === '/hist' }">
          历史作业
        </router-link>
      </div>

      <div class="navbar-right">
        <template v-if="currentUser">
          <div class="user-info">
            <span class="user-label">欢迎，</span>
            <span class="username">{{ currentUser }}</span>
            <span class="user-avatar">👤</span>
          </div>
          <button @click="handleLogout" class="logout-btn">退出</button>
        </template>
        <router-link to="/login" class="login-link" v-else>登录</router-link>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const currentUser = ref(null)

axios.defaults.withCredentials = true

onMounted(async () => {
  await checkAuthStatus()
})

const checkAuthStatus = async () => {
  try {
    const response = await axios.get('/api/auth-status')
    if (response.data.authenticated) {
      currentUser.value = response.data.username
    }
  } catch (err) {
    console.error('Auth status check failed:', err)
  }
}

const handleLogout = async () => {
  try {
    await axios.post('/api/logout')
    currentUser.value = null
    router.push('/login')
  } catch (err) {
    console.error('Logout failed:', err)
  }
}
</script>

<style scoped>
.navbar {
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.navbar-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 20px;
  height: 70px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #333;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 22px;
  font-weight: bold;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.navbar-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: center;
}

.nav-link {
  color: #666;
  text-decoration: none;
  padding: 10px 20px;
  border-radius: 20px;
  font-weight: 500;
  transition: all 0.3s;
}

.nav-link:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.nav-link.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 25px;
  color: white;
}

.user-label {
  font-size: 13px;
  opacity: 0.9;
}

.username {
  font-weight: bold;
  font-size: 15px;
}

.user-avatar {
  font-size: 18px;
}

.logout-btn {
  background: #ea4335;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: #d33426;
  transform: translateY(-2px);
}

.login-link {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 10px 24px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: bold;
  transition: all 0.3s;
}

.login-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>
