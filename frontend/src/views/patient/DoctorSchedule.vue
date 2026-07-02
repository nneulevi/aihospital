<!-- src/views/patient/DoctorSchedule.vue -->
<template>
  <div class="doctor-schedule-page">
    <van-nav-bar title="出诊查询" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 搜索 -->
    <van-search
        v-model="keyword"
        placeholder="搜索科室或医生姓名"
        shape="round"
        background="transparent"
    />

    <!-- 科室列表 -->
    <div v-if="!selectedDeptId" class="dept-list">
      <div
          v-for="dept in filteredDepts"
          :key="dept.id"
          class="dept-item"
          @click="selectDept(dept)"
      >
        <div class="dept-icon">{{ dept.icon || '🏥' }}</div>
        <div class="dept-info">
          <div class="dept-name">{{ dept.name }}</div>
          <div class="dept-desc">{{ dept.description || '点击查看医生排班' }}</div>
        </div>
        <van-icon name="arrow" />
      </div>
      <div v-if="loadingDepts" class="loading-state">
        <van-loading size="32px" /><p>加载科室中...</p>
      </div>
      <div v-if="!loadingDepts && departments.length === 0" class="empty-state">
        <van-icon name="medal-o" size="48" />
        <p>暂无科室数据</p>
      </div>
    </div>

    <!-- 医生排班 -->
    <div v-else class="schedule-content">
      <div class="dept-breadcrumb">
        <span class="breadcrumb-text">{{ selectedDeptName }}</span>
        <span class="breadcrumb-back" @click="selectedDeptId = 0; selectedDeptName = ''">重新选择</span>
      </div>

      <!-- 日期选择 -->
      <div class="date-selector">
        <div
            v-for="date in dateList"
            :key="date.value"
            class="date-item"
            :class="{ active: selectedDate === date.value }"
            @click="selectDate(date.value)"
        >
          <div class="date-week">{{ date.week }}</div>
          <div class="date-day">{{ date.day }}</div>
        </div>
      </div>

      <!-- 医生列表 -->
      <div class="doctor-list">
        <div
            v-for="doc in filteredDoctors"
            :key="doc.doctorId"
            class="doctor-card"
        >
          <div class="doctor-avatar">
            <van-icon name="doctor-o" size="36" color="#4CAF50" />
          </div>
          <div class="doctor-info">
            <div class="doctor-name">{{ doc.doctorName }}</div>
            <div class="doctor-title">{{ doc.titleLevel }}</div>
            <div class="doctor-dept">{{ doc.deptName }}</div>
            <div class="doctor-schedule">
              <span class="slot-tag">{{ doc.noon === 'MORNING' ? '上午' : '下午' }}</span>
              <span class="quota-tag">余号 {{ doc.remainingQuota || 0 }}</span>
            </div>
          </div>
          <div class="doctor-right">
            <div class="doctor-fee">¥{{ doc.registFee || 50 }}</div>
          </div>
        </div>
        <div v-if="loadingDoctors" class="loading-state">
          <van-loading size="32px" /><p>加载中...</p>
        </div>
        <div v-else-if="filteredDoctors.length === 0" class="empty-state">
          <van-icon name="doctor-o" size="64" color="#C4C4D6" />
          <p>暂无出诊医生</p>
          <span class="empty-desc">请选择其他日期或调整搜索条件</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import dayjs from 'dayjs'
import { listDepartments, getDoctors } from '@/api'
import type { DeptListVO, DoctorListVO } from '@/api/model'

const router = useRouter()

const keyword = ref('')
const selectedDeptId = ref(0)
const selectedDeptName = ref('')
const selectedDate = ref('')
const departments = ref<DeptListVO[]>([])
const doctorList = ref<DoctorListVO[]>([])
const loadingDepts = ref(false)
const loadingDoctors = ref(false)

// 日期列表（未来7天）
const dateList = computed(() => {
  const dates = []
  for (let i = 0; i < 7; i++) {
    const date = dayjs().add(i, 'day')
    dates.push({
      value: date.format('YYYY-MM-DD'),
      week: date.format('ddd'),
      day: date.format('DD')
    })
  }
  return dates
})

// 筛选科室（按科室名称）
const filteredDepts = computed(() => {
  if (!keyword.value) return departments.value
  return departments.value.filter(d =>
      (d.name || '').includes(keyword.value)
  )
})

