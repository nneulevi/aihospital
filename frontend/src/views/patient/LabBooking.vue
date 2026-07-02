<!-- src/views/patient/LabBooking.vue -->
<template>
  <div class="lab-booking-page">
    <van-nav-bar title="检验预约" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 步骤引导 -->
    <van-steps :active="step - 1" class="steps">
      <van-step>选择项目</van-step>
      <van-step>确认信息</van-step>
      <van-step>预约成功</van-step>
    </van-steps>

    <!-- ========== Step 1: 选择检验项目 ========== -->
    <div v-if="step === 1" class="step-content">
      <!-- 搜索 -->
      <van-search
          v-model="keyword"
          placeholder="搜索检验项目名称"
          shape="round"
          background="transparent"
          @search="onSearch"
      />

      <!-- 分类筛选 -->
      <div class="category-tabs">
        <span
            v-for="cat in categories"
            :key="cat.key"
            class="category-tab"
            :class="{ active: activeCategory === cat.key }"
            @click="activeCategory = cat.key"
        >
          {{ cat.label }}
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
            <div class="project-name">{{ item.techName || item.name }}</div>
            <div class="project-desc">
              <span>{{ item.categoryName || '检验科' }}</span>
              <span>{{ item.inspectionPosition || item.specimenType || '--' }}</span>
            </div>
            <div class="project-tips" v-if="item.tips">
              <van-icon name="info-o" />
              <span>{{ item.tips }}</span>
            </div>
          </div>
          <div class="project-price">
            ¥{{ (item.techPrice || item.price || 0).toFixed(2) }}
          </div>
        </div>

        <div v-if="filteredProjects.length === 0" class="empty-state">
          <van-icon name="search" size="48" color="#C4C4D6" />
          <p>{{ keyword ? '未找到匹配的检验项目' : '暂无待预约的检验项目' }}</p>
          <p v-if="!keyword" style="font-size: 12px; color: #999; margin-top: 4px;">请先由医生开具检验申请</p>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="bottom-bar" v-if="filteredProjects.length > 0">
        <div class="bar-left">
          <van-checkbox v-model="selectAll" @change="onSelectAllChange">全选</van-checkbox>
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
            <span class="item-name">{{ item.techName || item.name }}</span>
            <span class="item-price">¥{{ (item.techPrice || item.price || 0).toFixed(2) }}</span>
          </div>
          <div class="total-price">
            <span>合计</span>
            <span class="price">¥{{ totalPrice.toFixed(2) }}</span>
          </div>
        </div>
      </div>

      <!-- 温馨提示 -->
      <div class="tips-card">
        <van-icon name="info-o" />
        <span>请按预约时间提前15分钟到检验科登记，空腹项目请保持空腹</span>
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
            <span class="label">预约项目</span>
            <span class="value">{{ selectedItems.map(i => i.techName || i.name).join('、') }}</span>
          </div>
          <div class="info-row">
            <span class="label">预约日期</span>
            <span class="value">{{ formatDate(selectedDate) }}</span>
          </div>
          <div class="info-row">
            <span class="label">预约时间</span>
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

        <div class="success-tips">
          <div class="tip-item">📍 请到检验科登记窗口报到</div>
          <div class="tip-item">📋 请携带身份证和医保卡</div>
          <div class="tip-item">⏰ 请提前15分钟到达</div>
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
import {
  getCurrentPatient,
  list,
  getPendingInspectionRequests,
  bookInspectionRequest
} from '@/api'

const router = useRouter()

// ============ 状态 ============
const step = ref(1)
const keyword = ref('')
const activeCategory = ref('all')
const projects = ref<any[]>([])
const selectedItems = ref<any[]>([])
const selectedPatient = ref<any>(null)
const selectedDate = ref('')
const selectedTime = ref('')
const submitting = ref(false)
const showPatientSheet = ref(false)
const bookingResult = ref<any>(null)
const patientList = ref<any[]>([])

// ============ 分类（用于前端筛选） ============
const categories = [
  { key: 'all', label: '全部' },
  { key: 'blood', label: '血液检验' },
  { key: 'urine', label: '尿液检验' },
  { key: 'stool', label: '粪便检验' },
  { key: 'biochemistry', label: '生化检验' },
  { key: 'immunology', label: '免疫检验' },
]

// 后端类型映射到前端分类
const categoryMapping: Record<string, string> = {
  'BLOOD': 'blood',
  'URINE': 'urine',
  'STOOL': 'stool',
  'BIOCHEMISTRY': 'biochemistry',
  'IMMUNOLOGY': 'immunology',
}

// 类型名称映射
const categoryNameMapping: Record<string, string> = {
  'BLOOD': '血液检验',
  'URINE': '尿液检验',
  'STOOL': '粪便检验',
  'BIOCHEMISTRY': '生化检验',
  'IMMUNOLOGY': '免疫检验',
}

// ============ 计算属性 ============

const filteredProjects = computed(() => {
  let result = projects.value
  if (activeCategory.value !== 'all') {
    result = result.filter(p => {
      const cat = categoryMapping[p.type] || 'other'
      return cat === activeCategory.value
    })
  }
  if (keyword.value.trim()) {
    const kw = keyword.value.trim().toLowerCase()
    result = result.filter(p => (p.techName || p.name || '').toLowerCase().includes(kw))
  }
  return result
})

