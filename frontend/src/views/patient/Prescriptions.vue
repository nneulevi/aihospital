<!-- src/views/patient/Prescriptions.vue -->
<template>
  <div class="prescriptions-page">
    <van-nav-bar title="处方查询" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-item">
        <span class="stat-number">{{ prescriptions.length }}</span>
        <span class="stat-label">总处方</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-number">{{ activeCount }}</span>
        <span class="stat-label">进行中</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-number">{{ completedCount }}</span>
        <span class="stat-label">已完成</span>
      </div>
    </div>

    <!-- Tab 切换 -->
    <van-tabs v-model:active="activeTab" class="prescription-tabs">
      <van-tab title="全部" name="all" />
      <van-tab title="进行中" name="ACTIVE" />
      <van-tab title="已完成" name="COMPLETED" />
      <van-tab title="已取消" name="CANCELLED" />
    </van-tabs>

    <!-- 处方列表 -->
    <div class="prescription-list">
      <div
          v-for="prescription in filteredPrescriptions"
          :key="prescription.id"
          class="prescription-card"
          @click="viewPrescription(prescription)"
      >
        <div class="card-header">
          <div class="header-left">
            <span class="prescription-no">处方号：{{ prescription.prescriptionNo }}</span>
            <span class="prescription-date">{{ formatDate(prescription.creationTime) }}</span>
          </div>
          <van-tag :type="getStatusType(prescription.status)" size="small">
            {{ getStatusText(prescription.status) }}
          </van-tag>
        </div>

        <div class="card-body">
          <div class="dept-info">
            <span>🏥 {{ prescription.deptName || '--' }}</span>
            <span>👨‍⚕️ {{ prescription.doctorName || '--' }}</span>
          </div>
          <div class="drug-summary">
            <span class="drug-count">共 {{ prescription.drugs?.length || 0 }} 种药品</span>
            <span class="total-amount">¥{{ prescription.totalAmount?.toFixed(2) || '0.00' }}</span>
          </div>
        </div>

        <div class="card-footer">
          <div class="drug-tags">
            <van-tag
                v-for="drug in (prescription.drugs || []).slice(0, 3)"
                :key="drug.drugId"
                size="small"
                plain
            >
              {{ drug.drugName }}
            </van-tag>
            <van-tag v-if="(prescription.drugs || []).length > 3" size="small" plain>
              +{{ (prescription.drugs || []).length - 3 }}
            </van-tag>
          </div>
          <van-button
              v-if="prescription.status === 'ACTIVE'"
              size="small"
              type="primary"
              round
              @click.stop="goToPay(prescription)"
          >
            去缴费
          </van-button>
        </div>
      </div>

      <div v-if="filteredPrescriptions.length === 0" class="empty-state">
        <van-icon name="bill-o" size="64" color="#C4C4D6" />
        <p>暂无处方</p>
        <span class="empty-desc">医生开具处方后，将在此显示</span>
      </div>
    </div>

    <!-- ===== 处方详情弹窗 ===== -->
    <van-popup
        v-model:show="showDetail"
        position="bottom"
        :style="{ height: '85%', borderRadius: '16px 16px 0 0' }"
        closeable
        close-icon-position="top-right"
    >
      <div class="prescription-detail" v-if="currentPrescription">
        <!-- 头部 -->
        <div class="detail-header">
          <div class="detail-title">处方详情</div>
          <div class="detail-subtitle">
            <span>处方号：{{ currentPrescription.prescriptionNo }}</span>
            <span>{{ formatDateTime(currentPrescription.creationTime) }}</span>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="detail-section">
          <div class="info-grid">
            <div class="info-item">
              <span class="label">就诊科室</span>
              <span class="value">{{ currentPrescription.deptName || '--' }}</span>
            </div>
            <div class="info-item">
              <span class="label">开方医生</span>
              <span class="value">{{ currentPrescription.doctorName || '--' }}</span>
            </div>
            <div class="info-item">
              <span class="label">患者姓名</span>
              <span class="value">{{ currentPrescription.patientName || '--' }}</span>
            </div>
            <div class="info-item">
              <span class="label">处方状态</span>
              <van-tag :type="getStatusType(currentPrescription.status)" size="small">
                {{ getStatusText(currentPrescription.status) }}
              </van-tag>
            </div>
          </div>
        </div>

        <!-- 药品列表 -->
        <div class="detail-section">
          <div class="section-title">
            <span>💊 药品明细</span>
            <span class="section-count">共 {{ currentPrescription.drugs?.length || 0 }} 种</span>
          </div>
          <div class="drug-list">
            <div
                v-for="(item, index) in currentPrescription.drugs"
                :key="item.drugId || index"
                class="drug-item"
            >
              <div class="drug-top">
                <span class="drug-name">{{ item.drugName }}</span>
                <span class="drug-price">¥{{ item.price?.toFixed(2) || '0.00' }}</span>
              </div>
              <div class="drug-bottom">
                <span>规格：{{ item.specification || '--' }}</span>
                <span>用量：{{ item.dosage || '--' }}</span>
                <span>频次：{{ item.frequency || '--' }}</span>
                <span>天数：{{ item.days || '--' }}天</span>
                <span>数量：{{ item.quantity || 0 }}</span>
              </div>
            </div>
          </div>

          <div class="total-price-row">
            <span class="total-label">合计金额</span>
            <span class="total-price">¥{{ currentPrescription.totalAmount?.toFixed(2) || '0.00' }}</span>
          </div>
        </div>

        <!-- 医嘱说明 -->
        <div class="detail-section" v-if="currentPrescription.remark">
          <div class="section-title">📋 医嘱说明</div>
          <div class="remark-content">{{ currentPrescription.remark }}</div>
        </div>

        <!-- 底部操作 -->
        <div class="detail-actions">
          <van-button plain round size="small" @click="showDetail = false">
            关闭
          </van-button>
          <van-button
              v-if="currentPrescription.status === 'ACTIVE'"
              type="primary"
              round
              size="small"
              @click="goToPay(currentPrescription)"
          >
            去缴费
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()

