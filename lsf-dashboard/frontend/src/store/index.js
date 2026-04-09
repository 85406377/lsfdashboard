import { defineStore } from 'pinia'
import axios from 'axios'

export const useLsfStore = defineStore('lsf', {
  state: () => ({
    systemInfo: {},
    jobs: [],
    hosts: [],
    users: [],
    queues: [],
    load: [],
    loadTrend: [],
    loading: false,
    error: null
  }),

  actions: {
    async fetchSystemInfo() {
      try {
        const res = await axios.get('/api/system-info')
        this.systemInfo = res.data
      } catch (error) {
        console.error('获取系统信息失败:', error)
      }
    },

    async fetchJobs() {
      try {
        const res = await axios.get('/api/jobs')
        if (res.data.success) {
          this.jobs = res.data.data || []
        }
      } catch (error) {
        console.error('获取作业列表失败:', error)
      }
    },

    async fetchHosts() {
      try {
        const res = await axios.get('/api/hosts')
        if (res.data.success) {
          this.hosts = res.data.data || []
        }
      } catch (error) {
        console.error('获取主机列表失败:', error)
      }
    },

    async fetchUsers() {
      try {
        const res = await axios.get('/api/users')
        if (res.data.success) {
          this.users = res.data.data || []
        }
      } catch (error) {
        console.error('获取用户列表失败:', error)
      }
    },

    async fetchQueues() {
      try {
        const res = await axios.get('/api/queues')
        if (res.data.success) {
          this.queues = res.data.data || []
        }
      } catch (error) {
        console.error('获取队列列表失败:', error)
      }
    },

    async fetchLoad() {
      try {
        const res = await axios.get('/api/load')
        if (res.data.success) {
          this.load = res.data.data || []
        }
      } catch (error) {
        console.error('获取负载信息失败:', error)
      }
    },

    async fetchLoadTrend() {
      try {
        const res = await axios.get('/api/load-trend')
        if (res.data.success) {
          this.loadTrend = res.data.data || []
        }
      } catch (error) {
        console.error('获取负载趋势失败:', error)
      }
    },

    async fetchJobDetail(jobId) {
      try {
        const res = await axios.get('/api/job/' + jobId)
        if (res.data.success) {
          return res.data.data
        }
        return null
      } catch (error) {
        console.error('获取作业详情失败:', error)
        return null
      }
    },

    async killJob(jobId) {
      try {
        const res = await axios.post('/api/kill/' + jobId)
        return res.data
      } catch (error) {
        console.error('终止作业失败:', error)
        return { success: false, error: error.message }
      }
    }
  }
})
