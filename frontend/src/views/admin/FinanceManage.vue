<!-- src/views/admin/FinanceManage.vue -->
<template>
  <div class="finance-manage">
    <van-tabs v-model:active="activeTab" class="finance-tabs">
      <!-- 门诊退费 -->
      <van-tab title="门诊退费" name="refund">
        <div class="tab-content">
          <div class="search-bar">
            <van-field v-model="refundRegisterId" label="挂号ID" placeholder="输入挂号ID" type="digit">
              <template #button>
                <van-button size="small" type="primary" @click="loadPaidItems" :loading="refundLoading">查询</van-button>
              </template>
            </van-field>
          </div>
          <div v-if="paidItems.length > 0" class="item-list">
            <div v-for="item in paidItems" :key="item.id" class="item-card">
              <van-checkbox v-model="item.checked" />
              <div class="item-info">
                <div class="item-name">{{ item.itemName }}</div>
                <div class="item-type">{{ getItemTypeName(item.itemType) }}</div>
              </div>
              <div class="item-amount">¥{{ item.amount?.toFixed(2) }}</div>
            </div>
            <van-field v-model="refundReason" label="退费原因" placeholder="请输入退费原因" />
          </div>
          <div v-else class="empty-state">
            <van-icon name="refund-o" size="48" color="#C4B8A8" />
            <p>{{ refundRegisterId ? '暂无已收费项目' : '请输入挂号ID查询已收费项目' }}</p>
          </div>
        </div>
        <div v-if="paidItems.length > 0" class="bottom-bar">
          <div class="total">合计：<span class="amount">¥{{ refundTotal.toFixed(2) }}</span></div>
          <van-button type="danger" round :disabled="selectedPaid.length === 0 || refunding" :loading="refunding" @click="handleRefund">
            确认退费 ({{ selectedPaid.length }})
          </van-button>
        </div>
      </van-tab>

      <!-- 收费记录 -->
      <van-tab title="收费记录" name="records">
        <div class="tab-content">
          <div class="filter-bar">
            <van-field v-model="recordStartDate" label="开始" placeholder="YYYY-MM-DD" readonly @click="showRecordStartPicker = true" />
            <van-field v-model="recordEndDate" label="结束" placeholder="YYYY-MM-DD" readonly @click="showRecordEndPicker = true" />
            <van-button size="small" type="primary" @click="loadRecords" :loading="recordsLoading">查询</van-button>
          </div>
          <div class="record-list">
            <div v-for="rec in financeRecords" :key="rec.id" class="record-card">
              <div class="record-header">
                <span class="record-no">{{ rec.recordNo }}</span>
                <van-tag :type="rec.recordType === 'CHARGE' ? 'success' : 'danger'">
                  {{ rec.recordType === 'CHARGE' ? '收费' : '退费' }}
                </van-tag>
              </div>
              <div class="record-body">
                <div class="record-patient">{{ rec.patientName }}</div>
                <div class="record-item">{{ rec.itemName }}</div>
              </div>
              <div class="record-footer">
                <span class="record-method">{{ rec.chargeMethod || '—' }}</span>
                <span class="record-amount" :class="rec.recordType === 'REFUND' ? 'refund' : ''">
                  {{ rec.recordType === 'REFUND' ? '-' : '+' }}¥{{ rec.amount?.toFixed(2) }}
                </span>
              </div>
              <div class="record-time">{{ formatDateTime(rec.createTime) }}</div>
            </div>
            <div v-if="financeRecords.length === 0 && !recordsLoading" class="empty-state">
              <van-icon name="records-o" size="48" color="#C4B8A8" />
              <p>暂无记录</p>
            </div>
            <div v-if="recordsLoading" class="loading-state">
              <van-loading size="24" /> 加载中...
            </div>
          </div>
        </div>
      </van-tab>

      <!-- 日结统计 -->
      <van-tab title="日结统计" name="summary">
        <div class="tab-content">
          <van-field v-model="summaryDate" label="日期" placeholder="选择日期" readonly @click="showSummaryDatePicker = true" />
          <van-button type="primary" block round @click="loadSummary" :loading="summaryLoading" class="query-btn">查询日结</van-button>

          <div v-if="summaryData" class="summary-cards">
            <div class="summary-card">
              <div class="summary-label">交易总笔数</div>
              <div class="summary-value">{{ summaryData.totalTransactions || 0 }}</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">收费总额</div>
              <div class="summary-value charge">¥{{ summaryData.totalAmount?.toFixed(2) || '0.00' }}</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">退费总额</div>
              <div class="summary-value refund">¥{{ summaryData.refundAmount?.toFixed(2) || '0.00' }}</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">收费笔数</div>
              <div class="summary-value">{{ summaryData.chargeCount || 0 }}</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">退费笔数</div>
              <div class="summary-value">{{ summaryData.refundCount || 0 }}</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">操作员</div>
              <div class="summary-value text">{{ summaryData.operatorName || '—' }}</div>
            </div>
          </div>
          <div v-else-if="!summaryLoading" class="empty-state">
            <van-icon name="chart-trending-o" size="48" color="#C4B8A8" />
            <p>请选择日期查询日结统计</p>
          </div>
          <div v-if="summaryLoading" class="loading-state">
            <van-loading size="24" /> 加载中...
          </div>
        </div>
      </van-tab>
    </van-tabs>

    <van-popup v-model:show="showRecordStartPicker" position="bottom">
      <van-date-picker v-model="recordStartDateValue" @confirm="onRecordStartConfirm" @cancel="showRecordStartPicker = false" />
    </van-popup>
    <van-popup v-model:show="showRecordEndPicker" position="bottom">
      <van-date-picker v-model="recordEndDateValue" @confirm="onRecordEndConfirm" @cancel="showRecordEndPicker = false" />
    </van-popup>
    <van-popup v-model:show="showSummaryDatePicker" position="bottom">
      <van-date-picker v-model="summaryDateValue" @confirm="onSummaryDateConfirm" @cancel="showSummaryDatePicker = false" />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { refund, getFinanceRecords, getDailySummary, getPaidItems } from '@/api'
