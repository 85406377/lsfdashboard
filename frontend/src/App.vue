<template>
  <div id="app">
    <!-- Logo 显示在登录页面外所有页面 -->
    <div v-if="showLogo" class="global-logo">
      <router-link to="/" class="logo-link">
        <img v-if="hasLogo" :src="logoUrl" alt="企业Logo" class="logo-img">
        <span v-else class="logo-text">LSF Dashboard</span>
      </router-link>
    </div>
    <router-view />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const hasLogo = ref(false)
const logoUrl = ref('/logo.png')

// 不在登录页面显示Logo
const showLogo = computed(() => {
  return route.path !== '/login'
})

const checkLogo = async () => {
  try {
    const res = await axios.get('/api/get-logo')
    if (res.data.success) {
      hasLogo.value = res.data.hasLogo
      logoUrl.value = '/logo.png'
    }
  } catch (err) {
    console.error('检查Logo失败:', err)
  }
}

onMounted(() => {
  checkLogo()
})
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

.global-logo {
  position: fixed;
  top: 15px;
  left: 20px;
  z-index: 1000;
}

.logo-link {
  display: flex;
  align-items: center;
  text-decoration: none;
}

.logo-img {
  max-height: 50px;
  max-width: 150px;
  object-fit: contain;
  background: rgba(255, 255, 255, 0.95);
  padding: 8px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}
</style>
