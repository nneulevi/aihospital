<template>
  <section class="workspace">
    <div class="toolbar">
      <el-input v-model="drugName" clearable placeholder="药品名称" style="width: 220px" @keyup.enter="loadAll" />
      <el-button type="primary" :loading="loading" @click="loadAll">刷新</el-button>
      <el-button @click="loadAlerts">低库存预警</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :md="16">
        <el-table :data="inventory" stripe border v-loading="loading">
          <el-table-column prop="drugId" label="药品ID" width="90" />
          <el-table-column prop="drugCode" label="编码" min-width="130" show-overflow-tooltip />
          <el-table-column prop="drugName" label="药品" min-width="150" show-overflow-tooltip />
          <el-table-column prop="drugFormat" label="规格" min-width="120" show-overflow-tooltip />
          <el-table-column prop="drugUnit" label="单位" width="80" />
          <el-table-column prop="stockNum" label="库存" width="90">
            <template #default="{ row }">
              <el-tag :type="row.alert ? 'danger' : 'success'">{{ row.stockNum }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="110">
            <template #default="{ row }">¥{{ formatMoney(row.drugPrice) }}</template>
          </el-table-column>
          <el-table-column prop="manufacturer" label="厂家" min-width="160" show-overflow-tooltip />
          <el-table-column label="操作" width="220">
            <template #default="{ row }">
              <el-button size="small" @click="openStockIn(row)">入库</el-button>
              <el-button size="small" @click="openStockCheck(row)">盘点</el-button>
              <el-button size="small" @click="loadRecords(row.drugId)">流水</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="side-panel">
          <h2>处方发药/退药</h2>
          <el-input v-model.number="prescriptionId" placeholder="处方ID" />
          <div class="side-actions">
            <el-button type="primary" @click="dispensePrescription">发药</el-button>
            <el-button @click="refundPrescription">退药</el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-table :data="records" stripe border>
      <el-table-column prop="createTime" label="时间" min-width="170" />
      <el-table-column prop="drugName" label="药品" min-width="150" />
      <el-table-column prop="recordType" label="类型" width="100" />
      <el-table-column prop="quantity" label="数量" width="90" />
      <el-table-column prop="beforeStock" label="变动前" width="90" />
      <el-table-column prop="afterStock" label="变动后" width="90" />
      <el-table-column prop="operatorName" label="操作人" width="120" />
      <el-table-column prop="reason" label="原因" min-width="180" />
    </el-table>

    <el-dialog v-model="stockDialog.visible" :title="stockDialog.mode === 'in' ? '药品入库' : '库存盘点'" width="420px">
      <el-form label-width="90px">
        <el-form-item label="药品">
          <el-input v-model="stockDialog.drugName" disabled />
        </el-form-item>
        <el-form-item :label="stockDialog.mode === 'in' ? '入库数量' : '实际库存'">
          <el-input-number v-model="stockDialog.quantity" :min="stockDialog.mode === 'in' ? 1 : 0" />
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="stockDialog.reason" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitStockDialog">确认</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  drugstoreDispense,
  drugstoreRefund,
  getDrugstoreInventory,
  getStockAlerts,
  getStockRecords,
  stockCheck,
  stockIn,
  type DrugStockRecordVO,
} from '@/api'
import type { DrugInventoryVO } from '@/api/model'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const loading = ref(false)
const drugName = ref('')
const prescriptionId = ref<number>()
const inventory = ref<DrugInventoryVO[]>([])
const records = ref<DrugStockRecordVO[]>([])
const stockDialog = reactive({
  visible: false,
  mode: 'in' as 'in' | 'check',
  drugId: 0,
  drugName: '',
  quantity: 1,
  reason: '',
})

const loadInventory = async () => {
  const res: any = await getDrugstoreInventory({
    pageNum: 1,
    pageSize: 50,
    drugName: drugName.value || undefined,
  })
  inventory.value = res.records || []
}

const loadRecords = async (drugId?: number) => {
  const res: any = await getStockRecords({ pageNum: 1, pageSize: 50, drugId })
  records.value = res.records || []
}

const loadAlerts = async () => {
  const res: any = await getStockAlerts({ threshold: 10, pageNum: 1, pageSize: 50 })
  inventory.value = res.records || []
  ElMessage.info('已切换到低库存列表')
}

const loadAll = async () => {
  loading.value = true
  try {
    await loadInventory()
    await loadRecords()
  } finally {
    loading.value = false
  }
}

const openStockIn = (row: DrugInventoryVO) => {
  Object.assign(stockDialog, { visible: true, mode: 'in', drugId: row.drugId, drugName: row.drugName, quantity: 1, reason: '采购入库' })
}

const openStockCheck = (row: DrugInventoryVO) => {
  Object.assign(stockDialog, { visible: true, mode: 'check', drugId: row.drugId, drugName: row.drugName, quantity: row.stockNum || 0, reason: '库存盘点' })
}

const submitStockDialog = async () => {
  if (stockDialog.mode === 'in') {
    await stockIn({ drugId: stockDialog.drugId, quantity: stockDialog.quantity, operatorId: userStore.userId, reason: stockDialog.reason })
  } else {
    await stockCheck({ drugId: stockDialog.drugId, actualStock: stockDialog.quantity, operatorId: userStore.userId, reason: stockDialog.reason })
  }
  stockDialog.visible = false
  ElMessage.success('库存已更新')
  await loadAll()
}

const dispensePrescription = async () => {
  if (!prescriptionId.value) return ElMessage.warning('请输入处方ID')
  await drugstoreDispense({ prescriptionId: prescriptionId.value, pharmacistId: userStore.userId })
  ElMessage.success('发药完成')
  await loadAll()
}

const refundPrescription = async () => {
  if (!prescriptionId.value) return ElMessage.warning('请输入处方ID')
  await drugstoreRefund({ prescriptionId: prescriptionId.value, pharmacistId: userStore.userId, refundReason: '药房工作台退药' })
  ElMessage.success('退药完成')
  await loadAll()
}

const formatMoney = (value?: number) => Number(value || 0).toFixed(2)

onMounted(loadAll)
</script>

<style scoped>
.workspace {
  display: grid;
  gap: 16px;
}
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}
.side-panel {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid #dce5dc;
  border-radius: 8px;
  background: #fff;
}
.side-panel h2 {
  margin: 0;
  font-size: 18px;
}
.side-actions {
  display: flex;
  gap: 10px;
}
</style>
