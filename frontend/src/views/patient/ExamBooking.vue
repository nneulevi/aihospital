<!-- src/views/patient/ExamBooking.vue -->
<template>
  <div class="exam-booking-page">
    <van-nav-bar title="检查预约" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 步骤引导 -->
    <van-steps :active="step - 1" class="steps">
      <van-step>选择项目</van-step>
      <van-step>确认信息</van-step>
      <van-step>预约成功</van-step>
    </van-steps>

    <!-- ========== Step 1: 选择检查项目 ========== -->
    <div v-if="step === 1" class="step-content">
      <!-- 按类型筛选 -->
      <div class="type-tabs">
        <span
            v-for="type in examTypes"
            :key="type.key"
            class="type-tab"
            :class="{ active: activeType === type.key }"
            @click="activeType = type.key"
        >
          <van-icon :name="type.icon" />
          {{ type.label }}
        </span>
      </div>

      <!-- 项目列表 -->
      <div class="project-list">
        <div
            v-for="item in filteredProjects"
            :key="item.id"
            class="project-card"
            :class="{ selected: selectedItems.some(i => i.id === item.id) }"
            @click="toggleSelect(item)"
        >
          <div class="project-left">
            <van-checkbox
                :model-value="selectedItems.some(i => i.id === item.id)"
                @click.stop="toggleSelect(item)"
            />
          </div>
          <div class="project-info">
            <div class="project-name">{{ item.name }}</div>
            <div class="project-desc">
              <span>{{ item.typeName }}</span>
              <span>{{ item.bodyPart || '--' }}</span>
            </div>
            <div class="project-tips" v-if="item.tips">
              <van-icon name="info-o" />
              <span>{{ item.tips }}</span>
            </div>
          </div>
          <div class="project-price">
            ¥{{ item.price.toFixed(2) }}
          </div>
        </div>

        <div v-if="filteredProjects.length === 0" class="empty-state">
          <van-icon name="search" size="48" color="#C4C4D6" />
          <p>暂无{{ getTypeLabel(activeType) }}项目</p>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="bottom-bar" v-if="filteredProjects.length > 0">
        <div class="bar-left">
          <van-checkbox v-model="selectAll">全选</van-checkbox>
          <span class="selected-count">已选 {{ selectedItems.length }} 项</span>
        </div>
        <van-button
            type="primary"
            round
            :disabled="selectedItems.length === 0"
            @click="step = 2"
        >
          下一步
        </van-button>
      </div>
    </div>

    <!-- ========== Step 2: 确认预约信息 ========== -->
    <div v-if="step === 2" class="step-content">
      <!-- 选择就诊人 -->
      <div class="confirm-card">
        <div class="card-title">选择就诊人</div>
        <div class="patient-select" @click="showPatientSheet = true">
          <div class="patient-info">
            <span class="patient-name">{{ selectedPatient?.realName || '请选择就诊人' }}</span>
            <span class="patient-id" v-if="selectedPatient">病历号：{{ selectedPatient.caseNumber }}</span>
          </div>
          <van-icon name="arrow" />
        </div>
      </div>

      <!-- 选择预约日期 -->
      <div class="confirm-card">
        <div class="card-title">选择预约日期</div>
        <div class="date-selector">
          <div
              v-for="date in availableDates"
              :key="date.value"
              class="date-item"
              :class="{ active: selectedDate === date.value }"
              @click="selectedDate = date.value"
          >
            <div class="date-week">{{ date.week }}</div>
            <div class="date-day">{{ date.day }}</div>
            <div class="date-month">{{ date.month }}</div>
          </div>
        </div>
      </div>

      <!-- 选择时间段 -->
      <div class="confirm-card">
        <div class="card-title">选择时间段</div>
        <div class="time-slots">
          <span
              v-for="slot in timeSlots"
              :key="slot.value"
              class="time-slot"
              :class="{ active: selectedTime === slot.value, disabled: slot.disabled }"
              @click="selectTimeSlot(slot)"
          >
            {{ slot.label }}
            <span class="slot-status" v-if="slot.disabled">已满</span>
          </span>
        </div>
      </div>

      <!-- 已选项目 -->
      <div class="confirm-card">
        <div class="card-title">已选项目 ({{ selectedItems.length }})</div>
        <div class="selected-items">
          <div v-for="item in selectedItems" :key="item.id" class="selected-item">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-price">¥{{ item.price.toFixed(2) }}</span>
          </div>
          <div class="total-price">
            <span>合计</span>
            <span class="price">¥{{ totalPrice.toFixed(2) }}</span>
          </div>
        </div>
      </div>

      <!-- 检查前注意事项 -->
      <div class="tips-card warning">
        <van-icon name="warning-o" />
        <span>检查前请仔细阅读注意事项，部分检查需空腹或提前准备</span>
      </div>

      <div class="step-actions">
        <van-button plain round block @click="step = 1">返回上一步</van-button>
        <van-button type="primary" round block :loading="submitting" @click="submitBooking">
          确认预约
        </van-button>
      </div>
    </div>

    <!-- ========== Step 3: 预约成功 ========== -->
    <div v-if="step === 3" class="step-content success-content">
      <div class="success-card">
        <div class="success-icon">
          <van-icon name="checked" size="64" color="#4CAF50" />
        </div>
        <div class="success-title">🎉 预约成功</div>
        <div class="success-subtitle">请按时到院进行检查</div>

        <div class="booking-info">
          <div class="info-row">
            <span class="label">检查项目</span>
            <span class="value">{{ selectedItems.map(i => i.name).join('、') }}</span>
          </div>
          <div class="info-row">
            <span class="label">检查日期</span>
            <span class="value">{{ formatDate(selectedDate) }}</span>
          </div>
          <div class="info-row">
            <span class="label">检查时间</span>
            <span class="value">{{ getTimeLabel(selectedTime) }}</span>
          </div>
          <div class="info-row">
            <span class="label">就诊人</span>
            <span class="value">{{ selectedPatient?.realName }}</span>
          </div>
          <div class="info-row">
            <span class="label">预约号</span>
            <span class="value highlight">{{ bookingResult?.bookingNo || '--' }}</span>
          </div>
          <div class="info-row">
            <span class="label">总费用</span>
            <span class="value price">¥{{ totalPrice.toFixed(2) }}</span>
          </div>
        </div>

        <!-- 检查前注意事项 -->
        <div class="exam-notice">
          <div class="notice-title">📋 检查前注意事项</div>
          <div class="notice-item" v-for="(tip, idx) in getExamTips()" :key="idx">
            {{ idx + 1 }}. {{ tip }}
          </div>
        </div>

        <div class="step-actions">
          <van-button plain round @click="goToHome">返回首页</van-button>
          <van-button type="primary" round @click="goToRecords">查看预约记录</van-button>
        </div>
      </div>
    </div>

    <!-- ========== 就诊人选择弹窗 ========== -->
    <van-action-sheet v-model:show="showPatientSheet" title="选择就诊人">
      <div class="patient-list">
        <div
            v-for="patient in patientList"
            :key="patient.patientId"
            class="patient-option"
            :class="{ active: selectedPatient?.patientId === patient.patientId }"
            @click="selectPatient(patient)"
        >
          <div class="patient-info">
            <div class="patient-name">{{ patient.realName }}</div>
            <div class="patient-meta">
              <span>{{ patient.gender === 'MALE' ? '男' : '女' }}</span>
              <span>{{ patient.age || '--' }}岁</span>
              <span>病历号：{{ patient.caseNumber }}</span>
            </div>
          </div>
          <van-icon v-if="selectedPatient?.patientId === patient.patientId" name="success" color="#4CAF50" />
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()

