<!-- src/views/admin/DrugManage.vue -->
<template>
  <div class="drug-manage">
    <van-tabs v-model:active="activeTab" class="drug-tabs">
      <!-- 药品库存 -->
      <van-tab title="药品库存" name="inventory">
        <div class="tab-content">
          <div class="search-bar">
            <van-search
                v-model="drugKeyword"
                placeholder="搜索药品名称"
                shape="round"
                background="transparent"
                @search="onSearch"
                @clear="onClear"
            />
          </div>
          <div class="inventory-list">
            <div v-for="drug in displayList" :key="drug.drugId" class="drug-card" :class="{ 'low-stock': drug.alert }">
              <div class="drug-header">
                <div class="drug-name">{{ drug.drugName }}</div>
                <van-tag v-if="drug.alert" type="danger">库存不足</van-tag>
              </div>
              <div class="drug-info">
                <div class="info-row"><span class="label">编码</span><span class="value">{{ drug.drugCode }}</span></div>
                <div class="info-row"><span class="label">规格</span><span class="value">{{ drug.drugFormat }}</span></div>
                <div class="info-row"><span class="label">单位</span><span class="value">{{ drug.drugUnit }}</span></div>
                <div class="info-row"><span class="label">库存</span><span class="value" :class="drug.alert ? 'warning' : ''">{{ drug.stockNum }}</span></div>
                <div class="info-row"><span class="label">单价</span><span class="value">¥{{ drug.drugPrice?.toFixed(2) }}</span></div>
                <div class="info-row"><span class="label">厂家</span><span class="value">{{ drug.manufacturer }}</span></div>
              </div>
            </div>
            <div v-if="displayList.length === 0" class="empty-state">
              <van-icon name="medal-o" size="48" color="#C4B8A8" />
              <p>暂无库存数据</p>
            </div>
          </div>
          <div v-if="filteredList.length > pageSize" class="pagination">
            <van-button size="small" :disabled="currentPage === 1" @click="currentPage--">上一页</van-button>
            <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
            <van-button size="small" :disabled="currentPage === totalPages" @click="currentPage++">下一页</van-button>
          </div>
        </div>
      </van-tab>

      <!-- 发药 -->
      <van-tab title="发药" name="dispense">
        <div class="tab-content">
          <div v-if="pendingDispenseList.length > 0" class="prescription-list">
            <div v-for="p in pendingDispenseList" :key="p.prescriptionId"
                 class="prescription-card"
                 :class="{ selected: selectedDispense?.prescriptionId === p.prescriptionId }"
                 @click="selectDispense(p)">
              <div class="prescription-header">
                <span class="patient-name">{{ p.patientName }}</span>
                <span class="prescription-id">处方#{{ p.prescriptionId }}</span>
              </div>
              <div class="drug-list">
                <div v-for="drug in p.drugList" :key="drug.drugId" class="drug-item">
                  {{ drug.drugName }} × {{ drug.quantity }}{{ drug.drugUnit }}
                </div>
              </div>
              <div class="prescription-footer">
                <span class="amount">¥{{ p.totalAmount?.toFixed(2) }}</span>
                <van-tag type="warning">待发药</van-tag>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <van-icon name="medal-o" size="48" color="#C4B8A8" />
            <p>暂无待发药处方</p>
          </div>
          <div v-if="selectedDispense" class="form-card">
            <van-field v-model="dispensePharmacistId" label="药师ID" placeholder="请输入药师ID" type="digit" />
            <van-button type="primary" block round :loading="dispensing" @click="handleDispense" class="action-btn">
              确认发药（处方#{{ selectedDispense.prescriptionId }}）
            </van-button>
          </div>
        </div>
      </van-tab>

      <!-- 退药 -->
      <van-tab title="退药" name="drugRefund">
        <div class="tab-content">
          <div v-if="pendingRefundList.length > 0" class="prescription-list">
            <div v-for="p in pendingRefundList" :key="p.prescriptionId"
                 class="prescription-card"
                 :class="{ selected: selectedRefund?.prescriptionId === p.prescriptionId }"
                 @click="selectRefund(p)">
              <div class="prescription-header">
                <span class="patient-name">{{ p.patientName }}</span>
                <span class="prescription-id">处方#{{ p.prescriptionId }}</span>
              </div>
              <div class="drug-list">
                <div v-for="drug in p.drugList" :key="drug.drugId" class="drug-item">
                  {{ drug.drugName }} × {{ drug.quantity }}{{ drug.drugUnit }}
                </div>
              </div>
              <div class="prescription-footer">
                <span class="amount">¥{{ p.totalAmount?.toFixed(2) }}</span>
                <van-tag type="success">已发药</van-tag>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <van-icon name="medal-o" size="48" color="#C4B8A8" />
            <p>暂无可退药处方</p>
          </div>
          <div v-if="selectedRefund" class="form-card">
            <van-field v-model="refundPharmacistId" label="药师ID" placeholder="请输入药师ID" type="digit" />
            <van-field v-model="refundReason" label="退药原因" placeholder="请输入退药原因" />
            <van-button type="danger" block round :loading="refunding" @click="handleDrugRefund" class="action-btn">
              确认退药（处方#{{ selectedRefund.prescriptionId }}）
            </van-button>
          </div>
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { getDrugInventory, dispense, drugRefund, getPendingDispense, getPendingRefund } from '@/api'
import type { DrugInventoryVO, PrescriptionDispenseVO, PrescriptionRefundVO } from '@/api/model'

const activeTab = ref('inventory')

