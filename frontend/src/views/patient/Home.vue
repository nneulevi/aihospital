<!-- src/views/patient/Home.vue -->
<template>
  <div class="home-page">
    <section class="header-area">
      <div class="greeting-row">
        <div>
          <div class="greeting">
            <span class="greeting-icon">☀️</span>
            <span class="greeting-text">{{ greeting }}，{{ displayName }}</span>
          </div>
          <p class="header-subtitle">门诊问诊、挂号、缴费与病历查询都可以在这里完成</p>
        </div>
        <van-icon name="bell-o" size="22" @click="router.push('/patient/messages')" />
      </div>

      <button class="patient-switcher" type="button" @click="router.push('/patient/patient-manager')">
        <span>
          <strong>{{ displayName || '请选择就诊人' }}</strong>
          <small>{{ patientMeta }}</small>
        </span>
        <van-icon name="arrow" />
      </button>
    </section>

    <section class="summary-grid" aria-label="就诊概览">
      <button class="summary-card" type="button" @click="router.push('/patient/records')">
        <strong>{{ summary.recordCount }}</strong>
        <span>就诊记录</span>
      </button>
      <button class="summary-card warning" type="button" @click="router.push('/patient/orders')">
        <strong>{{ summary.unpaidOrderCount }}</strong>
        <span>待缴费</span>
      </button>
      <button class="summary-card success" type="button" @click="router.push('/patient/orders')">
        <strong>¥{{ formatAmount(summary.unpaidAmount) }}</strong>
        <span>待缴金额</span>
      </button>
    </section>

    <section class="core-services">
      <button class="service-card" type="button" @click="router.push('/patient/appointment')">
        <span class="service-icon green"><van-icon name="calendar-o" /></span>
        <span class="service-text">
          <strong>预约挂号</strong>
          <small>选择科室医生并提交挂号</small>
        </span>
        <van-icon name="arrow" class="service-arrow" />
      </button>
      <button class="service-card" type="button" @click="router.push('/patient/orders')">
        <span class="service-icon orange"><van-icon name="gold-coin-o" /></span>
        <span class="service-text">
          <strong>门诊缴费</strong>
          <small>查看待缴项目并完成确认</small>
        </span>
        <van-icon name="arrow" class="service-arrow" />
      </button>
    </section>

    <section class="service-section">
      <div class="section-header">
        <span>门诊服务</span>
      </div>
      <div class="service-grid">
        <button
          v-for="item in serviceItems"
          :key="item.label"
          class="grid-item"
          type="button"
          @click="router.push(item.path)"
        >
          <span class="grid-icon" :class="item.tone">
            <van-icon :name="item.icon" />
          </span>
          <span>{{ item.label }}</span>
        </button>
      </div>
    </section>

    <section class="service-section latest-section">
      <div class="section-header">
        <span>最近就诊</span>
        <button type="button" @click="router.push('/patient/records')">查看</button>
      </div>
      <div class="latest-row">
        <van-icon name="clock-o" />
        <p>{{ summary.latestVisitState || '暂无进行中的就诊记录' }}</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import { getPatientDashboardSummary, type PatientDashboardSummary } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const summary = reactive<PatientDashboardSummary>({
  patientId: userStore.patientId || 0,
  recordCount: 0,
  unpaidOrderCount: 0,
  unpaidAmount: 0,
  latestVisitState: '',
})

const displayName = computed(() => userStore.userInfo?.realName || userStore.userName || '患者')
const patientMeta = computed(() => {
  const caseNumber = userStore.userInfo?.caseNumber
  return caseNumber ? `病历号：${caseNumber}` : '点击查看个人信息'
})
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了'
})

