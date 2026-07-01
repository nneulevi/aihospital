<!-- src/views/patient/Appointment.vue -->
<template>
  <div class="appointment-page">
    <van-nav-bar title="门诊挂号" fixed placeholder left-arrow @click-left="() => router.back()" />

    <van-steps :active="step - 1" class="steps">
      <van-step>选择科室</van-step>
      <van-step>选择医生</van-step>
      <van-step>确认信息</van-step>
    </van-steps>

    <!-- Step1: 选择科室 -->
    <div v-if="step === 1" class="step-content">
      <div class="search-bar">
        <van-search v-model="deptKeyword" placeholder="搜索科室名称" shape="round" background="transparent" />
      </div>
      <div class="dept-list">
        <div
            v-for="dept in filteredDepts"
            :key="dept.id || dept.deptId || Math.random()"
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
        <div v-if="loadingDepts" class="loading-state"><van-loading size="32px" /><p>加载科室中...</p></div>
        <div v-if="!loadingDepts && departments.length === 0" class="empty-state">
          <van-icon name="medal-o" size="48" />
          <p>暂无科室数据</p>
        </div>
      </div>
    </div>

    <!-- Step2: 选择医生 -->
    <div v-if="step === 2" class="step-content">
      <div class="dept-breadcrumb">
        <span class="breadcrumb-text">当前科室：{{ selectedDeptName }}</span>
        <span class="breadcrumb-back" @click="step = 1">重新选择</span>
      </div>

      <div class="date-selector">
        <div
            v-for="date in dateList"
            :key="date.value"
            :class="['date-item', { active: selectedDate === date.value }]"
            @click="selectDate(date.value)"
        >
          <div class="date-week">{{ date.week }}</div>
          <div class="date-day">{{ date.day }}</div>
          <div class="date-month">{{ date.month }}</div>
        </div>
      </div>

      <div class="noon-selector">
        <van-button
            :type="selectedNoon === 'MORNING' ? 'primary' : 'default'"
            size="small"
            round
            @click="selectedNoon = 'MORNING'; loadDoctors()"
        >
          上午
        </van-button>
        <van-button
            :type="selectedNoon === 'AFTERNOON' ? 'primary' : 'default'"
            size="small"
            round
            @click="selectedNoon = 'AFTERNOON'; loadDoctors()"
        >
          下午
        </van-button>
      </div>

      <div class="doctor-list">
        <div
            v-for="doc in doctorList"
            :key="doc.doctorId"
            class="doctor-item"
            @click="selectDoctor(doc)"
        >
          <div class="doctor-avatar">
            <van-icon name="doctor-o" size="36" />
          </div>
          <div class="doctor-info">
            <div class="doctor-name">{{ doc.doctorName }}</div>
            <div class="doctor-title">{{ doc.titleLevel }}</div>
            <div class="doctor-dept">{{ doc.deptName }}</div>
          </div>
          <div class="doctor-right">
            <div class="doctor-slots">
              <span class="slot-label">剩余号源</span>
              <span class="slot-count">{{ doc.remainingQuota || 0 }}</span>
            </div>
            <div class="doctor-fee">
              <span class="fee-amount">¥{{ doc.registFee || 50 }}</span>
            </div>
          </div>
        </div>
        <div v-if="loadingDoctors" class="loading-state">
          <van-loading size="32px" />
          <p>加载医生排班中...</p>
        </div>
        <div v-else-if="doctorList.length === 0" class="empty-state">
          <van-icon name="medal-o" size="48" />
          <p>暂无医生排班</p>
        </div>
      </div>
    </div>

    <!-- Step3: 确认信息 -->
    <div v-if="step === 3" class="step-content">
      <div class="confirm-card">
        <div class="card-title">就诊信息</div>
        <van-cell-group inset>
          <van-cell title="就诊科室" :value="selectedDeptName" />
          <van-cell title="医生" :value="selectedDoctor?.doctorName" />
          <van-cell title="职称" :value="selectedDoctor?.titleLevel" />
          <van-cell title="就诊日期" :value="formatDate(selectedDate)" />
          <van-cell title="就诊时间" :value="selectedNoon === 'MORNING' ? '上午' : '下午'" />
          <van-cell title="挂号费" :value="`¥${selectedDoctor?.registFee || 50}`" />
        </van-cell-group>
      </div>

      <div class="confirm-card">
        <div class="card-header">
          <span class="card-title">患者信息</span>
          <span class="card-action" @click="showPatientSelector = true">切换就诊人</span>
        </div>
        <div class="patient-form">
          <!-- 病历号（只读） -->
          <van-field
              v-model="formData.caseNumber"
              label="病历号"
              placeholder="病历号"
              readonly
              left-icon="records"
          />
          <!-- 姓名 -->
          <van-field
              v-model="formData.realName"
              label="姓名"
              placeholder="请输入姓名"
              clearable
              left-icon="user-o"
              :rules="[{ required: true, message: '请输入姓名' }]"
          />
          <!-- 性别 - 使用 Picker -->
          <van-field
              v-model="formData.gender"
              label="性别"
              placeholder="请选择性别"
              readonly
              is-link
              left-icon="user-o"
              @click="showGenderPicker = true"
          />
          <!-- 身份证号 -->
          <van-field
              v-model="formData.cardNumber"
              label="身份证号"
              placeholder="请输入身份证号"
              clearable
              left-icon="idcard"
              :rules="[{ required: true, message: '请输入身份证号' }]"
          />
          <!-- 出生日期 - 使用原生 input -->
          <van-field
              label="出生日期"
              left-icon="calendar-o"
          >
            <template #input>
              <input
                  type="date"
                  v-model="formData.birthdate"
                  class="custom-date-input"
                  placeholder="请选择出生日期"
              />
            </template>
          </van-field>
          <!-- 手机号 -->
          <van-field
              v-model="formData.phone"
              label="手机号"
              placeholder="请输入手机号"
              clearable
              left-icon="phone-o"
              type="tel"
              :rules="[{ required: true, message: '请输入手机号' }]"
          />
          <!-- 家庭地址 -->
          <van-field
              v-model="formData.homeAddress"
              label="家庭地址"
              placeholder="请输入家庭地址"
              clearable
              left-icon="location-o"
          />
        </div>
      </div>

      <div class="confirm-footer">
        <van-button
            type="primary"
            block
            round
            :loading="submitting"
            :disabled="!selectedPatient"
            @click="submitRegister"
        >
          确认挂号
        </van-button>
      </div>
    </div>

    <!-- 就诊人选择弹窗 -->
    <van-action-sheet v-model:show="showPatientSelector" title="选择就诊人">
      <div class="patient-select-list">
        <div
            v-for="patient in patientList"
            :key="patient.patientId"
            class="patient-select-item"
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
        <div class="add-patient-btn" @click="goToPatientManager">
          <van-icon name="plus" /> 添加就诊人
        </div>
      </div>
    </van-action-sheet>

    <!-- 性别选择器 -->
    <van-picker
        v-model:show="showGenderPicker"
        :columns="genderColumns"
        title="请选择性别"
        @confirm="onGenderConfirm"
        @cancel="showGenderPicker = false"
    />

    <!-- 挂号成功弹窗 -->
    <van-dialog
        v-model:show="showSuccessDialog"
        title="🎉 挂号成功"
        :show-cancel-button="false"
        confirm-button-text="查看挂号记录"
        @confirm="goToRecords"
    >
      <div class="success-content">
        <div class="success-icon">
          <van-icon name="checked" size="48" color="#4CAF50" />
        </div>
        <div class="success-info">
          <div class="info-row">
            <span class="label">就诊科室</span>
            <span class="value">{{ selectedDeptName }}</span>
          </div>
          <div class="info-row">
            <span class="label">就诊医生</span>
            <span class="value">{{ selectedDoctor?.doctorName }}</span>
          </div>
          <div class="info-row">
            <span class="label">就诊时间</span>
            <span class="value">{{ formatDate(selectedDate) }} {{ selectedNoon === 'MORNING' ? '上午' : '下午' }}</span>
          </div>
          <div class="info-row">
            <span class="label">排队序号</span>
            <span class="value highlight">{{ newRegisterId ? (newRegisterId % 20 + 1) : '--' }}</span>
          </div>
        </div>
        <div class="success-tip">请按时到院就诊，携带身份证和医保卡</div>
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'
import {
  listDepartments,
  getDoctors,
  patientRegister,
  list,
} from '@/api'
import { useUserStore } from '@/stores/user'
import type { DeptListVO, DoctorListVO, PatientListVO } from '@/api/model'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// ============ 状态 ============
const step = ref(1)
const deptKeyword = ref('')
const selectedDeptId = ref<number | null>(null)
const selectedDeptName = ref('')
const selectedDoctor = ref<any>(null)
const selectedDate = ref(dayjs().format('YYYY-MM-DD'))
const selectedNoon = ref('MORNING')
const selectedPatient = ref<any>(null)
const submitting = ref(false)
const loadingDoctors = ref(false)
const loadingDepts = ref(false)
const showPatientSelector = ref(false)
const showSuccessDialog = ref(false)
const newRegisterId = ref<number | null>(null)
const showGenderPicker = ref(false)

