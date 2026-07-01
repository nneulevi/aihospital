<!-- src/views/patient/Checkin.vue -->
<template>
  <div class="checkin-page">
    <van-nav-bar title="就诊报到" fixed placeholder left-arrow @click-left="() => router.back()" />

    <div class="steps-guide">
      <van-steps :active="stepStatus" class="custom-steps">
        <van-step>选择就诊</van-step>
        <van-step>确认报到</van-step>
        <van-step>报到成功</van-step>
      </van-steps>
    </div>

    <!-- Step 1: 选择就诊 -->
    <div v-if="stepStatus === 0" class="step-content">
      <div class="section-title">
        <span>📋 今日可报到的就诊</span>
        <span class="section-hint">请选择您要报到的挂号</span>
      </div>

      <div
          v-for="record in todayRecords"
          :key="record.registerId"
          class="record-card"
          :class="{ selected: selectedRecord?.registerId === record.registerId }"
          @click="selectRecord(record)"
      >
        <div class="record-left">
          <van-checkbox
              :model-value="selectedRecord?.registerId === record.registerId"
              @click.stop="selectRecord(record)"
          />
        </div>
        <div class="record-info">
          <div class="record-top">
            <span class="record-dept">{{ record.deptName }}</span>
            <van-tag type="warning" size="small">待报到</van-tag>
          </div>
          <div class="record-detail">
            <span>👨‍⚕️ {{ record.doctorName }}</span>
            <span>📅 {{ formatDate(record.visitDate) }}</span>
            <span>🕐 {{ record.noon === 'MORNING' ? '上午' : '下午' }}</span>
          </div>
          <div class="record-location" v-if="record.location">
            📍 {{ record.location }}
          </div>
        </div>
        <van-icon
            v-if="selectedRecord?.registerId === record.registerId"
            name="success"
            color="#4CAF50"
            size="20"
        />
      </div>

      <div v-if="todayRecords.length === 0" class="empty-state">
        <van-icon name="clock-o" size="64" color="#C4C4D6" />
        <p class="empty-title">今日暂无就诊安排</p>
        <p class="empty-desc">您今天没有需要报到的挂号</p>
        <van-button type="primary" round size="small" @click="goToHome">返回首页</van-button>
      </div>

      <div v-if="todayRecords.length > 0" class="step-actions">
        <van-button
            type="primary"
            block
            round
            :disabled="!selectedRecord"
            @click="stepStatus = 1"
        >
          下一步：确认报到
        </van-button>
      </div>
    </div>

    <!-- Step 2: 确认报到 -->
    <div v-if="stepStatus === 1" class="step-content">
      <div class="confirm-card">
        <div class="confirm-header">
          <span class="confirm-icon">✅</span>
          <span class="confirm-title">确认报到信息</span>
        </div>

        <div class="confirm-info">
          <div class="info-row">
            <span class="label">就诊科室</span>
            <span class="value">{{ selectedRecord?.deptName }}</span>
          </div>
          <div class="info-row">
            <span class="label">就诊医生</span>
            <span class="value">{{ selectedRecord?.doctorName }}</span>
          </div>
          <div class="info-row">
            <span class="label">就诊时间</span>
            <span class="value">
              {{ formatDate(selectedRecord?.visitDate) }}
              {{ selectedRecord?.noon === 'MORNING' ? '上午' : '下午' }}
            </span>
          </div>
          <div class="info-row">
            <span class="label">就诊地点</span>
            <span class="value">{{ selectedRecord?.location || '门诊楼' }}</span>
          </div>
          <div class="info-row">
            <span class="label">就诊人</span>
            <span class="value">{{ selectedRecord?.patientName || '--' }}</span>
          </div>
        </div>

        <div class="confirm-tips">
          <van-icon name="info-o" />
          <span>请确认信息无误后点击报到，报到后请到候诊区等待叫号</span>
        </div>
      </div>

      <div class="step-actions">
        <van-button plain round block @click="stepStatus = 0">返回上一步</van-button>
        <van-button
            type="primary"
            block
            round
            :loading="submitting"
            @click="submitCheckin"
        >
          确认报到
        </van-button>
      </div>
    </div>

    <!-- Step 3: 报到成功 -->
    <div v-if="stepStatus === 2" class="step-content success-content">
      <div class="success-card">
        <div class="success-icon">
          <van-icon name="checked" size="64" color="#4CAF50" />
        </div>
        <div class="success-title">🎉 报到成功</div>
        <div class="success-subtitle">请前往候诊区等待叫号</div>

        <div class="queue-info">
          <div class="queue-number">
            <span class="queue-label">您的排队号</span>
            <span class="queue-value">{{ checkinResult?.queueNumber || '--' }}</span>
          </div>
          <div class="queue-position">
            <span class="position-label">当前前面还有</span>
            <span class="position-value">{{ checkinResult?.aheadCount || 0 }} 人</span>
          </div>
        </div>

        <div class="location-info" v-if="selectedRecord?.location">
          <van-icon name="location-o" />
          <span>就诊地点：{{ selectedRecord.location }}</span>
        </div>

        <div class="success-tips">
          <div class="tip-item">⏰ 请提前 10 分钟到达候诊区</div>
          <div class="tip-item">📋 请携带身份证和医保卡</div>
          <div class="tip-item">📱 可在「候诊查询」中查看实时排队进度</div>
        </div>

        <div class="step-actions">
          <van-button plain round @click="goToQueue">
            <van-icon name="clock-o" /> 候诊查询
          </van-button>
          <van-button type="primary" round @click="goToHome">
            <van-icon name="home-o" /> 返回首页
          </van-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import dayjs from 'dayjs'
