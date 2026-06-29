<!-- src/views/patient/AppointmentRecords.vue -->
<template>
  <div class="appointment-records">
    <van-nav-bar title="挂号记录" fixed placeholder left-arrow @click-left="() => router.back()" />

    <van-tabs v-model:active="activeTab" class="record-tabs" @change="onTabChange">
      <van-tab title="全部" name="all" />
      <van-tab title="待就诊" name="REGISTERED" />
      <van-tab title="就诊中" name="CONSULTING" />
      <van-tab title="已完成" name="FINISHED" />
      <van-tab title="已取消" name="CANCELLED" />
    </van-tabs>

    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多记录了"
          @load="onLoad"
      >
        <div
            v-for="record in recordList"
            :key="record.registerId"
            class="record-card"
            @click="goToDetail(record.registerId!)"
        >
          <div class="record-top">
            <div class="record-dept">
              <span class="dept-icon">{{ getDeptIcon(record.deptName) }}</span>
              {{ record.deptName }}
            </div>
            <van-tag :type="getStateType(record.visitState)" size="small">
              {{ record.visitStateName || getStateText(record.visitState) }}
            </van-tag>
          </div>
          <div class="record-info">
            <span class="info-item"><van-icon name="doctor-o" /> {{ record.doctorName }}</span>
            <span class="info-item"><van-icon name="calendar-o" /> {{ formatDate(record.visitDate) }}</span>
            <span class="info-item"><van-icon name="clock-o" /> {{ record.noon === 'MORNING' ? '上午' : '下午' }}</span>
          </div>
          <div class="record-footer">
            <template v-if="record.visitState === 'REGISTERED'">
              <span class="queue-info"><van-icon name="label-o" /> 排队序号：{{ record.queueNumber || '--' }}</span>
              <div class="footer-actions">
                <van-button
                    v-if="!record.checkinStatus"
                    size="small"
                    type="primary"
                    round
                    @click.stop="goToCheckin(record)"
                >
                  就诊报到
                </van-button>
                <van-button
                    v-else
                    size="small"
                    type="success"
                    plain
                    round
                    disabled
                >
                  已报到
                </van-button>
                <van-button size="small" plain round @click.stop="cancelRegister(record)">取消挂号</van-button>
              </div>
            </template>
            <template v-else-if="record.visitState === 'CONSULTING'">
              <span class="consulting-info"><van-icon name="volume-o" /> 正在就诊，请耐心等待</span>
              <van-button size="small" type="warning" plain round disabled>就诊中</van-button>
            </template>
            <template v-else-if="record.visitState === 'FINISHED'">
              <span class="diagnosis-preview"><van-icon name="file-o" /> {{ record.diagnosis || '查看诊断详情' }}</span>
              <van-button size="small" plain round @click.stop="goToDetail(record.registerId!)">查看详情</van-button>
            </template>
            <template v-else-if="record.visitState === 'CANCELLED'">
              <span class="cancelled-info"><van-icon name="info-o" /> 已取消挂号</span>
              <van-button size="small" type="primary" plain round @click.stop="reRegister(record)">重新挂号</van-button>
            </template>
          </div>
        </div>
        <div v-if="recordList.length === 0 && !loading" class="empty-state">
          <van-icon name="records-o" size="64" color="#C4C4D6" />
          <p class="empty-title">暂无挂号记录</p>
          <p class="empty-desc">去首页预约挂号吧</p>
          <van-button type="primary" round size="small" @click="goToHome">去挂号</van-button>
        </div>
      </van-list>
    </van-pull-refresh>

    <van-dialog
        v-model:show="showCancelDialog"
        title="确认取消挂号"
        message="取消后号源将释放，确定要取消吗？"
        show-cancel-button
        confirm-button-color="#E76F51"
        @confirm="confirmCancel"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import dayjs from 'dayjs'
import { getRecords, cancelRegister } from '@/api'
import { useUserStore } from '@/stores/user'
import type { PageResultPatientRecordListVO, PatientRecordListVO } from '@/api/model'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('all')
const recordList = ref<PatientRecordListVO[]>([])
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const showCancelDialog = ref(false)
const cancelTarget = ref<PatientRecordListVO | null>(null)

// ===== 科室图标映射 =====
const deptIcons: Record<string, string> = {
  '神经内科': '🧠',
  '呼吸内科': '🫁',
  '消化内科': '🫀',
  '心血管内科': '❤️',
  '骨科': '🦴',
  '儿科': '👶',
  '眼科': '👁️',
  '皮肤科': '🧴',
}

const getDeptIcon = (name?: string) => {
  if (!name) return '🏥'
  return deptIcons[name] || '🏥'
}