import type { FinanceRecordVO, DailySummaryVO, ChargeItem } from '@/api/model'
import dayjs from 'dayjs'

const activeTab = ref('refund')

// ========== 退费 ==========
const refundRegisterId = ref('')
const paidItems = ref<(ChargeItem & { checked: boolean })[]>([])
const refundReason = ref('')
const refundLoading = ref(false)
const refunding = ref(false)

const selectedPaid = computed(() => paidItems.value.filter(i => i.checked))
const refundTotal = computed(() => selectedPaid.value.reduce((sum, i) => sum + (Number(i.amount) || 0), 0))

const loadPaidItems = async () => {
  if (!refundRegisterId.value) { showToast('请输入挂号ID'); return }
  refundLoading.value = true
  try {
    const res = await getPaidItems({ registerId: Number(refundRegisterId.value) })
    paidItems.value = (res as any)?.map((item: ChargeItem) => ({ ...item, checked: false })) || []
    if (paidItems.value.length === 0) {
      showToast('暂无已收费项目')
    }
  } catch {
    showToast('查询失败')
  } finally {
    refundLoading.value = false
  }
}

const handleRefund = async () => {
  if (!refundReason.value) { showToast('请输入退费原因'); return }
  refunding.value = true
  try {
    await refund({
      registerId: Number(refundRegisterId.value),
      itemIds: selectedPaid.value.map(i => i.id),
      refundAmount: refundTotal.value,
      refundReason: refundReason.value
    })
    showToast('退费成功')
    paidItems.value = []
    refundRegisterId.value = ''
    refundReason.value = ''
  } catch {
    showToast('退费失败')
  } finally {
    refunding.value = false
  }
}

// ========== 收费记录 ==========
const recordStartDate = ref(dayjs().subtract(7, 'day').format('YYYY-MM-DD'))
const recordEndDate = ref(dayjs().format('YYYY-MM-DD'))
const recordStartDateValue = ref(recordStartDate.value.split('-'))
const recordEndDateValue = ref(recordEndDate.value.split('-'))
const financeRecords = ref<FinanceRecordVO[]>([])
const recordsLoading = ref(false)
const showRecordStartPicker = ref(false)
const showRecordEndPicker = ref(false)

const onRecordStartConfirm = ({ selectedValues }: any) => {
  recordStartDate.value = selectedValues.join('-')
  showRecordStartPicker.value = false
}
const onRecordEndConfirm = ({ selectedValues }: any) => {
  recordEndDate.value = selectedValues.join('-')
  showRecordEndPicker.value = false
}

