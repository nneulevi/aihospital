<template>
  <div class="drug-manage">
    <van-tabs v-model:active="activeTab" class="drug-tabs">
      <van-tab title="药品库存" name="inventory">
        <section class="search-panel">
          <van-search v-model="drugKeyword" placeholder="搜索药品名称" shape="round" @search="loadInventory" />
          <van-button size="small" type="primary" :loading="inventoryLoading" @click="loadInventory">刷新库存</van-button>
          <van-button size="small" plain type="primary" :loading="inventoryLoading" @click="loadDrugstoreInventory">
            药房库存
          </van-button>
        </section>

        <div class="inventory-list">
          <article v-for="drug in inventoryList" :key="drug.drugId" class="drug-card" :class="{ warning: drug.alert }">
            <header>
              <strong>{{ drug.drugName || '未命名药品' }}</strong>
              <van-tag v-if="drug.alert" type="danger">库存预警</van-tag>
            </header>
            <div class="drug-grid">
              <span>编码：{{ drug.drugCode || '--' }}</span>
              <span>规格：{{ drug.drugFormat || '--' }}</span>
              <span>单位：{{ drug.drugUnit || '--' }}</span>
              <span>库存：{{ drug.stockNum ?? 0 }}</span>
              <span>单价：¥{{ formatMoney(drug.drugPrice) }}</span>
              <span>厂家：{{ drug.manufacturer || '--' }}</span>
            </div>
          </article>
          <van-empty v-if="!inventoryLoading && inventoryList.length === 0" description="暂无库存数据" />
        </div>
      </van-tab>

      <van-tab title="发药" name="dispense">
        <section class="form-panel">
          <van-field v-model="dispensePrescriptionId" label="处方ID" type="digit" placeholder="输入处方ID" />
          <van-field v-model="dispensePharmacistId" label="药师ID" type="digit" placeholder="输入药师ID" />
          <van-button type="primary" block round :loading="dispensing" @click="handleDispense">确认发药</van-button>
        </section>
      </van-tab>

      <van-tab title="退药" name="drugRefund">
        <section class="form-panel">
          <van-field v-model="refundPrescriptionId" label="处方ID" type="digit" placeholder="输入处方ID" />
          <van-field v-model="refundPharmacistId" label="药师ID" type="digit" placeholder="输入药师ID" />
          <van-field v-model="refundReason" label="退药原因" type="textarea" rows="2" autosize placeholder="输入退药原因" />
          <van-button type="danger" block round :loading="refunding" @click="handleDrugRefund">确认退药</van-button>
        </section>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import { dispense, drugRefund, getDrugInventory, getInventory } from '@/api'
import type { DispenseRequestDTO, DrugInventoryVO, DrugRefundRequestDTO } from '@/api/model'

const activeTab = ref('inventory')
const drugKeyword = ref('')
const inventoryList = ref<DrugInventoryVO[]>([])
const inventoryLoading = ref(false)

const dispensePrescriptionId = ref('')
const dispensePharmacistId = ref('1')
const dispensing = ref(false)

const refundPrescriptionId = ref('')
const refundPharmacistId = ref('1')
const refundReason = ref('')
const refunding = ref(false)

const loadInventory = async () => {
  inventoryLoading.value = true
  try {
    const res = await getDrugInventory({
      query: {
        drugName: drugKeyword.value || undefined,
        pageNum: 1,
        pageSize: 50
      }
    })
    const data = res.data || res
    inventoryList.value = data.records || []
  } catch {
    showToast('库存加载失败')
  } finally {
    inventoryLoading.value = false
  }
}

const loadDrugstoreInventory = async () => {
  inventoryLoading.value = true
  try {
    const res = await getInventory({
      pageNum: 1,
      pageSize: 50
    })
    const data = res.data || res
    inventoryList.value = data.records || []
    showToast('药房库存加载完成')
  } catch {
    showToast('药房库存加载失败')
  } finally {
    inventoryLoading.value = false
  }
}

const handleDispense = async () => {
  const prescriptionId = Number(dispensePrescriptionId.value)
  const pharmacistId = Number(dispensePharmacistId.value)
  if (!prescriptionId || !pharmacistId) {
    showToast('请填写处方ID和药师ID')
    return
  }

  dispensing.value = true
  try {
    const dto: DispenseRequestDTO = { prescriptionId, pharmacistId }
    await dispense(dto)
    showToast('发药成功')
    dispensePrescriptionId.value = ''
    await loadInventory()
  } catch {
    showToast('发药失败')
  } finally {
    dispensing.value = false
  }
}

const handleDrugRefund = async () => {
  const prescriptionId = Number(refundPrescriptionId.value)
  const pharmacistId = Number(refundPharmacistId.value)
  if (!prescriptionId || !pharmacistId || !refundReason.value) {
    showToast('请填写完整退药信息')
    return
  }

  refunding.value = true
  try {
    const dto: DrugRefundRequestDTO = {
      prescriptionId,
      pharmacistId,
      refundReason: refundReason.value
    }
    await drugRefund(dto)
    showToast('退药成功')
    refundPrescriptionId.value = ''
    refundReason.value = ''
    await loadInventory()
  } catch {
    showToast('退药失败')
  } finally {
    refunding.value = false
  }
}

const formatMoney = (value?: number) => Number(value || 0).toFixed(2)

onMounted(loadInventory)
</script>

<style lang="scss" scoped>
.drug-manage {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 20px;
}
.search-panel,
.form-panel {
  display: grid;
  gap: 10px;
  margin: 12px;
  padding: 12px;
  background: #fff;
  border: 1px solid #eef0f3;
  border-radius: 8px;
}
.inventory-list {
  padding: 0 12px 12px;
}
.drug-card {
  margin-bottom: 10px;
  padding: 12px;
  background: #fff;
  border: 1px solid #eef0f3;
  border-radius: 8px;
}
.drug-card.warning {
  border-left: 4px solid #d93025;
}
.drug-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.drug-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  color: #4f5b67;
  font-size: 13px;
}
</style>
