<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>🚀 LSF Dashboard</h1>
        <p>请登录以访问作业监控系统</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input 
            type="text" 
            id="username" 
            v-model="username" 
            placeholder="请输入 NIS 账号"
            autocomplete="username"
            required
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input 
            type="password" 
            id="password" 
            v-model="password" 
            placeholder="请输入密码"
            autocomplete="current-password"
            required
          />
        </div>

        <div class="form-group checkbox-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="rememberMe" />
            <span>记住我 (7 天免登)</span>
          </label>
        </div>

        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div class="login-footer">
          <p>使用您的 NIS 账号登录</p>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const loading = ref(false)
const error = ref('')

axios.defaults.withCredentials = true

// 获取重定向地址
const redirectPath = ref(route.query.next || '/')

onMounted(() => {
  // 检查是否已登录
  checkAuthStatus()
})

const checkAuthStatus = async () => {
  try {
    const response = await axios.get('/api/auth-status')
    if (response.data.authenticated) {
      // 已登录，重定向到首页或原页面
      router.push(redirectPath.value)
    }
  } catch (err) {
    console.error('Auth check failed:', err)
  }
}

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await axios.post('/api/login', {
      username: username.value,
      password: password.value,
      remember_me: rememberMe.value
    })

    if (response.data.success) {
      // 登录成功，保存登录状态到 localStorage
      localStorage.setItem('isLoggedIn', 'true')
      localStorage.setItem('currentUser', response.data.username)
      
      // 跳转回原页面或首页
      router.push(redirectPath.value)
    } else {
      error.value = response.data.error || '登录失败'
    }
  } catch (err) {
    console.error('Login error:', err)
    const errorMessage = err.response?.data?.error || '登录失败，请检查网络连接'
    error.value = errorMessage
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 40px;
  width: 100%;
  max-width: 420px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  color: #333;
  font-size: 32px;
  margin-bottom: 10px;
}

.login-header p {
  color: #666;
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  color: #333;
  font-weight: bold;
  font-size: 14px;
}

.form-group input[type="text"],
.form-group input[type="password"] {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.checkbox-group {
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: normal;
  color: #666;
  font-size: 14px;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.login-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 14px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  border-left: 4px solid #c33;
}

.login-footer {
  text-align: center;
  margin-top: 10px;
}

.login-footer p {
  color: #999;
  font-size: 12px;
}
</style>
