<!-- src/views/layouts/AdminLayout.vue -->
<template>
  <div class="admin-layout">
    <van-nav-bar :title="pageTitle" fixed placeholder class="admin-nav">
      <template #right>
        <span class="nav-role" @click="handleLogout">退出</span>
      </template>
    </van-nav-bar>

    <div class="admin-content">
      <router-view />
    </div>

    <van-tabbar v-model="activeTab" class="admin-tabbar" @change="onTabChange">
      <van-tabbar-item icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item icon="calendar-o">排班</van-tabbar-item>
      <van-tabbar-item icon="balance-pay">收费</van-tabbar-item>
      <van-tabbar-item icon="medal-o">药房</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeTab = ref(0)

// Tab 索引与路径的映射
const tabMap = [
  '/admin',
  '/admin/schedule',
  '/admin/finance',
  '/admin/drug'
]

// 根据当前路径更新 activeTab
const updateActiveTab = () => {
  const path = route.path
  let index = 0
  if (path === '/admin') index = 0
  else if (path === '/admin/schedule') index = 1
  else if (path === '/admin/finance') index = 2
  else if (path === '/admin/drug') index = 3
  else if (path.startsWith('/admin/schedule')) index = 1
  else if (path.startsWith('/admin/finance')) index = 2
  else if (path.startsWith('/admin/drug')) index = 3
  else if (path.startsWith('/admin')) index = 0

  activeTab.value = index
}

// Tab 切换事件
const onTabChange = (index: number) => {
  router.push(tabMap[index])
}

// 监听路由变化
watch(() => route.path, () => {
  updateActiveTab()
}, { immediate: true })

// 页面标题
const pageTitle = ref('管理首页')
watch(() => route.path, (path) => {
  const titles: Record<string, string> = {
    '/admin': '管理首页',
    '/admin/schedule': 'AI排班',
    '/admin/finance': '收费管理',
    '/admin/drug': '药房管理'
  }
  if (titles[path]) {
    pageTitle.value = titles[path]
  } else if (path.startsWith('/admin/schedule')) {
    pageTitle.value = 'AI排班'
  } else if (path.startsWith('/admin/finance')) {
    pageTitle.value = '收费管理'
  } else if (path.startsWith('/admin/drug')) {
    pageTitle.value = '药房管理'
  } else if (path.startsWith('/admin/staff')) {
    pageTitle.value = '创建档案'
  } else if (path.startsWith('/admin/doctor-stats')) {
    pageTitle.value = '医生统计'
  } else if (path.startsWith('/admin/dept-stats')) {
    pageTitle.value = '部门统计'
  } else {
    pageTitle.value = '管理后台'
  }
}, { immediate: true })

// ============ 退出登录 ============
const handleLogout = () => {
  showDialog({
    title: '确认退出',
    message: '确定要退出登录吗？',
    showCancelButton: true,
    confirmButtonText: '退出',
    confirmButtonColor: '#E76F51'
  })
      .then(() => {
        userStore.logout()
        showToast('已退出')
        router.replace('/auth/login')
      })
      .catch(() => {})
}
</script>

<style lang="scss" scoped>
.admin-layout {
  min-height: 100vh;
  background: #F5F5F5;
}
.admin-content {
  padding-bottom: 60px;
}
.admin-nav :deep(.van-nav-bar__title) {
  font-weight: 600;
}
.nav-role {
  font-size: 12px;
  color: #E76F51;
  border: 1px solid #E76F51;
  padding: 2px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #E76F51;
    color: white;
  }
  &:active {
    transform: scale(0.95);
  }
}
.admin-tabbar :deep(.van-tabbar-item--active) {
  color: #F4A261;
}
</style>