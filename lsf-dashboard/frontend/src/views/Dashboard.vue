<template>
  <div class="dashboard">
    <NavMenu />
    
    <!-- 顶部信息栏 -->
    <div class="header">
      <div class="header-title">
        <h1>{{ username }} 的仿真作业监控 - {{ hostname }}</h1>
        <span class="run-value">busers RUN 值：{{ totalRunUsers }}</span>
      </div>
      <div class="header-info">
        <div class="info-item">
          <span class="label">日期时间:</span>
          <span class="value">{{ currentTime }}</span>
        </div>
        <div class="info-item">
          <span class="label">操作系统:</span>
          <span class="value">{{ osVersion }}</span>
        </div>
        <div class="info-item">
          <span class="label">网络状态:</span>
          <span :class="['value', 'status', networkStatus === 'Connected' ? 'connected' : 'disconnected']">
            {{ networkStatus }}
          </span>
        </div>
        <div class="user-info">
          <span class="label">用户:</span>
          <span class="value">{{ currentUser }}</span>
          <router-link to="/profile" class="profile-link">👤 个人中心</router-link>
        </div>
        <button @click="refreshAll" class="refresh-btn" :disabled="loading">
          {{ loading ? '刷新中...' : '🔄 刷新' }}
        </button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="content">
      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-number">{{ jobs.length }}</div>
          <div class="stat-label">总作业数</div>
        </div>
        <div class="stat-card stat-run">
          <div class="stat-number">{{ runningJobs }}</div>
          <div class="stat-label">运行中 (RUN)</div>
        </div>
        <div class="stat-card stat-pend">
          <div class="stat-number">{{ pendingJobs }}</div>
          <div class="stat-label">等待中 (PEND)</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ hosts.length }}</div>
          <div class="stat-label">主机数</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ queues.length }}</div>
          <div class="stat-label">队列数</div>
        </div>
      </div>

      <!-- 作业列表 -->
      <div class="card jobs-card">
        <div class="card-header">
          <h2>📋 作业列表 (bjobs)</h2>
          <span class="badge">{{ jobs.length }} 个作业</span>
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
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <!-- 限制显示8条记录 -->
                <tr v-for="(job, index) in jobs.slice(0, 8)" :key="index">
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
                
                <!-- 超过8条时显示更多作业链接 -->
                <tr v-if="jobs.length > 8">
                  <td colspan="7" class="job-more-link">
                    <router-link to="/jobs" class="btn-view btn-more">
                      更多作业
                      <span class="more-count">（共{{ jobs.length }}个作业）</span>
                    </router-link>
                  </td>
                </tr>
                
                <tr v-if="jobs.length === 0">
                  <td colspan="7" class="empty-message">
                    暂无作业数据（未安装 LSF 或无作业）
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 主机和负载 -->
      <div class="row">
        <div class="card">
          <div class="card-header">
            <h2>🖥️ 主机列表 (bhosts)</h2>
          </div>
          <div class="card-body">
            <table class="data-table">
              <thead>
                <tr>
                  <th>HOST_NAME</th>
                  <th>STATUS</th>
                  <th>R1M</th>
                  <th>R15M</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="host in hosts" :key="host.host_name">
                  <td>{{ host.host_name }}</td>
                  <td>
                    <span :class="['status-badge', host.status.toLowerCase()]">
                      {{ host.status }}
                    </span>
                  </td>
                  <td>{{ host.r1m }}</td>
                  <td>{{ host.r15m }}</td>
                </tr>
                <tr v-if="hosts.length === 0">
                  <td colspan="4" class="empty-message">暂无主机数据</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2>📊 系统负载 (lsload) - 实时</h2>
          </div>
          <div class="card-body">
            <div ref="loadChart" class="chart-container"></div>
          </div>
        </div>
      </div>

      <!-- 用户和队列 -->
      <div class="row">
        <div class="card">
          <div class="card-header">
            <h2>👥 用户列表 (busers)</h2>
          </div>
          <div class="card-body">
            <table class="data-table">
              <thead>
                <tr>
                  <th>USER</th>
                  <th>MAX</th>
                  <th>NJOBS</th>
                  <th>RUN</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.user">
                  <td>{{ user.user }}</td>
                  <td>{{ user.max }}</td>
                  <td>{{ user.njobs }}</td>
                  <td>{{ user.run }}</td>
                </tr>
                <tr v-if="users.length === 0">
                  <td colspan="4" class="empty-message">暂无用户数据</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2>📁 队列列表 (bqueues)</h2>
          </div>
          <div class="card-body">
            <table class="data-table">
              <thead>
                <tr>
                  <th>QUEUE_NAME</th>
                  <th>STATUS</th>
                  <th>MAX</th>
                  <th>NJOBS</th>
                  <th>RUN</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="queue in queues" :key="queue.queue_name">
                  <td>{{ queue.queue_name }}</td>
                  <td>
                    <span :class="['status-badge', queue.status.toLowerCase()]">
                      {{ queue.status }}
                    </span>
                  </td>
                  <td>{{ queue.max }}</td>
                  <td>{{ queue.njobs }}</td>
                  <td>{{ queue.run }}</td>
                </tr>
                <tr v-if="queues.length === 0">
                  <td colspan="5" class="empty-message">暂无队列数据</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 负载趋势图 - 从数据库获取 -->
      <div class="card">
        <div class="card-header">
          <h2>📈 负载趋势 (数据库)</h2>
        </div>
        <div class="card-body">
          <div ref="trendChart" class="chart-container-large"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useLsfStore } from '../store'