const departments = ref<DeptListVO[]>([])
const patientList = ref<PatientListVO[]>([])
const doctorList = ref<DoctorListVO[]>([])

// ============ 表单数据 ============
const formData = ref({
  caseNumber: '',
  realName: '',
  gender: '',
  cardNumber: '',
  birthdate: '',
  phone: '',
  homeAddress: ''
})

// ============ Picker 列配置 ============
const genderColumns = [
  { text: '男', value: '男' },
  { text: '女', value: '女' }
]

// ============ 计算属性 ============
const dateList = computed(() => {
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

const filteredDepts = computed(() => {
  if (!deptKeyword.value) return departments.value
  return departments.value.filter(d =>
      (d.name || '').includes(deptKeyword.value) ||
      (d.description || '').includes(deptKeyword.value)
  )
})

// ============ 监听就诊人变化，更新表单 ============
watch(selectedPatient, (newPatient) => {
  if (newPatient) {
    formData.value = {
      caseNumber: newPatient.caseNumber || '',
      realName: newPatient.realName || '',
      gender: newPatient.gender === 'MALE' ? '男' : (newPatient.gender || ''),
      cardNumber: newPatient.cardNumber || '',
      birthdate: newPatient.birthdate || '',
      phone: newPatient.phone || '',
      homeAddress: newPatient.homeAddress || ''
    }
    console.log('📝 [Appointment] 表单数据已更新:', formData.value)
  }
}, { immediate: true })

// ============ 获取科室ID ============
const getDeptId = (dept: DeptListVO): number | null => {
  const id = (dept as any).id ?? (dept as any).deptId ?? (dept as any).departmentId ?? null
  if (id === null || id === undefined) return null
  return typeof id === 'string' ? parseInt(id) : id
}

// ============ 加载科室 ============
const loadDepartments = async () => {
  loadingDepts.value = true
  try {
    const res = await listDepartments() as DeptListVO[]
    departments.value = res.map(d => {
      const id = getDeptId(d)
      return {
        ...d,
        id: id || undefined,
        icon: d.icon || '🏥',
        description: d.description || '点击查看医生排班'
      }
    })
  } catch (error) {
    console.error('❌ [Appointment] 加载科室失败:', error)
    showToast('加载科室失败')
  } finally {
    loadingDepts.value = false
  }
}

// ============ 加载就诊人 ============
const loadPatients = async () => {
  try {
    const res = await list() as PatientListVO[]
    console.log('📥 [Appointment] 就诊人数据:', res)
    patientList.value = res.map(p => ({
      patientId: (p as any).id || (p as any).patientId,
      realName: p.realName,
      gender: p.gender,
      cardNumber: p.cardNumber,
      phone: p.phone,
      age: p.age,
      caseNumber: p.caseNumber,
      birthdate: (p as any).birthdate || '',
      homeAddress: (p as any).homeAddress || '',
      isDefault: (p as any).isDefault
    }))
    if (!selectedPatient.value && patientList.value.length > 0) {
      selectedPatient.value = patientList.value.find(p => p.isDefault) || patientList.value[0]
    }
  } catch (error) {
    console.error('❌ [Appointment] 加载就诊人失败:', error)
    showToast('加载就诊人失败')
  }
}

// ============ 加载医生排班 ============
const loadDoctors = async () => {
  console.log('🔍 [Appointment] ===== loadDoctors 开始 =====')
  console.log('🔍 [Appointment] selectedDeptId 值:', selectedDeptId.value)
  console.log('🔍 [Appointment] selectedDate 值:', selectedDate.value)
  console.log('🔍 [Appointment] selectedNoon 原始值:', selectedNoon.value)

  const noonStr = selectedNoon.value === 'MORNING' ? '上午' : '下午'
  console.log('🔍 [Appointment] 转换后的 noon:', noonStr)

  if (!selectedDeptId.value) {
    console.warn('⚠️ [Appointment] selectedDeptId 为空，跳过加载')
    showToast('请先选择科室')
    return
  }

  loadingDoctors.value = true
  doctorList.value = []

  try {
    const params = {
      deptId: selectedDeptId.value,
      visitDate: selectedDate.value,
      noon: noonStr,
      pageNum: 1,
      pageSize: 20
    }

    console.log('📤 [Appointment] 请求医生排班参数:', JSON.stringify(params, null, 2))

    const res = await getDoctors(params) as any

    if (res && res.records) {
      doctorList.value = res.records
      console.log('📥 [Appointment] 医生列表长度:', doctorList.value.length)
    } else if (Array.isArray(res)) {
      doctorList.value = res
    } else {
      doctorList.value = []
    }
  } catch (error: any) {
    console.error('❌ [Appointment] 加载医生排班失败:', error)
    if (error.response) {
      const errorMsg = error.response.data?.message || error.response.data?.msg || '加载医生排班失败'
      showToast(errorMsg)
    } else {
      showToast(error.message || '加载医生排班失败')
    }
  } finally {
    loadingDoctors.value = false
  }
}

// ============ 选择科室 ============
const selectDept = (dept: DeptListVO) => {
  const id = getDeptId(dept)
  if (id === null || id === undefined) {
    showToast('科室ID获取失败，请重新选择')
    return
  }
  selectedDeptId.value = id
  selectedDeptName.value = dept.name || ''
  step.value = 2
  loadDoctors()
}

// ============ 选择日期 ============
const selectDate = (date: string) => {
  selectedDate.value = date
  loadDoctors()
}

// ============ 选择医生 ============
const selectDoctor = (doctor: DoctorListVO) => {
  selectedDoctor.value = doctor
  step.value = 3
  if (!selectedPatient.value && patientList.value.length > 0) {
    selectedPatient.value = patientList.value.find(p => p.isDefault) || patientList.value[0]
  }
}

// ============ 选择就诊人 ============
const selectPatient = (patient: any) => {
  selectedPatient.value = patient
  showPatientSelector.value = false
}

const goToPatientManager = () => {
  showPatientSelector.value = false
  router.push('/patient/patient-manager')
}

// ============ 性别选择 ============
const onGenderConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  if (selectedValues && selectedValues.length > 0) {
    formData.value.gender = selectedValues[0]
  }
  showGenderPicker.value = false
}

// ============ 格式化日期 ============
const formatDate = (date: string) => dayjs(date).format('YYYY年MM月DD日')

// ============ 提交挂号 ============
const submitRegister = async () => {
  // 验证表单
  if (!formData.value.realName) {
    showToast('请输入姓名')
    return
  }
  if (!formData.value.gender) {
    showToast('请选择性别')
    return
  }
  if (!formData.value.cardNumber) {
    showToast('请输入身份证号')
    return
  }
  if (!formData.value.phone) {
    showToast('请输入手机号')
    return
  }

  // 转换 noon 为中文
  const noonStr = selectedNoon.value === 'MORNING' ? '上午' : '下午'

  // 构建完整的挂号请求参数
  const registerData = {
    patientId: selectedPatient.value.patientId,
    caseNumber: formData.value.caseNumber,
    realName: formData.value.realName,
    gender: formData.value.gender,
    cardNumber: formData.value.cardNumber,
    birthdate: formData.value.birthdate || '',
    phone: formData.value.phone,
    homeAddress: formData.value.homeAddress || '',
    deptId: selectedDeptId.value,
    doctorId: selectedDoctor.value.doctorId,
    visitDate: selectedDate.value,
    noon: noonStr,
    registLevelId: 1,
    settleCategoryId: 1,
    registMethod: '在线预约'
  }

  console.log('📤 [Appointment] ===== 提交挂号 =====')
  console.log('📤 [Appointment] 请求参数:', JSON.stringify(registerData, null, 2))

  submitting.value = true
  try {
    const res = await patientRegister(registerData) as number
    console.log('📥 [Appointment] 挂号响应:', res)
    newRegisterId.value = res
    showSuccessDialog.value = true
  } catch (error: any) {
    console.error('❌ [Appointment] 挂号失败:', error)
    if (error.response?.data?.message) {
      showToast(error.response.data.message)
    } else if (error.response?.data?.msg) {
      showToast(error.response.data.msg)
    } else {
      showToast(error.message || '挂号失败，请重试')
    }
  } finally {
    submitting.value = false
  }
}

// 🔥 修改：跳转到挂号记录列表，传递 patientId
const goToRecords = () => {
  showSuccessDialog.value = false
  const patientId = selectedPatient.value?.patientId
  console.log('📤 [Appointment] 跳转到挂号记录，patientId:', patientId)
  router.push({
    path: '/patient/appointments',
    query: {
      patientId: patientId ? String(patientId) : ''
    }
  })
}

// ============ 生命周期 ============
onMounted(async () => {
  console.log('🚀 [Appointment] 页面加载')

  await loadDepartments()
  await loadPatients()

  const { deptId, deptName, doctorId } = route.query

  if (deptId && deptName) {
    selectedDeptId.value = Number(deptId)
    selectedDeptName.value = deptName as string
    step.value = 2
    await loadDoctors()
    if (doctorId) {
      const target = doctorList.value.find(d => d.doctorId === Number(doctorId))
      if (target) selectDoctor(target)
    }
  }
})
</script>

<style lang="scss" scoped>
.appointment-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}