// ===== 加载数据 =====
const loadRecords = async () => {
  loading.value = true
  try {
    const patientId = userStore.patientId
    if (!patientId) {
      loading.value = false
      return
    }
    const res = await getRecords({
      query: {
        pageNum: pageNum.value,
        pageSize: pageSize.value,
        patientId: patientId,
        visitState: activeTab.value === 'all' ? undefined : activeTab.value
      }
    }) as PageResultPatientRecordListVO
    total.value = res.total || 0
    const records = res.records || []
    if (refreshing.value) {
      recordList.value = records
      refreshing.value = false
    } else {
      recordList.value.push(...records)
    }
    if (recordList.value.length >= total.value) finished.value = true
  } catch {
    showToast('加载挂号记录失败')
  } finally {
    loading.value = false
  }
}

const onRefresh = () => {
  pageNum.value = 1
  recordList.value = []
  finished.value = false
  loadRecords()
}

const onLoad = () => {
  if (recordList.value.length < total.value) {
    pageNum.value++
    loadRecords()
  } else {
    finished.value = true
  }
}

const onTabChange = () => {
  pageNum.value = 1
  recordList.value = []
  finished.value = false
  loadRecords()
}

// ===== 工具方法 =====
const getStateText = (state?: string) => {
  const map: Record<string, string> = {
    REGISTERED: '待就诊', CONSULTING: '就诊中', FINISHED: '已完成', CANCELLED: '已取消'
  }
  return map[state || ''] || state || ''
}

const getStateType = (state?: string) => {
  const map: Record<string, string> = {
    REGISTERED: 'primary', CONSULTING: 'warning', FINISHED: 'success', CANCELLED: 'danger'
  }
  return map[state || ''] || 'default'
}

const formatDate = (date?: string) => {
  if (!date) return ''
  return dayjs(date).format('MM-DD')
}

// ===== 操作 =====
const goToDetail = (registerId: number) => {
  router.push(`/patient/record/${registerId}`)
}

const goToCheckin = (record: PatientRecordListVO) => {
  router.push({
    path: '/patient/checkin',
    query: { registerId: String(record.registerId) }
  })
}

const cancelRegister = (record: PatientRecordListVO) => {
  cancelTarget.value = record
  showCancelDialog.value = true
}

const confirmCancel = async () => {
  if (!cancelTarget.value) return
  try {
    await cancelRegister({
      registerId: cancelTarget.value.registerId!,
      cancelReason: '用户主动取消'
    })
    showSuccessToast('已取消挂号')
    // 刷新列表
    pageNum.value = 1
    recordList.value = []
    finished.value = false
    await loadRecords()
  } catch {
    showToast('取消挂号失败')
  }
  cancelTarget.value = null
  showCancelDialog.value = false
}

const reRegister = (record: PatientRecordListVO) => {
  router.push({
    path: '/patient/appointment',
    query: {
      deptId: String(record.deptId || ''),
      deptName: record.deptName || '',
      doctorId: String(record.doctorId || '')
    }
  })
}

const goToHome = () => router.push('/patient/home')

onMounted(loadRecords)
</script>



<style lang="scss" scoped>
.appointment-records {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}
.record-tabs { background: white; :deep(.van-tabs__line) { background-color: #4CAF50; } }
.record-card {
  background: white; margin: 12px 16px; padding: 16px; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06); cursor: pointer;
  &:active { transform: scale(0.98); }
}
.record-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.record-dept { font-size: 16px; font-weight: 600; color: #1A1A2E; .dept-icon { margin-right: 6px; } }
.record-info { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 10px; }
.info-item { font-size: 14px; color: #6B6B7E; display: flex; align-items: center; gap: 4px; }
.record-footer {
  display: flex; justify-content: space-between; align-items: center; padding-top: 10px;
  border-top: 1px solid #F0F0F0; flex-wrap: wrap; gap: 8px;
}
.queue-info { font-size: 14px; color: #FF9800; display: flex; align-items: center; gap: 4px; }
.footer-actions { display: flex; gap: 8px; .van-button--primary { background: #4CAF50; border-color: #4CAF50; } }
.consulting-info { font-size: 14px; color: #FF9800; display: flex; align-items: center; gap: 4px; }
.diagnosis-preview { font-size: 14px; color: #6B6B7E; display: flex; align-items: center; gap: 4px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cancelled-info { font-size: 14px; color: #E76F51; display: flex; align-items: center; gap: 4px; }
.empty-state { text-align: center; padding: 60px 20px; color: #C4C4D6; }
.empty-title { font-size: 16px; color: #6B6B7E; margin-top: 12px; }
.empty-desc { font-size: 14px; margin: 4px 0 16px; }
</style>