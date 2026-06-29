<!-- src/views/admin/DrugManage.vue -->
<template>
  <div class="drug-manage">
    <van-tabs v-model:active="activeTab" class="drug-tabs">
      <!-- 药品库存 -->
      <van-tab title="药品库存" name="inventory">
        <div class="tab-content">
          <div class="search-bar">
            <van-search v-model="drugKeyword" placeholder="搜索药品名称" shape="round" background="transparent" @search="loadInventory" />
          </div>
          <div class="inventory-list">
            <div v-for="drug in inventoryList" :key="drug.drugId" class="drug-card" :class="{ 'low-stock': drug.alert }">
              <div class="drug-header">
                <div class="drug-name">{{ drug.drugName }}</div>
                <van-tag v-if="drug.alert" type="danger" size="small">库存不足</van-tag>
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
            <div v-if="inventoryList.length === 0" class="empty-state">
              <van-icon name="medal-o" size="48" color="#C4B8A8" />
              <p>暂无库存数据</p>
            </div>
          </div>
        </div>
      </van-tab>

      <!-- 发药 -->
      <van-tab title="发药" name="dispense">
        <div class="tab-content">
          <div class="form-card">
            <van-field v-model="dispensePrescriptionId" label="处方ID" placeholder="请输入处方ID" type="digit" />
            <van-field v-model="dispensePharmacistId" label="药师ID" placeholder="请输入药师ID" type="digit" />
            <div class="mock-info">
              <div class="mock-title">模拟处方信息</div>
              <div class="mock-item">处方ID: 1</div>
              <div class="mock-item">患者: 张三</div>
              <div class="mock-item">药品: 阿莫西林胶囊 × 2盒</div>
              <div class="mock-item">状态: 已缴费，待发药</div>
            </div>
            <van-button type="primary" block round :loading="dispensing" @click="handleDispense" class="action-btn">
              确认发药
            </van-button>
          </div>
        </div>
      </van-tab>

      <!-- 退药 -->
      <van-tab title="退药" name="drugRefund">
        <div class="tab-content">
          <div class="form-card">
            <van-field v-model="refundPrescriptionId" label="处方ID" placeholder="请输入处方ID" type="digit" />
            <van-field v-model="refundPharmacistId" label="药师ID" placeholder="请输入药师ID" type="digit" />
            <van-field v-model="refundReason" label="退药原因" placeholder="请输入退药原因" />
            <div class="mock-info">
              <div class="mock-title">模拟处方信息</div>
              <div class="mock-item">处方ID: 4</div>
              <div class="mock-item">患者: 李四</div>
              <div class="mock-item">药品: 布洛芬缓释胶囊 × 1盒</div>
              <div class="mock-item">状态: 已发药，可退药</div>
            </div>
            <van-button type="danger" block round :loading="refunding" @click="handleDrugRefund" class="action-btn">
              确认退药
            </van-button>
          </div>
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { getDrugInventory, dispense, drugRefund } from '@/api'
import type { DrugInventoryVO } from '@/api/model'

const activeTab = ref('inventory')

// 库存
const drugKeyword = ref('')
const inventoryList = ref<DrugInventoryVO[]>([])

const loadInventory = async () => {
  showLoadingToast({ message: '加载中...', forbidClick: true })
  try {
    const res = await getDrugInventory({
      query: { drugName: drugKeyword.value, pageNum: 1, pageSize: 50 }
    })
    inventoryList.value = res.data?.records || []
    closeToast()
  } catch {
    closeToast()
    showToast('加载失败')
  }
}

// 发药
const dispensePrescriptionId = ref('')
const dispensePharmacistId = ref('1')
const dispensing = ref(false)

const handleDispense = async () => {
  if (!dispensePrescriptionId.value) { showToast('请输入处方ID'); return }
  dispensing.value = true
  try {
    await dispense({
      prescriptionId: Number(dispensePrescriptionId.value),
      pharmacistId: Number(dispensePharmacistId.value) || 1
    })
    showToast('发药成功')
    dispensePrescriptionId.value = ''
  } catch {
    showToast('发药失败')
  } finally {
    dispensing.value = false
  }
}

// 退药
const refundPrescriptionId = ref('')
const refundPharmacistId = ref('1')
const refundReason = ref('')
const refunding = ref(false)

const handleDrugRefund = async () => {
  if (!refundPrescriptionId.value) { showToast('请输入处方ID'); return }
  if (!refundReason.value) { showToast('请输入退药原因'); return }
  refunding.value = true
  try {
    await drugRefund({
      prescriptionId: Number(refundPrescriptionId.value),
      pharmacistId: Number(refundPharmacistId.value) || 1,
      refundReason: refundReason.value
    })
    showToast('退药成功')
    refundPrescriptionId.value = ''
    refundReason.value = ''
  } catch {
    showToast('退药失败')
  } finally {
    refunding.value = false
  }
}

onMounted(() => loadInventory())
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
.form-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
}
.mock-info {
  background: #FFF9F0;
  border-radius: 8px;
  padding: 12px;
  margin: 12px 0;
  .mock-title {
    font-size: 14px;
    font-weight: 500;
    color: #F4A261;
    margin-bottom: 8px;
  }
  .mock-item {
    font-size: 13px;
    color: #5C4B3A;
    padding: 2px 0;
  }
}
.action-btn {
  margin-top: 16px;
  height: 44px;
}
</style>