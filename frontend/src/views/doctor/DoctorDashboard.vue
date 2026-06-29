<!-- src/views/doctor/DoctorDashboard.vue -->
<template>
  <div class="doctor-dashboard">
    <!-- 欢迎语 -->
    <div class="welcome-section">
      <div class="greeting">👋 您好，{{ doctorName }}</div>
      <div class="date">{{ today }}</div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-bar">
      <div class="stat-item" @click="switchTab('pending')">
        <div class="stat-num">{{ pendingList.length }}</div>
        <div class="stat-label">待诊</div>
        <van-tag v-if="pendingList.length > 0" type="danger" size="mini" class="badge">新</van-tag>
      </div>
      <div class="stat-item" @click="switchTab('consulting')">
        <div class="stat-num">{{ consultingList.length }}</div>
        <div class="stat-label">就诊中</div>
        <van-tag v-if="consultingList.length > 0" type="warning" size="mini" class="badge">进行中</van-tag>
      </div>
      <div class="stat-item" @click="switchTab('finished')">
        <div class="stat-num">{{ finishedToday }}</div>
        <div class="stat-label">今日已接诊</div>
      </div>
    </div>

    <!-- 患者列表 -->
    <van-tabs v-model:active="listTab" class="patient-tabs" @change="onTabChange">
      <van-tab title="待诊队列" name="pending">
        <div class="patient-list">
          <van-pull-refresh v-model="refreshing" @refresh="loadPatients">
            <div v-for="p in pendingList" :key="p.registerId" class="patient-card" @click="goToVisit(p)">
              <div class="patient-header">
                <div class="patient-name">{{ p.patientName }}</div>
                <van-tag type="primary" size="small">待诊</van-tag>
              </div>
              <div class="patient-info">
                <span>{{ p.gender || '男' }}</span>
                <span>{{ p.age || 35 }}岁</span>
                <span>病历号: {{ p.caseNumber || 'HN202600001' }}</span>
              </div>
              <div class="patient-time">
                <van-icon name="clock-o" />
                {{ formatTime(p.registrationTime) }} {{ p.noon === 'MORNING' ? '上午' : '下午' }}
                <span class="wait-time" v-if="p.waitTime">等待 {{ p.waitTime }}min</span>
              </div>
              <div class="patient-tags" v-if="p.tags && p.tags.length">
                <van-tag v-for="tag in p.tags" :key="tag" size="mini" plain>{{ tag }}</van-tag>
              </div>
            </div>
            <div v-if="pendingList.length === 0" class="empty-state">
              <van-icon name="smile-o" size="48" color="#C4B8A8" />
              <p>暂无待诊患者</p>
            </div>
          </van-pull-refresh>
        </div>
      </van-tab>

      <van-tab title="就诊中" name="consulting">
        <div class="patient-list">
          <div v-for="p in consultingList" :key="p.registerId" class="patient-card active" @click="goToVisit(p)">
            <div class="patient-header">
              <div class="patient-name">{{ p.patientName }}</div>
              <van-tag type="warning" size="small">就诊中</van-tag>
            </div>
            <div class="patient-info">
              <span>{{ p.gender || '女' }}</span>
              <span>{{ p.age || 42 }}岁</span>
              <span>病历号: {{ p.caseNumber || 'HN202600002' }}</span>
            </div>
            <div class="patient-time">
              <van-icon name="clock-o" /> {{ formatTime(p.registrationTime) }}
            </div>
            <div class="progress-bar" v-if="p.progress">
              <span class="progress-label">诊疗进度</span>
              <van-progress :percentage="p.progress" stroke-width="6" color="#5E60CE" />
            </div>
          </div>
          <div v-if="consultingList.length === 0" class="empty-state">
            <van-icon name="smile-o" size="48" color="#C4B8A8" />
            <p>暂无就诊中患者</p>
          </div>
        </div>
      </van-tab>

      <van-tab title="今日已完成" name="finished">
        <div class="patient-list">
          <div v-for="p in finishedList" :key="p.registerId" class="patient-card done">
            <div class="patient-header">
              <div class="patient-name">{{ p.patientName }}</div>
              <van-tag type="success" size="small">已完成</van-tag>
            </div>
            <div class="patient-info">
              <span>{{ p.gender || '男' }}</span>
              <span>{{ p.age || 28 }}岁</span>
            </div>
            <div class="patient-time">
              <van-icon name="clock-o" /> {{ formatTime(p.registrationTime) }}
              <span class="duration" v-if="p.duration">诊疗 {{ p.duration }}min</span>
            </div>
          </div>
          <div v-if="finishedList.length === 0" class="empty-state">
            <van-icon name="smile-o" size="48" color="#C4B8A8" />
            <p>今日暂无已完成</p>
          </div>
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()
const listTab = ref('pending')
const refreshing = ref(false)

// 模拟医生信息
const doctorName = ref('张明医生')

