<!-- src/views/patient/QueueQuery.vue -->
<template>
  <div class="queue-page">
    <van-nav-bar title="候诊查询" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 刷新提示 -->
    <div class="refresh-hint">
      <van-icon name="replay" :class="{ spinning: refreshing }" />
      <span>上次更新：{{ lastUpdateTime }}</span>
      <span class="refresh-btn" @click="refreshQueue">刷新</span>
    </div>

    <!-- ===== 当前排队状态 ===== -->
    <div v-if="currentQueue" class="queue-status">
      <div class="status-card">
        <div class="status-left">
          <div class="status-label">当前排队</div>
          <div class="status-number">{{ currentQueue.queueNumber }}</div>
          <div class="status-dept">{{ currentQueue.deptName }}</div>
        </div>
        <div class="status-divider"></div>
        <div class="status-right">
          <div class="status-label">前面还有</div>
          <div class="status-ahead">{{ currentQueue.aheadCount }}</div>
          <div class="status-unit">人</div>
        </div>
      </div>

      <!-- 预估时间 -->
      <div class="estimate-time">
        <van-icon name="clock-o" />
        <span>预计等待约 <strong>{{ estimatedWaitTime }}</strong> 分钟</span>
      </div>

      <!-- 当前叫号 -->
      <div class="calling-info" v-if="currentQueue.currentCalling">
        <span class="calling-label">当前叫号</span>
        <span class="calling-number">{{ currentQueue.currentCalling }}</span>
        <span class="calling-room">→ {{ currentQueue.currentRoom || '诊室' }}</span>
      </div>
    </div>

    <!-- ===== 候诊列表 ===== -->
    <div class="queue-list-section">
      <div class="section-header">
        <span class="section-title">📋 候诊队列</span>
        <span class="section-count">共 {{ queueList.length }} 人</span>
      </div>

      <div class="queue-list">
        <div
            v-for="(item, index) in queueList"
            :key="item.registerId"
            class="queue-item"
            :class="{
            'is-current': item.registerId === currentQueue?.registerId,
            'is-passed': item.status === 'PASSED'
          }"
        >
          <div class="queue-position">
            <span class="position-number">{{ index + 1 }}</span>
          </div>
          <div class="queue-info">
            <div class="queue-name">{{ item.patientName || '患者' }}</div>
            <div class="queue-detail">
              <span>{{ item.deptName }}</span>
              <span>{{ item.doctorName }}</span>
            </div>
          </div>
          <div class="queue-status-tag">
            <van-tag
                :type="item.registerId === currentQueue?.registerId ? 'warning' : 'default'"
                size="small"
            >
              {{ item.registerId === currentQueue?.registerId ? '当前' : '等待中' }}
            </van-tag>
          </div>
        </div>

        <div v-if="queueList.length === 0" class="empty-state">
          <van-icon name="clock-o" size="48" color="#C4C4D6" />
          <p>当前没有候诊患者</p>
        </div>
      </div>
    </div>

    <!-- ===== 科室选择快速查看 ===== -->
    <div class="dept-switcher" v-if="availableDepts.length > 1">
      <span class="switcher-label">切换科室：</span>
      <div class="dept-tags">
        <van-tag
            v-for="dept in availableDepts"
            :key="dept.deptId"
            :type="selectedDeptId === dept.deptId ? 'primary' : 'default'"
            @click="switchDept(dept.deptId)"
        >
          {{ dept.deptName }}
        </van-tag>
      </div>
    </div>

    <!-- 底部提示 -->
    <div class="footer-tip">
      <van-icon name="info-o" />
      <span>数据每30秒自动刷新，请留意叫号</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()

// ============ 状态 ============
const refreshing = ref(false)
const lastUpdateTime = ref('')
const selectedDeptId = ref<number | null>(null)
const currentQueue = ref<any>(null)
const queueList = ref<any[]>([])
const availableDepts = ref<any[]>([])
let refreshTimer: number | null = null

// ============ 模拟数据 ============

// 模拟候诊数据
const mockQueueData = {
  depts: [
    { deptId: 2, deptName: '呼吸内科' },
    { deptId: 4, deptName: '心血管内科' },
    { deptId: 1, deptName: '神经内科' }
  ],
  queues: {
    2: [
      { registerId: 1001, patientName: '张明', deptName: '呼吸内科', doctorName: '张敏', status: 'WAITING' },
      { registerId: 1005, patientName: '李芳', deptName: '呼吸内科', doctorName: '张敏', status: 'WAITING' },
      { registerId: 1006, patientName: '王强', deptName: '呼吸内科', doctorName: '李华', status: 'WAITING' },
      { registerId: 1007, patientName: '刘梅', deptName: '呼吸内科', doctorName: '李华', status: 'WAITING' },
      { registerId: 1008, patientName: '赵磊', deptName: '呼吸内科', doctorName: '张敏', status: 'WAITING' }
    ],
    4: [
      { registerId: 1002, patientName: '张秀兰', deptName: '心血管内科', doctorName: '孙伟', status: 'WAITING' },
      { registerId: 1009, patientName: '周明', deptName: '心血管内科', doctorName: '孙伟', status: 'WAITING' },
      { registerId: 1010, patientName: '吴丽', deptName: '心血管内科', doctorName: '郑红', status: 'WAITING' }
    ],
    1: [
      { registerId: 1003, patientName: '王建国', deptName: '神经内科', doctorName: '王建国', status: 'WAITING' },
      { registerId: 1011, patientName: '陈芳', deptName: '神经内科', doctorName: '李敏', status: 'WAITING' }
    ]
  }
}

// ============ 计算属性 ============