import * as echarts from 'echarts'
import axios from 'axios'
import NavMenu from '../components/NavMenu.vue'

const router = useRouter()
const store = useLsfStore()
const loadChart = ref(null)
const trendChart = ref(null)
const currentUser = ref('')

// 直接从 store 获取响应式数据
const jobs = computed(() => store.jobs)
const hosts = computed(() => store.hosts)
const users = computed(() => store.users)
const queues = computed(() => store.queues)
const loading = computed(() => store.loading)

const username = computed(() => store.systemInfo?.username || 'unknown')
const hostname = computed(() => store.systemInfo?.hostname || 'unknown')
const currentTime = computed(() => store.systemInfo?.current_time || '')
const osVersion = computed(() => store.systemInfo?.os_version || '')
const networkStatus = computed(() => store.systemInfo?.network_status || '')

const totalRunUsers = computed(() => {
  return store.users.reduce((sum, u) => sum + parseInt(u.run || 0), 0)
})

const runningJobs = computed(() => store.jobs.filter(j => j.status === 'RUN').length)
const pendingJobs = computed(() => store.jobs.filter(j => j.status === 'PEND').length)

const getCurrentUser = async () => {
  try {
    const res = await axios.get('/api/check-login')
    if (res.data.success) {
      currentUser.value = res.data.user
    }
  } catch (err) {
    console.error('获取用户信息失败:', err)
  }
}

const refreshAll = async () => {
  store.loading = true
  await Promise.all([
    store.fetchSystemInfo(),
    store.fetchJobs(),
    store.fetchHosts(),
    store.fetchUsers(),
    store.fetchQueues(),
    store.fetchLoad(),
    store.fetchLoadTrend()
  ])
  store.loading = false
  await nextTick()
  initCharts()
}

const viewJob = (jobId) => {
  router.push('/job/' + jobId)
}

const initLoadChart = () => {
  if (!loadChart.value || store.load.length === 0) return
  const chart = echarts.init(loadChart.value)
  const hosts = store.load.map(l => l.host)
  const r1mData = store.load.map(l => l.r1m)
  const r15mData = store.load.map(l => l.r15m)

  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['1分钟负载', '15分钟负载'], textStyle: { color: '#333' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: hosts, axisLabel: { interval: 0, rotate: 30 } },
    yAxis: { type: 'value', name: '负载值' },
    series: [
      {
        name: '1分钟负载', type: 'bar', data: r1mData,
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' }, { offset: 1, color: '#188df0' }
        ])}
      },
      {
        name: '15分钟负载', type: 'bar', data: r15mData,
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#a8e6cf' }, { offset: 1, color: '#34a853' }
        ])}
      }
    ]
  })
}