// ============ 状态 ============
const activeTab = ref('all')
const prescriptions = ref<any[]>([])
const showDetail = ref(false)
const currentPrescription = ref<any>(null)

// ============ 模拟数据 ============

const mockPrescriptions = [
  {
    id: 1,
    prescriptionNo: 'CF202606250001',
    deptName: '呼吸内科',
    doctorName: '张敏',
    patientName: '张明',
    status: 'ACTIVE',
    totalAmount: 156.50,
    creationTime: '2026-06-25 10:30:00',
    remark: '饭后服用，多喝水，注意休息',
    drugs: [
      { drugId: 1, drugName: '阿莫西林胶囊', specification: '0.5g*20粒', dosage: '0.5g', frequency: '每日3次', days: 7, quantity: 2, price: 36.50 },
      { drugId: 2, drugName: '盐酸氨溴索片', specification: '30mg*20片', dosage: '30mg', frequency: '每日3次', days: 7, quantity: 1, price: 28.00 },
      { drugId: 3, drugName: '复方甘草口服液', specification: '100ml', dosage: '10ml', frequency: '每日3次', days: 5, quantity: 1, price: 22.00 }
    ]
  },
  {
    id: 2,
    prescriptionNo: 'CF202606240001',
    deptName: '消化内科',
    doctorName: '陈明',
    patientName: '张明',
    status: 'ACTIVE',
    totalAmount: 89.50,
    creationTime: '2026-06-24 15:20:00',
    remark: '饭前服用，忌辛辣刺激食物',
    drugs: [
      { drugId: 4, drugName: '奥美拉唑肠溶胶囊', specification: '20mg*14粒', dosage: '20mg', frequency: '每日1次', days: 14, quantity: 1, price: 45.00 },
      { drugId: 5, drugName: '铝碳酸镁咀嚼片', specification: '0.5g*20片', dosage: '0.5g', frequency: '每日3次', days: 7, quantity: 1, price: 44.50 }
    ]
  },
  {
    id: 3,
    prescriptionNo: 'CF202606200001',
    deptName: '心血管内科',
    doctorName: '孙伟',
    patientName: '张秀兰',
    status: 'COMPLETED',
    totalAmount: 125.00,
    creationTime: '2026-06-20 09:00:00',
    remark: '按时服药，定期监测血压',
    drugs: [
      { drugId: 6, drugName: '苯磺酸氨氯地平片', specification: '5mg*28片', dosage: '5mg', frequency: '每日1次', days: 28, quantity: 1, price: 78.00 },
      { drugId: 7, drugName: '酒石酸美托洛尔片', specification: '25mg*20片', dosage: '25mg', frequency: '每日1次', days: 20, quantity: 1, price: 47.00 }
    ]
  },
  {
    id: 4,
    prescriptionNo: 'CF202606150001',
    deptName: '骨科',
    doctorName: '吴刚',
    patientName: '张明',
    status: 'CANCELLED',
    totalAmount: 78.00,
    creationTime: '2026-06-15 11:30:00',
    remark: '--',
    drugs: [
      { drugId: 8, drugName: '布洛芬缓释胶囊', specification: '0.3g*20粒', dosage: '0.3g', frequency: '每日2次', days: 10, quantity: 1, price: 38.00 },
      { drugId: 9, drugName: '活血止痛胶囊', specification: '0.5g*24粒', dosage: '1g', frequency: '每日2次', days: 10, quantity: 1, price: 40.00 }
    ]
  },
  {
    id: 5,
    prescriptionNo: 'CF202606180001',
    deptName: '呼吸内科',
    doctorName: '李华',
    patientName: '张明',
    status: 'COMPLETED',
    totalAmount: 210.00,
    creationTime: '2026-06-18 14:00:00',
    remark: '如症状加重及时复诊',
    drugs: [
      { drugId: 10, drugName: '头孢克肟分散片', specification: '0.1g*12片', dosage: '0.1g', frequency: '每日2次', days: 6, quantity: 1, price: 65.00 },
      { drugId: 11, drugName: '肺力咳合剂', specification: '100ml', dosage: '15ml', frequency: '每日3次', days: 6, quantity: 1, price: 45.00 },
      { drugId: 12, drugName: '盐酸氨溴索片', specification: '30mg*20片', dosage: '30mg', frequency: '每日3次', days: 6, quantity: 1, price: 28.00 },
      { drugId: 13, drugName: '孟鲁司特钠片', specification: '10mg*6片', dosage: '10mg', frequency: '每日1次', days: 6, quantity: 1, price: 72.00 }
    ]
  }
]

