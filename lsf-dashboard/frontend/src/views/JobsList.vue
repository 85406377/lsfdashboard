<template>
  <div class="jobs-list-page">
    <NavMenu />
    
    <div class="card">
      <div class="card-header">
        <h2>🚀 所有状态作业列表</h2>
        <span class="badge">{{ total }} 个作业</span>
      </div>
      <div class="card-body">
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>JOBID</th>
                <th>USER</th>
                <th>STATUS</th>
                <th>QUEUE</th>
                <th>HOST</th>
                <th>JOB_NAME</th>
                <th>SLOTS</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in jobs" :key="job.job_id">
                <td>
                  <router-link :to="'/job/' + job.job_id" class="job-link">
                    {{ job.job_id }}
                  </router-link>
                </td>
                <td>{{ job.user }}</td>
                <td>
                  <span :class="['status-badge', job.status.toLowerCase()]">
                    {{ job.status }}
                  </span>
                </td>
                <td>{{ job.queue }}</td>
                <td>{{ job.host }}</td>
                <td>{{ job.job_name }}</td>
                <td>{{ job.slots }}</td>
                <td>
                  <button @click="viewJob(job.job_id)" class="btn-view">详情</button>
                </td>
              </tr>
              <tr v-if="jobs.length === 0">
                <td colspan="8" class="empty-message">
                  暂无作业
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- 分页 -->
        <div class="pagination" v-if="totalPages > 1">
          <button 
            @click="goPage(page - 1)" 
            :disabled="page <= 1"
            class="page-btn"
          >
            上一页
          </button>
          <span class="page-info">第 {{ page }} / {{ totalPages }} 页</span>
          <button 
            @click="goPage(page + 1)" 
            :disabled="page >= totalPages"
            class="page-btn"
          >
            下一页
          </button>
          <span class="total-info">共 {{ total }} 条</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import NavMenu from '../components/NavMenu.vue'

const router = useRouter()
const jobs = ref([])
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const loading = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const fetchJobs = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/jobs/all', {
      params: { page: page.value, pageSize: pageSize.value }
    })
    if (res.data.success) {
      jobs.value = res.data.data
      total.value = res.data.total
    }
  } catch (error) {
    console.error('获取所有作业列表失败:', error)
  } finally {
    loading.value = false
  }
}

const goPage = (newPage) => {
  if (newPage >= 1 && newPage <= totalPages.value) {
    page.value = newPage
    fetchJobs()
  }
}

const viewJob = (jobId) => {
  router.push('/job/' + jobId)
}

onMounted(() => {
  fetchJobs()
})
</script>

<style scoped>
.jobs-list-page {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  font-size: 18px;
  margin: 0;
}

.badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
}

.card-body {
  padding: 20px;
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background: #f8f9fa;
  color: #333;
  font-weight: bold;
}

.data-table tr:hover {
  background: #f8f9fa;
}

.job-link {
  color: #667eea;
  text-decoration: none;
  font-weight: bold;
}

.job-link:hover {
  text-decoration: underline;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  display: inline-block;
}

.status-badge.run {
  background: #d4edda;
  color: #155724;
}

.status-badge.pend {
  background: #fff3cd;
  color: #856404;
}

.status-badge.done {
  background: #d1ecf1;
  color: #0c5460;
}

.status-badge.exit {
  background: #f8d7da;
  color: #721c24;
}

.btn-view {
  background: #667eea;
  color: white;
  border: none;
  padding: 6px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-view:hover {
  background: #5568d3;
}

.empty-message {
  text-align: center;
  color: #999;
  padding: 40px !important;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.page-btn {
  padding: 8px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}

.page-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.page-info {
  font-weight: bold;
  color: #333;
}

.total-info {
  color: #666;
}
</style>
