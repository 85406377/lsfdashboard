<template>
  <nav class="nav-menu">
    <ul class="nav-list">
      <li>
        <router-link to="/" class="nav-link" :class="{ active: currentRoute === '/' }">
          <span class="nav-icon">🏠</span>
          <span class="nav-text">首页</span>
        </router-link>
      </li>
      <li>
        <router-link to="/jobs" class="nav-link" :class="{ active: currentRoute === '/jobs' }">
          <span class="nav-icon">🚀</span>
          <span class="nav-text">所有作业</span>
        </router-link>
      </li>
      <li>
        <router-link to="/hist" class="nav-link" :class="{ active: currentRoute === '/hist' }">
          <span class="nav-icon">📜</span>
          <span class="nav-text">历史作业</span>
        </router-link>
      </li>
      <li v-if="isAdmin">
        <router-link to="/profile" class="nav-link" :class="{ active: currentRoute === '/profile' }">
          <span class="nav-icon">⚙️</span>
          <span class="nav-text">个人信息</span>
        </router-link>
      </li>
    </ul>
    <div class="user-section">
      <span class="username">{{ username }}</span>
      <button @click="handleLogout" class="logout-btn">退出</button>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const currentRoute = computed(() => route.path)

const username = ref('')
const isAdmin = ref(false)
const loading = ref(true)

const checkLogin = async () => {
  try {
    const res = await axios.get('/api/check-login')
    if (res.data.success) {
      username.value = res.data.user || '用户'
      isAdmin.value = res.data.role === 'admin'
    }
  } catch (err) {
    console.error('检查登录状态失败:', err)
  } finally {
    loading.value = false
  }
}

const handleLogout = async () => {
  try {
    await axios.post('/api/logout')
    router.push('/login')
  } catch (err) {
    console.error('退出登录失败:', err)
    router.push('/login')
  }
}

onMounted(() => {
  checkLogin()
})
</script>

<style scoped>
.nav-menu {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.nav-list {
  list-style: none;
  display: flex;
  gap: 20px;
  padding: 0;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  color: #333;
  text-decoration: none;
  border-radius: 8px;
  font-weight: bold;
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

.nav-icon {
  font-size: 20px;
}

.nav-text {
  font-size: 16px;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 15px;
  padding-left: 20px;
  border-left: 1px solid #ddd;
  margin-left: 10px;
}

.username {
  font-weight: bold;
  color: #333;
}

.logout-btn {
  padding: 6px 16px;
  background: #ea4335;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.logout-btn:hover {
  background: #d32f2f;
}

.logout-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
