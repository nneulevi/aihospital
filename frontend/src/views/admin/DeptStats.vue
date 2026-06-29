<!-- src/views/admin/DeptStats.vue -->
<template>
  <div class="dept-stats">
    <div class="page-header">
      <van-icon name="arrow-left" @click="goBack" />
      <span class="title">🏥 部门统计</span>
      <van-button size="small" round type="primary" plain @click="loadStats" :loading="loading">刷新</van-button>
    </div>

    <!-- 汇总 -->
    <div class="summary-row">
      <div class="summary-item">
        <span class="num">{{ deptList.length }}</span>
        <span class="label">科室总数</span>
      </div>
      <div class="summary-item">
        <span class="num">{{ totalDoctors }}</span>
        <span class="label">医生总数</span>
      </div>
      <div class="summary-item">
        <span class="num">{{ totalVisits }}</span>
        <span class="label">总接诊</span>
      </div>
      <div class="summary-item">
        <span class="num">{{ totalPatients }}</span>
        <span class="label">总患者</span>
      </div>
    </div>

    <!-- 部门列表 -->
    <div class="list-card">
      <div
          v-for="dept in deptList"
          :key="dept.id"
          class="dept-item"
          @click="showDetail(dept)"
      >
        <div class="dept-header">
          <div class="dept-name">
            <span class="icon">{{ dept.icon || '🏥' }}</span>
            {{ dept.name }}
          </div>
          <van-tag :type="getStatusType(dept.status)" size="small">
            {{ dept.status || '正常' }}
          </van-tag>
        </div>

        <div class="dept-stats-grid">
          <div class="stat-cell">
            <span class="stat-num">{{ dept.doctorCount || 0 }}</span>
            <span class="stat-label">👨‍⚕️ 医生</span>
          </div>
          <div class="stat-cell">
            <span class="stat-num">{{ dept.visits || 0 }}</span>
            <span class="stat-label">📋 接诊</span>
          </div>
          <div class="stat-cell">
            <span class="stat-num">{{ dept.revisitRate || 0 }}%</span>
            <span class="stat-label">🔄 复查率</span>
          </div>
          <div class="stat-cell">
            <span class="stat-num">{{ dept.avgRating || 0 }}</span>
            <span class="stat-label">⭐ 评分</span>
          </div>
        </div>

        <div class="dept-progress">
          <div class="progress-label">
            <span>饱和度</span>
            <span>{{ dept.saturation || 0 }}%</span>
          </div>
          <van-progress
              :percentage="dept.saturation || 0"
              stroke-width="8"
              :color="(dept.saturation || 0) > 80 ? '#E76F51' : (dept.saturation || 0) > 60 ? '#F4A261' : '#27AE60'"
              track-color="#F0F0F0"
          />
        </div>
      </div>

      <div v-if="deptList.length === 0 && !loading" class="empty-state">
        <van-icon name="search" size="48" color="#BDC3C7" />
        <p>暂无部门数据</p>
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
import { getDeptStats } from '@/api'
import type { DeptStatsVO } from '@/api/model'

const router = useRouter()
const loading = ref(false)
const deptList = ref<DeptStatsVO[]>([])

const totalDoctors = computed(() => {
  return deptList.value.reduce((sum, d) => sum + (d.doctorCount || 0), 0)
})

const totalVisits = computed(() => {
  return deptList.value.reduce((sum, d) => sum + (d.visits || 0), 0)
})

const totalPatients = computed(() => {
  return Math.round(totalVisits.value / 1.8) || 0
})

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    '正常': 'success',
    '繁忙': 'warning',
    '饱和': 'danger'
  }
  return map[status || ''] || 'default'
}

const loadStats = async () => {
  loading.value = true
  try {
    const res = await getDeptStats()
    deptList.value = (res as DeptStatsVO[]) || []
  } catch {
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

const showDetail = (dept: DeptStatsVO) => {
  showToast(`查看 ${dept.name} 详细数据`)
}

const goBack = () => router.back()

onMounted(loadStats)
</script>

<style lang="scss" scoped>
.dept-stats {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 12px;
  padding-bottom: 20px;
}
.page-header {
  display: flex; align-items: center; background: white; padding: 14px 16px; border-radius: 12px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .van-icon { font-size: 22px; cursor: pointer; color: #2C3E50; }
  .title { flex: 1; margin-left: 12px; font-size: 17px; font-weight: 600; color: #2C3E50; }
}
.summary-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px;
}
.summary-item {
  background: white; border-radius: 10px; padding: 12px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .num { display: block; font-size: 20px; font-weight: 700; color: #005B96; }
  .label { font-size: 11px; color: #7F8C8D; }
}
.list-card { display: flex; flex-direction: column; gap: 12px; }
.dept-item {
  background: white; border-radius: 12px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); cursor: pointer;
  &:active { transform: scale(0.98); }
}
.dept-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
  .dept-name { font-size: 16px; font-weight: 600; color: #2C3E50; .icon { margin-right: 8px; } }
}
.dept-stats-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px;
}
.stat-cell {
  text-align: center; background: #F8FAFC; border-radius: 6px; padding: 8px 4px;
  .stat-num { display: block; font-size: 16px; font-weight: 600; color: #2C3E50; }
  .stat-label { font-size: 11px; color: #7F8C8D; }
}
.dept-progress {
  .progress-label { display: flex; justify-content: space-between; font-size: 12px; color: #7F8C8D; margin-bottom: 4px; }
}
.empty-state { text-align: center; padding: 40px 0; color: #BDC3C7; }
.loading-state { text-align: center; padding: 40px 0; color: #7F8C8D; display: flex; justify-content: center; align-items: center; gap: 8px; }
</style>