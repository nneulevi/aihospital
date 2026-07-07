<template>
  <div class="profile-page">
    <van-nav-bar title="我的" fixed placeholder />

    <div class="user-card">
      <div class="user-avatar">
        <van-icon name="user-circle-o" size="64" color="#4CAF50" />
      </div>
      <div v-if="isLoggedIn" class="user-info">
        <div class="user-name">{{ userStore.userName || '患者用户' }}</div>
        <div class="user-phone">{{ displayPhone }}</div>
      </div>
      <div v-else class="user-info">
        <div class="user-name">未登录</div>
        <div class="user-tip">登录后享受更多服务</div>
      </div>
      <van-button v-if="!isLoggedIn" size="small" type="primary" round @click="goToLogin">
        立即登录
      </van-button>
    </div>

    <div v-if="isLoggedIn" class="summary-card">
      <div class="summary-grid">
        <div class="summary-item">
          <span class="summary-value">{{ summary.recordCount }}</span>
          <span class="summary-label">就诊记录</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">{{ summary.unpaidOrderCount }}</span>
          <span class="summary-label">待缴费</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">¥{{ formatAmount(summary.unpaidAmount) }}</span>
          <span class="summary-label">待缴金额</span>
        </div>
      </div>
      <div class="latest-state">最近就诊状态：{{ summary.latestVisitState || '暂无记录' }}</div>
    </div>

    <div class="menu-group">
      <div class="menu-item" @click="goToRecords">
        <van-icon name="records-o" size="22" />
        <span class="menu-label">我的病历</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
      <div class="menu-item" @click="goToOrders">
        <van-icon name="bill-o" size="22" />
        <span class="menu-label">缴费记录</span>
        <van-icon name="arrow" class="menu-arrow" />
      </div>
    </div>

    <div v-if="isLoggedIn" class="logout-btn" @click="handleLogout">
      <van-button block plain type="danger" round>退出登录</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import { maskPhone } from '@/utils/format'
import { getPatientDashboardSummary, type PatientDashboardSummary } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const isLoggedIn = computed(() => userStore.isLoggedIn)
const userInfo = computed(() => userStore.userInfo)
const displayPhone = computed(() => maskPhone((userInfo.value as any)?.phone || ''))
const summary = reactive<PatientDashboardSummary>({
  patientId: 0,
  recordCount: 0,
  unpaidOrderCount: 0,
  unpaidAmount: 0,
  latestVisitState: ''
})

const formatAmount = (value?: number) => Number(value || 0).toFixed(2)

const loadSummary = async () => {
  if (!userStore.patientId) return
  try {
    const res = await getPatientDashboardSummary(userStore.patientId)
    Object.assign(summary, res.data || res)
  } catch {
    showToast('个人概览加载失败')
  }
}

const goToLogin = () => router.push('/patient/login')
const goToRecords = () => {
  if (!isLoggedIn.value) {
    goToLogin()
    return
  }
  router.push('/patient/records')
}
const goToOrders = () => {
  if (!isLoggedIn.value) {
    goToLogin()
    return
  }
  router.push('/patient/orders')
}

const handleLogout = () => {
  showDialog({
    title: '提示',
    message: '确定要退出登录吗？',
    showCancelButton: true,
    confirmButtonColor: '#4CAF50'
  }).then(() => {
    userStore.logout()
    showToast('已退出登录')
    router.push('/patient/ai')
  }).catch(() => {})
}

onMounted(loadSummary)
watch(() => userStore.patientId, loadSummary)
</script>

<style lang="scss" scoped>
.profile-page { min-height: 100vh; background: #F5F7FA; padding-bottom: 20px; }
.user-card { background: white; margin: 12px; padding: 32px 16px; border-radius: 8px; text-align: center; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.user-avatar { margin-bottom: 12px; }
.user-info .user-name { font-size: 18px; font-weight: 500; color: #1A1A2E; }
.user-info .user-phone { font-size: 14px; color: #687789; margin-top: 4px; }
.user-info .user-tip { font-size: 14px; color: #687789; margin-top: 4px; }
.summary-card { background: white; margin: 12px; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 8px rgba(31,42,55,.06); }
.summary-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-bottom: 1px solid #E6EBF2; }
.summary-item { padding: 14px 6px; text-align: center; display: flex; flex-direction: column; gap: 4px; }
.summary-value { color: #4CAF50; font-weight: 700; font-size: 16px; word-break: break-word; }
.summary-label { color: #687789; font-size: 12px; }
.latest-state { padding: 12px 16px; color: #687789; font-size: 13px; }
.menu-group { background: white; margin: 12px; border-radius: 8px; overflow: hidden; }
.menu-item { display: flex; align-items: center; padding: 14px 16px; border-bottom: 1px solid #E6EBF2; cursor: pointer; &:last-child { border-bottom: none; } }
.menu-label { flex: 1; margin-left: 12px; font-size: 14px; color: #1A1A2E; }
.menu-arrow { color: #94A3B8; }
.logout-btn { margin: 24px 12px; }
</style>