// 模拟数据
const mockPatients = [
  {
    registerId: 1001,
    patientName: '王建国',
    gender: '男',
    age: 58,
    caseNumber: 'HN202600001',
    registrationTime: '2026-06-24 08:30:00',
    noon: 'MORNING',
    visitState: 'REGISTERED',
    tags: ['复诊', '高血压'],
    waitTime: 5
  },
  {
    registerId: 1002,
    patientName: '李秀英',
    gender: '女',
    age: 42,
    caseNumber: 'HN202600002',
    registrationTime: '2026-06-24 09:15:00',
    noon: 'MORNING',
    visitState: 'REGISTERED',
    tags: ['首诊', '咳嗽'],
    waitTime: 15
  },
  {
    registerId: 1003,
    patientName: '张伟',
    gender: '男',
    age: 35,
    caseNumber: 'HN202600003',
    registrationTime: '2026-06-24 08:45:00',
    noon: 'MORNING',
    visitState: 'CONSULTING',
    progress: 60
  },
  {
    registerId: 1004,
    patientName: '赵丽华',
    gender: '女',
    age: 67,
    caseNumber: 'HN202600004',
    registrationTime: '2026-06-24 07:50:00',
    noon: 'MORNING',
    visitState: 'FINISHED',
    duration: 25
  },
  {
    registerId: 1005,
    patientName: '孙明',
    gender: '男',
    age: 28,
    caseNumber: 'HN202600005',
    registrationTime: '2026-06-24 09:30:00',
    noon: 'MORNING',
    visitState: 'FINISHED',
    duration: 18
  }
]

const allPatients = ref(mockPatients)
const finishedToday = computed(() => finishedList.value.length)

const pendingList = ref([])
const consultingList = ref([])
const finishedList = ref([])

const loadPatients = async () => {
  refreshing.value = true
  // 模拟网络请求
  await new Promise(resolve => setTimeout(resolve, 500))

  pendingList.value = allPatients.value.filter((p: any) => p.visitState === 'REGISTERED')
  consultingList.value = allPatients.value.filter((p: any) => p.visitState === 'CONSULTING')
  finishedList.value = allPatients.value.filter((p: any) => p.visitState === 'FINISHED')

  refreshing.value = false
}

const switchTab = (tab: string) => {
  listTab.value = tab
}

const onTabChange = () => {
  // Tab切换时刷新数据
  loadPatients()
}

const goToVisit = (patient: any) => {
  router.push({
    name: 'PatientVisit',
    query: {
      registerId: String(patient.registerId),
      name: patient.patientName,
      from: 'dashboard'
    }
  })
}

const formatTime = (time?: string) => time ? dayjs(time).format('HH:mm') : ''

const today = computed(() => dayjs().format('YYYY年MM月DD日 dddd'))

onMounted(() => {
  loadPatients()
})
</script>

<style lang="scss" scoped>
.doctor-dashboard {
  padding: 12px;
  padding-bottom: 20px;
}

.welcome-section {
  background: linear-gradient(135deg, #005B96 0%, #0077B6 100%);
  margin: -12px -12px 12px -12px;
  padding: 20px 16px 16px;
  color: white;

  .greeting {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 4px;
  }

  .date {
    font-size: 14px;
    opacity: 0.8;
  }
}

.stats-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  margin-top: 8px;
}

.stat-item {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  position: relative;
  transition: all 0.3s;

  &:active {
    transform: scale(0.95);
  }

  .stat-num {
    font-size: 24px;
    font-weight: 700;
    color: #005B96;
  }

  .stat-label {
    font-size: 12px;
    color: #8B7A6B;
    margin-top: 4px;
  }

  .badge {
    position: absolute;
    top: 8px;
    right: 8px;
  }
}

.patient-tabs :deep(.van-tabs__line) {
  background-color: #005B96;
}

.patient-list {
  padding: 8px 0;
}

.patient-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.3s;

  &:active {
    transform: scale(0.98);
  }

  &.active {
    border-left: 4px solid #F4A261;
  }

  &.done {
    border-left: 4px solid #8CB369;
    opacity: 0.8;
  }
}

.patient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;

  .patient-name {
    font-size: 16px;
    font-weight: 600;
    color: #2C3E50;
  }
}

.patient-info {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #7F8C8D;
  margin-bottom: 8px;
}

.patient-time {
  font-size: 12px;
  color: #95A5A6;
  display: flex;
  align-items: center;
  gap: 4px;

  .wait-time {
    color: #E74C3C;
    margin-left: 8px;
  }

  .duration {
    color: #27AE60;
    margin-left: 8px;
  }
}

.patient-tags {
  margin-top: 8px;
  display: flex;
  gap: 6px;
}

.progress-bar {
  margin-top: 8px;

  .progress-label {
    font-size: 12px;
    color: #7F8C8D;
    margin-bottom: 4px;
    display: block;
  }
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #BDC3C7;
}
</style>