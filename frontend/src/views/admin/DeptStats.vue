<template>
  <div class="admin-page">
    <div class="summary-card">
      <div>
        <div class="page-title">科室统计</div>
        <div class="page-subtitle">按科室展示医生数、今日挂号、在诊患者、号源额度和待处理检查。</div>
      </div>
      <van-button size="small" plain type="primary" :loading="loading" @click="load">刷新</van-button>
    </div>

    <div class="dept-list">
      <div class="dept-card" v-for="item in departments" :key="item.deptId">
        <div class="dept-header">
          <div>
            <div class="dept-name">{{ item.deptName }}</div>
            <div class="dept-meta">{{ item.deptType || '普通科室' }}</div>
          </div>
          <van-tag :type="Number(item.pendingChecks || 0) > 0 ? 'warning' : 'success'">
            {{ Number(item.pendingChecks || 0) > 0 ? '待处理' : '平稳' }}
          </van-tag>
        </div>
        <div class="dept-metrics">
          <div>
            <strong>{{ item.doctorCount || 0 }}</strong>
            <span>医生数</span>
          </div>
          <div>
            <strong>{{ item.todayRegistrations || 0 }}</strong>
            <span>今日挂号</span>
          </div>
          <div>
            <strong>{{ item.activePatients || 0 }}</strong>
            <span>在诊患者</span>
          </div>
          <div>
            <strong>{{ item.scheduleQuota || 0 }}</strong>
            <span>今日号源</span>
          </div>
          <div>
            <strong>{{ item.pendingChecks || 0 }}</strong>
            <span>待处理检查</span>
          </div>
        </div>
      </div>
      <van-empty v-if="!loading && departments.length === 0" description="暂无科室统计数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import { getAdminDepartmentStats, type DepartmentStatsVO } from '@/api'

const loading = ref(false)
const departments = ref<DepartmentStatsVO[]>([])

const load = async () => {
  loading.value = true
  try {
    const res = await getAdminDepartmentStats()
    departments.value = (res.data || res || []) as DepartmentStatsVO[]
  } catch {
    showToast('科室统计加载失败')
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
.dept-card {
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
.dept-list {
  display: grid;
  gap: 12px;
}
.dept-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.dept-name {
  font-weight: 700;
  color: #1f2937;
}
.dept-meta {
  color: #64748b;
  font-size: 13px;
  margin-top: 4px;
}
.dept-metrics {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  margin-top: 14px;
  gap: 10px;
}
.dept-metrics div {
  background: #f8fafc;
  border-radius: 10px;
  padding: 12px;
}
.dept-metrics strong {
  display: block;
  color: #1677ff;
  font-size: 20px;
}
.dept-metrics span {
  color: #64748b;
  font-size: 12px;
}
</style>