<template>
  <div class="admin-page">
    <div class="summary-card">
      <div>
        <div class="page-title">医生统计</div>
        <div class="page-subtitle">按医生维度展示今日挂号、在诊患者、已完成接诊和待处理检查。</div>
      </div>
      <van-button size="small" plain type="primary" :loading="loading" @click="load">刷新</van-button>
    </div>

    <div class="doctor-list">
      <div v-for="item in doctors" :key="item.doctorId" class="doctor-card">
        <div class="doctor-header">
          <div>
            <div class="doctor-name">{{ item.doctorName }}</div>
            <div class="doctor-meta">{{ item.deptName || '未分配科室' }} · {{ item.titleLevel || '医生' }}</div>
          </div>
          <van-tag type="primary">ID {{ item.doctorId }}</van-tag>
        </div>
        <div class="stats-grid">
          <div>
            <strong>{{ item.todayRegistrations || 0 }}</strong>
            <span>今日挂号</span>
          </div>
          <div>
            <strong>{{ item.activePatients || 0 }}</strong>
            <span>在诊患者</span>
          </div>
          <div>
            <strong>{{ item.finishedToday || 0 }}</strong>
            <span>今日完成</span>
          </div>
          <div>
            <strong>{{ item.pendingChecks || 0 }}</strong>
            <span>待处理检查</span>
          </div>
        </div>
      </div>
      <van-empty v-if="!loading && doctors.length === 0" description="暂无医生统计数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import { getAdminDoctorStats, type DoctorStatsVO } from '@/api'

const loading = ref(false)
const doctors = ref<DoctorStatsVO[]>([])

const load = async () => {
  loading.value = true
  try {
    const res = await getAdminDoctorStats()
    doctors.value = (res.data || res || []) as DoctorStatsVO[]
  } catch {
    showToast('医生统计加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.admin-page {
  padding: 12px;
}
.summary-card,
.doctor-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
}
.summary-card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}
.page-subtitle {
  margin-top: 6px;
  color: #64748b;
  line-height: 1.6;
}
.doctor-list {
  display: grid;
  gap: 12px;
}
.doctor-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.doctor-name {
  font-weight: 700;
  color: #1f2937;
}
.doctor-meta {
  color: #64748b;
  font-size: 13px;
  margin-top: 4px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-top: 14px;
}
.stats-grid div {
  background: #f8fafc;
  border-radius: 10px;
  padding: 12px;
}
.stats-grid strong {
  display: block;
  color: #1677ff;
  font-size: 20px;
}
.stats-grid span {
  color: #64748b;
  font-size: 12px;
}
</style>