// ========== 库存（前端分页 + 模糊查询）==========
const drugKeyword = ref('')
const allInventoryList = ref<DrugInventoryVO[]>([])
const currentPage = ref(1)
const pageSize = ref(10)

const filteredList = computed(() => {
  const kw = drugKeyword.value.trim().toLowerCase()
  if (!kw) return allInventoryList.value
  return allInventoryList.value.filter(drug =>
      drug.drugName?.toLowerCase().includes(kw) ||
      drug.drugCode?.toLowerCase().includes(kw) ||
      drug.manufacturer?.toLowerCase().includes(kw)
  )
})

const displayList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredList.value.slice(start, end)
})

const totalPages = computed(() =>
    Math.ceil(filteredList.value.length / pageSize.value) || 1
)

const onSearch = () => { currentPage.value = 1 }
const onClear = () => { drugKeyword.value = ''; currentPage.value = 1 }

const loadInventory = async () => {
  showLoadingToast({ message: '加载中...', forbidClick: true })
  try {
    const all: DrugInventoryVO[] = []
    let page = 1
    let total = 1
    while (all.length < total) {
      const res = await getDrugInventory({
        pageNum: page,
        pageSize: 50
      })
      const records = res.records || []
      all.push(...records)
      total = res.total || 0
      if (records.length === 0) break
      page++
    }
    allInventoryList.value = all
    closeToast()
  } catch {
    closeToast()
    showToast('加载失败')
  }
}

// ========== 发药 ==========
const pendingDispenseList = ref<PrescriptionDispenseVO[]>([])
const selectedDispense = ref<PrescriptionDispenseVO | null>(null)
const dispensePharmacistId = ref('1')
const dispensing = ref(false)

const loadPendingDispense = async () => {
  try {
    const res = await getPendingDispense()
    pendingDispenseList.value = (res as any) || []
  } catch {
    showToast('加载待发药列表失败')
  }
}

const selectDispense = (p: PrescriptionDispenseVO) => {
  selectedDispense.value = p
}

const handleDispense = async () => {
  if (!selectedDispense.value) { showToast('请选择处方'); return }
  dispensing.value = true
  try {
    await dispense({
      prescriptionId: selectedDispense.value.prescriptionId,
      pharmacistId: Number(dispensePharmacistId.value) || 1
    })
    showToast('发药成功')
    selectedDispense.value = null
    loadPendingDispense()
  } catch {
    showToast('发药失败')
  } finally {
    dispensing.value = false
  }
}

// ========== 退药 ==========
const pendingRefundList = ref<PrescriptionRefundVO[]>([])
const selectedRefund = ref<PrescriptionRefundVO | null>(null)
const refundPharmacistId = ref('1')
const refundReason = ref('')
const refunding = ref(false)

const loadPendingRefund = async () => {
  try {
    const res = await getPendingRefund()
    pendingRefundList.value = (res as any) || []
  } catch {
    showToast('加载可退药列表失败')
  }
}

const selectRefund = (p: PrescriptionRefundVO) => {
  selectedRefund.value = p
}

const handleDrugRefund = async () => {
  if (!selectedRefund.value) { showToast('请选择处方'); return }
  if (!refundReason.value) { showToast('请输入退药原因'); return }
  refunding.value = true
  try {
    await drugRefund({
      prescriptionId: selectedRefund.value.prescriptionId,
      pharmacistId: Number(refundPharmacistId.value) || 1,
      refundReason: refundReason.value
    })
    showToast('退药成功')
    selectedRefund.value = null
    refundReason.value = ''
    loadPendingRefund()
  } catch {
    showToast('退药失败')
  } finally {
    refunding.value = false
  }
}

onMounted(() => {
  loadInventory()
  loadPendingDispense()
  loadPendingRefund()
})
</script>

<style lang="scss" scoped>
.drug-manage {
  min-height: 100vh;
  background: #F5F5F5;
  padding-bottom: 20px;
}
.drug-tabs :deep(.van-tabs__line) {
  background-color: #F4A261;
}
.tab-content {
  padding: 12px;
}
.search-bar {
  margin-bottom: 12px;
}
.inventory-list {
  margin-bottom: 12px;
}
.drug-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  &.low-stock {
    border-left: 3px solid #E76F51;
  }
}
.drug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  .drug-name {
    font-size: 16px;
    font-weight: 500;
    color: #5C4B3A;
  }
}
.drug-info {
  .info-row {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    .label {
      font-size: 13px;
      color: #8B7A6B;
    }
    .value {
      font-size: 13px;
      color: #5C4B3A;
      font-weight: 500;
      &.warning {
        color: #E76F51;
      }
    }
  }
}
.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #C4B8A8;
}
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 16px 0;
  .page-info {
    font-size: 14px;
    color: #5C4B3A;
    font-weight: 500;
  }
}
.prescription-list {
  margin-bottom: 12px;
}
.prescription-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  border: 2px solid transparent;
  &.selected {
    border-color: #F4A261;
  }
}
.prescription-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  .patient-name {
    font-size: 15px;
    font-weight: 500;
    color: #5C4B3A;
  }
  .prescription-id {
    font-size: 12px;
    color: #8B7A6B;
  }
}
.drug-list {
  margin-bottom: 8px;
  .drug-item {
    font-size: 13px;
    color: #5C4B3A;
    padding: 2px 0;
  }
}
.prescription-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .amount {
    font-size: 16px;
    font-weight: 700;
    color: #E76F51;
  }
}
.form-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-top: 12px;
}
.action-btn {
  margin-top: 16px;
  height: 44px;
}
</style>