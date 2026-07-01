<!-- src/views/patient/DoctorSchedule.vue -->
<template>
  <div class="doctor-schedule-page">
    <van-nav-bar title="出诊查询" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 搜索 -->
    <van-search
        v-model="keyword"
        placeholder="搜索医生姓名或科室"
        shape="round"
        background="transparent"
        @search="onSearch"
    />

    <!-- 科室筛选 -->
    <div class="dept-filter">
      <span
          v-for="dept in deptFilters"
          :key="dept.key"
          class="filter-tag"
          :class="{ active: activeDept === dept.key }"
          @click="activeDept = dept.key"
      >
        {{ dept.label }}
      </span>
    </div>

    <!-- 日期选择 -->
    <div class="date-selector">
      <div
          v-for="date in dateList"
          :key="date.value"
          class="date-item"
          :class="{ active: selectedDate === date.value }"
          @click="selectedDate = date.value"
      >
        <div class="date-week">{{ date.week }}</div>
        <div class="date-day">{{ date.day }}</div>
      </div>
    </div>

    <!-- 医生列表 -->
    <div class="doctor-list">
      <div
          v-for="doc in filteredDoctors"
          :key="doc.id"
          class="doctor-card"
          @click="viewDoctor(doc)"
      >
        <div class="doctor-avatar">
          <van-icon name="doctor-o" size="36" color="#4CAF50" />
        </div>
        <div class="doctor-info">
          <div class="doctor-name">{{ doc.name }}</div>
          <div class="doctor-title">{{ doc.title }}</div>
          <div class="doctor-dept">{{ doc.dept }}</div>
          <div class="doctor-schedule">
            <span v-for="slot in doc.slots" :key="slot" class="slot-tag">
              {{ slot }}
            </span>
          </div>
        </div>
        <div class="doctor-right">
          <div class="doctor-fee">¥{{ doc.fee }}</div>
          <van-button size="small" type="primary" round @click.stop="goToRegister(doc)">
            挂号
          </van-button>
        </div>
      </div>

      <div v-if="filteredDoctors.length === 0" class="empty-state">
        <van-icon name="doctor-o" size="64" color="#C4C4D6" />
        <p>暂无出诊医生</p>
        <span class="empty-desc">请选择其他日期或科室查询</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()

const keyword = ref('')
const activeDept = ref('all')
const selectedDate = ref('')

const deptFilters = [
  { key: 'all', label: '全部' },
  { key: '神经内科', label: '神经内科' },
  { key: '心血管内科', label: '心血管内科' },
  { key: '呼吸内科', label: '呼吸内科' },
  { key: '消化内科', label: '消化内科' },
  { key: '骨科', label: '骨科' }
]

const doctors = ref([
  { id: 1, name: '张敏', title: '主任医师', dept: '呼吸内科', fee: 100, slots: ['上午', '下午'] },
  { id: 2, name: '李为民', title: '副主任医师', dept: '心血管内科', fee: 80, slots: ['上午'] },
  { id: 3, name: '王建国', title: '主任医师', dept: '神经内科', fee: 100, slots: ['下午'] },
  { id: 4, name: '孙伟', title: '副主任医师', dept: '心血管内科', fee: 80, slots: ['上午', '下午'] },
  { id: 5, name: '陈明', title: '主治医师', dept: '消化内科', fee: 50, slots: ['上午'] },
  { id: 6, name: '吴刚', title: '主任医师', dept: '骨科', fee: 100, slots: ['上午', '下午'] },
  { id: 7, name: '郑红', title: '主治医师', dept: '呼吸内科', fee: 50, slots: ['下午'] },
  { id: 8, name: '刘芳', title: '副主任医师', dept: '神经内科', fee: 80, slots: ['上午'] }
])

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

const filteredDoctors = computed(() => {
  let result = doctors.value
  if (activeDept.value !== 'all') {
    result = result.filter(d => d.dept === activeDept.value)
  }
  if (keyword.value.trim()) {
    result = result.filter(d =>
        d.name.includes(keyword.value.trim()) ||
        d.dept.includes(keyword.value.trim())
    )
  }
  return result
})

const onSearch = () => {
  // 由 computed 处理
}

const viewDoctor = (doc: any) => {
  showToast(`${doc.name} ${doc.title}`)
}

const goToRegister = (doc: any) => {
  router.push({
    path: '/patient/appointment',
    query: {
      doctorId: String(doc.id),
      deptName: doc.dept
    }
  })
}

onMounted(() => {
  if (dateList.value.length > 0) {
    selectedDate.value = dateList.value[0].value
  }
})
</script>

<style lang="scss" scoped>
.doctor-schedule-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}

.dept-filter {
  display: flex;
  gap: 8px;
  padding: 0 16px 12px;
  overflow-x: auto;
  &::-webkit-scrollbar { height: 0; }
}

.filter-tag {
  flex-shrink: 0;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  color: #6B6B7E;
  background: white;
  cursor: pointer;
  &.active {
    background: #4CAF50;
    color: white;
  }
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
  cursor: pointer;
  &:active { transform: scale(0.98); }
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
  }
}

.doctor-right {
  text-align: right;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
  .doctor-fee {
    font-size: 18px;
    font-weight: 700;
    color: #E76F51;
  }
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
  }
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #C4C4D6;
  p { font-size: 16px; color: #6B6B7E; margin-top: 12px; }
  .empty-desc { font-size: 13px; color: #6B6B7E; }
}
</style>