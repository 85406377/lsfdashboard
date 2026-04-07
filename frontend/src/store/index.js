import { defineStore } from 'pinia'
import axios from 'axios'

export const useLsfStore = defineStore('lsf', {
  state: () => ({
    // 认证状态
    isLoggedIn: false,
    currentUser: null,
    isAdmin: false,
    
    systemInfo: {},
    jobs: [],
    hosts: [],
    users: [],
    queues: [],
    load: [],
    loadTrend: [],
    loading: false,
    error: null,
    // 历史作业数据
    historyJobs: [],
    totalHistory: 0,
    currentPage: 1,
    pageSize: 20,
    // 用户配置
    userProfile: {},
    // 管理员配置
    adminConfig: {
      admin_users: ['admin'],
      company_logo: '',
      company_name: 'LSF Dashboard'
    },
    // Slots 趋势
    slotsTrend: [],
    slotsPeriod: 'day'
  }),

  actions: {
    /**
     * 检查认证状态
     */
    async checkAuthStatus() {
      try {
        const res = await axios.get('/api/auth-status')
        if (res.data.authenticated) {
          this.isLoggedIn = true
          this.currentUser = res.data.username
          this.isAdmin = res.data.is_admin || false
          localStorage.setItem('isLoggedIn', 'true')
          localStorage.setItem('currentUser', res.data.username)
          localStorage.setItem('isAdmin', res.data.is_admin ? 'true' : 'false')
        } else {
          this.isLoggedIn = false
          this.currentUser = null
          this.isAdmin = false
          localStorage.removeItem('isLoggedIn')
          localStorage.removeItem('currentUser')
          localStorage.removeItem('isAdmin')
        }
        return res.data
      } catch (error) {
        console.error('检查认证状态失败:', error)
        return { authenticated: false, username: null, is_admin: false }
      }
    },

    /**
     * 更新当前用户信息
     * @param {string} username
     * @param {boolean} is_admin
     */
    updateCurrentUser(username, is_admin = false) {
      this.isLoggedIn = !!username
      this.currentUser = username || null
      this.isAdmin = is_admin
      if (username) {
        localStorage.setItem('isLoggedIn', 'true')
        localStorage.setItem('currentUser', username)
        localStorage.setItem('isAdmin', is_admin ? 'true' : 'false')
      } else {
        localStorage.removeItem('isLoggedIn')
        localStorage.removeItem('currentUser')
        localStorage.removeItem('isAdmin')
      }
    },

    /**
     * 退出登录
     */
    async logout() {
      try {
        await axios.post('/api/logout')
        this.isLoggedIn = false
        this.currentUser = null
        this.isAdmin = false
        localStorage.removeItem('isLoggedIn')
        localStorage.removeItem('currentUser')
        localStorage.removeItem('isAdmin')
      } catch (error) {
        console.error('退出登录失败:', error)
      }
    },

    async fetchSystemInfo() {
      try {
        const res = await axios.get('/api/system-info')
        this.systemInfo = res.data
        // 更新管理员配置
        if (res.data.company_logo) {
          this.adminConfig.company_logo = res.data.company_logo
        }
        if (res.data.company_name) {
          this.adminConfig.company_name = res.data.company_name
        }
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
    },

    // ==================== 历史作业相关 ====================

    /**
     * 分页获取历史作业
     * @param {number} page - 页码
     * @param {number} pageSize - 每页数量
     * @param {string} userFilter - 用户过滤
     */
    async fetchHistoryJobs(page = 1, pageSize = 20, userFilter = '') {
      try {
        this.loading = true
        let url = `/api/history/jobs?page=${page}&page_size=${pageSize}`
        if (userFilter) {
          url += `&user=${encodeURIComponent(userFilter)}`
        }
        const res = await axios.get(url)
        if (res.data.success) {
          this.historyJobs = res.data.data.jobs || []
          this.totalHistory = res.data.data.total || 0
          this.currentPage = res.data.data.page || 1
          this.pageSize = res.data.data.page_size || 20
        }
      } catch (error) {
        console.error('获取历史作业失败:', error)
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取单个历史作业详情
     * @param {number} bid - 作业 ID
     */
    async fetchJobHistoryDetail(bid) {
      try {
        const res = await axios.get('/api/history/job/' + bid)
        if (res.data.success) {
          return res.data.data
        }
        return null
      } catch (error) {
        console.error('获取历史作业详情失败:', error)
        return null
      }
    },

    /**
     * 导入 bhist 数据
     */
    async importBhistData() {
      try {
        this.loading = true
        const res = await axios.post('/api/history/import')
        if (res.data.success) {
          alert(`导入完成！\n新增：${res.data.imported} 条\n更新：${res.data.updated} 条\n总计处理：${res.data.total_processed} 条`)
          // 重新加载列表
          await this.fetchHistoryJobs(this.currentPage, this.pageSize)
          return res.data
        } else {
          alert(`导入失败：${res.data.error}`)
        }
      } catch (error) {
        console.error('导入 bhist 数据失败:', error)
        alert('导入失败：' + error.message)
        return { success: false, error: error.message }
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取 Slots 使用趋势
     * @param {string} period - 周期：day, week, month
     */
    async fetchSlotsTrend(period = 'day') {
      try {
        this.slotsPeriod = period
        const res = await axios.get(`/api/history/stats/slots?period=${period}`)
        if (res.data.success) {
          this.slotsTrend = res.data.data || []
        }
      } catch (error) {
        console.error('获取 Slots 趋势失败:', error)
      }
    },

    // ==================== 用户配置相关 ====================

    /**
     * 获取用户配置
     */
    async fetchUserProfile() {
      try {
        const res = await axios.get('/api/user/profile')
        if (res.data.success) {
          this.userProfile = res.data.data || {}
        }
      } catch (error) {
        console.error('获取用户配置失败:', error)
      }
    },

    /**
     * 更新用户配置
     * @param {object} data - 要更新的字段
     */
    async updateUserProfile(data) {
      try {
        const res = await axios.put('/api/user/profile', data)
        if (res.data.success) {
          this.userProfile = res.data.data
          return res.data
        } else {
          alert(`更新失败：${res.data.error}`)
          return res.data
        }
      } catch (error) {
        console.error('更新用户配置失败:', error)
        alert('更新失败：' + error.message)
        return { success: false, error: error.message }
      }
    },

    // ==================== 管理员配置相关 ====================

    /**
     * 获取管理员配置
     */
    async fetchAdminConfig() {
      try {
        const res = await axios.get('/api/admin/config')
        if (res.data.success) {
          this.adminConfig = res.data.data || {
            admin_users: ['admin'],
            company_logo: '',
            company_name: 'LSF Dashboard'
          }
        }
      } catch (error) {
        console.error('获取管理员配置失败:', error)
      }
    },

    /**
     * 更新管理员配置
     * @param {object} data - 要更新的字段
     */
    async updateAdminConfig(data) {
      try {
        const res = await axios.put('/api/admin/config', data)
        if (res.data.success) {
          this.adminConfig = res.data.data
          // 更新系统信息中的logo和公司名称
          this.systemInfo.company_logo = res.data.data.company_logo
          this.systemInfo.company_name = res.data.data.company_name
          return res.data
        } else {
          alert(`更新失败：${res.data.error}`)
          return res.data
        }
      } catch (error) {
        console.error('更新管理员配置失败:', error)
        alert('更新失败：' + error.message)
        return { success: false, error: error.message }
      }
    },

    /**
     * 修改管理员密码
     * @param {string} old_password - 旧密码
     * @param {string} new_password - 新密码
     */
    async changeAdminPassword(old_password, new_password) {
      try {
        const res = await axios.post('/api/admin/change-password', {
          old_password,
          new_password
        })
        if (res.data.success) {
          alert('密码修改成功！')
          return res.data
        } else {
          alert(`密码修改失败：${res.data.error}`)
          return res.data
        }
      } catch (error) {
        console.error('修改管理员密码失败:', error)
        alert('密码修改失败：' + error.message)
        return { success: false, error: error.message }
      }
    },

    /**
     * 刷新所有数据（包括首页和历史）
     */
    async refreshAll() {
      this.loading = true
      await Promise.all([
        this.fetchSystemInfo(),
        this.fetchJobs(),
        this.fetchHosts(),
        this.fetchUsers(),
        this.fetchQueues(),
        this.fetchLoad(),
        this.fetchLoadTrend(),
        this.fetchSlotsTrend(this.slotsPeriod)
      ])
      if (this.isAdmin) {
        await this.fetchAdminConfig()
      }
      this.loading = false
    }
  }
})
