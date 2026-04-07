<template>
  <div class="dashboard">
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
                <tr v-for="job in displayJobs" :key="job.job_id">
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
                <tr v-if="jobs.length === 0">
                  <td colspan="7" class="empty-message">
                    暂无作业数据（未安装 LSF 或无作业）
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- 更多按钮 -->
          <div class="more-section" v-if="jobs.length > 5">
            <button @click="goToJobsList" class="btn-more">查看更多作业 →</button>
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
            <h2>📊 系统负载 (lsload)</h2>
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

      <!-- 负载趋势图 -->
      <div class="card">
        <div class="card-header">
          <h2>📊 负载趋势</h2>
        </div>
        <div class="card-body">
          <div ref="trendChart" class="chart-container-large"></div>
        </div>
      </div>

      <!-- 管理后台入口 -->
      <div class="admin-entry">
        <router-link to="/admin" class="admin-btn">
          🚀 进入管理后台
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useLsfStore } from '../store'
import * as echarts from 'echarts'

const router = useRouter()
const store = useLsfStore()
const loadChart = ref(null)
const trendChart = ref(null)

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

const refreshAll = async () => {
  await store.refreshAll()
  await nextTick()
  initCharts()
}

// 只展示前 5 条作业用于首页
const displayJobs = computed(() => jobs.value.slice(0, 5))

const viewJob = (jobId) => {
  router.push('/job/' + jobId)
}

const goToJobsList = () => {
  router.push('/jobs')
}

const initLoadChart = () => {
  if (!loadChart.value || store.load.length === 0) return
  const chart = echarts.init(loadChart.value)
  
  // 获取主机列表
  const hosts = store.load.map(l => l.host)
  
  // 准备数据 - 转换为折线图数据
  // 为了展示折线图效果，需要按主机分组
  const utData = store.load.map(l => l.ut)
  const pgData = store.load.map(l => l.pg)
  const lsData = store.load.map(l => l.ls)

  chart.setOption({
    tooltip: { 
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: { data: ['UT (CPU负载)', 'PG (分页)', 'LS (负载状态)'], textStyle: { color: '#333' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: hosts,
      axisLabel: { interval: 0, rotate: 30 }
    },
    yAxis: { type: 'value', name: '数值' },
    series: [
      {
        name: 'UT (CPU负载)', 
        type: 'line', 
        data: utData,
        smooth: true,
        itemStyle: { color: '#667eea' },
        lineStyle: { width: 2 }
      },
      {
        name: 'PG (分页)', 
        type: 'line', 
        data: pgData,
        smooth: true,
        itemStyle: { color: '#fbbc04' },
        lineStyle: { width: 2 }
      },
      {
        name: 'LS (负载状态)', 
        type: 'line', 
        data: lsData,
        smooth: true,
        itemStyle: { color: '#34a853' },
        lineStyle: { width: 2 }
      }
    ]
  })
}

const initTrendChart = () => {
  if (!trendChart.value || store.loadTrend.length === 0) return
  const chart = echarts.init(trendChart.value)
  
  const hostData = {}
  store.loadTrend.forEach(item => {
    if (!hostData[item.host]) hostData[item.host] = []
    hostData[item.host].push(item)
  })

  const series = Object.keys(hostData).map(host => ({
    name: host, type: 'line', data: hostData[host].map(d => d.r1m), smooth: true
  }))

  const times = [...new Set(store.loadTrend.map(d => d.time))]

  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: Object.keys(hostData), textStyle: { color: '#333' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: times },
    yAxis: { type: 'value', name: '负载值' },
    series: series
  })
}

const initCharts = () => {
  initLoadChart()
  initTrendChart()
}

onMounted(async () => {
  await refreshAll()
  setInterval(async () => {
    await Promise.all([
      store.fetchJobs(), store.fetchHosts(), store.fetchUsers(),
      store.fetchQueues(), store.fetchLoad()
    ])
    initCharts()
  }, 5000)
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

.more-section {
  text-align: center;
  padding: 15px 0;
  border-top: 1px solid #eee;
  margin-top: 15px;
}

.btn-more {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 20px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s;
}

.btn-more:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.empty-message { text-align: center; color: #999; padding: 40px !important; }

.chart-container { height: 300px; width: 100%; }
.chart-container-large { height: 400px; width: 100%; }

/* 周期切换按钮 */
.period-tabs {
  display: flex;
  gap: 8px;
}

.tab-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.tab-btn.active {
  background: white;
  color: #667eea;
  font-weight: bold;
}

/* 管理后台入口按钮 */
.admin-entry {
  text-align: center;
  padding: 20px;
}

.admin-btn {
  display: inline-block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 32px;
  border-radius: 25px;
  text-decoration: none;
  font-weight: bold;
  font-size: 16px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  transition: all 0.3s;
}

.admin-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}
</style>