// ============ 计算属性 ============

const activeCount = computed(() => {
  return prescriptions.value.filter(p => p.status === 'ACTIVE').length
})

const completedCount = computed(() => {
  return prescriptions.value.filter(p => p.status === 'COMPLETED').length
})

const filteredPrescriptions = computed(() => {
  if (activeTab.value === 'all') return prescriptions.value
  return prescriptions.value.filter(p => p.status === activeTab.value)
})

// ============ 工具方法 ============

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    ACTIVE: 'warning',
    COMPLETED: 'success',
    CANCELLED: 'danger'
  }
  return map[status] || 'default'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    ACTIVE: '进行中',
    COMPLETED: '已完成',
    CANCELLED: '已取消'
  }
  return map[status] || status
}

const formatDate = (date: string) => {
  if (!date) return ''
  return dayjs(date).format('MM-DD')
}

const formatDateTime = (date: string) => {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

// ============ 操作方法 ============

const viewPrescription = (prescription: any) => {
  currentPrescription.value = prescription
  showDetail.value = true
}

const goToPay = (prescription: any) => {
  showDetail.value = false
  router.push({
    path: '/patient/orders',
    query: { prescriptionId: String(prescription.id) }
  })
}

// ============ 加载数据 ============

const loadPrescriptions = async () => {
  try {
    await new Promise(resolve => setTimeout(resolve, 300))
    prescriptions.value = mockPrescriptions.map(p => ({ ...p }))
  } catch {
    showToast('加载处方失败')
  }
}

// ============ 生命周期 ============

onMounted(() => {
  loadPrescriptions()
})
</script>

<style lang="scss" scoped>
.prescriptions-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}

