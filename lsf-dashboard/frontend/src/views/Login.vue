<template>
  <div class="login-page">
    <div class="login-container">
      <div class="logo-section">
        <div class="logo-placeholder">
          <img v-if="hasLogo" :src="logoUrl" alt="企业Logo" class="logo-img">
          <div v-else class="logo-text">LSF Dashboard</div>
        </div>
      </div>
      
      <div class="login-form">
        <h2>LSF Dashboard - 项目管理后台</h2>
        
        <div class="input-group">
          <label for="username">用户名</label>
          <input
            type="text"
            id="username"
            v-model="username"
            placeholder="请输入用户名"
            @keyup.enter="login"
          />
        </div>
        
        <div class="input-group">
          <label for="password">密码</label>
          <input
            type="password"
            id="password"
            v-model="password"
            placeholder="请输入密码"
            @keyup.enter="login"
          />
        </div>
        
        <button @click="login" class="login-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        
        <div v-if="error" class="error-message">{{ error }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const hasLogo = ref(false)
const logoUrl = ref('/logo.png')

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

const login = async () => {
  if (!username.value || !password.value) {
    error.value = '用户名和密码不能为空'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const res = await axios.post('/api/login', {
      username: username.value,
      password: password.value
    })
    
    if (res.data.success) {
      router.push('/')
    } else {
      error.value = res.data.error || '登录失败'
    }
  } catch (err) {
    error.value = '网络错误，请检查服务器连接'
    console.error('登录失败:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  checkLogo()
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 500px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.logo-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 30px;
  text-align: center;
}

.logo-placeholder {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-img {
  max-height: 120px;
  max-width: 200px;
  object-fit: contain;
}

.logo-text {
  font-size: 36px;
  font-weight: bold;
  color: white;
}

.login-form {
  padding: 40px;
}

.login-form h2 {
  text-align: center;
  color: #333;
  margin-bottom: 10px;
  font-size: 24px;
}

.login-subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 30px;
  font-size: 14px;
}

.input-group {
  margin-bottom: 20px;
}

.input-group label {
  display: block;
  color: #333;
  font-weight: bold;
  margin-bottom: 8px;
}

.input-group input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.input-group input:focus {
  border-color: #667eea;
  outline: none;
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s;
}

.login-btn:hover {
  transform: translateY(-2px);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  margin-top: 15px;
  padding: 12px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 6px;
  text-align: center;
  font-size: 14px;
}

.login-info {
  margin-top: 25px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  text-align: center;
  color: #666;
  font-size: 14px;
}

.login-info p {
  margin: 5px 0;
}
</style>
