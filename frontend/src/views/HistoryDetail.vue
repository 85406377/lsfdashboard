<template>
  <div class="history-detail">
    <div class="page-header">
      <div class="header-left">
        <router-link to="/hist" class="back-link">← 返回列表</router-link>
        <h2>作业详情 #{{ bid }}</h2>
      </div>
    </div>
    
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div v-else-if="!jobData" class="error-container">
      <p>未找到该作业信息</p>
      <router-link to="/hist" class="btn btn-primary">返回列表</router-link>
    </div>
    
    <div v-else class="detail-content">
      <div class="detail-card">
        <div class="card-header">
          <h3>基本信息</h3>
        </div>
        <div class="card-body">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">BID (作业 ID)</span>
              <span class="info-value">{{ jobData.bid }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">提交用户</span>
              <span class="info-value">{{ jobData.buser }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">作业状态</span>
              <span class="info-value">
                <span :class="['status-badge', getStatusClass(jobData.status)]">
                  {{ jobData.status }}
                </span>
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">退出码</span>
              <span class="info-value" :class="getExitCodeClass(jobData.exit_code)">
                {{ jobData.exit_code !== undefined ? jobData.exit_code : 'N/A' }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="detail-card">
        <div class="card-header">
          <h3>时间信息</h3>
        </div>
        <div class="card-body">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">提交时间</span>
              <span class="info-value">{{ jobData.submitted_at || 'N/A' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">开始时间</span>
              <span class="info-value">{{ jobData.start_time || 'N/A' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">结束时间</span>
              <span class="info-value">{{ jobData.end_time || 'N/A' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">创建记录时间</span>
              <span class="info-value">{{ jobData.created_at || 'N/A' }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="detail-card">
        <div class="card-header">
          <h3>资源信息</h3>
        </div>
        <div class="card-body">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">运行主机</span>
              <span class="info-value">{{ jobData.host || 'N/A' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">占用 Slots</span>
              <span class="info-value">{{ jobData.slots || 0 }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">作业数量</span>
              <span class="info-value">{{ jobData.count || 1 }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="detail-card">
        <div class="card-header">
          <h3>命令信息</h3>
        </div>
        <div class="card-body">
          <div class="command-box">
            <code>{{ jobData.command || 'N/A' }}</code>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useLsfStore } from '../store/index'

export default {
  name: 'HistoryDetail',
  setup() {
    return { store: useLsfStore() }
  },
  data() {
    return {
      jobData: null,
      loading: true
    }
  },
  computed: {
    bid() {
      return this.$route.params.bid
    }
  },
  watch: {
    '$route.params.bid': {
      immediate: true,
      handler(newBid) {
        if (newBid) {
          this.loadJobDetail(newBid)
        }
      }
    }
  },
  methods: {
    async loadJobDetail(bid) {
      this.loading = true
      this.jobData = null
      try {
        const data = await this.store.fetchJobDetail(bid)
        this.jobData = data
      } catch (error) {
        console.error('加载作业详情失败:', error)
      } finally {
        this.loading = false
      }
    },
    
    getStatusClass(status) {
      const statusMap = {
        'E': 'running',
        'R': 'running',
        'Z': 'running',
        'PD': 'warning',
        'SS': 'warning',
        'CD': 'info',
        'FW': 'info',
        'DY': 'info'
      }
      return statusMap[status] || 'default'
    },
    
    getExitCodeClass(exitCode) {
      if (exitCode === undefined || exitCode === null) return ''
      if (exitCode === 0) return 'success'
      return 'error'
    }
  }
}
</script>

<style scoped>
.history-detail {
  min-height: calc(100vh - 100px);
}

.page-header {
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-link {
  color: #1890ff;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.3s;
}

.back-link:hover {
  color: #40a9ff;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.loading-container,
.error-container {
  text-align: center;
  padding: 60px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-container p {
  color: #999;
  margin-bottom: 20px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-card {
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

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  color: #999;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  color: #333;
  font-size: 15px;
  font-weight: 500;
}

.info-value.success {
  color: #52c41a;
}

.info-value.error {
  color: #ff4d4f;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  display: inline-block;
}

.status-badge.running {
  background: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.status-badge.warning {
  background: #fffbe6;
  color: #faad14;
  border: 1px solid #ffe58f;
}

.status-badge.info {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.status-badge.default {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #d9d9d9;
}

.command-box {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
}

.command-box code {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  color: #333;
  word-break: break-all;
  line-height: 1.6;
}

.btn {
  padding: 8px 20px;
  font-size: 14px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
  transition: all 0.3s;
}

.btn-primary {
  background: #1890ff;
  color: #fff;
}

.btn-primary:hover {
  background: #40a9ff;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .card-body {
    padding: 16px;
  }
}
</style>
