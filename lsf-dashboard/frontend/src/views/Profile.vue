<template>
  <div class="profile-page">
    <div class="profile-container">
      <div class="profile-header">
        <h1>👤 个人信息管理</h1>
        <p>管理您的账户密码和企业Logo</p>
      </div>

      <div class="profile-sections">
        <!-- 修改密码 (仅admin可见) -->
        <div class="profile-card" v-if="isAdmin">
          <div class="card-title">
            <span class="icon">🔐</span>
            <h3>修改管理密码</h3>
          </div>

          <div class="form-group">
            <label for="oldPassword">原密码</label>
            <input
              type="password"
              id="oldPassword"
              v-model="oldPassword"
              placeholder="请输入原密码"
            />
          </div>

          <div class="form-group">
            <label for="newPassword">新密码</label>
            <input
              type="password"
              id="newPassword"
              v-model="newPassword"
              placeholder="请输入新密码"
            />
          </div>

          <div class="form-group">
            <label for="confirmPassword">确认新密码</label>
            <input
              type="password"
              id="confirmPassword"
              v-model="confirmPassword"
              placeholder="请再次输入新密码"
            />
          </div>

          <button @click="changePassword" class="btn-primary" :disabled="passwordLoading">
            {{ passwordLoading ? '修改中...' : '修改密码' }}
          </button>

          <div v-if="passwordMessage" :class="['message', passwordSuccess ? 'success' : 'error']">
            {{ passwordMessage }}
          </div>
        </div>

        <!-- 上传Logo (仅admin可见) -->
        <div class="profile-card" v-if="isAdmin">
          <div class="card-title">
            <span class="icon">🏢</span>
            <h3>企业Logo设置</h3>
          </div>

          <div class="logo-preview">
            <p class="preview-label">当前Logo</p>
            <div class="logo-box">
              <img v-if="hasLogo" :src="logoUrl" alt="企业Logo" class="current-logo">
              <div v-else class="no-logo">暂无Logo</div>
            </div>
          </div>

          <div class="form-group">
            <label for="logoFile">上传新Logo</label>
            <input
              type="file"
              id="logoFile"
              accept="image/*"
              @change="handleFileChange"
              ref="logoInput"
            />
            <p class="file-hint">支持格式: PNG, JPG, JPEG, GIF, SVG, WebP</p>
          </div>

          <button @click="uploadLogo" class="btn-primary" :disabled="logoLoading || !selectedFile">
            {{ logoLoading ? '上传中...' : '上传Logo' }}
          </button>

          <div v-if="logoMessage" :class="['message', logoSuccess ? 'success' : 'error']">
            {{ logoMessage }}
          </div>
        </div>

        <!-- 普通用户信息 (仅普通用户可见) -->
        <div class="profile-card" v-if="!isAdmin">
          <div class="card-title">
            <span class="icon">👤</span>
            <h3>用户信息</h3>
          </div>

          <div class="user-info-box">
            <p class="info-item">
              <span class="label">用户名:</span>
              <span class="value">{{ username }}</span>
            </p>
            <p class="info-item">
              <span class="label">角色:</span>
              <span class="value">普通用户</span>
            </p>
            <p class="info-item">
              <span class="label">权限:</span>
              <span class="value">仅查看自己的作业</span>
            </p>
          </div>
        </div>
      </div>

      <div class="profile-footer">
        <router-link to="/" class="back-link">← 返回首页</router-link>
        <button @click="logout" class="btn-logout">退出登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const isAdmin = ref(false)
const username = ref('')

// 密码修改相关
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordLoading = ref(false)
const passwordMessage = ref('')
const passwordSuccess = ref(false)

// Logo上传相关
const hasLogo = ref(false)
const logoUrl = ref('/logo.png')
const selectedFile = ref(null)
const logoLoading = ref(false)
const logoMessage = ref('')
const logoSuccess = ref(false)
const logoInput = ref(null)

