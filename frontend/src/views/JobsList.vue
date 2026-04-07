<template>
  <div class="jobs-list">
    <div class="header-section">
      <router-link to="/" class="back-btn">← 返回首页</router-link>
      <h1>📋 全部作业列表</h1>
      <div class="actions">
        <button @click="refreshJobs" class="btn-refresh" :disabled="loading">
          {{ loading ? '刷新中...' : '🔄 刷新' }}
        </button>
        <span class="total-count">{{ jobs.length }} 个作业</span>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-section">
      <div class="search-box">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="搜索作业 ID、作业名称或用户名..." 
          class="search-input"
        />
      </div>
      <div class="status-filter">
        <select v-model="statusFilter" class="status-select">
          <option value="">全部状态</option>
          <option value="RUN">运行中 (RUN)</option>
          <option value="PEND">等待中 (PEND)</option>
          <option value="DONE">已完成 (DONE)</option>
          <option value="EXIT">已退出 (EXIT)</option>
        </select>
      </div>
    </div>

    <!-- 作业表格 -->
    <div class="card jobs-card">
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
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in paginatedAndFilteredJobs" :key="job.job_id">
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
                <td>
                  <button @click="viewJob(job.job_id)" class="btn-view">详情</button>
                </td>
              </tr>
              <tr v-if="paginatedAndFilteredJobs.length === 0">
                <td colspan="7" class="empty-message">
                  {{ searchQuery || statusFilter ? '没有找到匹配的作业' : '暂无作业数据（未安装 LSF 或无作业）' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页控件 -->
        <div class="pagination" v-if="totalPages > 1">
          <button 
            @click="currentPage = 1" 
            :disabled="currentPage === 1"
            class="page-btn page-first"
          >
            首页
          </button>
          <button 
            @click="prevPage" 
            :disabled="currentPage === 1"
            class="page-btn"
          >
            上一页
          </button>
          
          <span class="page-info">
            第 {{ currentPage }} / {{ totalPages }} 页
          </span>
          
          <button 
            @click="nextPage" 
            :disabled="currentPage === totalPages"
            class="page-btn"
          >
            下一页
          </button>
          <button 
            @click="currentPage = totalPages" 
            :disabled="currentPage === totalPages"
            class="page-btn page-last"
          >
            末页
          </button>

          <div class="items-per-page">
            每页显示:
            <select v-model="itemsPerPage" class="items-select">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useLsfStore } from '../store'

const router = useRouter()
const store = useLsfStore()

const jobs = computed(() => store.jobs)
const loading = computed(() => store.loading)

// 分页相关
const currentPage = ref(1)
const itemsPerPage = ref(10)

// 搜索和筛选
const searchQuery = ref('')
const statusFilter = ref('')

// 计算分页后的数据
const filteredJobs = computed(() => {
  let filtered = jobs.value
  
  // 按状态筛选
  if (statusFilter.value) {
    filtered = filtered.filter(job => job.status === statusFilter.value)
  }
  
  // 按搜索框筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(job => 
      job.job_id.toLowerCase().includes(query) ||
      job.job_name.toLowerCase().includes(query) ||
      job.user.toLowerCase().includes(query)
    )
  }
  
  return filtered
})

const totalPages = computed(() => {
  return Math.ceil(filteredJobs.value.length / itemsPerPage.value)
})

const paginatedAndFilteredJobs = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredJobs.value.slice(start, end)
})

// 监听分页参数变化，重置到第一页
watch([itemsPerPage, statusFilter, searchQuery], () => {
  currentPage.value = 1
})

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const viewJob = (jobId) => {
  router.push('/job/' + jobId)
}

const refreshJobs = async () => {
  await store.fetchJobs()
}

onMounted(() => {
  store.fetchJobs()
})
</script>

<style scoped>
.jobs-list {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.back-btn {
  color: #667eea;
  text-decoration: none;
  font-weight: bold;
  font-size: 14px;
}
.back-btn:hover {
  text-decoration: underline;
}

.header-section h1 {
  color: #333;
  font-size: 24px;
  margin: 0;
  flex-grow: 1;
  text-align: center;
}

.actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.btn-refresh {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: transform 0.2s;
}
.btn-refresh:hover:not(:disabled) { transform: translateY(-2px); }
.btn-refresh:disabled { opacity: 0.6; cursor: not-allowed; }

.total-count {
  background: #f1f3f4;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: bold;
  color: #333;
}

.filter-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 15px 20px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 250px;
}

.search-input {
  width: 100%;
  padding: 10px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s;
}
.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.status-filter {
  min-width: 150px;
}

.status-select {
  width: 100%;
  padding: 10px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}
.status-select:focus {
  outline: none;
  border-color: #667eea;
}

.card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-body { padding: 20px; }

.table-container { overflow-x: auto; }

.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
.data-table th { background: #f8f9fa; color: #333; font-weight: bold; }
.data-table tr:hover { background: #f8f9fa; }

.job-link { color: #667eea; text-decoration: none; font-weight: bold; }
.job-link:hover { text-decoration: underline; }

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  display: inline-block;
}
.status-badge.run { background: #d4edda; color: #155724; }
.status-badge.pend { background: #fff3cd; color: #856404; }
.status-badge.done { background: #d1ecf1; color: #0c5460; }
.status-badge.exit { background: #f8d7da; color: #721c24; }
.status-badge.ok { background: #d4edda; color: #155724; }

.btn-view {
  background: #667eea;
  color: white;
  border: none;
  padding: 6px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-view:hover { background: #5568d3; }

.empty-message { text-align: center; color: #999; padding: 40px !important; }

/* 分页样式 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 20px 0;
  flex-wrap: wrap;
}

.page-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid #e0e0e0;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s;
}
.page-btn:hover:not(:disabled) {
  background: #667eea;
  color: white;
  border-color: #667eea;
}
.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-first, .page-last {
  min-width: 60px;
}

.page-info {
  font-weight: bold;
  color: #666;
  padding: 0 10px;
}

.items-per-page {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.items-select {
  padding: 6px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}
.items-select:focus {
  outline: none;
  border-color: #667eea;
}
</style>
