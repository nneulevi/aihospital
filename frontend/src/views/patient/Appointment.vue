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
        <div v-for="dept in filteredDepts" :key="dept.id" class="dept-item" @click="selectDept(dept)">
          <div class="dept-icon">🏥</div>
          <div class="dept-info">
            <div class="dept-name">{{ dept.name }}</div>
            <div class="dept-desc">{{ dept.description || '点击查看医生排班' }}</div>
          </div>
          <van-icon name="arrow" />
        </div>
      </div>
    </div>

    <!-- Step2: 选择医生 -->
    <div v-if="step === 2" class="step-content">
      <div class="date-selector">
        <div v-for="date in dateList" :key="date.value" :class="['date-item', { active: selectedDate === date.value }]" @click="selectDate(date.value)">
          <div class="date-week">{{ date.week }}</div>
          <div class="date-day">{{ date.day }}</div>
        </div>
      </div>
      <div class="noon-selector">
        <van-button :type="selectedNoon === 'MORNING' ? 'primary' : 'default'" size="small" round @click="selectedNoon = 'MORNING'">上午</van-button>
        <van-button :type="selectedNoon === 'AFTERNOON' ? 'primary' : 'default'" size="small" round @click="selectedNoon = 'AFTERNOON'">下午</van-button>
      </div>
      <div class="doctor-list">
        <div v-for="doc in doctorList" :key="doc.doctorId" class="doctor-item" @click="selectDoctor(doc)">
          <div class="doctor-avatar"><van-icon name="doctor-o" size="36" /></div>
          <div class="doctor-info">
            <div class="doctor-name">{{ doc.doctorName }}</div>
            <div class="doctor-title">{{ doc.titleLevel }}</div>
            <div class="doctor-slots">
              <span class="slot-label">剩余号源</span>
              <span class="slot-count">{{ doc.remainingQuota || 0 }}</span>
            </div>
          </div>
          <div class="doctor-fee">
            <div class="fee-amount">¥{{ (doc as any).registFee || 50 }}</div>
            <div class="fee-type">{{ (doc as any).registLevelName || '普通号' }}</div>
          </div>
        </div>
        <div v-if="doctorList.length === 0" class="empty-state"><van-icon name="medal-o" size="48" /><p>暂无医生排班</p></div>
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
          <van-cell title="挂号费" :value="`¥${(selectedDoctor as any)?.registFee || 50}`" />
        </van-cell-group>
      </div>
      <div class="confirm-card">
        <div class="card-title">患者信息</div>
        <van-cell-group inset>
          <van-field v-model="patientInfo.realName" label="姓名" placeholder="请输入真实姓名" />
          <van-field v-model="patientInfo.gender" label="性别" placeholder="请选择性别" readonly @click="showGenderPicker = true" />
          <van-field v-model="patientInfo.cardNumber" label="身份证号" placeholder="请输入身份证号" />
          <van-field v-model="patientInfo.phone" label="手机号" placeholder="请输入手机号" />
        </van-cell-group>
      </div>
      <div class="confirm-footer">
        <van-button type="primary" block round :loading="submitting" @click="submitRegister">确认挂号</van-button>
      </div>
    </div>

    <van-action-sheet v-model:show="showGenderPicker" title="选择性别">
      <div class="gender-picker">
        <div class="gender-option" @click="selectGender('MALE')">男</div>
        <div class="gender-option" @click="selectGender('FEMALE')">女</div>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { getDoctors, patientRegister } from '@/api'
import type { DoctorListVO, PatientRegisterRequestDTO, PageResultDoctorListVO } from '@/api/model'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const step = ref(1)
const deptKeyword = ref('')
const departments = ref([
  { id: 1, name: '神经内科', description: '脑血管疾病、头痛头晕' },
  { id: 2, name: '呼吸内科', description: '感冒、咳嗽、肺炎、哮喘' },
  { id: 3, name: '消化内科', description: '胃痛、腹泻、消化不良' },
  { id: 4, name: '心血管内科', description: '高血压、冠心病' },
  { id: 5, name: '骨科', description: '骨折、关节痛' }
])
const selectedDeptId = ref<number | null>(null)
const selectedDeptName = ref('')
const doctorList = ref<DoctorListVO[]>([])
const selectedDoctor = ref<DoctorListVO | null>(null)
const selectedDate = ref(dayjs().format('YYYY-MM-DD'))
const selectedNoon = ref('MORNING')
const submitting = ref(false)
const showGenderPicker = ref(false)

const dateList = computed(() => {
  const dates = []
  for (let i = 0; i < 7; i++) {
    const date = dayjs().add(i, 'day')
    dates.push({ value: date.format('YYYY-MM-DD'), week: date.format('ddd'), day: date.format('DD') })
  }
  return dates
})

