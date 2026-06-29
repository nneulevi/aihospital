<!-- src/views/admin/DoctorStats.vue -->
<template>
  <div class="doctor-stats">
    <div class="page-header">
      <van-icon name="arrow-left" @click="goBack" />
      <span class="title">📊 医生统计</span>
      <van-button size="small" round type="primary" plain @click="loadStats" :loading="loading">刷新</van-button>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <van-field v-model="keyword" placeholder="搜索医生姓名" left-icon="search" />
      <van-dropdown-menu>
        <van-dropdown-item v-model="filterDept" :options="deptFilterOptions" />
      </van-dropdown-menu>
    </div>

    <!-- 汇总 -->
    <div class="summary-row">
      <div class="summary-item">
        <span class="num">{{ doctorList.length }}</span>
        <span class="label">在职医生</span>
      </div>
      <div class="summary-item">
        <span class="num">{{ totalVisits }}</span>
        <span class="label">总接诊</span>
      </div>
      <div class="summary-item">
        <span class="num">{{ avgVisits }}</span>
        <span class="label">平均接诊</span>
      </div>
      <div class="summary-item">
        <span class="num">{{ avgRevisitRate }}%</span>
        <span class="label">平均复查率</span>
      </div>
    </div>

    <!-- 列表 -->
    <div class="list-card">
      <div
          v-for="doc in filteredDoctors"
          :key="doc.id"
          class="doctor-item"
          @click="showDetail(doc)"
      >
        <div class="doc-avatar">
          <van-icon name="user-circle-o" size="36" color="#005B96" />
        </div>
        <div class="doc-info">
          <div class="doc-name">{{ doc.name }}</div>
          <div class="doc-dept">{{ doc.dept }} | {{ doc.title || '未设置职称' }}</div>
        </div>
        <div class="doc-stats">
          <div class="stat-row">
            <span class="stat-num">{{ doc.visits || 0 }}</span>
            <span class="stat-label">接诊</span>
          </div>
          <div class="stat-row">
            <span class="stat-num">{{ doc.revisitRate || 0 }}%</span>
            <span class="stat-label">复查率</span>
          </div>
        </div>
        <van-icon name="arrow" class="arrow" />
      </div>

      <div v-if="filteredDoctors.length === 0 && !loading" class="empty-state">
        <van-icon name="search" size="48" color="#BDC3C7" />
        <p>未找到匹配医生</p>
      </div>
      <div v-if="loading" class="loading-state">
        <van-loading size="24" /> 加载中...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getDoctorStats } from '@/api'
import type { DoctorStatsVO } from '@/api/model'

const router = useRouter()
const loading = ref(false)
const keyword = ref('')
const filterDept = ref('')
const doctorList = ref<DoctorStatsVO[]>([])

const deptFilterOptions = computed(() => {
  const depts = [...new Set(doctorList.value.map(d => d.dept).filter(Boolean))]
  return [
    { text: '全部科室', value: '' },
    ...depts.map(d => ({ text: d, value: d }))
  ]
})

const filteredDoctors = computed(() => {
  return doctorList.value.filter(d => {
    const matchName = d.name?.includes(keyword.value) ?? true
    const matchDept = !filterDept.value || d.dept === filterDept.value
    return matchName && matchDept
  })
})

const totalVisits = computed(() => {
  return doctorList.value.reduce((sum, d) => sum + (d.visits || 0), 0)
})

const avgVisits = computed(() => {
  if (doctorList.value.length === 0) return 0
  return Math.round(totalVisits.value / doctorList.value.length)
})

const avgRevisitRate = computed(() => {
  if (doctorList.value.length === 0) return 0
  const sum = doctorList.value.reduce((s, d) => s + (d.revisitRate || 0), 0)
  return Math.round(sum / doctorList.value.length)
})

const loadStats = async () => {
  loading.value = true
  try {
    const res = await getDoctorStats()
    doctorList.value = (res as DoctorStatsVO[]) || []
  } catch {
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

const showDetail = (doc: DoctorStatsVO) => {
  showToast(`查看 ${doc.name} 详细数据`)
}

const goBack = () => router.back()

onMounted(loadStats)
</script>

<style lang="scss" scoped>
.doctor-stats {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 12px;
  padding-bottom: 20px;
}
.page-header {
  display: flex;
  align-items: center;
  background: white;
  padding: 14px 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .van-icon { font-size: 22px; cursor: pointer; color: #2C3E50; }
  .title { flex: 1; margin-left: 12px; font-size: 17px; font-weight: 600; color: #2C3E50; }
}
.filter-bar {
  display: flex; gap: 8px; margin-bottom: 12px;
  :deep(.van-field) { flex: 1; background: white; border-radius: 8px; padding: 0 12px; }
  :deep(.van-dropdown-menu) {
    flex-shrink: 0;
    .van-dropdown-menu__bar { background: white; border-radius: 8px; box-shadow: none; }
  }
}
.summary-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px;
}
.summary-item {
  background: white; border-radius: 10px; padding: 12px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .num { display: block; font-size: 20px; font-weight: 700; color: #005B96; }
  .label { font-size: 11px; color: #7F8C8D; }
}
.list-card {
  background: white; border-radius: 12px; padding: 8px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.doctor-item {
  display: flex; align-items: center; padding: 12px 16px; border-bottom: 1px solid #F5F5F5; cursor: pointer;
  &:last-child { border-bottom: none; }
  &:active { background: #F5F7FA; }
  .doc-avatar { flex-shrink: 0; margin-right: 12px; }
  .doc-info { flex: 1; .doc-name { font-size: 15px; font-weight: 600; color: #2C3E50; } .doc-dept { font-size: 12px; color: #7F8C8D; } }
  .doc-stats { display: flex; gap: 16px; margin-right: 8px;
    .stat-row { text-align: center; .stat-num { display: block; font-size: 14px; font-weight: 600; color: #2C3E50; } .stat-label { font-size: 10px; color: #BDC3C7; } }
  }
  .arrow { color: #BDC3C7; font-size: 14px; }
}
.empty-state { text-align: center; padding: 40px 0; color: #BDC3C7; }
.loading-state { text-align: center; padding: 40px 0; color: #7F8C8D; display: flex; justify-content: center; align-items: center; gap: 8px; }
</style>