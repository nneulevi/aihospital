<!-- src/views/patient/Profile.vue -->
<template>
  <div class="profile-page">
    <van-nav-bar title="我的" fixed placeholder />

    <div class="user-card" @click="goToPatientManager">
      <div class="user-avatar">
        <van-icon name="user-circle-o" size="56" color="#4CAF50" />
      </div>
      <div class="user-info">
        <div class="user-name">{{ displayName }}</div>
        <div class="user-phone">{{ maskPhone(userInfo?.phone) || '未绑定手机号' }}</div>
        <div class="user-tip">点击管理就诊人</div>
      </div>
      <van-icon name="arrow" class="user-arrow" />
    </div>

    <div class="menu-section">
      <div class="menu-item" @click="goToPatientManager">
        <van-icon name="contact-o" size="22" color="#4CAF50" />
        <span class="menu-label">就诊人管理</span>
        <span class="menu-badge">{{ patientCount }}人</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
    </div>

    <div class="menu-section">
      <div class="menu-item" @click="goToAppointments">
        <van-icon name="records-o" size="22" color="#2196F3" />
        <span class="menu-label">挂号记录</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
      <div class="menu-item" @click="goToOrders">
        <van-icon name="bill-o" size="22" color="#FF9800" />
        <span class="menu-label">缴费记录</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
      <div class="menu-item" @click="goToReports">
        <van-icon name="file-o" size="22" color="#E91E63" />
        <span class="menu-label">我的报告</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
      <div class="menu-item" @click="goToPrescriptions">
        <van-icon name="bill-o" size="22" color="#9C27B0" />
        <span class="menu-label">我的处方</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
    </div>

    <div class="menu-section">
      <div class="menu-item" @click="goToSettings">
        <van-icon name="setting-o" size="22" color="#6B6B7E" />
        <span class="menu-label">设置</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
    </div>

    <div class="logout-btn" v-if="isLoggedIn" @click="handleLogout">
      <van-button block plain type="danger" round>退出登录</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import { maskPhone } from '@/utils/format'
import { list, getCurrentPatient } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const isLoggedIn = computed(() => userStore.isLoggedIn)
const userInfo = computed(() => userStore.userInfo)
const patientCount = ref(0)

// ===== 显示名称 =====
const displayName = computed(() => {
  return userInfo.value?.realName || userStore.userName || '患者用户'
})

// ===== 加载就诊人数量 =====
const loadPatientCount = async () => {
  try {
    const res = await list()
    if (res && Array.isArray(res)) {
      patientCount.value = res.length
    }
  } catch (error) {
    console.error('获取就诊人列表失败', error)
    patientCount.value = 0
  }
}

// ===== 加载当前患者信息（补充 phone 等字段） =====
const loadCurrentPatient = async () => {
  try {
    const res = await getCurrentPatient()
    if (res) {
      // 使用 store 的 updateUserInfo 方法补充 phone 等字段
      userStore.updateUserInfo({
        phone: res.phone,
        realName: res.realName || userInfo.value?.realName,
        caseNumber: res.caseNumber || userInfo.value?.caseNumber,
      })
    }
  } catch (error) {
    console.error('获取当前患者信息失败', error)
  }
}

// ===== 路由跳转 =====
const goToPatientManager = () => router.push('/patient/patient-manager')
const goToAppointments = () => router.push('/patient/appointments')
const goToOrders = () => router.push('/patient/orders')
const goToReports = () => router.push('/patient/reports')
const goToPrescriptions = () => router.push('/patient/prescriptions')
const goToSettings = () => showToast('设置功能开发中')

// ===== 退出登录 =====
const handleLogout = () => {
  showDialog({
    title: '提示',
    message: '确定要退出登录吗？',
    showCancelButton: true,
    confirmButtonColor: '#E76F51'
  })
      .then(() => {
        userStore.logout()
        showToast('已退出')
        router.replace('/patient/login')
      })
      .catch(() => {})
}

onMounted(async () => {
  await loadCurrentPatient()
  await loadPatientCount()
})
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}

.user-card {
  background: white;
  margin: 12px 16px;
  padding: 20px 16px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.user-info {
  flex: 1;

  .user-name {
    font-size: 18px;
    font-weight: 600;
    color: #1A1A2E;
  }

  .user-phone {
    font-size: 14px;
    color: #6B6B7E;
  }

  .user-tip {
    font-size: 12px;
    color: #4CAF50;
    margin-top: 2px;
  }
}

.user-arrow {
  color: #C4C4D6;
}

.menu-section {
  background: white;
  margin: 0 16px 12px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #F0F0F0;
  cursor: pointer;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: #F5F7FA;
  }
}

.menu-label {
  flex: 1;
  margin-left: 12px;
  font-size: 15px;
  color: #1A1A2E;
}

.menu-badge {
  font-size: 13px;
  color: #4CAF50;
  background: #E8F5E9;
  padding: 2px 10px;
  border-radius: 10px;
}

.menu-arrow {
  color: #C4C4D6;
}

.logout-btn {
  margin: 24px 16px;
}
</style>