import { getTodayRegisters, submitCheckin } from '@/api'
import { useUserStore } from '@/stores/user'
import type { TodayRegisterVO, CheckinResultVO } from '@/api/model'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const stepStatus = ref(0)
const selectedRecord = ref<TodayRegisterVO | null>(null)
const submitting = ref(false)
const todayRecords = ref<TodayRegisterVO[]>([])
const checkinResult = ref<{ queueNumber: string; aheadCount: number } | null>(null)

// ============ 加载今日就诊 ============
const loadTodayRecords = async () => {
  try {
    const patientId = userStore.patientId
    console.log('📤 [Checkin] 加载今日就诊，patientId:', patientId)

    if (!patientId) {
      showToast('请先登录')
      return
    }

    const res = await getTodayRegisters({ patientId }) as TodayRegisterVO[]
    console.log('📥 [Checkin] 今日就诊数据:', res)

    // 只显示未报到的 (checkinStatus === 0)
    todayRecords.value = (res || []).filter(r => r.checkinStatus === 0)
    console.log('📥 [Checkin] 未报到记录:', todayRecords.value)

    const { registerId } = route.query
    if (registerId) {
      const target = todayRecords.value.find(r => r.registerId === Number(registerId))
      if (target) {
        selectedRecord.value = target
        if (todayRecords.value.length === 1) {
          stepStatus.value = 1
        }
      }
    }
  } catch (error) {
    console.error('❌ [Checkin] 加载就诊记录失败:', error)
    showToast('加载就诊记录失败')
  }
}

// ============ 选择就诊记录 ============
const selectRecord = (record: TodayRegisterVO) => {
  if (selectedRecord.value?.registerId === record.registerId) {
    selectedRecord.value = null
  } else {
    selectedRecord.value = record
  }
}

// ============ 提交报到 ============
const submitCheckin = async () => {
  if (!selectedRecord.value) {
    showToast('请选择就诊记录')
    return
  }

  const registerId = selectedRecord.value.registerId!
  console.log('📤 [Checkin] ===== 提交报到 =====')
  console.log('📤 [Checkin] registerId:', registerId)

  submitting.value = true
  try {
    // 🔥 使用 request.ts 的 request.post，直接返回 CheckinResultVO
    const res = await submitCheckin({ registerId })
    console.log('📥 [Checkin] 报到响应:', res)
    console.log('📥 [Checkin] 响应类型:', typeof res)
    console.log('📥 [Checkin] 是否有 queueNumber:', res && 'queueNumber' in res)

    // 🔥 空值安全检查
    if (!res) {
      showToast('后端返回为空，请检查网络或接口')
      return
    }

    checkinResult.value = {
      queueNumber: res.queueNumber || '--',
      aheadCount: res.aheadCount ?? 0
    }
    showSuccessToast('报到成功')
    stepStatus.value = 2
  } catch (error: any) {
    console.error('❌ [Checkin] 报到失败:', error)

    // 详细错误信息
    if (error.response) {
      console.error('📥 错误响应状态:', error.response.status)
      console.error('📥 错误响应数据:', error.response.data)
      const errorMsg = error.response.data?.message || error.response.data?.msg || '报到失败，请重试'
      showToast(errorMsg)
    } else if (error.request) {
      console.error('📥 请求已发送但未收到响应:', error.request)
      showToast('网络错误，请检查后端服务是否启动')
    } else {
      showToast(error.message || '报到失败，请重试')
    }
  } finally {
    submitting.value = false
  }
}

