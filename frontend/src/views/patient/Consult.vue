<!-- src/views/patient/Consult.vue -->
<template>
  <div class="consult-page">
    <van-nav-bar title="在线咨询" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 咨询入口 -->
    <div class="consult-banner">
      <div class="banner-icon">💬</div>
      <div class="banner-text">
        <div class="banner-title">在线问诊</div>
        <div class="banner-desc">专业医生在线为您解答</div>
      </div>
    </div>

    <!-- 快速问诊 -->
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">快速问诊</span>
        <span class="section-hint">图文咨询 · 24小时响应</span>
      </div>
      <div class="quick-consult" @click="startQuickConsult">
        <div class="quick-icon">📝</div>
        <div class="quick-info">
          <div class="quick-title">图文问诊</div>
          <div class="quick-desc">描述症状，医生快速回复</div>
        </div>
        <van-icon name="arrow" class="quick-arrow" />
      </div>
    </div>

    <!-- 科室选择 -->
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">按科室咨询</span>
        <span class="section-hint">选择专科医生</span>
      </div>
      <div class="dept-grid">
        <div
            v-for="dept in departments"
            :key="dept.id"
            class="dept-item"
            @click="selectDept(dept)"
        >
          <div class="dept-icon">{{ dept.icon }}</div>
          <span class="dept-name">{{ dept.name }}</span>
        </div>
      </div>
    </div>

    <!-- 咨询记录 -->
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">咨询记录</span>
        <span class="section-more" @click="goToConsultHistory">全部</span>
      </div>
      <div
          v-for="record in consultRecords"
          :key="record.id"
          class="record-item"
          @click="viewConsult(record)"
      >
        <div class="record-left">
          <div class="record-status" :style="{ background: getStatusColor(record.status) }">
            {{ getStatusText(record.status) }}
          </div>
          <div class="record-info">
            <div class="record-title">{{ record.title }}</div>
            <div class="record-time">{{ formatTime(record.createTime) }}</div>
          </div>
        </div>
        <van-icon name="arrow" class="record-arrow" />
      </div>
      <div v-if="consultRecords.length === 0" class="empty-hint">
        暂无咨询记录
      </div>
    </div>

    <!-- 底部提示 -->
    <div class="footer-tip">
      <van-icon name="info-o" />
      <span>在线咨询不替代线下就诊，急重症请立即就医</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()

const departments = [
  { id: 1, name: '神经内科', icon: '🧠' },
  { id: 2, name: '心血管内科', icon: '❤️' },
  { id: 3, name: '呼吸内科', icon: '🫁' },
  { id: 4, name: '消化内科', icon: '🫀' },
  { id: 5, name: '骨科', icon: '🦴' },
  { id: 6, name: '儿科', icon: '👶' },
  { id: 7, name: '皮肤科', icon: '🧴' },
  { id: 8, name: '眼科', icon: '👁️' }
]

const consultRecords = ref([
  { id: 1, title: '头痛头晕咨询', status: 'COMPLETED', createTime: '2026-06-28 15:30:00' },
  { id: 2, title: '胸闷气短咨询', status: 'WAITING', createTime: '2026-06-30 09:20:00' },
  { id: 3, title: '膝关节疼痛咨询', status: 'COMPLETED', createTime: '2026-06-25 11:00:00' }
])

const formatTime = (time: string) => dayjs(time).format('MM-DD HH:mm')

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    WAITING: '待回复',
    COMPLETED: '已回复',
    CLOSED: '已关闭'
  }
  return map[status] || status
}

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    WAITING: '#FF9800',
    COMPLETED: '#4CAF50',
    CLOSED: '#C4C4D6'
  }
  return map[status] || '#C4C4D6'
}

const startQuickConsult = () => {
  showToast('即将进入图文问诊...')
}

const selectDept = (dept: any) => {
  showToast(`选择${dept.name}咨询`)
}

const goToConsultHistory = () => {
  showToast('全部咨询记录')
}

const viewConsult = (record: any) => {
  showToast(`查看咨询：${record.title}`)
}
</script>

<style lang="scss" scoped>
.consult-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 0 16px 80px;
}

.consult-banner {
  background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
  margin: 0 -16px 16px;
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  color: white;

  .banner-icon {
    font-size: 40px;
  }
  .banner-title {
    font-size: 20px;
    font-weight: 600;
  }
  .banner-desc {
    font-size: 14px;
    opacity: 0.85;
  }
}

.section-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
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
  .section-hint {
    font-size: 12px;
    color: #6B6B7E;
  }
  .section-more {
    font-size: 13px;
    color: #4CAF50;
    cursor: pointer;
  }
}

.quick-consult {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #F5F7FA;
  border-radius: 10px;
  cursor: pointer;
  &:active { background: #E8E8E8; }

  .quick-icon { font-size: 28px; }
  .quick-info {
    flex: 1;
    .quick-title { font-size: 15px; font-weight: 500; color: #1A1A2E; }
    .quick-desc { font-size: 13px; color: #6B6B7E; }
  }
  .quick-arrow { color: #C4C4D6; }
}

.dept-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.dept-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  border-radius: 8px;
  cursor: pointer;
  &:active { background: #F5F7FA; }

  .dept-icon { font-size: 28px; }
  .dept-name { font-size: 12px; color: #1A1A2E; text-align: center; }
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #F0F0F0;
  cursor: pointer;
  &:last-child { border-bottom: none; }

  .record-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .record-status {
    font-size: 11px;
    color: white;
    padding: 2px 10px;
    border-radius: 10px;
    flex-shrink: 0;
  }
  .record-title { font-size: 14px; color: #1A1A2E; }
  .record-time { font-size: 12px; color: #C4C4D6; }
  .record-arrow { color: #C4C4D6; }
}

.empty-hint {
  text-align: center;
  padding: 12px 0;
  color: #C4C4D6;
  font-size: 14px;
}

.footer-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: #C4C4D6;
  padding: 12px 0;
}
</style>