const totalPrice = computed(() => {
  return selectedItems.value.reduce((sum, item) => sum + (item.techPrice || item.price || 0), 0)
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

// ============ 方法 ============

const toggleSelect = (item: any) => {
  const index = selectedItems.value.findIndex(i => i.id === item.id)
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    selectedItems.value.push(item)
  }
}

const onSelectAllChange = (val: boolean) => {
  // 由 computed 处理
}

const onSearch = () => {
  // 搜索已由 computed 处理
}

const selectPatient = (patient: any) => {
  selectedPatient.value = patient
  showPatientSheet.value = false
  // 切换就诊人后重新加载数据
  loadPendingRequests(patient.patientId || patient.id)
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

// 加载待预约检验列表
const loadPendingRequests = async (patientId: number) => {
  try {
    const res = await getPendingInspectionRequests({ patientId })
    const data = res.data || res
    projects.value = (data || []).map((item: any) => ({
      ...item,
      type: item.type || 'INSPECTION',
      categoryName: categoryNameMapping[item.type] || '检验科',
      specimenType: item.inspectionPosition,
      price: item.techPrice,
      name: item.techName,
      tips: getInspectionTips(item.techName)
    }))
  } catch (error) {
    console.error('加载检验列表失败:', error)
    projects.value = []
  }
}

// 根据项目名称生成提示
const getInspectionTips = (name: string) => {
  if (!name) return '无需特殊准备'
  if (name.includes('肝功能') || name.includes('肾功能') || name.includes('血脂')) {
    return '需空腹8小时以上'
  }
  if (name.includes('尿') && !name.includes('培养')) {
    return '留取中段尿'
  }
  if (name.includes('尿培养')) {
    return '需留取清洁中段尿'
  }
  if (name.includes('粪便')) {
    return '留取新鲜标本'
  }
  if (name.includes('糖耐量')) {
    return '需空腹10-12小时'
  }
  return '无需特殊准备'
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
    // 组装预约时间（ISO 格式）
    const bookedTime = `${selectedDate.value}T${selectedTime.value.split('-')[0]}:00`

    // 批量预约每个选中的项目
    for (const item of selectedItems.value) {
      await bookInspectionRequest({
        requestId: item.id,
        bookedTime: bookedTime
      })
    }

    bookingResult.value = {
      bookingNo: `JY${dayjs().format('YYYYMMDD')}${String(Date.now()).slice(-4)}`
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

onMounted(async () => {
  try {
    // 1. 获取当前患者信息
    const patientRes = await getCurrentPatient()
    const patient = patientRes.data || patientRes
    if (patient) {
      selectedPatient.value = patient
    }

    // 2. 获取就诊人列表
    const listRes = await list()
    const patients = listRes.data || listRes
    if (patients && patients.length > 0) {
      patientList.value = patients
      if (!selectedPatient.value) {
        const defaultPatient = patients.find((p: any) => p.isDefault) || patients[0]
        selectedPatient.value = defaultPatient
      }
    }

    // 3. 获取待预约检验列表
    const patientId = selectedPatient.value?.patientId || selectedPatient.value?.id
    if (patientId) {
      await loadPendingRequests(patientId)
    }

    // 4. 默认选中第一个日期
    if (availableDates.value.length > 0) {
      selectedDate.value = availableDates.value[0].value
    }

    // 5. 默认选中第一个可用时间段
    const firstAvailable = timeSlots.find(s => !s.disabled)
    if (firstAvailable) {
      selectedTime.value = firstAvailable.value
    }

  } catch (error) {
    console.error('加载数据失败:', error)
    showToast('加载数据失败，请重试')
  }
})
</script>


<style lang="scss" scoped>
.lab-booking-page {
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

// ===== 分类标签 =====
.category-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 8px 0 12px;
  &::-webkit-scrollbar { height: 0; }
}
.category-tab {
  flex-shrink: 0;
  padding: 4px 14px;
  border-radius: 14px;
  font-size: 13px;
  color: #6B6B7E;
  background: white;
  cursor: pointer;
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

// ===== 确认卡片 =====
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

// 就诊人选择
.patient-select {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #F5F7FA;
  border-radius: 8px;
  cursor: pointer;
  .patient-name {
    font-size: 15px;
    font-weight: 500;
  }
  .patient-id {
    font-size: 12px;
    color: #6B6B7E;
    margin-left: 8px;
  }
}

// 日期选择
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

// 时间段
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

// 已选项目
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

// ===== 温馨提示 =====
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
  .van-icon { margin-top: 2px; }
}

// ===== 步骤按钮 =====
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
.success-tips {
  text-align: left;
  background: #F5F7FA;
  border-radius: 8px;
  padding: 12px 16px;
  margin: 16px 0;
  .tip-item { font-size: 13px; color: #6B6B7E; padding: 4px 0; }
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

// ===== 空状态 =====
.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #C4C4D6;
  p { margin-top: 8px; }
}
</style>