const checkLogin = async () => {
  try {
    const res = await axios.get('/api/check-login')
    if (res.data.success) {
      isAdmin.value = res.data.role === 'admin'
      username.value = res.data.user || '用户'
    }
  } catch (err) {
    console.error('检查登录状态失败:', err)
  }
}

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

const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    logoMessage.value = ''
  }
}

const changePassword = async () => {
  if (!oldPassword.value || !newPassword.value || !confirmPassword.value) {
    passwordMessage.value = '请填写所有密码字段'
    passwordSuccess.value = false
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    passwordMessage.value = '两次输入的新密码不一致'
    passwordSuccess.value = false
    return
  }

  if (newPassword.value.length < 6) {
    passwordMessage.value = '新密码长度不能少于6位'
    passwordSuccess.value = false
    return
  }

  passwordLoading.value = true
  passwordMessage.value = ''

  try {
    const res = await axios.post('/api/change-password', {
      oldPassword: oldPassword.value,
      newPassword: newPassword.value
    })

    if (res.data.success) {
      passwordMessage.value = '密码修改成功！'
      passwordSuccess.value = true
      oldPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
    } else {
      passwordMessage.value = res.data.error || '密码修改失败'
      passwordSuccess.value = false
    }
  } catch (err) {
    passwordMessage.value = '网络错误，请检查服务器连接'
    passwordSuccess.value = false
    console.error('修改密码失败:', err)
  } finally {
    passwordLoading.value = false
  }
}

const uploadLogo = async () => {
  if (!selectedFile.value) {
    logoMessage.value = '请先选择要上传的文件'
    logoSuccess.value = false
    return
  }

  logoLoading.value = true
  logoMessage.value = ''

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const res = await axios.post('/api/upload-logo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (res.data.success) {
      logoMessage.value = 'Logo上传成功！'
      logoSuccess.value = true
      selectedFile.value = null
      logoInput.value.value = ''
      await checkLogo()
    } else {
      logoMessage.value = res.data.error || 'Logo上传失败'
      logoSuccess.value = false
    }
  } catch (err) {
    logoMessage.value = '网络错误，请检查服务器连接'
    logoSuccess.value = false
    console.error('上传Logo失败:', err)
  } finally {
    logoLoading.value = false
  }
}

const logout = async () => {
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
  checkLogo()
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.profile-container {
  max-width: 900px;
  margin: 0 auto;
}

.profile-header {
  text-align: center;
  color: white;
  margin-bottom: 30px;
}

.profile-header h1 {
  font-size: 28px;
  margin-bottom: 10px;
}

.profile-header p {
  font-size: 16px;
  opacity: 0.9;
}

.profile-sections {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .profile-sections {
    grid-template-columns: 1fr;
  }
}

.profile-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.card-title .icon {
  font-size: 24px;
}

.card-title h3 {
  font-size: 18px;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  color: #333;
  font-weight: bold;
  margin-bottom: 8px;
}

.form-group input[type="password"],
.form-group input[type="file"] {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  border-color: #667eea;
  outline: none;
}

.file-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.btn-primary {
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

.btn-primary:hover {
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message {
  margin-top: 15px;
  padding: 12px;
  border-radius: 6px;
  text-align: center;
  font-size: 14px;
}

.message.success {
  background: #d4edda;
  color: #155724;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
}

.logo-preview {
  margin-bottom: 25px;
}

.preview-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 10px;
}

.logo-box {
  width: 100%;
  height: 120px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
}

.current-logo {
  max-height: 100px;
  max-width: 200px;
  object-fit: contain;
}

.no-logo {
  color: #999;
  font-size: 14px;
}

.user-info-box {
  padding: 30px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 15px 0;
  border-bottom: 1px solid #eee;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  font-weight: bold;
  color: #333;
}

.info-item .value {
  color: #667eea;
  font-weight: bold;
}

.profile-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.back-link {
  color: #667eea;
  text-decoration: none;
  font-weight: bold;
}

.back-link:hover {
  text-decoration: underline;
}

.btn-logout {
  padding: 12px 24px;
  background: #ea4335;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-logout:hover {
  transform: translateY(-2px);
}
</style>