const serviceItems = [
  { label: 'AI 问诊', icon: 'chat-o', path: '/patient/ai', tone: 'cyan' },
  { label: '就诊报到', icon: 'location-o', path: '/patient/checkin', tone: 'pink' },
  { label: '候诊查询', icon: 'clock-o', path: '/patient/queue', tone: 'purple' },
  { label: '报告查询', icon: 'file-o', path: '/patient/reports', tone: 'blue' },
  { label: '联系客服', icon: 'service-o', path: '/patient/customer-service', tone: 'green' },
  { label: '检验预约', icon: 'medical-o', path: '/patient/lab-booking', tone: 'blue' },
  { label: '检查预约', icon: 'scan-o', path: '/patient/exam-booking', tone: 'green' },
  { label: '处方查询', icon: 'bill-o', path: '/patient/prescriptions', tone: 'yellow' },
  { label: '全部服务', icon: 'apps-o', path: '/patient/services', tone: 'slate' },
]

const formatAmount = (value?: number) => Number(value || 0).toFixed(2)

const loadSummary = async () => {
  if (!userStore.patientId) return
  try {
    const res = await getPatientDashboardSummary(userStore.patientId)
    Object.assign(summary, res.data || res)
  } catch {
    showToast('患者首页加载失败')
  }
}

onMounted(loadSummary)
</script>

<style lang="scss" scoped>
.home-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 0 16px 84px;
}

.header-area {
  margin: 0 -16px 16px;
  padding: 20px 16px 24px;
  border-radius: 0 0 8px 8px;
  color: #ffffff;
  background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
}

.greeting-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.greeting {
  display: flex;
  align-items: center;
  gap: 8px;
}

.greeting-text {
  font-size: 18px;
  font-weight: 600;
}

.header-subtitle {
  margin: 8px 0 0;
  color: rgba(255, 255, 255, 0.84);
  font-size: 13px;
  line-height: 1.55;
}

.patient-switcher {
  width: 100%;
  margin-top: 16px;
  padding: 12px 14px;
  border: 0;
  border-radius: 8px;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
}

.patient-switcher strong,
.patient-switcher small {
  display: block;
}

.patient-switcher small {
  margin-top: 3px;
  color: rgba(255, 255, 255, 0.82);
  font-size: 12px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.summary-card {
  min-width: 0;
  padding: 14px 6px;
  border: 0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.summary-card strong,
.summary-card span {
  display: block;
}

.summary-card strong {
  color: #4caf50;
  font-size: 18px;
}

.summary-card span {
  margin-top: 4px;
  color: #687789;
  font-size: 12px;
}

.summary-card.warning strong { color: #e76f51; }
.summary-card.success strong { color: #2a9d8f; }

.core-services {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 16px;
}

.service-card {
  min-width: 0;
  min-height: 88px;
  padding: 14px;
  border: 0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
}

.service-icon,
.grid-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.service-icon {
  width: 46px;
  height: 46px;
  border-radius: 8px;
  font-size: 25px;
}

.service-text {
  min-width: 0;
  flex: 1;
}

.service-text strong,
.service-text small {
  display: block;
}

.service-text strong {
  color: #1a1a2e;
  font-size: 15px;
}

.service-text small {
  margin-top: 3px;
  color: #6b6b7e;
  font-size: 12px;
  line-height: 1.35;
}

.service-arrow {
  color: #c4c4d6;
}

.service-section {
  margin-top: 16px;
  padding: 16px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  color: #1a1a2e;
  font-size: 16px;
  font-weight: 600;
}

.section-header button {
  border: 0;
  background: transparent;
  color: #4caf50;
  font-size: 13px;
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px 8px;
}

.grid-item {
  min-width: 0;
  border: 0;
  background: transparent;
  color: #4a4a5e;
  font-size: 12px;
  line-height: 1.4;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
}

.grid-icon {
  width: 46px;
  height: 46px;
  border-radius: 8px;
  font-size: 24px;
}

.latest-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  color: #4caf50;
}

.latest-row p {
  margin: 0;
  color: #5b6b80;
  font-size: 14px;
  line-height: 1.6;
}

.green { background: #e8f5e9; color: #4caf50; }
.orange { background: #fff3e0; color: #ff9800; }
.cyan { background: #e0f7fa; color: #00bcd4; }
.purple { background: #f3e5f5; color: #9c27b0; }
.blue { background: #e3f2fd; color: #2196f3; }
.slate { background: #f5f5f5; color: #607d8b; }
</style>
