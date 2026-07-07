<!-- src/views/layouts/DoctorLayout.vue -->
<template>
  <div class="doctor-app">
    <header class="doctor-header">
      <div class="header-left">
        <span class="brand">智能诊疗系统</span>
        <span class="dept-tag">{{ departmentName }}</span>
      </div>
      <div class="header-right">
        <button type="button" title="工作台" @click="goHome">
          <van-icon name="wap-home-o" />
        </button>
        <button type="button" title="我的" @click="goProfile">
          <van-icon name="manager-o" />
        </button>
        <button type="button" title="退出登录" @click="handleLogout">
          <van-icon name="logout" />
        </button>
      </div>
    </header>

    <main class="main-content">
      <router-view />
    </main>

    <nav class="bottom-tab" aria-label="医生端导航">
      <button
        type="button"
        class="tab-item"
        :class="{ active: route.path === '/doctor' || route.path === '/doctor/' }"
        @click="goHome"
      >
        <van-icon name="wap-home-o" />
        <span>工作台</span>
      </button>
      <button
        type="button"
        class="tab-item"
        :class="{ active: route.path === '/doctor/profile' }"
        @click="goProfile"
      >
        <van-icon name="manager-o" />
        <span>我的</span>
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const departmentName = computed(() => {
  const userInfo = userStore.userInfo as any
  return userInfo?.department || userInfo?.deptName || '门诊科室'
})

const goHome = () => {
  if (route.path === '/doctor/visit') {
    window.dispatchEvent(new CustomEvent('save-draft'))
    showToast('草稿已保存')
  }
  router.push('/doctor')
}

const goProfile = () => router.push('/doctor/profile')

const handleLogout = () => {
  showDialog({
    title: '提示',
    message: '确定要退出登录吗？',
    showCancelButton: true,
    confirmButtonColor: '#E76F51',
  }).then(() => {
    userStore.logout()
    showToast('已退出登录')
    router.push('/auth/login')
  }).catch(() => {})
}
</script>

<style lang="scss" scoped>
.doctor-app {
  min-height: 100vh;
  padding-bottom: 60px;
  background: #f5f7fa;
}

.doctor-header {
  position: sticky;
  top: 0;
  z-index: 100;
  min-height: 56px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #005b96 0%, #0077b6 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-left {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand {
  font-size: 18px;
  font-weight: 650;
  white-space: nowrap;
}

.dept-tag {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  font-size: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-right button {
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.14);
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.main-content {
  min-height: calc(100vh - 116px);
  padding-bottom: 20px;
}

.bottom-tab {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  display: flex;
  border-top: 1px solid #ebedf0;
  background: #ffffff;
  padding: 6px 0 env(safe-area-inset-bottom);
}

.tab-item {
  flex: 1;
  border: 0;
  background: transparent;
  color: #969799;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 0;
  font-size: 12px;
}

.tab-item :deep(.van-icon) {
  font-size: 24px;
}

.tab-item.active {
  color: #005b96;
}

@media (min-width: 900px) {
  .doctor-header {
    padding-inline: 24px;
  }
}
</style>