// ============ 状态 ============
const step = ref(1)
const activeType = ref('all')
const selectedItems = ref<any[]>([])
const selectedPatient = ref<any>(null)
const selectedDate = ref('')
const selectedTime = ref('')
const submitting = ref(false)
const showPatientSheet = ref(false)
const bookingResult = ref<any>(null)

// ============ 模拟数据 ============

// 检查类型
const examTypes = [
  { key: 'all', label: '全部', icon: 'apps-o' },
  { key: 'radiology', label: '放射科', icon: 'scan-o' },
  { key: 'ultrasound', label: '超声科', icon: 'records-o' },
  { key: 'endoscopy', label: '内镜科', icon: 'eye-o' },
  { key: 'ecg', label: '心电图', icon: 'heartbeat-o' },
  { key: 'other', label: '其他', icon: 'medical-o' },
]

// 检查项目
const projects = [
  // 放射科
  { id: 101, name: '胸部X光（DR）', type: 'radiology', typeName: '放射科', bodyPart: '胸部', price: 120.00, tips: '无需特殊准备' },
  { id: 102, name: '胸部CT平扫', type: 'radiology', typeName: '放射科', bodyPart: '胸部', price: 450.00, tips: '需空腹4小时' },
  { id: 103, name: '头颅CT平扫', type: 'radiology', typeName: '放射科', bodyPart: '头部', price: 380.00, tips: '无需特殊准备' },
  { id: 104, name: '腰椎X光（DR）', type: 'radiology', typeName: '放射科', bodyPart: '腰椎', price: 150.00, tips: '无需特殊准备' },
  { id: 105, name: '骨密度检测', type: 'radiology', typeName: '放射科', bodyPart: '全身', price: 200.00, tips: '无需特殊准备' },

  // 超声科
  { id: 201, name: '腹部彩超', type: 'ultrasound', typeName: '超声科', bodyPart: '腹部', price: 280.00, tips: '需空腹8小时以上' },
  { id: 202, name: '心脏彩超', type: 'ultrasound', typeName: '超声科', bodyPart: '心脏', price: 350.00, tips: '无需特殊准备' },
  { id: 203, name: '甲状腺彩超', type: 'ultrasound', typeName: '超声科', bodyPart: '甲状腺', price: 200.00, tips: '无需特殊准备' },
  { id: 204, name: '乳腺彩超', type: 'ultrasound', typeName: '超声科', bodyPart: '乳腺', price: 220.00, tips: '无需特殊准备' },
  { id: 205, name: '颈动脉彩超', type: 'ultrasound', typeName: '超声科', bodyPart: '颈部', price: 300.00, tips: '无需特殊准备' },

  // 内镜科
  { id: 301, name: '胃镜', type: 'endoscopy', typeName: '内镜科', bodyPart: '胃', price: 350.00, tips: '需空腹8小时以上，需家属陪同' },
  { id: 302, name: '肠镜', type: 'endoscopy', typeName: '内镜科', bodyPart: '肠道', price: 420.00, tips: '需提前1天做肠道准备，需家属陪同' },
  { id: 303, name: '无痛胃镜', type: 'endoscopy', typeName: '内镜科', bodyPart: '胃', price: 550.00, tips: '需空腹8小时以上，需家属陪同' },
  { id: 304, name: '无痛肠镜', type: 'endoscopy', typeName: '内镜科', bodyPart: '肠道', price: 650.00, tips: '需提前1天做肠道准备，需家属陪同' },

  // 心电图
  { id: 401, name: '常规心电图', type: 'ecg', typeName: '心电图', bodyPart: '心脏', price: 80.00, tips: '无需特殊准备' },
  { id: 402, name: '24小时动态心电图', type: 'ecg', typeName: '心电图', bodyPart: '心脏', price: 280.00, tips: '需佩戴24小时' },
  { id: 403, name: '运动平板试验', type: 'ecg', typeName: '心电图', bodyPart: '心脏', price: 320.00, tips: '需穿运动鞋' },

  // 其他
  { id: 501, name: '脑电图', type: 'other', typeName: '其他', bodyPart: '头部', price: 180.00, tips: '需洗头、保持清醒' },
  { id: 502, name: '肌电图', type: 'other', typeName: '其他', bodyPart: '四肢', price: 220.00, tips: '无需特殊准备' },
]