const initTrendChart = async () => {
  if (!trendChart.value) return
  
  try {
    // 从数据库获取历史数据
    const res = await axios.get('/api/load-db', { params: { limit: 60 } })
    if (res.data.success) {
      const history = res.data.history
      const chart = echarts.init(trendChart.value)
      
      // 将数据转换为图表格式
      const series = []
      const times = new Set()
      
      Object.keys(history).forEach(host => {
        const data = history[host].slice(0, 60).reverse()
        const timeData = data.map(d => d.timestamp ? d.timestamp.substring(11, 16) : '')
        const r1mData = data.map(d => d.r1m)
        
        timeData.forEach(t => times.add(t))
        
        series.push({
          name: host + ' R1M',
          type: 'line',
          data: r1mData,
          smooth: true
        })
        
        // 添加 UT 列
        const utData = data.map(d => d.utotal)
        series.push({
          name: host + ' UT',
          type: 'line',
          data: utData,
          smooth: true
        })
      })
      
      const sortedTimes = Array.from(times).sort()
      
      chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: series.map(s => s.name), textStyle: { color: '#333' }, type: 'scroll' },
        grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: sortedTimes },
        yAxis: { type: 'value', name: '值' },
        series: series
      })
    }
  } catch (err) {
    console.error('获取负载趋势失败:', err)
  }
}

const initCharts = () => {
  initLoadChart()
  initTrendChart()
}

onMounted(async () => {
  await getCurrentUser()
  await refreshAll()
  setInterval(async () => {
    await Promise.all([
      store.fetchJobs(), store.fetchHosts(), store.fetchUsers(),
      store.fetchQueues(), store.fetchLoad()
    ])
    initCharts()
  }, 30000)
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.header {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.header-title h1 {
  color: #333;
  font-size: 24px;
  margin-bottom: 10px;
}

.run-value {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: bold;
  display: inline-block;
}

.header-info {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
  margin-top: 15px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.label { color: #666; font-weight: bold; }
.value { color: #333; }
.status.connected { color: #34a853; font-weight: bold; }
.status.disconnected { color: #ea4335; font-weight: bold; }

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profile-link {
  color: #667eea;
  text-decoration: none;
  font-weight: bold;
  margin-left: 10px;
  padding: 6px 12px;
  border-radius: 4px;
  background: rgba(102, 126, 234, 0.1);
  transition: background 0.2s;
}

.profile-link:hover {
  background: rgba(102, 126, 234, 0.2);
}

.refresh-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: transform 0.2s;
}
.refresh-btn:hover { transform: translateY(-2px); }
.refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  color: #667eea;
}

.stat-label {
  color: #666;
  margin-top: 5px;
  font-size: 14px;
}

.stat-run .stat-number { color: #34a853; }
.stat-pend .stat-number { color: #fbbc04; }

.content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 1200px) {
  .row { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: repeat(3, 1fr); }
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

.card-header h2 { font-size: 18px; margin: 0; }
.badge { background: rgba(255, 255, 255, 0.2); padding: 4px 12px; border-radius: 12px; font-size: 14px; }
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

.job-more-link {
  background: #f8f9fa;
  padding: 15px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top: 1px solid #e5e7eb;
}

.btn-more {
  background: #ea4335;
  padding: 10px 20px;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.more-count {
  font-size: 12px;
  opacity: 0.9;
}

.empty-message { text-align: center; color: #999; padding: 40px !important; }

.chart-container { height: 300px; width: 100%; }
.chart-container-large { height: 400px; width: 100%; }
</style>