// ============ 工具方法 ============
const formatDate = (date?: string) => {
  if (!date) return ''
  return dayjs(date).format('MM月DD日')
}

// ============ 路由跳转 ============
const goToHome = () => router.push('/patient/home')
const goToQueue = () => router.push('/patient/queue')

// ============ 生命周期 ============
onMounted(() => {
  console.log('🚀 [Checkin] 页面加载')
  loadTodayRecords()
})
</script>

<style lang="scss" scoped>
.checkin-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 80px;
}

// ===== 步骤引导 =====
.steps-guide {
  background: white;
  padding: 16px 16px 0;
  margin-bottom: 12px;
}
.custom-steps {
  :deep(.van-step__title) {
    font-size: 12px;
  }
}

// ===== 步骤内容 =====
.step-content {
  padding: 0 16px;
}

// ===== 区域标题 =====
.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1A1A2E;
  .section-hint {
    font-size: 13px;
    font-weight: 400;
    color: #6B6B7E;
  }
}

// ===== 就诊记录卡片 =====
.record-card {
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;

  &.selected {
    border-color: #4CAF50;
    background: #F6FDF6;
  }

  &:active {
    transform: scale(0.98);
  }
}

.record-left {
  padding-top: 2px;
}

.record-info {
  flex: 1;
  .record-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }
  .record-dept {
    font-size: 16px;
    font-weight: 600;
    color: #1A1A2E;
  }
  .record-detail {
    display: flex;
    gap: 16px;
    font-size: 14px;
    color: #6B6B7E;
    flex-wrap: wrap;
  }
  .record-location {
    font-size: 13px;
    color: #4CAF50;
    margin-top: 4px;
  }
}

// ===== 确认报到 =====
.confirm-card {
  background: white;
  border-radius: 12px;
  padding: 20px 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}

.confirm-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  .confirm-icon {
    font-size: 24px;
  }
  .confirm-title {
    font-size: 18px;
    font-weight: 600;
    color: #1A1A2E;
  }
}

.confirm-info {
  background: #F5F7FA;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
  .info-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #E8E8E8;
    &:last-child {
      border-bottom: none;
    }
    .label {
      font-size: 14px;
      color: #6B6B7E;
    }
    .value {
      font-size: 14px;
      color: #1A1A2E;
      font-weight: 500;
    }
  }
}

.confirm-tips {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #FF9800;
  background: #FFF8E1;
  padding: 10px 14px;
  border-radius: 8px;
  .van-icon {
    margin-top: 2px;
    flex-shrink: 0;
  }
}

// ===== 步骤按钮 =====
.step-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
  padding-bottom: 16px;
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
    height: 46px;
  }
}

// ===== 空状态 =====
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #C4C4D6;
  .empty-title {
    font-size: 16px;
    color: #6B6B7E;
    margin-top: 12px;
  }
  .empty-desc {
    font-size: 14px;
    margin: 4px 0 16px;
  }
}

// ===== 报到成功 =====
.success-content {
  padding-top: 20px;
}

.success-card {
  background: white;
  border-radius: 16px;
  padding: 32px 20px 24px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.success-icon {
  margin-bottom: 12px;
}

.success-title {
  font-size: 24px;
  font-weight: 700;
  color: #1A1A2E;
}

.success-subtitle {
  font-size: 14px;
  color: #6B6B7E;
  margin-bottom: 20px;
}

.queue-info {
  display: flex;
  justify-content: center;
  gap: 40px;
  background: #F5F7FA;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
}

.queue-number,
.queue-position {
  text-align: center;
  .queue-label,
  .position-label {
    font-size: 12px;
    color: #6B6B7E;
    display: block;
  }
  .queue-value {
    font-size: 32px;
    font-weight: 700;
    color: #4CAF50;
  }
  .position-value {
    font-size: 24px;
    font-weight: 700;
    color: #FF9800;
  }
}

.location-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
  color: #1A1A2E;
  background: #E8F5E9;
  padding: 8px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.success-tips {
  text-align: left;
  background: #F5F7FA;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  .tip-item {
    font-size: 13px;
    color: #6B6B7E;
    padding: 4px 0;
  }
}

.success-content .step-actions {
  flex-direction: row;
  gap: 12px;
  .van-button {
    flex: 1;
    height: 44px;
  }
}
</style>