// 就诊人
const patientList = [
  { patientId: 1, realName: '张明', gender: 'MALE', age: 35, caseNumber: 'HN202600001', isDefault: true },
  { patientId: 2, realName: '张秀兰', gender: 'FEMALE', age: 68, caseNumber: 'HN202600002', isDefault: false },
]

// 可选日期
const availableDates = computed(() => {
  const dates = []
  for (let i = 0; i < 7; i++) {
    const date = dayjs().add(i, 'day')
    dates.push({
      value: date.format('YYYY-MM-DD'),
      week: date.format('ddd'),
      day: date.format('DD'),
      month: date.format('MM/DD')
    })
  }
  return dates
})

// 时间段
const timeSlots = [
  { value: '08:00-09:00', label: '08:00-09:00', disabled: false },
  { value: '09:00-10:00', label: '09:00-10:00', disabled: false },
  { value: '10:00-11:00', label: '10:00-11:00', disabled: false },
  { value: '11:00-12:00', label: '11:00-12:00', disabled: true },
  { value: '14:00-15:00', label: '14:00-15:00', disabled: false },
  { value: '15:00-16:00', label: '15:00-16:00', disabled: false },
  { value: '16:00-17:00', label: '16:00-17:00', disabled: false },
]

// 检查类型对应的注意事项
const examTipsMap: Record<string, string[]> = {
  radiology: ['检查前请取下金属物品（项链、手表、钥匙等）', '孕妇请提前告知医生'],
  ultrasound: ['腹部超声需空腹8小时以上', '盆腔超声需憋尿'],
  endoscopy: ['需空腹8小时以上', '需家属陪同', '检查前签署知情同意书'],
  ecg: ['检查前请勿剧烈运动', '保持心情平静'],
  other: ['请根据医生指导进行准备'],
}

