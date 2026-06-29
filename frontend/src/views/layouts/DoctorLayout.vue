<!-- src/views/layouts/DoctorLayout.vue -->
<template>
  <div class="doctor-app">
    <!-- 顶部导航 -->
    <div class="doctor-header">
      <div class="header-left">
        <span class="brand">👨‍⚕️ 智能诊疗系统</span>
        <span class="dept-tag">{{ doctorInfo?.department || '呼吸内科' }}</span>
      </div>
      <div class="header-right">
        <van-icon name="wap-home-o" size="22" @click="goHome" />
        <van-icon name="manager-o" size="22" @click="goProfile" />
        <van-icon name="logout" size="22" @click="handleLogout" />
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <router-view />
    </div>

    <!-- 底部Tab（医生端专用） -->
    <div class="bottom-tab">
      <div
          class="tab-item"
          :class="{ active: $route.path === '/doctor' || $route.path === '/doctor/' }"
          @click="goHome"
      >
        <van-icon name="wap-home-o" size="24" />
        <span>工作台</span>
      </div>
      <div
          class="tab-item"
          :class="{ active: $route.path === '/doctor/profile' }"
          @click="goProfile"
      >
        <van-icon name="manager-o" size="24" />
        <span>我的</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 模拟医生信息
const doctorInfo = ref({
  name: '张明',
  department: '呼吸内科',
  title: '主任医师',
  hospital: '市中心医院'
})

const goHome = () => {
  // 如果在诊疗页，先保存草稿
  if (route.path === '/doctor/visit') {
    // 触发保存草稿事件
    window.dispatchEvent(new CustomEvent('save-draft'))
    showToast('草稿已保存')
  }
  router.push('/doctor')
}

const goProfile = () => {
  router.push('/doctor/profile')
}

const handleLogout = () => {
  showDialog({
    title: '提示',
    message: '确定要退出登录吗？',
    showCancelButton: true,
    confirmButtonColor: '#E76F51'
  }).then(() => {
    userStore.logout()
    showToast('已退出登录')
    router.push('/auth/login')
  }).catch(() => {})
}

onMounted(() => {
  // 从store获取医生信息
  if (userStore.userInfo) {
    doctorInfo.value = { ...doctorInfo.value, ...userStore.userInfo }
  }
})
</script>

<style lang="scss" scoped>
.doctor-app {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 60px;
}

.doctor-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: linear-gradient(135deg, #005B96 0%, #0077B6 100%);
  color: white;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    .brand {
      font-size: 18px;
      font-weight: 600;
    }

    .dept-tag {
      background: rgba(255, 255, 255, 0.2);
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 12px;
    }
  }

  .header-right {
    display: flex;
    gap: 16px;
    align-items: center;

    .van-icon {
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        transform: scale(1.1);
        opacity: 0.8;
      }
    }
  }
}

.main-content {
  margin-top: 64px;
  min-height: calc(100vh - 124px);
  padding-bottom: 20px;
}

.bottom-tab {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  display: flex;
  border-top: 1px solid #EBEDF0;
  z-index: 100;
  padding: 6px 0 env(safe-area-inset-bottom);

  .tab-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    padding: 6px 0;
    color: #969799;
    cursor: pointer;
    transition: all 0.3s;
    font-size: 12px;

    .van-icon {
      font-size: 24px;
    }

    &.active {
      color: #005B96;

      .van-icon {
        color: #005B96;
      }
    }
  }
}
</style>