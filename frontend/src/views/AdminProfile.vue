<template>
  <div class="admin-profile">
    <div class="page-header">
      <h2>个人信息</h2>
      <p class="subtitle">管理您的账户设置和偏好</p>
    </div>
    
    <div class="profile-card">
      <div class="card-header">
        <h3>账户信息</h3>
      </div>
      <div class="card-body">
        <form @submit.prevent="updateProfile">
          <div class="form-group">
            <label for="username">用户名</label>
            <input 
              type="text" 
              id="username" 
              v-model="formData.username" 
              readonly
              class="form-control readonly"
            />
          </div>
          
          <div class="form-group">
            <label for="display_name">显示名称</label>
            <input 
              type="text" 
              id="display_name" 
              v-model="formData.display_name" 
              class="form-control"
              placeholder="请输入显示名称"
            />
          </div>
          
          <div class="form-group">
            <label for="email">邮箱</label>
            <input 
              type="email" 
              id="email" 
              v-model="formData.email" 
              class="form-control"
              placeholder="请输入邮箱地址"
            />
          </div>
          
          <div class="form-group">
            <label for="theme">主题</label>
            <select id="theme" v-model="formData.theme" class="form-control">
              <option value="light">浅色</option>
              <option value="dark">深色</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="language">语言</label>
            <select id="language" v-model="formData.language" class="form-control">
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </select>
          </div>
          
          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="loading">
              {{ loading ? '保存中...' : '保存更改' }}
            </button>
            <button type="button" class="btn btn-secondary" @click="resetForm">
              重置
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <div class="profile-card mt-4">
      <div class="card-header">
        <h3>系统信息</h3>
      </div>
      <div class="card-body">
        <div class="info-row">
          <span class="info-label">主机名:</span>
          <span class="info-value">{{ systemInfo.hostname || 'N/A' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">操作系统:</span>
          <span class="info-value">{{ systemInfo.os_version || 'N/A' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">网络状态:</span>
          <span class="info-value">
            <span :class="['status-badge', systemInfo.network_status === 'Connected' ? 'success' : 'danger']">
              {{ systemInfo.network_status || 'N/A' }}
            </span>
          </span>
        </div>
        <div class="info-row">
          <span class="info-label">当前时间:</span>
          <span class="info-value">{{ systemInfo.current_time || 'N/A' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useLsfStore } from '../store/index'

export default {
  name: 'AdminProfile',
  setup() {
    return { store: useLsfStore() }
  },
  data() {
    return {
      formData: {
        username: '',
        display_name: '',
        email: '',
        theme: 'light',
        language: 'zh-CN'
      },
      originalData: {},
      loading: false,
      systemInfo: {}
    }
  },
  async mounted() {
    await this.loadProfile()
    await this.loadSystemInfo()
  },
  methods: {
    async loadProfile() {
      const profile = await this.store.fetchUserProfile()
      if (profile) {
        this.formData = { ...profile }
        this.originalData = { ...profile }
      }
    },
    
    async loadSystemInfo() {
      await this.store.fetchSystemInfo()
      this.systemInfo = this.store.systemInfo
    },
    
    async updateProfile() {
      this.loading = true
      try {
        const result = await this.store.updateUserProfile(this.formData)
        if (result && result.success) {
          this.$message?.success('保存成功')
          this.originalData = { ...this.formData }
        } else {
          this.$message?.error('保存失败')
        }
      } catch (error) {
        this.$message?.error('保存失败：' + error.message)
      } finally {
        this.loading = false
      }
    },
    
    resetForm() {
      this.formData = { ...this.originalData }
    }
  }
}
</script>

<style scoped>
.admin-profile {
  max-width: 800px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #333;
}

.subtitle {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.profile-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e8e8e8;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.card-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  font-size: 14px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  transition: all 0.3s;
}

.form-control:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.form-control.readonly {
  background: #f5f5f5;
  cursor: not-allowed;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn {
  padding: 8px 20px;
  font-size: 14px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #1890ff;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #40a9ff;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
  border: 1px solid #d9d9d9;
}

.btn-secondary:hover {
  background: #e6e6e6;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: #666;
  font-weight: 500;
}

.info-value {
  color: #333;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
}

.status-badge.success {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.status-badge.danger {
  background: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

.mt-4 {
  margin-top: 24px;
}

@media (max-width: 576px) {
  .admin-profile {
    padding: 0 12px;
  }
  
  .card-body {
    padding: 16px;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
