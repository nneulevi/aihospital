<template>
  <div class="finance-manage">
    <van-tabs v-model:active="activeTab" class="finance-tabs">
      <van-tab title="门诊收费" name="charge">
        <section class="form-panel">
          <van-field v-model="chargeForm.registerId" label="挂号ID" type="digit" placeholder="输入挂号ID" />
          <van-field v-model="chargeForm.itemIds" label="项目ID" placeholder="多个项目用英文逗号分隔" />
          <van-field v-model="chargeForm.itemTypes" label="项目类型" placeholder="PRESCRIPTION,CHECK,INSPECTION,DISPOSAL" />
          <van-field v-model="chargeForm.amount" label="收费金额" type="number" placeholder="输入本次收费金额" />
          <van-field v-model="chargeForm.chargeMethod" label="收费方式" placeholder="CASH / WECHAT / ALIPAY" />
          <van-button type="primary" block round :loading="charging" @click="confirmCharge">确认收费</van-button>
        </section>
      </van-tab>

      <van-tab title="门诊退费" name="refund">
        <section class="form-panel">
          <van-field v-model="refundForm.registerId" label="挂号ID" type="digit" placeholder="输入挂号ID" />
          <van-field v-model="refundForm.itemIds" label="项目ID" placeholder="多个项目用英文逗号分隔" />
          <van-field v-model="refundForm.itemTypes" label="项目类型" placeholder="PRESCRIPTION,CHECK,INSPECTION,DISPOSAL" />
          <van-field v-model="refundForm.amount" label="退费金额" type="number" placeholder="输入本次退费金额" />
          <van-field v-model="refundForm.reason" label="退费原因" type="textarea" rows="2" autosize placeholder="输入退费原因" />
          <van-button type="danger" block round :loading="refunding" @click="handleRefund">确认退费</van-button>
        </section>
      </van-tab>

      <van-tab title="收费记录" name="records">
        <section class="query-panel">
          <van-field v-model="recordStartDate" label="开始日期" readonly placeholder="YYYY-MM-DD" @click="showRecordStartPicker = true" />
          <van-field v-model="recordEndDate" label="结束日期" readonly placeholder="YYYY-MM-DD" @click="showRecordEndPicker = true" />
          <van-button size="small" type="primary" :loading="recordsLoading" @click="loadRecords">查询</van-button>
        </section>

        <div class="record-list">
          <article v-for="record in financeRecords" :key="record.id" class="record-card">
            <header>
              <span>{{ record.recordNo || `#${record.id}` }}</span>
              <van-tag :type="record.recordType === 'REFUND' ? 'danger' : 'success'">
                {{ record.recordType === 'REFUND' ? '退费' : '收费' }}
              </van-tag>
            </header>
            <div class="record-main">
              <strong>{{ record.patientName || '未知患者' }}</strong>
              <span>{{ record.itemName || record.itemType || '未命名项目' }}</span>
            </div>
            <footer>
              <span>{{ record.chargeMethod || '--' }}</span>
              <span :class="{ refund: record.recordType === 'REFUND' }">
                {{ record.recordType === 'REFUND' ? '-' : '+' }}¥{{ formatMoney(record.amount) }}
              </span>
            </footer>
            <div class="record-time">{{ formatDateTime(record.createTime) }}</div>
          </article>
          <van-empty v-if="!recordsLoading && financeRecords.length === 0" description="暂无收费记录" />
        </div>
      </van-tab>

      <van-tab title="日结统计" name="summary">
        <section class="query-panel">
          <van-field v-model="summaryDate" label="日期" readonly placeholder="YYYY-MM-DD" @click="showSummaryDatePicker = true" />
          <van-button type="primary" block round :loading="summaryLoading" @click="loadSummary">查询日结</van-button>
        </section>

        <section v-if="summaryData" class="summary-grid">
          <div class="summary-item"><span>交易笔数</span><strong>{{ summaryData.totalTransactions ?? 0 }}</strong></div>
          <div class="summary-item"><span>收费总额</span><strong>¥{{ formatMoney(summaryData.totalAmount) }}</strong></div>
          <div class="summary-item"><span>退费总额</span><strong class="refund">¥{{ formatMoney(summaryData.refundAmount) }}</strong></div>
          <div class="summary-item"><span>收费笔数</span><strong>{{ summaryData.chargeCount ?? 0 }}</strong></div>
          <div class="summary-item"><span>退费笔数</span><strong>{{ summaryData.refundCount ?? 0 }}</strong></div>
          <div class="summary-item"><span>操作员</span><strong>{{ summaryData.operatorName || '--' }}</strong></div>
        </section>
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
import { ref } from 'vue'
import { showToast } from 'vant'
import dayjs from 'dayjs'
import { charge, refund, getFinanceRecords, getDailySummary } from '@/api'
import type { ChargeRequestDTO, DailySummaryVO, FinanceRecordVO, RefundRequestDTO } from '@/api/model'

const activeTab = ref('charge')
const charging = ref(false)
const refunding = ref(false)
const recordsLoading = ref(false)
const summaryLoading = ref(false)

const chargeForm = ref({ registerId: '', itemIds: '', itemTypes: '', amount: '', chargeMethod: 'CASH' })
const refundForm = ref({ registerId: '', itemIds: '', itemTypes: '', amount: '', reason: '' })

const recordStartDate = ref(dayjs().subtract(7, 'day').format('YYYY-MM-DD'))
const recordEndDate = ref(dayjs().format('YYYY-MM-DD'))
const recordStartDateValue = ref(recordStartDate.value.split('-'))
const recordEndDateValue = ref(recordEndDate.value.split('-'))
const financeRecords = ref<FinanceRecordVO[]>([])
const showRecordStartPicker = ref(false)
const showRecordEndPicker = ref(false)