const estimatedWaitTime = computed(() => {
  if (!currentQueue.value?.aheadCount) return 0
  // 假设每人平均15分钟
  return Math.ceil(currentQueue.value.aheadCount * 15)
})

// ============ 方法 ============

// 加载候诊数据
const loadQueueData = async () => {
  refreshing.value = true

  try {
    await new Promise(resolve => setTimeout(resolve, 400))

    // 设置科室列表
    availableDepts.value = mockQueueData.depts

    // 默认选中第一个科室
    if (!selectedDeptId.value && availableDepts.value.length > 0) {
      selectedDeptId.value = availableDepts.value[0].deptId
    }

    // 获取当前科室的候诊列表
    const deptId = selectedDeptId.value || availableDepts.value[0]?.deptId
    if (deptId) {
      const records = mockQueueData.queues[deptId as keyof typeof mockQueueData.queues] || []
      queueList.value = records

      // 模拟当前排队状态（取第一条作为当前患者）
      if (records.length > 0) {
        // 随机生成前面人数（2-8人）
        const ahead = Math.floor(Math.random() * 8) + 2
        const currentCalling = Math.floor(Math.random() * 20) + 1

        currentQueue.value = {
          registerId: records[0].registerId,
          deptName: records[0].deptName,
          queueNumber: String(currentCalling).padStart(2, '0'),
          aheadCount: ahead,
          currentCalling: String(currentCalling - ahead).padStart(2, '0'),
          currentRoom: `${Math.floor(Math.random() * 5) + 1}号诊室`
        }
      } else {
        currentQueue.value = null
      }
    }

    lastUpdateTime.value = dayjs().format('HH:mm:ss')

  } catch {
    showToast('加载候诊数据失败')
  } finally {
    refreshing.value = false
  }
}

// 刷新
const refreshQueue = () => {
  loadQueueData()
}

// 切换科室
const switchDept = (deptId: number) => {
  selectedDeptId.value = deptId
  loadQueueData()
}

// ============ 自动刷新 ============

const startAutoRefresh = () => {
  // 每30秒刷新一次
  refreshTimer = window.setInterval(() => {
    loadQueueData()
  }, 30000)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// ============ 生命周期 ============

onMounted(() => {
  loadQueueData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.queue-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 0 16px 80px;
}

// ===== 刷新提示 =====
.refresh-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  font-size: 13px;
  color: #6B6B7E;
  .van-icon {
    font-size: 16px;
    &.spinning {
      animation: spin 0.8s linear infinite;
    }
  }
  .refresh-btn {
    color: #4CAF50;
    cursor: pointer;
    font-weight: 500;
    margin-left: auto;
    padding: 0 8px;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ===== 排队状态 =====
.queue-status {
  margin-bottom: 16px;
}

.status-card {
  display: flex;
  align-items: center;
  background: white;
  border-radius: 16px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.status-left,
.status-right {
  flex: 1;
  text-align: center;
}

.status-divider {
  width: 1px;
  height: 60px;
  background: #E8E8E8;
  margin: 0 16px;
}

.status-label {
  font-size: 12px;
  color: #6B6B7E;
}

.status-number {
  font-size: 42px;
  font-weight: 700;
  color: #4CAF50;
  line-height: 1.2;
}

.status-dept {
  font-size: 13px;
  color: #6B6B7E;
  margin-top: 2px;
}

.status-ahead {
  font-size: 42px;
  font-weight: 700;
  color: #FF9800;
  line-height: 1.2;
}

.status-unit {
  font-size: 13px;
  color: #6B6B7E;
}

// ===== 预估时间 =====
.estimate-time {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: white;
  border-radius: 10px;
  padding: 10px 16px;
  margin-top: 10px;
  font-size: 14px;
  color: #6B6B7E;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  strong {
    color: #4CAF50;
  }
}

// ===== 当前叫号 =====
.calling-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: #E8F5E9;
  border-radius: 10px;
  padding: 10px 16px;
  margin-top: 10px;
  .calling-label {
    font-size: 14px;
    color: #6B6B7E;
  }
  .calling-number {
    font-size: 24px;
    font-weight: 700;
    color: #4CAF50;
  }
  .calling-room {
    font-size: 14px;
    color: #1A1A2E;
  }
}

// ===== 候诊列表 =====
.queue-list-section {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #1A1A2E;
  }
  .section-count {
    font-size: 13px;
    color: #6B6B7E;
  }
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: background 0.2s;

  &.is-current {
    background: #E8F5E9;
    border: 1px solid #4CAF50;
  }
  &.is-passed {
    opacity: 0.5;
    .queue-position .position-number {
      text-decoration: line-through;
    }
  }
}

.queue-position {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #F5F7FA;
  flex-shrink: 0;
  .position-number {
    font-size: 14px;
    font-weight: 600;
    color: #6B6B7E;
  }
}

.queue-info {
  flex: 1;
  .queue-name {
    font-size: 15px;
    font-weight: 500;
    color: #1A1A2E;
  }
  .queue-detail {
    font-size: 12px;
    color: #6B6B7E;
    display: flex;
    gap: 12px;
  }
}

// ===== 科室切换 =====
.dept-switcher {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .switcher-label {
    font-size: 13px;
    color: #6B6B7E;
  }
  .dept-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    .van-tag {
      padding: 4px 12px;
      cursor: pointer;
      border-radius: 14px;
    }
    .van-tag--primary {
      background: #4CAF50;
    }
  }
}

// ===== 底部提示 =====
.footer-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: #C4C4D6;
  padding: 12px 0;
}

// ===== 空状态 =====
.empty-state {
  text-align: center;
  padding: 30px 0;
  color: #C4C4D6;
  p {
    margin-top: 8px;
    color: #6B6B7E;
  }
}
</style>