// ============ 计算属性 ============

const filteredProjects = computed(() => {
  if (activeType.value === 'all') return projects
  return projects.filter(p => p.type === activeType.value)
})

const totalPrice = computed(() => {
  return selectedItems.value.reduce((sum, item) => sum + item.price, 0)
})

const selectAll = computed({
  get: () => {
    return filteredProjects.value.length > 0 &&
        filteredProjects.value.every(p => selectedItems.value.some(i => i.id === p.id))
  },
  set: (val) => {
    if (val) {
      filteredProjects.value.forEach(p => {
        if (!selectedItems.value.some(i => i.id === p.id)) {
          selectedItems.value.push(p)
        }
      })
    } else {
      const ids = filteredProjects.value.map(p => p.id)
      selectedItems.value = selectedItems.value.filter(i => !ids.includes(i.id))
    }
  }
})

// ============ 方法 ============

const getTypeLabel = (key: string) => {
  const type = examTypes.find(t => t.key === key)
  return type?.label || ''
}

const toggleSelect = (item: any) => {
  const index = selectedItems.value.findIndex(i => i.id === item.id)
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    selectedItems.value.push(item)
  }
}

const selectPatient = (patient: any) => {
  selectedPatient.value = patient
  showPatientSheet.value = false
}

const selectTimeSlot = (slot: any) => {
  if (slot.disabled) {
    showToast('该时间段已满')
    return
  }
  selectedTime.value = slot.value
}

const getTimeLabel = (value: string) => {
  const slot = timeSlots.find(s => s.value === value)
  return slot?.label || value
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY年MM月DD日')
}

const getExamTips = () => {
  if (selectedItems.value.length === 0) return ['请按医嘱准备']
  // 根据选中的项目类型返回注意事项
  const types = selectedItems.value.map(i => i.type)
  const allTips: string[] = []
  types.forEach(t => {
    const tips = examTipsMap[t] || ['请按医嘱准备']
    tips.forEach(tip => {
      if (!allTips.includes(tip)) allTips.push(tip)
    })
  })
  return allTips
}

// 提交预约
const submitBooking = async () => {
  if (!selectedPatient.value) {
    showToast('请选择就诊人')
    return
  }
  if (!selectedDate.value) {
    showToast('请选择预约日期')
    return
  }
  if (!selectedTime.value) {
    showToast('请选择时间段')
    return
  }

  submitting.value = true

  try {
    await new Promise(resolve => setTimeout(resolve, 1000))

    bookingResult.value = {
      bookingNo: `JC${dayjs().format('YYYYMMDD')}${String(Date.now()).slice(-4)}`
    }

    showSuccessToast('预约成功')
    step.value = 3

  } catch (error: any) {
    showToast(error.message || '预约失败，请重试')
  } finally {
    submitting.value = false
  }
}

const goToHome = () => router.push('/patient/home')
const goToRecords = () => router.push('/patient/appointments')

// ============ 生命周期 ============

onMounted(() => {
  if (patientList.length > 0) {
    selectedPatient.value = patientList.find(p => p.isDefault) || patientList[0]
  }
  if (availableDates.value.length > 0) {
    selectedDate.value = availableDates.value[0].value
  }
  const firstAvailable = timeSlots.find(s => !s.disabled)
  if (firstAvailable) {
    selectedTime.value = firstAvailable.value
  }
})
</script>

<style lang="scss" scoped>
.exam-booking-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 80px;
}

.steps {
  background: white;
  padding: 12px 16px 0;
}

.step-content {
  padding: 12px 16px;
}

// ===== 类型标签 =====
.type-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 8px 0 12px;
  &::-webkit-scrollbar { height: 0; }
}
.type-tab {
  flex-shrink: 0;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  color: #6B6B7E;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  &.active {
    background: #4CAF50;
    color: white;
  }
}

// ===== 项目列表 =====
.project-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 70px;
}

.project-card {
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
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
}