// ===== 统计卡片 =====
.stats-row {
  display: flex;
  align-items: center;
  background: white;
  margin: 12px 16px;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stat-item {
  flex: 1;
  text-align: center;
  .stat-number {
    display: block;
    font-size: 24px;
    font-weight: 700;
    color: #1A1A2E;
  }
  .stat-label {
    font-size: 12px;
    color: #6B6B7E;
  }
}
.stat-divider {
  width: 1px;
  height: 36px;
  background: #E8E8E8;
}

// ===== Tab =====
.prescription-tabs {
  background: white;
  :deep(.van-tabs__line) {
    background-color: #4CAF50;
  }
}

// ===== 处方列表 =====
.prescription-list {
  padding: 12px 16px;
}

.prescription-card {
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: transform 0.1s;
  &:active {
    transform: scale(0.98);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    .prescription-no {
      font-size: 14px;
      font-weight: 600;
      color: #1A1A2E;
    }
    .prescription-date {
      font-size: 12px;
      color: #6B6B7E;
    }
  }
}

.card-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0 8px;
  border-bottom: 1px solid #F0F0F0;
  .dept-info {
    font-size: 13px;
    color: #6B6B7E;
    display: flex;
    gap: 16px;
  }
  .drug-summary {
    text-align: right;
    .drug-count {
      font-size: 12px;
      color: #6B6B7E;
      display: block;
    }
    .total-amount {
      font-size: 16px;
      font-weight: 600;
      color: #E76F51;
    }
  }
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  .drug-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    .van-tag {
      background: #F5F7FA;
      color: #6B6B7E;
    }
  }
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
  }
}

// ===== 空状态 =====
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #C4C4D6;
  p {
    font-size: 16px;
    color: #6B6B7E;
    margin-top: 12px;
  }
  .empty-desc {
    font-size: 13px;
    color: #6B6B7E;
  }
}

// ===== 处方详情弹窗 =====
.prescription-detail {
  padding: 20px 16px 80px;
  height: 100%;
  overflow-y: auto;
}

.detail-header {
  padding-bottom: 16px;
  border-bottom: 1px solid #E8E8E8;
  margin-bottom: 16px;
  .detail-title {
    font-size: 20px;
    font-weight: 600;
    color: #1A1A2E;
  }
  .detail-subtitle {
    font-size: 14px;
    color: #6B6B7E;
    display: flex;
    gap: 16px;
    margin-top: 4px;
  }
}

.detail-section {
  margin-bottom: 16px;
  .section-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 15px;
    font-weight: 600;
    color: #1A1A2E;
    margin-bottom: 10px;
    padding-left: 10px;
    border-left: 3px solid #4CAF50;
    .section-count {
      font-size: 13px;
      font-weight: 400;
      color: #6B6B7E;
    }
  }
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  .info-item {
    display: flex;
    flex-direction: column;
    padding: 6px 12px;
    background: #F5F7FA;
    border-radius: 6px;
    .label {
      font-size: 11px;
      color: #6B6B7E;
    }
    .value {
      font-size: 14px;
      color: #1A1A2E;
      font-weight: 500;
    }
  }
}

.drug-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.drug-item {
  background: #F5F7FA;
  border-radius: 8px;
  padding: 10px 14px;
  .drug-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .drug-name {
      font-size: 14px;
      font-weight: 500;
      color: #1A1A2E;
    }
    .drug-price {
      font-size: 14px;
      font-weight: 600;
      color: #E76F51;
    }
  }
  .drug-bottom {
    font-size: 12px;
    color: #6B6B7E;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 4px;
  }
}

.total-price-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #FFF8E1;
  border-radius: 8px;
  .total-label {
    font-size: 14px;
    font-weight: 500;
    color: #1A1A2E;
  }
  .total-price {
    font-size: 20px;
    font-weight: 700;
    color: #E76F51;
  }
}

.remark-content {
  background: #F5F7FA;
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 14px;
  color: #1A1A2E;
  line-height: 1.6;
}

.detail-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 16px;
  display: flex;
  gap: 12px;
  border-top: 1px solid #E8E8E8;
  .van-button {
    flex: 1;
    height: 40px;
  }
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
  }
}
</style>