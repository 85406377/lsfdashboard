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
          <span class="nav-text">Run列表</span>
        </router-link>
      </li>
      <li>
        <router-link to="/hist" class="nav-link" :class="{ active: currentRoute === '/hist' }">
          <span class="nav-icon">📜</span>
          <span class="nav-text">历史作业</span>
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentRoute = computed(() => route.path)
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
</style>
