<template>
  <div class="schedule-page">
    <div class="panel">
      <div class="page-title">我的排班</div>
      <div class="page-subtitle">展示当前医生今日接诊状态，并引导到管理员维护的号源排班。</div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <strong>{{ stats.finishedToday }}</strong>
        <span>今日已接诊</span>
      </div>
      <div class="stat-card">
        <strong>{{ stats.pendingCheckCount }}</strong>
        <span>待处理检查</span>
      </div>
    </div>

    <div class="panel timeline-panel">
      <div class="time-row">
        <span>上午门诊</span>
        <van-tag type="success">正常</van-tag>
      </div>
      <div class="time-row">
        <span>下午门诊</span>
        <van-tag type="primary">按号源执行</van-tag>
      </div>
      <van-button block round type="primary" @click="$router.push('/doctor')">进入接诊工作台</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { showToast } from 'vant'
import { getDoctorDashboardSummary } from '@/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const stats = reactive({
  finishedToday: 0,
  pendingCheckCount: 0
})

const load = async () => {
  try {
    const doctorId = userStore.doctorId || 1
    const res = await getDoctorDashboardSummary(doctorId)
    const data = res.data || res
    stats.finishedToday = data.finishedToday || 0
    stats.pendingCheckCount = data.pendingCheckCount || 0
  } catch {
    showToast('排班数据加载失败')
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.schedule-page {
  padding: 12px;
}
.panel,
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}
.page-subtitle {
  margin-top: 8px;
  color: #64748b;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin: 12px 0;
}
.stat-card strong {
  display: block;
  font-size: 26px;
  color: #1677ff;
}
.stat-card span {
  color: #64748b;
}
.timeline-panel {
  display: grid;
  gap: 14px;
}
.time-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
