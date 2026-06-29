<template>
  <main class="mini-page">
    <van-nav-bar title="预约挂号" />

    <section class="panel">
      <div class="section-title">
        <span>选择科室</span>
      </div>
      <div class="dept-grid">
        <button
          v-for="dept in departments"
          :key="dept.deptId"
          type="button"
          :class="{ active: selectedDeptId === dept.deptId }"
          @click="selectDept(dept)"
        >
          {{ dept.deptName }}
        </button>
      </div>
    </section>

    <section class="panel">
      <div class="section-title">
        <span>可预约医生</span>
        <small>{{ selectedDate }}</small>
      </div>
      <div class="doctor-list">
        <button
          v-for="doctor in doctorList"
          :key="doctor.doctorId"
          type="button"
          :class="{ active: selectedDoctor?.doctorId === doctor.doctorId }"
          @click="selectedDoctor = doctor"
        >
          <strong>{{ doctor.doctorName }}</strong>
          <span>{{ selectedDeptName }} · 剩余 {{ doctor.remainingQuota ?? doctor.registQuota ?? 0 }} 个号</span>
        </button>
      </div>
      <van-empty v-if="!doctorList.length" description="暂无可预约号源" />
    </section>

    <section class="panel">
      <div class="section-title">
        <span>就诊信息</span>
      </div>
      <van-field v-model="patientInfo.realName" label="姓名" placeholder="请输入姓名" />
      <van-field v-model="patientInfo.phone" label="手机号" placeholder="请输入手机号" />
      <van-field v-model="patientInfo.cardNumber" label="身份证" placeholder="请输入身份证号" />
      <van-radio-group v-model="selectedNoon" direction="horizontal" class="noon-group">
        <van-radio name="MORNING">上午</van-radio>
        <van-radio name="AFTERNOON">下午</van-radio>
      </van-radio-group>
      <van-button block type="primary" :loading="submitting" @click="submitRegister">确认挂号</van-button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'
import { getDoctors, patientRegister } from '@/api'
import { useUserStore } from '@/stores/user'
import type { DoctorListVO, PatientRegisterRequestDTO } from '@/api/model'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const departments = [
  { deptId: 1, deptName: '神经内科' },
  { deptId: 2, deptName: '神经外科' },
  { deptId: 3, deptName: '放射科' },
  { deptId: 4, deptName: '全科门诊' },
]
const selectedDeptId = ref(Number(route.query.deptId) || departments[0].deptId)
const selectedDeptName = ref(String(route.query.deptName || departments[0].deptName))
const selectedDate = ref(dayjs().format('YYYY-MM-DD'))
const selectedNoon = ref('MORNING')
const selectedDoctor = ref<DoctorListVO | null>(null)
const doctorList = ref<DoctorListVO[]>([])
const submitting = ref(false)
const patientInfo = reactive({
  realName: userStore.userName || '',
  phone: (userStore.userInfo as any)?.phone || '13800001111',
  cardNumber: '110101199001011234',
})

const selectDept = async (dept: { deptId: number; deptName: string }) => {
  selectedDeptId.value = dept.deptId
  selectedDeptName.value = dept.deptName
  selectedDoctor.value = null
  await loadDoctors()
}

const loadDoctors = async () => {
  try {
    const res = await getDoctors({
      query: {
        deptId: selectedDeptId.value,
        scheduleDate: selectedDate.value,
        noon: selectedNoon.value,
        pageNum: 1,
        pageSize: 20,
      },
    })
    const rows = res.data?.records || res.records || []
    doctorList.value = rows
    selectedDoctor.value = rows[0] || null
  } catch {
    doctorList.value = []
  }
}

const submitRegister = async () => {
  if (!selectedDoctor.value?.doctorId) {
    showToast('请选择医生')
    return
  }
  submitting.value = true
  try {
    const payload: PatientRegisterRequestDTO = {
      realName: patientInfo.realName || userStore.userName || '患者',
      gender: 'MALE',
      cardNumber: patientInfo.cardNumber,
      birthdate: '1990-01-01',
      homeAddress: '本地患者登记地址',
      phone: patientInfo.phone,
      deptId: selectedDeptId.value,
      doctorId: selectedDoctor.value.doctorId,
      visitDate: selectedDate.value,
      noon: selectedNoon.value,
      registLevelId: 1,
      settleCategoryId: 1,
      registMethod: 'MINI_PROGRAM',
    }
    const res = await patientRegister(payload)
    showToast('挂号成功')
    router.push({ path: '/mini-patient/records', query: { registerId: String(res.data || res) } })
  } catch {
    showToast('当前号源暂不可约')
  } finally {
    submitting.value = false
  }
}

onMounted(loadDoctors)
</script>

<style lang="scss" scoped>
.mini-page {
  padding-bottom: 18px;
}

.panel {
  margin: 14px 16px;
  padding: 16px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(31, 42, 55, 0.06);
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  color: #1f2a37;
  font-size: 16px;
  font-weight: 600;
}

.section-title small {
  color: #687789;
  font-weight: 400;
}

.dept-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.dept-grid button,
.doctor-list button {
  border: 1px solid #e6ebf2;
  border-radius: 8px;
  background: #f9fbff;
  color: #243447;
}

.dept-grid button {
  min-height: 42px;
  font-size: 14px;
}

.dept-grid button.active,
.doctor-list button.active {
  border-color: #2375ff;
  background: #eef5ff;
  color: #2375ff;
}

.doctor-list {
  display: grid;
  gap: 10px;
}

.doctor-list button {
  text-align: left;
  padding: 12px;
}

.doctor-list strong,
.doctor-list span {
  display: block;
}

.doctor-list strong {
  font-size: 15px;
}

.doctor-list span {
  margin-top: 5px;
  color: #687789;
  font-size: 12px;
}

.noon-group {
  margin: 14px 0;
}

:deep(.van-button--primary) {
  background: #2375ff;
  border-color: #2375ff;
}
</style>
