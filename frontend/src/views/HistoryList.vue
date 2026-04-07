<template>
  <div class="history-list">
    <div class="page-header">
      <h2>历史作业</h2>
      <p class="subtitle">查看和管理 LSF 历史作业记录</p>
    </div>
    
    <div class="toolbar">
      <div class="filter-section">
        <label for="userFilter">按用户筛选:</label>
        <input 
          type="text" 
          id="userFilter"
          v-model="userFilter" 
          placeholder="输入用户名，留空显示全部"
          class="filter-input"
          @keyup.enter="loadJobs"
        />
        <button @click="loadJobs" class="btn btn-primary">筛选</button>
        <button @click="clearFilter" class="btn btn-secondary">清空</button>
      </div>
      <div class="action-section">
        <button @click="importData" class="btn btn-success" :disabled="importing">
          <span class="btn-icon">📥</span>
          {{ importing ? '导入中...' : '导入 bhist 数据' }}
        </button>
      </div>
    </div>
    
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>BID</th>
            <th>用户</th>
            <th>状态</th>
            <th>命令</th>
            <th>提交时间</th>
            <th>开始时间</th>
            <th>结束时间</th>
            <th>主机</th>
            <th>Slots</th>
            <th>退出码</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && historyJobs.length === 0">
            <td colspan="11" class="loading-text">加载中...</td>
          </tr>
          <tr v-else-if="!loading && historyJobs.length === 0">
            <td colspan="11" class="empty-text">暂无数据，请点击"导入 bhist 数据"按钮导入</td>
          </tr>
          <tr v-for="job in historyJobs" :key="job.bid">
            <td><router-link :to="`/hist/${job.bid}`" class="job-link">{{ job.bid }}</router-link></td>
            <td>{{ job.buser }}</td>
            <td>
              <span :class="['status-badge', getStatusClass(job.status)]">
                {{ job.status }}
              </span>
            </td>
            <td class="command-cell">{{ job.command }}</td>
            <td>{{ formatDateTime(job.submitted_at) }}</td>
            <td>{{ formatTime(job.start_time) }}</td>
            <td>{{ formatTime(job.end_time) }}</td>
            <td>{{ job.host || 'N/A' }}</td>
            <td>{{ job.slots || 0 }}</td>
            <td>{{ job.exit_code !== undefined ? job.exit_code : 'N/A' }}</td>
            <td>
              <router-link :to="`/hist/${job.bid}`" class="btn btn-sm btn-view">
                详情
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div class="pagination" v-if="!loading && totalPages > 1">
      <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1">上一页</button>
      <span class="page-info">
        第 {{ currentPage }} / {{ totalPages }} 页，共 {{ total }} 条记录
      </span>
      <button @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages">下一页</button>
    </div>
  </div>
</template>

<script>
import { useLsfStore } from '../store/index'

export default {
  name: 'HistoryList',
  setup() {
    return { store: useLsfStore() }
  },
  data() {
    return {
      currentPage: 1,
      pageSize: 20,
      userFilter: '',
      loading: false,
      importing: false,
      total: 0,
      historyJobs: []
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.pageSize)
    }
  },
  async mounted() {
    await this.loadJobs()
  },
  methods: {
    async loadJobs() {
      this.loading = true
      this.historyJobs = []
      try {
        const result = await this.store.fetchHistoryJobs(
          this.currentPage, 
          this.pageSize, 
          this.userFilter
        )
        if (result) {
          this.total = result.total
        }
      } catch (error) {
        console.error('加载作业列表失败:', error)
      } finally {
        this.loading = false
      }
    },
    
    clearFilter() {
      this.userFilter = ''
      this.loadJobs()
    },
    
    changePage(page) {
      if (page < 1 || page > this.totalPages) return
      this.currentPage = page
      this.loadJobs()
    },
    
    async importData() {
      this.importing = true
      try {
        const result = await this.store.importBhistData()
        if (result && result.success) {
          const count = result.imported || 0
          this.$message?.success(`导入成功！新增 ${count} 条记录`)
          // 重新加载列表
          await this.loadJobs()
        } else {
          this.$message?.error(result?.error || '导入失败')
        }
      } catch (error) {
        this.$message?.error('导入失败：' + error.message)
      } finally {
        this.importing = false
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
    
    formatDateTime(value) {
      if (!value) return '-'
      return value
    },
    
    formatTime(value) {
      if (!value || value === '-') return '-'
      return value
    }
  }
}
</script>

<style scoped>
.history-list {
  min-height: calc(100vh - 100px);
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

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-section label {
  font-weight: 500;
  color: #333;
}

.filter-input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  width: 200px;
}

.filter-input:focus {
  outline: none;
  border-color: #1890ff;
}

.action-section {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  font-size: 14px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background: #1890ff;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #40a9ff;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
  border: 1px solid #d9d9d9;
}

.btn-secondary:hover {
  background: #e6e6e6;
}

.btn-success {
  background: #52c41a;
  color: #fff;
}

.btn-success:hover:not(:disabled) {
  background: #73d13d;
}

.btn-success:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-view {
  color: #1890ff;
  text-decoration: none;
}

.btn-view:hover {
  color: #40a9ff;
}

.job-link {
  color: #667eea;
  text-decoration: none;
  font-weight: bold;
}

.job-link:hover {
  text-decoration: underline;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}

.table-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.data-table th {
  background: #fafafa;
  font-weight: 600;
  color: #333;
  position: sticky;
  top: 0;
}

.data-table tbody tr:hover {
  background: #fafafa;
}

.command-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loading-text,
.empty-text {
  text-align: center;
  padding: 40px !important;
  color: #999;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
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

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.pagination button:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-size: 14px;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-section,
  .action-section {
    justify-content: center;
  }
  
  .data-table {
    font-size: 12px;
  }
  
  .data-table th,
  .data-table td {
    padding: 8px;
  }
}
</style>