.steps {
  margin: 12px 16px 0;
  background: transparent;
}

.step-content {
  padding: 16px;
}

// ===== 科室面包屑 =====
.dept-breadcrumb {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);

  .breadcrumb-text {
    font-size: 15px;
    font-weight: 500;
    color: #1A1A2E;
  }

  .breadcrumb-back {
    font-size: 13px;
    color: #4CAF50;
    cursor: pointer;
    &:hover { text-decoration: underline; }
  }
}

// ===== 科室列表 =====
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
  transition: transform 0.1s;
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

// ===== 日期选择 =====
.date-selector {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  margin-bottom: 12px;
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  &::-webkit-scrollbar { height: 0; }
}
.date-item {
  flex-shrink: 0;
  width: 56px;
  text-align: center;
  padding: 8px 4px;
  border-radius: 10px;
  background: #F5F7FA;
  cursor: pointer;
  transition: all 0.2s;
  .date-week { font-size: 12px; color: #6B6B7E; }
  .date-day { font-size: 18px; font-weight: 600; color: #1A1A2E; }
  .date-month { font-size: 10px; color: #6B6B7E; }
  &.active {
    background: #4CAF50;
    .date-week, .date-day, .date-month { color: white; }
  }
}

// ===== 上下午切换 =====
.noon-selector {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 12px;
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
  }
}

// ===== 医生列表 =====
.doctor-item {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 8px;
  display: flex;
  gap: 12px;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: transform 0.1s;
  &:active { transform: scale(0.98); }
}
.doctor-avatar {
  width: 50px;
  height: 50px;
  background: #E8F5E9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4CAF50;
  flex-shrink: 0;
}
.doctor-info {
  flex: 1;
  .doctor-name { font-size: 16px; font-weight: 500; color: #1A1A2E; }
  .doctor-title { font-size: 13px; color: #4CAF50; margin-top: 2px; }
  .doctor-dept { font-size: 12px; color: #6B6B7E; margin-top: 2px; }
}
.doctor-right {
  text-align: right;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
}
.doctor-slots {
  .slot-label { font-size: 12px; color: #6B6B7E; }
  .slot-count {
    font-size: 18px;
    font-weight: 700;
    color: #4CAF50;
    margin-left: 4px;
  }
}
.doctor-fee {
  .fee-amount {
    font-size: 18px;
    font-weight: 700;
    color: #E76F51;
  }
}

// ===== 确认信息 =====
.confirm-card {
  background: white;
  border-radius: 12px;
  margin-bottom: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .card-title {
    padding: 12px 16px;
    font-size: 16px;
    font-weight: 500;
    border-bottom: 1px solid #E8E8E8;
  }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid #E8E8E8;
    .card-title { font-size: 16px; font-weight: 500; border: none; padding: 0; }
    .card-action { font-size: 13px; color: #4CAF50; cursor: pointer; }
  }
}

// ===== 患者表单 =====
.patient-form {
  padding: 8px 0;
  :deep(.van-field) {
    padding: 12px 16px;
    .van-field__label {
      width: 90px;
      color: #1A1A2E;
      font-weight: 500;
    }
    .van-field__body {
      input {
        &::placeholder {
          color: #B0B0C0;
        }
      }
    }
  }
}

// ===== 自定义日期输入框 =====
.custom-date-input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: #1A1A2E;
  width: 100%;
  padding: 4px 0;
  font-family: inherit;
  &::-webkit-calendar-picker-indicator {
    opacity: 0.6;
    padding: 4px;
    cursor: pointer;
  }
  &::placeholder {
    color: #B0B0C0;
  }
}

.confirm-footer {
  padding: 16px 0;
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
    height: 48px;
  }
}

// ===== 就诊人选择 =====
.patient-select-list {
  padding: 8px 16px 20px;
}
.patient-select-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 4px;
  cursor: pointer;
  &.active { background: #E8F5E9; }
}
.patient-info {
  .patient-name { font-size: 16px; font-weight: 500; color: #1A1A2E; }
  .patient-meta {
    font-size: 13px;
    color: #6B6B7E;
    display: flex;
    gap: 12px;
    margin-top: 2px;
  }
}
.add-patient-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  border: 2px dashed #D0D0D0;
  border-radius: 10px;
  margin-top: 8px;
  cursor: pointer;
  color: #4A4A5E;
  font-size: 14px;
  &:hover { border-color: #4CAF50; color: #4CAF50; }
}

// ===== 成功弹窗 =====
.success-content {
  padding: 16px 24px 24px;
  text-align: center;
}
.success-icon {
  margin-bottom: 12px;
}
.success-info {
  text-align: left;
  background: #F5F7FA;
  border-radius: 8px;
  padding: 12px 16px;
  margin: 12px 0;
  .info-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #E8E8E8;
    &:last-child { border-bottom: none; }
    .label { font-size: 14px; color: #6B6B7E; }
    .value { font-size: 14px; color: #1A1A2E; &.highlight { font-weight: 700; color: #FF9800; font-size: 18px; } }
  }
}
.success-tip {
  font-size: 13px;
  color: #6B6B7E;
  padding: 8px 12px;
  background: #FFF3E0;
  border-radius: 6px;
}

// ===== 加载/空状态 =====
.loading-state, .empty-state {
  text-align: center;
  padding: 40px 0;
  color: #6B6B7E;
  p { margin-top: 12px; }
}
</style>