const summaryDate = ref(dayjs().format('YYYY-MM-DD'))
const summaryDateValue = ref(summaryDate.value.split('-'))
const summaryData = ref<DailySummaryVO | null>(null)
const showSummaryDatePicker = ref(false)

const parseItemIds = (value: string) => value
  .split(',')
  .map(item => Number(item.trim()))
  .filter(item => Number.isInteger(item) && item > 0)

const parseItemTypes = (value: string) => value
  .split(',')
  .map(item => item.trim().toUpperCase())
  .filter(Boolean)

const confirmCharge = async () => {
  const itemIds = parseItemIds(chargeForm.value.itemIds)
  const itemTypes = parseItemTypes(chargeForm.value.itemTypes)
  const registerId = Number(chargeForm.value.registerId)
  const amount = Number(chargeForm.value.amount)
  if (!registerId || itemIds.length === 0 || !amount) {
    showToast('请填写挂号ID、项目ID和金额')
    return
  }
  if (itemTypes.length > 0 && itemTypes.length !== itemIds.length) {
    showToast('项目类型数量需与项目ID一致')
    return
  }

  charging.value = true
  try {
    const dto: ChargeRequestDTO = {
      registerId,
      itemIds,
      itemTypes: itemTypes.length ? itemTypes : undefined,
      amount,
      chargeMethod: chargeForm.value.chargeMethod || 'CASH'
    }
    await charge(dto)
    showToast('收费成功')
    chargeForm.value = { registerId: '', itemIds: '', itemTypes: '', amount: '', chargeMethod: 'CASH' }
    await loadRecords()
  } catch {
    showToast('收费失败')
  } finally {
    charging.value = false
  }
}

const handleRefund = async () => {
  const itemIds = parseItemIds(refundForm.value.itemIds)
  const itemTypes = parseItemTypes(refundForm.value.itemTypes)
  const registerId = Number(refundForm.value.registerId)
  const refundAmount = Number(refundForm.value.amount)
  if (!registerId || itemIds.length === 0 || !refundAmount || !refundForm.value.reason) {
    showToast('请填写完整退费信息')
    return
  }
  if (itemTypes.length > 0 && itemTypes.length !== itemIds.length) {
    showToast('项目类型数量需与项目ID一致')
    return
  }

  refunding.value = true
  try {
    const dto: RefundRequestDTO = {
      registerId,
      itemIds,
      itemTypes: itemTypes.length ? itemTypes : undefined,
      refundAmount,
      refundReason: refundForm.value.reason
    }
    await refund(dto)
    showToast('退费成功')
    refundForm.value = { registerId: '', itemIds: '', itemTypes: '', amount: '', reason: '' }
    await loadRecords()
  } catch {
    showToast('退费失败')
  } finally {
    refunding.value = false
  }
}

const onRecordStartConfirm = ({ selectedValues }: any) => {
  recordStartDate.value = selectedValues.join('-')
  recordStartDateValue.value = selectedValues
  showRecordStartPicker.value = false
}

const onRecordEndConfirm = ({ selectedValues }: any) => {
  recordEndDate.value = selectedValues.join('-')
  recordEndDateValue.value = selectedValues
  showRecordEndPicker.value = false
}

const loadRecords = async () => {
  recordsLoading.value = true
  try {
    const res = await getFinanceRecords({
      query: {
        startDate: recordStartDate.value,
        endDate: recordEndDate.value,
        pageNum: 1,
        pageSize: 50
      }
    })
    const data = res.data || res
    financeRecords.value = data.records || []
  } catch {
    showToast('收费记录加载失败')
  } finally {
    recordsLoading.value = false
  }
}

const onSummaryDateConfirm = ({ selectedValues }: any) => {
  summaryDate.value = selectedValues.join('-')
  summaryDateValue.value = selectedValues
  showSummaryDatePicker.value = false
}

const loadSummary = async () => {
  summaryLoading.value = true
  try {
    const res = await getDailySummary({ query: { summaryDate: summaryDate.value } })
    summaryData.value = (res.data || res) as DailySummaryVO
  } catch {
    showToast('日结统计加载失败')
  } finally {
    summaryLoading.value = false
  }
}

const formatDateTime = (date?: string) => date ? dayjs(date).format('MM-DD HH:mm') : '--'
const formatMoney = (value?: number) => Number(value || 0).toFixed(2)
</script>

<style lang="scss" scoped>
.finance-manage {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 20px;
}
.form-panel,
.query-panel {
  display: grid;
  gap: 10px;
  margin: 12px;
  padding: 12px;
  background: #fff;
  border: 1px solid #eef0f3;
  border-radius: 8px;
}
.record-list {
  padding: 0 12px 12px;
}
.record-card {
  margin-bottom: 10px;
  padding: 12px;
  background: #fff;
  border: 1px solid #eef0f3;
  border-radius: 8px;
}
.record-card header,
.record-card footer,
.record-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.record-main {
  margin: 10px 0;
  color: #263238;
}
.record-time {
  margin-top: 6px;
  color: #7a8699;
  font-size: 12px;
}
.refund {
  color: #d93025;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin: 12px;
}
.summary-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  background: #fff;
  border: 1px solid #eef0f3;
  border-radius: 8px;
}
.summary-item span {
  color: #7a8699;
  font-size: 13px;
}
.summary-item strong {
  color: #263238;
  font-size: 18px;
}
</style>