.project-info {
  flex: 1;
  .project-name {
    font-size: 15px;
    font-weight: 500;
    color: #1A1A2E;
  }
  .project-desc {
    font-size: 12px;
    color: #6B6B7E;
    display: flex;
    gap: 12px;
    margin-top: 2px;
  }
  .project-tips {
    font-size: 12px;
    color: #FF9800;
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 2px;
  }
}
.project-price {
  font-size: 16px;
  font-weight: 600;
  color: #E76F51;
  white-space: nowrap;
}

// ===== 底部栏 =====
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 16px;
  border-top: 1px solid #E8E8E8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  .bar-left {
    display: flex;
    align-items: center;
    gap: 12px;
    .selected-count {
      font-size: 13px;
      color: #6B6B7E;
    }
  }
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
  }
}

// ===== 确认卡片（复用了检验预约的样式，调整一下） =====
.confirm-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .card-title {
    font-size: 15px;
    font-weight: 500;
    color: #1A1A2E;
    margin-bottom: 12px;
  }
}

.patient-select {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #F5F7FA;
  border-radius: 8px;
  cursor: pointer;
  .patient-name { font-size: 15px; font-weight: 500; }
  .patient-id { font-size: 12px; color: #6B6B7E; margin-left: 8px; }
}

.date-selector {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 4px 0;
  &::-webkit-scrollbar { height: 0; }
}
.date-item {
  flex-shrink: 0;
  width: 52px;
  text-align: center;
  padding: 6px 4px;
  border-radius: 8px;
  background: #F5F7FA;
  cursor: pointer;
  .date-week { font-size: 11px; color: #6B6B7E; }
  .date-day { font-size: 16px; font-weight: 600; }
  .date-month { font-size: 10px; color: #6B6B7E; }
  &.active {
    background: #4CAF50;
    color: white;
    .date-week, .date-month { color: rgba(255,255,255,0.7); }
  }
}

.time-slots {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.time-slot {
  padding: 6px 14px;
  border-radius: 14px;
  font-size: 13px;
  background: #F5F7FA;
  cursor: pointer;
  &.active {
    background: #4CAF50;
    color: white;
  }
  &.disabled {
    background: #F0F0F0;
    color: #C4C4D6;
    cursor: not-allowed;
  }
  .slot-status {
    font-size: 10px;
    color: #E76F51;
    margin-left: 4px;
  }
}

.selected-items {
  .selected-item {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #F0F0F0;
    .item-name { font-size: 14px; color: #1A1A2E; }
    .item-price { font-size: 14px; color: #6B6B7E; }
  }
  .total-price {
    display: flex;
    justify-content: space-between;
    padding-top: 8px;
    font-size: 16px;
    font-weight: 600;
    .price { color: #E76F51; }
  }
}

.tips-card {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #FFF8E1;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  color: #FF9800;
  margin-bottom: 12px;
  &.warning {
    background: #FFEBEE;
    color: #E76F51;
  }
  .van-icon { margin-top: 2px; }
}

.step-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
    height: 46px;
  }
}

// ===== 成功页 =====
.success-content { padding-top: 20px; }
.success-card {
  background: white;
  border-radius: 16px;
  padding: 32px 20px 24px;
  text-align: center;
}
.booking-info {
  text-align: left;
  background: #F5F7FA;
  border-radius: 8px;
  padding: 12px 16px;
  margin: 16px 0;
  .info-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #E8E8E8;
    &:last-child { border-bottom: none; }
    .label { font-size: 14px; color: #6B6B7E; }
    .value { font-size: 14px; color: #1A1A2E; &.highlight { color: #4CAF50; font-weight: 600; } &.price { color: #E76F51; font-weight: 600; } }
  }
}

.exam-notice {
  text-align: left;
  background: #E3F2FD;
  border-radius: 8px;
  padding: 12px 16px;
  margin: 16px 0;
  .notice-title {
    font-size: 14px;
    font-weight: 600;
    color: #1565C0;
    margin-bottom: 6px;
  }
  .notice-item {
    font-size: 13px;
    color: #1565C0;
    padding: 2px 0;
  }
}

.success-content .step-actions {
  flex-direction: row;
  .van-button { flex: 1; height: 44px; }
}

// ===== 就诊人选择弹窗 =====
.patient-list { padding: 8px 16px 20px; }
.patient-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  &.active { background: #E8F5E9; }
  .patient-name { font-size: 16px; font-weight: 500; }
  .patient-meta { font-size: 13px; color: #6B6B7E; display: flex; gap: 12px; margin-top: 2px; }
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #C4C4D6;
  p { margin-top: 8px; }
}
</style>