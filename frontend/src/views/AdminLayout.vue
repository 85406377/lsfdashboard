<template>
  <div class="admin-layout">
    <div class="admin-sidebar">
      <div class="sidebar-header">
        <h3>管理后台</h3>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/admin/profile" class="nav-item">
          <span class="nav-icon">👤</span>
          <span>个人信息</span>
        </router-link>
        <router-link to="/admin/history" class="nav-item">
          <span class="nav-icon">📊</span>
          <span>历史作业</span>
        </router-link>
        <router-link to="/" class="nav-item nav-back">
          <span class="nav-icon">🏠</span>
          <span>返回首页</span>
        </router-link>
      </nav>
    </div>
    <div class="admin-content">
      <router-view />
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdminLayout'
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: #f0f2f5;
}

.admin-sidebar {
  width: 240px;
  background: #001529;
  color: #fff;
  box-shadow: 2px 0 6px rgba(0, 21, 41, 0.35);
  position: fixed;
  height: 100vh;
  overflow-y: auto;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-nav {
  padding: 10px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  color: rgba(255, 255, 255, 0.65);
  text-decoration: none;
  transition: all 0.3s;
}

.nav-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.nav-item.router-link-active {
  color: #fff;
  background: #1890ff;
}

.nav-icon {
  margin-right: 10px;
  font-size: 16px;
}

.nav-back {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.admin-content {
  margin-left: 240px;
  padding: 24px;
  flex: 1;
  min-height: 100vh;
}

@media (max-width: 768px) {
  .admin-sidebar {
    width: 100%;
    height: auto;
    position: relative;
  }
  
  .admin-content {
    margin-left: 0;
  }
  
  .admin-layout {
    flex-direction: column;
  }
}
</style>