const loadRecords = async () => {
  recordsLoading.value = true
  try {
    const res = await getFinanceRecords({
      startDate: recordStartDate.value,
      endDate: recordEndDate.value,
      pageNum: 1,
      pageSize: 50
    })
    financeRecords.value = (res as any)?.records || []
  } catch {
    showToast('加载记录失败')
  } finally {
    recordsLoading.value = false
  }
}

// ========== 日结统计 ==========
const summaryDate = ref(dayjs().format('YYYY-MM-DD'))
const summaryDateValue = ref(summaryDate.value.split('-'))
const summaryData = ref<DailySummaryVO | null>(null)
const summaryLoading = ref(false)
const showSummaryDatePicker = ref(false)

const onSummaryDateConfirm = ({ selectedValues }: any) => {
  summaryDate.value = selectedValues.join('-')
  showSummaryDatePicker.value = false
}

const loadSummary = async () => {
  summaryLoading.value = true
  try {
    const res = await getDailySummary({
      summaryDate: summaryDate.value
    })
    summaryData.value = res as DailySummaryVO
  } catch {
    showToast('加载日结数据失败')
  } finally {
    summaryLoading.value = false
  }
}

const getItemTypeName = (type?: string) => {
  const map: Record<string, string> = {
    'CHECK': '检查费',
    'INSPECTION': '检验费',
    'DRUG': '药费',
    'REGISTER': '挂号费',
    'DISPOSAL': '处置费'
  }
  return map[type || ''] || type || '其他'
}

const formatDateTime = (date?: string) => date ? dayjs(date).format('MM-DD HH:mm') : ''

onMounted(() => {
  loadRecords()
  loadSummary()
})
</script>

<style lang="scss" scoped>
.finance-manage {
  min-height: 100vh;
  background: #F5F5F5;
  padding-bottom: 80px;
}
.finance-tabs :deep(.van-tabs__line) {
  background-color: #F4A261;
}
.tab-content {
  padding: 12px;
}
.search-bar {
  background: white;
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 12px;
}
.item-list {
  margin-bottom: 12px;
}
.item-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.item-info {
  flex: 1;
  .item-name {
    font-size: 14px;
    color: #5C4B3A;
    font-weight: 500;
  }
  .item-type {
    font-size: 12px;
    color: #8B7A6B;
    margin-top: 2px;
  }
}
.item-amount {
  font-size: 16px;
  font-weight: 700;
  color: #E76F51;
}
.bottom-bar {
  position: fixed;
  bottom: 50px;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 16px;
  border-top: 1px solid #E8DCC8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 10;
}
.total {
  font-size: 14px;
  color: #5C4B3A;
  .amount {
    font-size: 18px;
    font-weight: 700;
    color: #E76F51;
  }
}
.filter-bar {
  background: white;
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
  align-items: center;
}
.record-list {
  margin-bottom: 12px;
}
.record-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}
.record-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  .record-no {
    font-size: 12px;
    color: #8B7A6B;
  }
}
.record-body {
  margin-bottom: 8px;
  .record-patient {
    font-size: 14px;
    font-weight: 500;
    color: #5C4B3A;
  }
  .record-item {
    font-size: 13px;
    color: #8B7A6B;
  }
}
.record-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .record-method {
    font-size: 12px;
    color: #8B7A6B;
  }
  .record-amount {
    font-size: 16px;
    font-weight: 700;
    color: #8CB369;
    &.refund {
      color: #E76F51;
    }
  }
}
.record-time {
  font-size: 12px;
  color: #C4B8A8;
  margin-top: 4px;
}
.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #C4B8A8;
}
.loading-state {
  text-align: center;
  padding: 40px 0;
  color: #7F8C8D;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}
.query-btn {
  margin: 12px 0;
  background: #F4A261;
  border-color: #F4A261;
}
.summary-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 12px;
}
.summary-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}
.summary-label {
  font-size: 13px;
  color: #8B7A6B;
  margin-bottom: 8px;
}
.summary-value {
  font-size: 20px;
  font-weight: 700;
  color: #5C4B3A;
  &.charge {
    color: #8CB369;
  }
  &.refund {
    color: #E76F51;
  }
  &.text {
    font-size: 16px;
  }
}
</style>