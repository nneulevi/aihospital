<template>
  <main class="mini-page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">{{ greeting }}</p>
        <h1>{{ userStore.userName || '患者' }}，您好</h1>
        <p class="hero-subtitle">今日可完成问诊、挂号、缴费与报告查看</p>
        <div class="patient-chip">
          <van-icon name="user-circle-o" />
          <span>{{ patientMeta }}</span>
        </div>
      </div>
      <div class="hero-icon">
        <van-icon name="shield-o" />
      </div>
    </section>

    <section class="stats">
      <button class="stat" type="button" @click="router.push('/mini-patient/records')">
        <strong>{{ summary.recordCount }}</strong>
        <span>就诊记录</span>
      </button>
      <button class="stat warning" type="button" @click="router.push('/mini-patient/orders')">
        <strong>{{ summary.unpaidOrderCount }}</strong>
        <span>待缴费</span>
      </button>
      <button class="stat success" type="button" @click="router.push('/mini-patient/orders')">
        <strong>¥{{ formatAmount(summary.unpaidAmount) }}</strong>
        <span>待缴金额</span>
      </button>
    </section>

    <section class="core-services" aria-label="核心服务">
      <button
        v-for="item in coreServices"
        :key="item.title"
        type="button"
        class="service-card"
        @click="router.push(item.path)"
      >
        <span class="service-icon" :class="item.tone">
          <van-icon :name="item.icon" />
        </span>
        <span class="service-copy">
          <strong>{{ item.title }}</strong>
          <small>{{ item.desc }}</small>
        </span>
        <van-icon name="arrow" class="service-arrow" />
      </button>
    </section>

    <section class="section-card">
      <div class="section-title">
        <span>门诊服务</span>
        <button type="button" @click="router.push('/mini-patient/profile')">全部</button>
      </div>
      <div class="quick-grid" aria-label="患者常用功能">
        <button
          v-for="item in quickActions"
          :key="item.title"
          type="button"
          class="quick-action"
          @click="router.push(item.path)"
        >
          <span class="quick-icon" :class="item.tone">
            <van-icon :name="item.icon" />
          </span>
          <span>{{ item.title }}</span>
        </button>
      </div>
    </section>

    <section class="section-card status-card">
      <div class="section-title">
        <span>最近就诊</span>
        <button type="button" @click="router.push('/mini-patient/records')">查看</button>
      </div>
      <div class="status-row">
        <van-icon name="clock-o" />
        <p class="status-text">{{ summary.latestVisitState || '暂无进行中的就诊记录' }}</p>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
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

const formatAmount = (value?: number) => Number(value || 0).toFixed(2)
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})
const patientMeta = computed(() => {
  const caseNumber = userStore.userInfo?.caseNumber
  return caseNumber ? `病历号 ${caseNumber}` : '当前就诊人'
})
const coreServices = [
  { title: 'AI 智能问诊', desc: '症状预问诊与科室推荐', icon: 'chat-o', path: '/mini-patient/ai', tone: 'green' },
  { title: '预约挂号', desc: '选择科室医生并提交', icon: 'calendar-o', path: '/mini-patient/appointment', tone: 'green' },
]
const quickActions = [
  { title: '电子病历', icon: 'records-o', path: '/mini-patient/records', tone: 'purple' },
  { title: '门诊缴费', icon: 'bill-o', path: '/mini-patient/orders', tone: 'orange' },
  { title: '个人中心', icon: 'user-o', path: '/mini-patient/profile', tone: 'cyan' },
  { title: '报告记录', icon: 'description-o', path: '/mini-patient/records', tone: 'slate' },
]

const loadSummary = async () => {
  if (!userStore.patientId) return
  try {
    const res = await getPatientDashboardSummary(userStore.patientId)
    Object.assign(summary, res.data || res)
  } catch {
    Object.assign(summary, {
      patientId: userStore.patientId,
      recordCount: 0,
      unpaidOrderCount: 0,
      unpaidAmount: 0,
      latestVisitState: '',
    })
  }
}

onMounted(loadSummary)
</script>

<style lang="scss" scoped>
.mini-page {
  padding: 16px 14px 24px;
}

.hero {
  min-height: 166px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 22px 20px;
  border-radius: 8px;
  background:
    radial-gradient(circle at right top, rgba(255, 255, 255, 0.42), transparent 34%),
    linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
  box-shadow: 0 8px 24px rgba(76, 175, 80, 0.16);
}

.hero-copy {
  min-width: 0;
}

.eyebrow {
  margin: 0 0 6px;
  color: rgba(255, 255, 255, 0.84);
  font-size: 12px;
  font-weight: 600;
}

.hero h1 {
  margin: 0;
  color: #ffffff;
  font-size: 22px;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.hero-subtitle {
  margin: 10px 0 0;
  color: rgba(255, 255, 255, 0.86);
  font-size: 13px;
  line-height: 1.5;
}

.patient-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 12px;
}

.hero-icon {
  width: 58px;
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
  font-size: 36px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.stat {
  min-width: 0;
  padding: 14px 6px 13px;
  border: 0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.stat strong,
.stat span {
  display: block;
}

.stat strong {
  color: #4caf50;
  font-size: 18px;
  line-height: 1.3;
}

.stat span {
  margin-top: 4px;
  color: #687789;
  font-size: 12px;
}

.stat.warning strong {
  color: #e76f51;
}

.stat.success strong {
  color: #2a9d8f;
}

.core-services {
  display: grid;
  gap: 12px;
  margin-top: 18px;
}

.service-card {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 76px;
  border: 0;
  border-radius: 8px;
  background: #ffffff;
  padding: 14px;
  text-align: left;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.service-icon,
.quick-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.service-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  font-size: 25px;
}

.service-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.service-copy strong {
  color: #1f2a37;
  font-size: 15px;
}

.service-copy small {
  color: #687789;
  font-size: 12px;
  line-height: 1.35;
}

.service-arrow {
  color: #b5c1cf;
}

.section-card {
  margin-top: 18px;
  padding: 16px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px 8px;
  margin-top: 14px;
}

.quick-action {
  min-width: 0;
  border: 0;
  background: transparent;
  color: #465568;
  font-size: 12px;
  line-height: 1.4;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
}

.quick-icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  font-size: 23px;
}

.blue {
  background: #e3f2fd;
  color: #2196f3;
}

.green {
  background: #e8f5e9;
  color: #4caf50;
}

.green {
  background: #eaf8f5;
  color: #2a9d8f;
}

.purple {
  background: #f1edfb;
  color: #7353ba;
}

.orange {
  background: #fff3ec;
  color: #e76f51;
}

.cyan {
  background: #e9f8fb;
  color: #119fb3;
}

.slate {
  background: #eef3f8;
  color: #52677e;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #1f2a37;
  font-size: 16px;
  font-weight: 600;
}

.section-title button {
  border: 0;
  background: transparent;
  color: #4caf50;
  font-size: 13px;
}

.status-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-top: 12px;
  color: #4caf50;
}

.status-text {
  margin: 0;
  color: #5b6b80;
  font-size: 14px;
  line-height: 1.6;
}
</style>