// 筛选医生（按医生名称前端模糊查询）
const filteredDoctors = computed(() => {
  if (!keyword.value) return doctorList.value
  const kw = keyword.value.trim()
  return doctorList.value.filter(d =>
      (d.doctorName || '').includes(kw)
  )
})

// 加载科室
const loadDepartments = async () => {
  loadingDepts.value = true
  try {
    const res = await listDepartments() as DeptListVO[]
    departments.value = res.map(d => ({
      ...d,
      id: d.id || 0,
      icon: d.icon || '🏥',
      description: d.description || '点击查看医生排班'
    }))
  } catch (error) {
    showToast('加载科室失败')
  } finally {
    loadingDepts.value = false
  }
}

// 选择科室
const selectDept = (dept: DeptListVO) => {
  selectedDeptId.value = dept.id || 0
  selectedDeptName.value = dept.name || ''
  keyword.value = '' // 清空搜索，切换到医生列表
  selectedDate.value = dateList.value[0]?.value || dayjs().format('YYYY-MM-DD')
  loadDoctors()
}

// 选择日期
const selectDate = (date: string) => {
  selectedDate.value = date
  loadDoctors()
}

// 加载医生排班
const loadDoctors = async () => {
  if (!selectedDeptId.value || !selectedDate.value) return

  loadingDoctors.value = true
  showLoadingToast({ message: '加载中...', forbidClick: true })
  doctorList.value = []

  try {
    const params = {
      deptId: selectedDeptId.value,
      visitDate: selectedDate.value,
      pageNum: 1,
      pageSize: 100
    }
    const res = await getDoctors(params) as any
    doctorList.value = res?.records || res || []
  } catch (error) {
    showToast('加载医生排班失败')
    doctorList.value = []
  } finally {
    loadingDoctors.value = false
    closeToast()
  }
}

onMounted(() => {
  loadDepartments()
})
</script>

<style lang="scss" scoped>
.doctor-schedule-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}

.dept-list {
  padding: 0 16px;
}

.dept-item {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  &:active { transform: scale(0.98); }
}

.dept-icon {
  font-size: 32px;
  width: 48px;
  text-align: center;
}

.dept-info {
  flex: 1;
  .dept-name { font-size: 16px; font-weight: 500; color: #1A1A2E; }
  .dept-desc { font-size: 13px; color: #6B6B7E; margin-top: 2px; }
}

.dept-breadcrumb {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  margin: 0 16px 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .breadcrumb-text { font-size: 15px; font-weight: 500; color: #1A1A2E; }
  .breadcrumb-back { font-size: 13px; color: #4CAF50; cursor: pointer; }
}

.date-selector {
  display: flex;
  gap: 8px;
  padding: 0 16px 12px;
  overflow-x: auto;
  &::-webkit-scrollbar { height: 0; }
}

.date-item {
  flex-shrink: 0;
  width: 48px;
  text-align: center;
  padding: 8px 4px;
  border-radius: 10px;
  background: white;
  cursor: pointer;
  .date-week { font-size: 12px; color: #6B6B7E; }
  .date-day { font-size: 18px; font-weight: 600; color: #1A1A2E; }
  &.active {
    background: #4CAF50;
    .date-week, .date-day { color: white; }
  }
}

.doctor-list {
  padding: 0 16px;
}

.doctor-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 10px;
  display: flex;
  gap: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.doctor-avatar {
  width: 52px;
  height: 52px;
  background: #E8F5E9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.doctor-info {
  flex: 1;
  .doctor-name { font-size: 16px; font-weight: 600; color: #1A1A2E; }
  .doctor-title { font-size: 13px; color: #4CAF50; }
  .doctor-dept { font-size: 13px; color: #6B6B7E; }
  .doctor-schedule {
    display: flex;
    gap: 6px;
    margin-top: 4px;
    .slot-tag {
      font-size: 12px;
      color: #4CAF50;
      background: #E8F5E9;
      padding: 2px 10px;
      border-radius: 10px;
    }
    .quota-tag {
      font-size: 12px;
      color: #FF9800;
      background: #FFF3E0;
      padding: 2px 10px;
      border-radius: 10px;
    }
  }
}

.doctor-right {
  text-align: right;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-end;
  .doctor-fee {
    font-size: 18px;
    font-weight: 700;
    color: #E76F51;
  }
}

.loading-state, .empty-state {
  text-align: center;
  padding: 40px 0;
  color: #6B6B7E;
  p { margin-top: 12px; }
}

.empty-desc {
  font-size: 13px;
  color: #6B6B7E;
}
</style>