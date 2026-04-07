<template>
  <div id="app">
    <Navbar v-if="!showingLogin" />
    <router-view />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Navbar from './components/Navbar.vue'
import axios from 'axios'

const showingLogin = ref(false)

axios.defaults.withCredentials = true

onMounted(async () => {
  // 检查是否已经在登录页面
  const currentPath = window.location.pathname
  if (currentPath === '/login') {
    showingLogin.value = true
  }
  
  // 检查认证状态
  try {
    const response = await axios.get('/api/auth-status')
    if (!response.data.authenticated && currentPath !== '/login') {
      showingLogin.value = true
    }
  } catch (err) {
    console.error('Auth check failed:', err)
  }
})

// 监听路由变化
if (typeof window !== 'undefined') {
  window.addEventListener('popstate', async () => {
    const path = window.location.pathname
    showingLogin.value = path === '/login'
    
    // 如果没有认证，且不在 login 页面，重定向到 login
    try {
      const response = await axios.get('/api/auth-status')
      if (!response.data.authenticated && path !== '/login') {
        showingLogin.value = true
      }
    } catch (err) {
      if (path !== '/login') {
        showingLogin.value = true
      }
    }
  })
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Arial', 'Microsoft YaHei', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  color: #333;
}

#app {
  width: 100%;
  min-height: 100vh;
}
</style>
