<template>
  <div class="job-detail">
    <div class="back-btn-container">
      <router-link to="/" class="back-btn">← 返回列表</router-link>
    </div>

    <div class="card">
      <div class="card-header">
        <h2>📝 作业详情 - JOB ID: {{ jobId }}</h2>
        <div class="actions">
          <button @click="killJob" class="btn-kill" :disabled="killing">
            {{ killing ? '终止中...' : '💀 终止作业 (bkill)' }}
          </button>
        </div>
      </div>
      <div class="card-body">
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>加载作业详情中...</p>
        </div>
        <div v-else-if="error" class="error">
          <p>{{ error }}</p>
        </div>
        <div v-else-if="jobDetail" class="detail-content">
          <pre>{{ jobDetail }}</pre>
        </div>
        <div v-else class="empty">
          <p>未找到作业详情</p>
        </div>
      </div>
    </div>

    <!-- 确认对话框 -->
    <div v-if="showConfirm" class="modal-overlay" @click="showConfirm = false">
      <div class="modal" @click.stop>
        <h3>确认终止作业</h3>
        <p>确定要终止作业 {{ jobId }} 吗？此操作不可恢复。</p>
        <div class="modal-actions">
          <button @click="confirmKill" class="btn-confirm">确认终止</button>
          <button @click="showConfirm = false" class="btn-cancel">取消</button>
        </div>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="message" :class="['message', messageType]">
      {{ message }}
      <button @click="message = null" class="close-msg">×</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLsfStore } from '../store'

const route = useRoute()
const router = useRouter()
const store = useLsfStore()

const jobId = ref(route.params.jobId)
const jobDetail = ref(null)
const loading = ref(true)
const error = ref(null)
const killing = ref(false)
const showConfirm = ref(false)
const message = ref(null)
const messageType = ref('success')

const loadJobDetail = async () => {
  loading.value = true
  error.value = null
  jobDetail.value = null

  const detail = await store.fetchJobDetail(jobId.value)
  if (detail) {
    jobDetail.value = detail
  } else {
    error.value = '无法获取作业详情，请检查作业 ID 是否正确'
  }
  loading.value = false
}

const killJob = () => {
  showConfirm.value = true
}

const confirmKill = async () => {
  killing.value = true
  showConfirm.value = false

  const result = await store.killJob(jobId.value)
  if (result.success) {
    message.value = '作业 ' + jobId.value + ' 已成功终止'
    messageType.value = 'success'
    setTimeout(() => {
      router.push('/')
    }, 2000)
  } else {
    message.value = '终止作业失败：' + (result.error || '未知错误')
    messageType.value = 'error'
  }
  killing.value = false
}

onMounted(() => {
  loadJobDetail()
})
</script>

<style scoped>
.job-detail { padding: 20px; max-width: 1200px; margin: 0 auto; }
.back-btn-container { margin-bottom: 20px; }
.back-btn {
  background: rgba(255, 255, 255, 0.9);
  color: #667eea;
  text-decoration: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: bold;
  display: inline-block;
  transition: transform 0.2s;
}
.back-btn:hover { transform: translateX(-4px); }

.card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}
.card-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header h2 { font-size: 20px; margin: 0; }

.btn-kill {
  background: #ea4335;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  font-size: 14px;
}
.btn-kill:hover:not(:disabled) { background: #d33426; }
.btn-kill:disabled { opacity: 0.6; cursor: not-allowed; }

.card-body { padding: 20px; min-height: 400px; }
.loading, .error, .empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #666;
}
.spinner {
  width: 40px; height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.error { color: #ea4335; font-weight: bold; }

.detail-content {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  overflow-x: auto;
}
.detail-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
}

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: white;
  border-radius: 12px;
  padding: 30px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}
.modal h3 { color: #333; margin-bottom: 15px; }
.modal p { color: #666; margin-bottom: 25px; line-height: 1.6; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
.btn-confirm {
  background: #ea4335;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}
.btn-cancel {
  background: #f1f3f4;
  color: #333;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}

.message {
  position: fixed;
  top: 20px; right: 20px;
  padding: 15px 25px;
  border-radius: 8px;
  color: white;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  z-index: 1001;
  animation: slideIn 0.3s ease;
}
@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
.message.success { background: #34a853; }
.message.error { background: #ea4335; }
.close-msg {
  background: transparent;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 24px; height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
