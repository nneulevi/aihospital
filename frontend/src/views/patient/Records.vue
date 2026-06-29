<!-- src/views/patient/Records.vue -->
<template>
  <div class="records-page">
    <van-nav-bar title="我的病历" fixed placeholder left-arrow @click-left="() => router.back()" />

    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="onLoad">
        <div v-for="record in recordList" :key="record.registerId" class="record-card" @click="goToDetail(record.registerId!)">
          <div class="record-header">
            <div class="record-date">{{ formatDate(record.visitDate) }}</div>
            <van-tag :type="getStateType(record.visitState)">
              {{ record.visitStateName || getStateText(record.visitState) }}
            </van-tag>
          </div>
          <div class="record-info">
            <div class="record-dept">🏥 {{ record.deptName }}</div>
            <div class="record-doctor">👨‍⚕️ {{ record.doctorName }}</div>
          </div>
          <div class="record-diagnosis">
            <span class="diagnosis-label">诊断：</span>
            <span class="diagnosis-content">{{ record.diagnosis || '暂无诊断' }}</span>
          </div>
          <div v-if="record.visitState === 'REGISTERED'" class="record-actions">
            <van-button size="small" plain type="danger" @click.stop="cancelRecord(record)">
              取消挂号
            </van-button>
          </div>
        </div>
        <div v-if="recordList.length === 0 && !loading" class="empty-state">
          <van-icon name="records-o" size="64" color="#C4B8A8" />
          <p>暂无病历记录</p>
        </div>
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { cancelRegister, getRecords } from '@/api'
import type { PatientRecordListVO, PageResultPatientRecordListVO } from '@/api/model'
import { useUserStore } from '@/stores/user'
import dayjs from 'dayjs'

const router = useRouter()
const userStore = useUserStore()

const recordList = ref<PatientRecordListVO[]>([])
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)

const getPatientId = () => {
  const user = userStore.userInfo
  if (user?.patientId) return user.patientId
  const stored = localStorage.getItem('patientId')
  if (stored) return Number(stored)
  return 1
}

const loadRecords = async () => {
  loading.value = true
  try {
    const res = await getRecords({
      query: {
        patientId: getPatientId(),
        pageNum: pageNum.value,
        pageSize: pageSize.value
      }
    })
    const newRecords = res.data?.records || []
    total.value = res.data?.total || 0
    if (refreshing.value) {
      recordList.value = newRecords
      refreshing.value = false
    } else {
      recordList.value.push(...newRecords)
    }
    loading.value = false
    if (recordList.value.length >= total.value) finished.value = true
  } catch (error) {
    showToast('加载失败')
    loading.value = false
    refreshing.value = false
  }
}

const onLoad = () => {
  if (recordList.value.length < total.value) {
    pageNum.value++
    loadRecords()
  } else {
    finished.value = true
  }
}

const onRefresh = () => {
  pageNum.value = 1
  recordList.value = []
  finished.value = false
  loadRecords()
}

const cancelRecord = async (record: PatientRecordListVO) => {
  if (!record.registerId) {
    showToast('缺少挂号ID')
    return
  }
  try {
    await showConfirmDialog({
      title: '取消挂号',
      message: '确定取消该挂号记录吗？'
    })
    await cancelRegister({
      registerId: record.registerId,
      cancelReason: '患者端取消'
    })
    showToast('已取消挂号')
    onRefresh()
  } catch (error) {
    if ((error as any)?.message) showToast('取消挂号失败')
  }
}

const formatDate = (date?: string) => date ? dayjs(date).format('YYYY-MM-DD') : ''
const getStateType = (state?: string) => {
  switch (state) {
    case 'FINISHED': return 'success'
    case 'CONSULTING': return 'warning'
    case 'REGISTERED': return 'primary'
    case 'CANCELLED': return 'danger'
    default: return 'default'
  }
}
const getStateText = (state?: string) => {
  switch (state) {
    case 'FINISHED': return '已完成'
    case 'CONSULTING': return '就诊中'
    case 'REGISTERED': return '待就诊'
    case 'CANCELLED': return '已取消'
    default: return ''
  }
}
const goToDetail = (registerId: number) => router.push(`/patient/record/${registerId}`)

onMounted(() => loadRecords())
</script>

<style lang="scss" scoped>
.records-page { min-height: 100vh; background: #FFF9F0; padding-bottom: 20px; }
.record-card { background: white; margin: 12px; padding: 16px; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); cursor: pointer; }
.record-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.record-date { font-size: 14px; color: #8B7A6B; }
.record-info { display: flex; gap: 20px; margin-bottom: 8px; font-size: 14px; color: #5C4B3A; }
.record-diagnosis { font-size: 14px; .diagnosis-label { color: #8B7A6B; } .diagnosis-content { color: #5C4B3A; } }
.record-actions { display: flex; justify-content: flex-end; margin-top: 10px; }
.empty-state { text-align: center; padding: 60px 0; color: #C4B8A8; }
</style>
