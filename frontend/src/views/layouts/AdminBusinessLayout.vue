<template>
  <div class="admin-layout">
    <van-nav-bar :title="pageTitle" fixed placeholder class="admin-nav">
      <template #right>
        <span class="nav-role">管理员</span>
        <van-button class="nav-action" plain size="small" icon="close" @click="handleLogout">退出</van-button>
      </template>
    </van-nav-bar>

    <div class="admin-content">
      <router-view />
    </div>

    <van-tabbar route class="admin-tabbar">
      <van-tabbar-item to="/admin" icon="home-o" @click="navigate('/admin')">首页</van-tabbar-item>
      <van-tabbar-item to="/admin/schedule" icon="calendar-o" @click="navigate('/admin/schedule')">AI排班</van-tabbar-item>
      <van-tabbar-item to="/admin/schedule-sources" icon="todo-list-o" @click="navigate('/admin/schedule-sources')">号源</van-tabbar-item>
      <van-tabbar-item to="/admin/finance" icon="balance-pay" @click="navigate('/admin/finance')">收费</van-tabbar-item>
      <van-tabbar-item to="/admin/drug" icon="medal-o" @click="navigate('/admin/drug')">药房</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { logout } from '@/utils/auth'
import { authLogout } from '@/api'

const route = useRoute()
const router = useRouter()
const titles: Record<string, string> = {
  '/admin': '首页',
  '/admin/schedule': 'AI排班',
  '/admin/schedule-sources': '号源管理',
  '/admin/finance': '收费管理',
  '/admin/drug': '药房管理',
  '/admin/staff/create': '人员新增',
  '/admin/stats/doctors': '医生统计',
  '/admin/stats/departments': '科室统计',
}

const pageTitle = computed(() => titles[route.path] || '管理后台')

const navigate = (path: string) => {
  if (route.path !== path) {
    router.replace(path)
  }
}

const handleLogout = async () => {
  try {
    await showConfirmDialog({
      title: '退出登录',
      message: '确定退出管理员工作台吗？',
      confirmButtonText: '退出',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await authLogout()
  } catch {
    // 本地会话仍需清理，避免后端登出失败导致前端无法退出。
  }
  logout()
  showToast('已退出登录')
  router.replace('/auth/login')
}
</script>

<style lang="scss" scoped>
.admin-layout {
  min-height: 100vh;
  background: #f5f5f5;
}
.admin-content {
  padding-bottom: 64px;
}
.admin-nav :deep(.van-nav-bar__title) {
  font-weight: 600;
}
.nav-role {
  font-size: 12px;
  color: #1677ff;
  border: 1px solid #1677ff;
  padding: 2px 8px;
  border-radius: 12px;
  margin-right: 8px;
}
.admin-nav :deep(.van-nav-bar__left),
.admin-nav :deep(.van-nav-bar__right) {
  gap: 8px;
}
.nav-action {
  height: 28px;
  padding: 0 8px;
  color: #1677ff;
  border-color: #c6d8ff;
  background: #f8fbff;
}
.admin-tabbar :deep(.van-tabbar-item--active) {
  color: #1677ff;
}
</style>
