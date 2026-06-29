<!-- src/views/layouts/AdminLayout.vue -->
<template>
  <div class="admin-layout">
    <van-nav-bar :title="pageTitle" fixed placeholder class="admin-nav">
      <template #right>
        <span class="nav-role">管理员</span>
      </template>
    </van-nav-bar>

    <div class="admin-content">
      <router-view />
    </div>

    <van-tabbar v-model="activeTab" route class="admin-tabbar">
      <van-tabbar-item to="/admin" icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item to="/admin/schedule" icon="calendar-o">排班</van-tabbar-item>
      <van-tabbar-item to="/admin/finance" icon="balance-pay">收费</van-tabbar-item>
      <van-tabbar-item to="/admin/drug" icon="medal-o">药房</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeTab = ref(0)
const pageTitle = ref('管理后台')

const titles: Record<string, string> = {
  '/admin': '首页',
  '/admin/schedule': 'AI排班',
  '/admin/finance': '收费管理',
  '/admin/drug': '药房管理'
}

watch(() => route.path, (path) => {
  pageTitle.value = titles[path] || '管理后台'
  const paths = ['/admin', '/admin/schedule', '/admin/finance', '/admin/drug']
  activeTab.value = paths.indexOf(path)
}, { immediate: true })
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
  color: #F4A261;
  border: 1px solid #F4A261;
  padding: 2px 8px;
  border-radius: 12px;
}
.admin-tabbar :deep(.van-tabbar-item--active) {
  color: #F4A261;
}
</style>