<!-- src/views/patient/Revisit.vue -->
<template>
  <div class="revisit-page">
    <van-nav-bar title="复诊预约" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 提示 -->
    <div class="tip-banner">
      <van-icon name="info-o" />
      <span>选择您需要复诊的挂号记录，快速预约复诊</span>
    </div>

    <!-- 历史就诊记录 -->
    <div class="record-list">
      <div
          v-for="record in revisitRecords"
          :key="record.id"
          class="record-card"
      >
        <div class="record-header">
          <span class="record-dept">{{ record.dept }}</span>
          <van-tag type="success" size="mini">可复诊</van-tag>
        </div>
        <div class="record-body">
          <div class="record-info">
            <span>👨‍⚕️ {{ record.doctor }}</span>
            <span>📅 {{ record.date }}</span>
            <span>🏷️ {{ record.diagnosis }}</span>
          </div>
        </div>
        <div class="record-footer">
          <span class="record-time">上次就诊：{{ record.visitTime }}</span>
          <van-button size="small" type="primary" round @click="revisit(record)">
            复诊预约
          </van-button>
        </div>
      </div>

      <div v-if="revisitRecords.length === 0" class="empty-state">
        <van-icon name="records-o" size="64" color="#C4C4D6" />
        <p>暂无复诊记录</p>
        <span class="empty-desc">您还没有完成就诊的记录</span>
      </div>
    </div>

    <!-- 复诊确认弹窗 -->
    <van-dialog
        v-model:show="showConfirm"
        title="确认复诊预约"
        :confirm-button-text="'确认预约'"
        @confirm="confirmRevisit"
    >
      <div class="revisit-confirm" v-if="selectedRecord">
        <div class="confirm-row">
          <span class="label">就诊科室</span>
          <span class="value">{{ selectedRecord.dept }}</span>
        </div>
        <div class="confirm-row">
          <span class="label">就诊医生</span>
          <span class="value">{{ selectedRecord.doctor }}</span>
        </div>
        <div class="confirm-row">
          <span class="label">上次诊断</span>
          <span class="value">{{ selectedRecord.diagnosis }}</span>
        </div>
        <div class="confirm-row">
          <span class="label">预约时间</span>
          <span class="value highlight">{{ selectedRevisitDate }}</span>
        </div>
      </div>
    </van-dialog>

    <!-- 预约成功 -->
    <van-dialog
        v-model:show="showSuccess"
        title="🎉 复诊预约成功"
        :show-cancel-button="false"
        confirm-button-text="查看预约"
        @confirm="goToRecords"
    >
      <div class="success-content">
        <div class="success-icon">
          <van-icon name="checked" size="48" color="#4CAF50" />
        </div>
        <p class="success-text">复诊预约已提交，请按时就诊</p>
        <div class="success-info">
          <div class="info-row">
            <span>预约号</span>
            <span class="highlight">{{ newRevisitNo }}</span>
          </div>
          <div class="info-row">
            <span>就诊时间</span>
            <span>{{ selectedRevisitDate }}</span>
          </div>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()

const revisitRecords = ref([
  {
    id: 1,
    dept: '呼吸内科',
    doctor: '张敏',
    date: '2026-06-25',
    diagnosis: '上呼吸道感染',
    visitTime: '2026-06-25 09:30'
  },
  {
    id: 2,
    dept: '心血管内科',
    doctor: '李为民',
    date: '2026-06-20',
    diagnosis: '高血压病',
    visitTime: '2026-06-20 10:00'
  },
  {
    id: 3,
    dept: '骨科',
    doctor: '吴刚',
    date: '2026-06-15',
    diagnosis: '膝关节骨关节炎',
    visitTime: '2026-06-15 14:30'
  }
])

const selectedRecord = ref<any>(null)
const selectedRevisitDate = ref('')
const newRevisitNo = ref('')
const showConfirm = ref(false)
const showSuccess = ref(false)

const revisit = (record: any) => {
  selectedRecord.value = record
  selectedRevisitDate.value = dayjs().add(7, 'day').format('YYYY年MM月DD日 上午')
  showConfirm.value = true
}

const confirmRevisit = () => {
  showConfirm.value = false
  newRevisitNo.value = `RF${dayjs().format('YYYYMMDD')}${String(Date.now()).slice(-4)}`
  showSuccess.value = true
}

const goToRecords = () => {
  showSuccess.value = false
  router.push('/patient/appointments')
}
</script>

<style lang="scss" scoped>
.revisit-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 0 16px 20px;
}

.tip-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #E8F5E9;
  border-radius: 10px;
  padding: 10px 14px;
  margin: 12px 0;
  font-size: 14px;
  color: #2E7D32;
  .van-icon { font-size: 18px; }
}

.record-card {
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  .record-dept { font-size: 16px; font-weight: 600; color: #1A1A2E; }
}

.record-info {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #6B6B7E;
  flex-wrap: wrap;
}

.record-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #F0F0F0;
  .record-time { font-size: 13px; color: #C4C4D6; }
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
  }
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #C4C4D6;
  p { font-size: 16px; color: #6B6B7E; margin-top: 12px; }
  .empty-desc { font-size: 13px; color: #6B6B7E; }
}

.revisit-confirm {
  padding: 8px 16px;
  .confirm-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #F0F0F0;
    &:last-child { border-bottom: none; }
    .label { font-size: 14px; color: #6B6B7E; }
    .value { font-size: 14px; color: #1A1A2E; &.highlight { color: #4CAF50; font-weight: 600; } }
  }
}

.success-content {
  text-align: center;
  padding: 16px 0;
  .success-icon { margin-bottom: 12px; }
  .success-text { font-size: 16px; color: #1A1A2E; margin-bottom: 12px; }
  .success-info {
    text-align: left;
    background: #F5F7FA;
    border-radius: 8px;
    padding: 10px 14px;
    .info-row {
      display: flex;
      justify-content: space-between;
      padding: 4px 0;
      font-size: 14px;
      color: #6B6B7E;
      .highlight { color: #4CAF50; font-weight: 600; }
    }
  }
}
</style>