const patientInfo = ref({ realName: '', gender: 'MALE', cardNumber: '', phone: '' })
const filteredDepts = computed(() => {
  if (!deptKeyword.value) return departments.value
  return departments.value.filter(d => d.name.includes(deptKeyword.value))
})

onMounted(() => {
  const { deptId, deptName, doctorId } = route.query
  if (deptId && deptName) {
    selectedDeptId.value = Number(deptId)
    selectedDeptName.value = deptName as string
    step.value = 2
    loadDoctors()
  }
  if (doctorId) {
    selectedDeptId.value = Number(route.query.deptId) || null
    selectedDoctor.value = { doctorId: Number(doctorId), doctorName: '张敏', titleLevel: '主任医师', remainingQuota: 5, registFee: 50 } as any
    step.value = 3
  }
})

const selectDept = (dept: any) => {
  selectedDeptId.value = dept.id
  selectedDeptName.value = dept.name
  step.value = 2
  loadDoctors()
}

const selectDate = (date: string) => {
  selectedDate.value = date
  loadDoctors()
}

const loadDoctors = async () => {
  if (!selectedDeptId.value) return
  try {
    const res = await getDoctors({
      query: {
        deptId: selectedDeptId.value,
        visitDate: selectedDate.value,
        noon: selectedNoon.value,
        pageNum: 1,
        pageSize: 50
      }
    })
    doctorList.value = res.data?.records || []
  } catch { showToast('加载医生列表失败') }
}

const selectDoctor = (doctor: DoctorListVO) => {
  selectedDoctor.value = doctor
  step.value = 3
}

const selectGender = (gender: string) => {
  patientInfo.value.gender = gender
  showGenderPicker.value = false
}

const formatDate = (date: string) => dayjs(date).format('YYYY年MM月DD日')

const submitRegister = async () => {
  if (!patientInfo.value.realName || !patientInfo.value.cardNumber) {
    showToast('请填写完整患者信息')
    return
  }
  submitting.value = true
  try {
    const params: PatientRegisterRequestDTO = {
      realName: patientInfo.value.realName,
      gender: patientInfo.value.gender,
      cardNumber: patientInfo.value.cardNumber,
      birthdate: '1990-01-01',
      homeAddress: '',
      phone: patientInfo.value.phone,
      deptId: selectedDeptId.value!,
      doctorId: selectedDoctor.value!.doctorId!,
      visitDate: selectedDate.value,
      noon: selectedNoon.value,
      registLevelId: 1,
      settleCategoryId: 1,
      registMethod: 'MOBILE'
    }
    const registerId = await patientRegister(params)
    showSuccessToast('挂号成功')
    router.push({ name: 'AppointmentSuccess', query: { registerId: String(registerId.data) } })
  } catch (error: any) {
    showToast(error.message || '挂号失败')
  } finally { submitting.value = false }
}
</script>

<style lang="scss" scoped>
.appointment-page { min-height: 100vh; background: #FFF9F0; padding-bottom: 20px; }
.steps { margin: 12px 16px 0; background: transparent; }
.step-content { padding: 16px; }
.date-selector { display: flex; gap: 8px; overflow-x: auto; padding: 12px 0; margin-bottom: 12px; background: white; border-radius: 8px; }
.date-item { flex-shrink: 0; width: 52px; text-align: center; padding: 8px; border-radius: 8px; background: #FAF3E8; cursor: pointer; &.active { background: #F4A261; color: white; } }
.noon-selector { display: flex; gap: 16px; justify-content: center; margin-bottom: 12px; }
.noon-selector .van-button--primary { background: #F4A261; border-color: #F4A261; }
.doctor-item { background: white; border-radius: 8px; padding: 12px; margin-bottom: 8px; display: flex; gap: 12px; cursor: pointer; }
.doctor-avatar { width: 50px; height: 50px; background: #FAF3E8; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #F4A261; }
.doctor-info { flex: 1; .doctor-name { font-size: 16px; font-weight: 500; } .doctor-title { font-size: 12px; color: #F4A261; } }
.doctor-fee { text-align: right; .fee-amount { font-size: 18px; font-weight: 700; color: #E76F51; } .fee-type { font-size: 12px; color: #8B7A6B; } }
.confirm-card { background: white; border-radius: 8px; margin-bottom: 12px; overflow: hidden; .card-title { padding: 12px 16px; font-size: 16px; font-weight: 500; border-bottom: 1px solid #E8DCC8; } }
.confirm-footer { padding: 16px; .van-button--primary { background: #F4A261; border-color: #F4A261; height: 48px; } }
.gender-option { padding: 16px; text-align: center; border-bottom: 1px solid #E8DCC8; cursor: pointer; }
.empty-state { text-align: center; padding: 40px; color: #8B7A6B; }
</style>