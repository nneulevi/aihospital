<template>
  <main class="mini-page">
    <section class="hero">
      <div>
        <p class="eyebrow">智慧医疗小程序</p>
        <h1>{{ userStore.userName || '患者' }}，您好</h1>
        <p class="hero-subtitle">今日可完成问诊、挂号、缴费与报告查看</p>
      </div>
      <van-icon name="shield-o" size="42" color="#2375ff" />
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

    <section class="quick-grid" aria-label="患者常用功能">
      <button type="button" class="quick-action ai" @click="router.push('/mini-patient/ai')">
        <van-icon name="chat-o" />
        <span>AI 智能问诊</span>
      </button>
      <button type="button" class="quick-action appointment" @click="router.push('/mini-patient/appointment')">
        <van-icon name="calendar-o" />
        <span>预约挂号</span>
      </button>
      <button type="button" class="quick-action record" @click="router.push('/mini-patient/records')">
        <van-icon name="records-o" />
        <span>电子病历</span>
      </button>
      <button type="button" class="quick-action order" @click="router.push('/mini-patient/orders')">
        <van-icon name="bill-o" />
        <span>门诊缴费</span>
      </button>
    </section>

    <section class="status-card">
      <div class="section-title">
        <span>最近就诊</span>
        <button type="button" @click="router.push('/mini-patient/records')">查看</button>
      </div>
      <p class="status-text">{{ summary.latestVisitState || '暂无进行中的就诊记录' }}</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
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
  padding: 18px 16px 24px;
}

.hero {
  min-height: 154px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 22px;
  border-radius: 8px;
  background: linear-gradient(135deg, #ffffff 0%, #eaf2ff 100%);
  box-shadow: 0 8px 24px rgba(35, 117, 255, 0.12);
}

.eyebrow {
  margin: 0 0 6px;
  color: #2375ff;
  font-size: 12px;
  font-weight: 600;
}

.hero h1 {
  margin: 0;
  color: #1f2a37;
  font-size: 24px;
  line-height: 1.25;
}

.hero-subtitle {
  margin: 10px 0 0;
  color: #5b6b80;
  font-size: 13px;
  line-height: 1.5;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.stat {
  min-width: 0;
  padding: 14px 6px;
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
  color: #2375ff;
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

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.quick-action {
  min-height: 94px;
  border: 0;
  border-radius: 8px;
  color: #ffffff;
  font-size: 15px;
  font-weight: 600;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px;
}

.quick-action :deep(.van-icon) {
  font-size: 28px;
}

.quick-action.ai {
  background: linear-gradient(135deg, #2375ff, #41a5ff);
}

.quick-action.appointment {
  background: linear-gradient(135deg, #2a9d8f, #48b9a8);
}

.quick-action.record {
  background: linear-gradient(135deg, #7353ba, #8b6fd3);
}

.quick-action.order {
  background: linear-gradient(135deg, #e76f51, #f4a261);
}

.status-card {
  margin-top: 18px;
  padding: 16px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
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
  color: #2375ff;
  font-size: 13px;
}

.status-text {
  margin: 12px 0 0;
  color: #5b6b80;
  font-size: 14px;
  line-height: 1.6;
}
</style>
