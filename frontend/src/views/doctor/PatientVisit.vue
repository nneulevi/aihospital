<!-- src/views/doctor/PatientVisit.vue -->
<template>
  <div class="patient-visit">
    <!-- 患者信息卡片 -->
    <div class="patient-card-top">
      <div class="info-row">
        <span class="name">{{ patientName }}</span>
        <span class="gender">{{ patientInfo.gender }}</span>
        <span class="age">{{ patientInfo.age }}岁</span>
        <van-tag type="primary" size="small" class="status-tag">就诊中</van-tag>
      </div>
      <div class="info-row sub">
        <span>病历号: {{ patientInfo.caseNumber }}</span>
        <span>挂号ID: {{ registerId }}</span>
        <span class="draft-status" v-if="hasDraft">
          <van-icon name="edit" /> 草稿
        </span>
      </div>
      <div class="action-row">
        <van-button size="small" type="primary" plain @click="saveDraft">💾 保存草稿</van-button>
        <van-button size="small" type="default" plain @click="goBack">⬅ 返回</van-button>
      </div>
    </div>

    <!-- 诊疗流程 Tab -->
    <van-tabs v-model:active="visitTab" class="visit-tabs" sticky offset-top="96" @change="onTabChange">
      <!-- 病历 -->
      <van-tab title="病历" name="record">
        <div class="tab-panel">
          <div class="form-card">
            <div class="card-title">📝 病历信息</div>
            <van-cell-group inset>
              <van-field v-model="recordForm.readme" label="主诉" type="textarea" rows="2" placeholder="患者主要不适..." />
              <van-field v-model="recordForm.present" label="现病史" type="textarea" rows="3" placeholder="现病史描述..." />
              <van-field v-model="recordForm.presentTreat" label="现病治疗" placeholder="已做治疗" />
              <van-field v-model="recordForm.history" label="既往史" placeholder="既往病史" />
              <van-field v-model="recordForm.allergy" label="过敏史" placeholder="过敏史" />
              <van-field v-model="recordForm.physique" label="体格检查" type="textarea" rows="2" placeholder="体格检查结果..." />
              <van-field v-model="recordForm.proposal" label="检查建议" type="textarea" rows="2" placeholder="建议检查项目..." />
              <van-field v-model="recordForm.careful" label="注意事项" placeholder="注意事项" />
              <van-field v-model="recordForm.diagnosis" label="初步诊断" type="textarea" rows="2" placeholder="初步诊断..." />
            </van-cell-group>
          </div>

          <van-button type="primary" block round :loading="savingRecord" @click="saveRecord" class="action-btn">
            保存病历
          </van-button>

          <van-button type="warning" block round @click="goToAIDiagnosis" class="action-btn">
            🤖 AI 诊断建议
          </van-button>
        </div>
      </van-tab>

      <!-- 检查/检验 -->
      <van-tab title="检查检验" name="check">
        <div class="tab-panel">
          <!-- 已开项目 -->
          <div class="list-card">
            <div class="card-title">📋 已开项目</div>
            <div v-if="orderedItems.length === 0" class="empty-mini">暂无已开项目</div>
            <div v-for="(item, idx) in orderedItems" :key="idx" class="ordered-item">
              <div class="item-main">
                <van-tag :type="item.type === 'CHECK' ? 'primary' : item.type === 'INSPECTION' ? 'warning' : 'success'" size="small">
                  {{ item.type === 'CHECK' ? '检查' : item.type === 'INSPECTION' ? '检验' : '处置' }}
                </van-tag>
                <span class="item-name">{{ item.name || item.checkInfo || item.inspectionInfo || item.disposalInfo }}</span>
                <van-icon name="cross" class="delete-icon" @click.stop="removeOrderItem(idx)" />
              </div>
              <div class="item-sub">{{ item.position || item.checkPosition || item.inspectionPosition || item.disposalPosition }}</div>
            </div>
          </div>

          <!-- 新开检查 -->
          <div class="form-card">
            <div class="card-title">➕ 开检查</div>
            <van-field v-model="newCheck.checkInfo" label="检查项目" placeholder="如：头颅CT平扫" />
            <van-field v-model="newCheck.checkPosition" label="检查部位" placeholder="如：头部" />
            <van-button type="primary" size="small" round @click="addCheck">添加检查</van-button>
          </div>

          <!-- 新开检验 -->
          <div class="form-card">
            <div class="card-title">➕ 开检验</div>
            <van-field v-model="newInspection.inspectionInfo" label="检验项目" placeholder="如：血常规检查" />
            <van-field v-model="newInspection.inspectionPosition" label="检验样本" placeholder="如：静脉血" />
            <van-button type="primary" size="small" round @click="addInspection">添加检验</van-button>
          </div>

          <!-- 新开处置 -->
          <div class="form-card">
            <div class="card-title">➕ 开处置</div>
            <van-field v-model="newDisposal.disposalInfo" label="处置项目" placeholder="如：换药处理" />
            <van-field v-model="newDisposal.disposalPosition" label="处置部位" placeholder="如：头部" />
            <van-button type="primary" size="small" round @click="addDisposal">添加处置</van-button>
          </div>

          <van-button type="primary" block round :loading="savingOrders" @click="submitOrders" class="action-btn">
            提交申请
          </van-button>
        </div>
      </van-tab>

      <!-- 结果查看 -->
      <van-tab title="结果" name="result">
        <div class="tab-panel">
          <van-button type="primary" block round @click="loadResults" class="action-btn">
            刷新结果
          </van-button>

          <div v-if="checkResults.checkRequests && checkResults.checkRequests.length > 0" class="result-group">
            <div class="result-title">🔬 检查结果</div>
            <div
                v-for="r in checkResults.checkRequests"
                :key="r.id"
                class="result-card clickable"
                @click="goToResultDetail('check', r.id)"
            >
              <div class="result-header">
                <span class="result-name">{{ r.checkInfo }}</span>
                <van-tag :type="r.checkState === 'DONE' ? 'success' : 'warning'" size="small">
                  {{ r.checkState === 'DONE' ? '已出结果' : '待执行' }}
                </van-tag>
              </div>
              <div v-if="r.checkResult" class="result-body">
                <div class="result-label">检查所见：</div>
                <div class="result-text">{{ r.checkResult }}</div>
              </div>
              <div class="result-arrow" v-if="r.checkState === 'DONE'">
                <van-icon name="arrow" />
              </div>
            </div>
          </div>

          <div v-if="checkResults.inspectionRequests && checkResults.inspectionRequests.length > 0" class="result-group">
            <div class="result-title">🧪 检验结果</div>
            <div
                v-for="r in checkResults.inspectionRequests"
                :key="r.id"
                class="result-card clickable"
                @click="goToResultDetail('inspection', r.id)"
            >
              <div class="result-header">
                <span class="result-name">{{ r.inspectionInfo }}</span>
                <van-tag :type="r.inspectionState === 'DONE' ? 'success' : 'warning'" size="small">
                  {{ r.inspectionState === 'DONE' ? '已出结果' : '待执行' }}
                </van-tag>
              </div>
              <div v-if="r.inspectionResult" class="result-body">
                <div class="result-text">{{ r.inspectionResult }}</div>
              </div>
              <div class="result-arrow" v-if="r.inspectionState === 'DONE'">
                <van-icon name="arrow" />
              </div>
            </div>
          </div>

          <!-- AI 分诊入口 -->
          <div v-if="hasAnyResult" class="triage-section">
            <div class="triage-divider">
              <span class="divider-line"></span>
              <span class="divider-text">🤖 AI 分诊</span>
              <span class="divider-line"></span>
            </div>

            <div class="triage-card" @click="goToAITriage">
              <div class="triage-icon">🧭</div>
              <div class="triage-content">
                <div class="triage-title">AI 分诊分析</div>
                <div class="triage-desc">
                  基于 {{ totalDoneResults }} 项检查检验结果，智能推荐转诊科室
                  <span v-if="hasTriageResult" class="triage-done">✅ 已分析</span>
                </div>
              </div>
              <van-icon name="arrow" class="triage-arrow" />
            </div>
          </div>

          <div v-if="!hasAnyResult" class="empty-state">
            <van-icon name="search" size="48" color="#C4B8A8" />
            <p>暂无结果，请先开检查/检验</p>
          </div>
        </div>
      </van-tab>

      <!-- 确诊 -->
      <van-tab title="确诊" name="confirm">
        <div class="tab-panel">
          <div class="form-card">
            <div class="card-title">✅ 门诊确诊</div>
            <van-cell-group inset>
              <van-field v-model="confirmForm.diagnosis" label="最终诊断" type="textarea" rows="3" placeholder="最终诊断结果..." />
              <van-field v-model="confirmForm.cure" label="治疗方案" type="textarea" rows="3" placeholder="治疗及处理意见..." />
              <van-field v-model="diseaseIdsText" label="疾病编码" placeholder="如：J01,J02（逗号分隔）" />
            </van-cell-group>
          </div>
          <van-button type="primary" block round :loading="confirming" @click="submitConfirm" class="action-btn">
            确认确诊
          </van-button>
        </div>
      </van-tab>

      <!-- 处方 -->
      <van-tab title="处方" name="prescription">
        <div class="tab-panel">
          <!-- 已选药品 -->
          <div class="list-card">
            <div class="card-title">💊 处方药品</div>
            <div v-if="prescriptionItems.length === 0" class="empty-mini">暂无药品</div>
            <div v-for="(item, idx) in prescriptionItems" :key="idx" class="drug-item">
              <div class="drug-header">
                <span class="drug-name">{{ item.drugName }}</span>
                <span class="drug-price">¥{{ item.drugPrice?.toFixed(2) }}</span>
              </div>
              <div class="drug-detail">
                {{ item.usageRoute || '口服' }} | {{ item.frequency || '每日三次' }} | {{ item.dosage || '100mg' }} | {{ item.useDays || 7 }}天 | ×{{ item.drugNumber || 1 }}
              </div>
              <van-icon name="cross" class="delete-icon" @click="removeDrug(idx)" />
            </div>
            <div v-if="prescriptionItems.length > 0" class="total-price">
              合计：<span class="price">¥{{ prescriptionTotal.toFixed(2) }}</span>
            </div>
          </div>

          <!-- 添加药品 -->
          <div class="form-card">
            <div class="card-title">➕ 添加药品</div>
            <van-field v-model="newDrug.drugName" label="药品名称" placeholder="搜索药品..." readonly @click="showDrugPicker = true" />
            <van-field v-model="newDrug.usageRoute" label="用法" placeholder="如：口服" />
            <van-field v-model="newDrug.frequency" label="频次" placeholder="如：每日三次" />
            <van-field v-model="newDrug.dosage" label="剂量" placeholder="如：100mg" />
            <van-field v-model="newDrug.singleDose" label="单次用量" placeholder="如：1片" />
            <van-field v-model="newDrug.useDays" label="天数" type="digit" placeholder="1-90" />
            <van-field v-model="newDrug.drugNumber" label="数量" type="digit" placeholder="1-999" />
            <van-button type="primary" size="small" round @click="addDrug">加入处方</van-button>
          </div>

          <van-button type="primary" block round :loading="savingRx" @click="submitPrescription" class="action-btn">
            提交处方
          </van-button>
        </div>
      </van-tab>
    </van-tabs>

    <!-- 药品选择弹出层 -->
    <van-action-sheet v-model:show="showDrugPicker" title="选择药品">
      <div class="drug-picker">
        <div
            v-for="drug in drugOptions"
            :key="drug.value"
            class="drug-option"
            @click="selectDrug(drug)"
        >
          <div class="drug-option-name">{{ drug.text }}</div>
          <div class="drug-option-price">¥{{ drug.price.toFixed(2) }}</div>
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'

const route = useRoute()
const router = useRouter()

const registerId = ref(Number(route.query.registerId) || 0)
const patientName = ref(route.query.name as string || '患者')

const visitTab = ref('record')
const hasDraft = ref(false)

// 患者信息
const patientInfo = ref({
  gender: '男',
  age: 35,
  caseNumber: 'HN202600006'
})

// ===== 草稿保存 =====
const saveDraft = () => {
  const draft = {
    registerId: registerId.value,
    recordForm: recordForm.value,
    orderedItems: orderedItems.value,
    prescriptionItems: prescriptionItems.value,
    confirmForm: confirmForm.value,
    timestamp: Date.now()
  }
  localStorage.setItem(`draft_${registerId.value}`, JSON.stringify(draft))
  hasDraft.value = true
  showToast('草稿已保存')
}

const loadDraft = () => {
  const key = `draft_${registerId.value}`
  const saved = localStorage.getItem(key)
  if (saved) {
    try {
      const draft = JSON.parse(saved)
      recordForm.value = draft.recordForm || recordForm.value
      orderedItems.value = draft.orderedItems || []
      prescriptionItems.value = draft.prescriptionItems || []
      confirmForm.value = draft.confirmForm || confirmForm.value
      hasDraft.value = true
      showToast('已加载草稿')
    } catch (e) {
      console.error('加载草稿失败', e)
    }
  }
}

const clearDraft = () => {
  localStorage.removeItem(`draft_${registerId.value}`)
  hasDraft.value = false
}

// 监听全局保存草稿事件
const handleSaveDraft = () => {
  saveDraft()
}

// ===== AI 分诊相关 =====
const hasTriageResult = ref(false)
const triageResultData = ref<any>(null)

const totalDoneResults = computed(() => {
  let count = 0
  const checks = checkResults.value.checkRequests || []
  const inspections = checkResults.value.inspectionRequests || []
  checks.forEach((r: any) => {
    if (r.checkState === 'DONE') count++
  })
  inspections.forEach((r: any) => {
    if (r.inspectionState === 'DONE') count++
  })
  return count
})

// ===== 跳转 AI 分诊 =====
const goToAITriage = () => {
  if (totalDoneResults.value === 0) {
    showToast('暂无已完成的结果，无法进行分诊')
    return
  }
  saveDraft()
  router.push({
    name: 'AITriage',
    query: {
      registerId: String(registerId.value),
      name: patientName.value
    }
  })
}

// ===== 监听分诊采纳事件 =====
const handleTriageAccepted = (e: any) => {
  const detail = e.detail
  hasTriageResult.value = true
  triageResultData.value = detail
  showToast(`✅ 已采纳分诊：转至 ${detail.department}`)
}

onMounted(() => {
  loadDraft()
  window.addEventListener('save-draft', handleSaveDraft)
  window.addEventListener('triage-accepted', handleTriageAccepted)
})

onBeforeUnmount(() => {
  saveDraft()
  window.removeEventListener('save-draft', handleSaveDraft)
  window.removeEventListener('triage-accepted', handleTriageAccepted)
})

const goBack = () => {
  saveDraft()
  router.push('/doctor')
}

// ===== 跳转 AI 诊断 =====
const goToAIDiagnosis = () => {
  saveDraft()
  router.push({
    name: 'AIDiagnosis',
    query: {
      registerId: String(registerId.value),
      name: patientName.value
    }
  })
}

// ===== 跳转结果详情 =====
const goToResultDetail = (type: string, id: number) => {
  saveDraft()
  router.push({
    name: 'ResultDetail',
    params: { type, id },
    query: {
      registerId: String(registerId.value),
      name: patientName.value
    }
  })
}

// ===== 病历 =====
const recordForm = ref({
  registerId: registerId.value,
  readme: '',
  present: '',
  presentTreat: '',
  history: '',
  allergy: '',
  physique: '',
  proposal: '',
  careful: '',
  diagnosis: ''
})
const savingRecord = ref(false)

const saveRecord = async () => {
  savingRecord.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 800))
    showToast('病历保存成功')
    clearDraft()
  } catch {
    showToast('保存失败')
  } finally {
    savingRecord.value = false
  }
}

// ===== 检查/检验/处置 =====
const orderedItems = ref<any[]>([])
const newCheck = ref({ medicalTechnologyId: 1, checkInfo: '', checkPosition: '' })
const newInspection = ref({ medicalTechnologyId: 4, inspectionInfo: '', inspectionPosition: '' })
const newDisposal = ref({ medicalTechnologyId: 6, disposalInfo: '', disposalPosition: '' })
const savingOrders = ref(false)

const addCheck = () => {
  if (!newCheck.value.checkInfo) { showToast('请填写检查项目'); return }
  orderedItems.value.push({
    type: 'CHECK',
    ...newCheck.value,
    name: newCheck.value.checkInfo,
    position: newCheck.value.checkPosition
  })
  newCheck.value = { medicalTechnologyId: 1, checkInfo: '', checkPosition: '' }
  showToast('已添加检查')
  saveDraft()
}

const addInspection = () => {
  if (!newInspection.value.inspectionInfo) { showToast('请填写检验项目'); return }
  orderedItems.value.push({
    type: 'INSPECTION',
    ...newInspection.value,
    name: newInspection.value.inspectionInfo,
    position: newInspection.value.inspectionPosition
  })
  newInspection.value = { medicalTechnologyId: 4, inspectionInfo: '', inspectionPosition: '' }
  showToast('已添加检验')
  saveDraft()
}

const addDisposal = () => {
  if (!newDisposal.value.disposalInfo) { showToast('请填写处置项目'); return }
  orderedItems.value.push({
    type: 'DISPOSAL',
    ...newDisposal.value,
    name: newDisposal.value.disposalInfo,
    position: newDisposal.value.disposalPosition
  })
  newDisposal.value = { medicalTechnologyId: 6, disposalInfo: '', disposalPosition: '' }
  showToast('已添加处置')
  saveDraft()
}

const removeOrderItem = (idx: number) => {
  orderedItems.value.splice(idx, 1)
  saveDraft()
}

const submitOrders = async () => {
  savingOrders.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 800))
    showToast('申请提交成功')
    orderedItems.value = []
    clearDraft()
  } catch {
    showToast('提交失败')
  } finally {
    savingOrders.value = false
  }
}

// ===== 结果查看 =====
const checkResults = ref<any>({})
const hasAnyResult = computed(() => {
  return (checkResults.value.checkRequests && checkResults.value.checkRequests.length > 0) ||
      (checkResults.value.inspectionRequests && checkResults.value.inspectionRequests.length > 0)
})

const loadResults = async () => {
  showLoadingToast({ message: '加载中...', forbidClick: true })
  try {
    await new Promise(resolve => setTimeout(resolve, 600))
    checkResults.value = {
      checkRequests: [
        { id: 1, checkInfo: '头颅CT平扫', checkState: 'DONE', checkResult: '右肺上叶见磨玻璃结节，直径约6mm，边界清晰' },
        { id: 2, checkInfo: '胸部X线', checkState: 'PENDING', checkResult: '' }
      ],
      inspectionRequests: [
        { id: 1, inspectionInfo: '血常规', inspectionState: 'DONE', inspectionResult: 'WBC 8.5×10⁹/L，N 72%' }
      ]
    }
    closeToast()
  } catch {
    closeToast()
    showToast('加载失败')
  }
}

// ===== 确诊 =====
const confirmForm = ref({
  registerId: registerId.value,
  diagnosis: '',
  cure: '',
  diseaseIds: []
})
const diseaseIdsText = ref('')
const confirming = ref(false)

const submitConfirm = async () => {
  if (!confirmForm.value.diagnosis) { showToast('请填写诊断'); return }
  confirming.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 800))
    showToast('确诊成功')
    clearDraft()
  } catch {
    showToast('确诊失败')
  } finally {
    confirming.value = false
  }
}

// ===== 处方 =====
const prescriptionItems = ref<any[]>([])
const newDrug = ref<any>({
  drugName: '',
  usageRoute: '口服',
  frequency: '每日三次',
  dosage: '100mg',
  singleDose: '1片',
  useDays: 7,
  drugNumber: 1,
  drugPrice: 0
})
const savingRx = ref(false)
const showDrugPicker = ref(false)

const drugOptions = [
  { text: '阿莫西林胶囊 0.25g×24粒', value: 1, price: 17.5 },
  { text: '布洛芬缓释胶囊 0.3g×20粒', value: 2, price: 14 },
  { text: '头孢克肟片 0.1g×12片', value: 3, price: 32 },
  { text: '奥美拉唑肠溶胶囊 20mg×14粒', value: 4, price: 28.5 },
  { text: '二甲双胍片 0.5g×30片', value: 5, price: 12 },
  { text: '氨氯地平片 5mg×28片', value: 6, price: 25 }
]

const selectDrug = (drug: any) => {
  newDrug.value.drugName = drug.text
  newDrug.value.drugPrice = drug.price
  newDrug.value.drugId = drug.value
  showDrugPicker.value = false
}

const addDrug = () => {
  if (!newDrug.value.drugName) { showToast('请选择药品'); return }
  prescriptionItems.value.push({ ...newDrug.value })
  newDrug.value = {
    drugName: '',
    usageRoute: '口服',
    frequency: '每日三次',
    dosage: '100mg',
    singleDose: '1片',
    useDays: 7,
    drugNumber: 1,
    drugPrice: 0
  }
  showToast('已添加')
  saveDraft()
}

const removeDrug = (idx: number) => {
  prescriptionItems.value.splice(idx, 1)
  saveDraft()
}

const prescriptionTotal = computed(() => {
  return prescriptionItems.value.reduce((sum, item) => sum + ((item.drugPrice || 0) * (item.drugNumber || 1)), 0)
})

const submitPrescription = async () => {
  if (prescriptionItems.value.length === 0) { showToast('处方不能为空'); return }
  savingRx.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 800))
    showToast('处方提交成功')
    prescriptionItems.value = []
    clearDraft()
  } catch {
    showToast('提交失败')
  } finally {
    savingRx.value = false
  }
}

// ===== Tab切换自动保存 =====
const onTabChange = () => {
  saveDraft()
}
</script>

<style lang="scss" scoped>
.patient-visit {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 20px;
}

.patient-card-top {
  background: white;
  padding: 16px;
  margin: 12px;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);

  .info-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 4px;

    &.sub {
      font-size: 13px;
      color: #8B7A6B;
    }

    .status-tag {
      margin-left: auto;
    }

    .draft-status {
      color: #F4A261;
      font-size: 12px;
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  .name {
    font-size: 18px;
    font-weight: 600;
    color: #2C3E50;
  }

  .gender, .age {
    font-size: 13px;
    color: #7F8C8D;
    background: #F5F5F5;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .action-row {
    margin-top: 12px;
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }
}

.visit-tabs :deep(.van-tabs__line) {
  background-color: #005B96;
}

.tab-panel {
  padding: 12px;
  padding-bottom: 20px;
}

.form-card, .list-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #2C3E50;
  margin-bottom: 12px;
}

.action-btn {
  margin-bottom: 12px;
  height: 44px;
}

.ordered-item {
  background: #F5F7FA;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  position: relative;

  .item-main {
    display: flex;
    align-items: center;
    gap: 8px;

    .delete-icon {
      margin-left: auto;
      color: #E74C3C;
      font-size: 16px;
      cursor: pointer;
    }
  }

  .item-name {
    font-size: 14px;
    color: #2C3E50;
  }

  .item-sub {
    font-size: 12px;
    color: #7F8C8D;
    margin-top: 4px;
  }
}

.result-group {
  margin-bottom: 16px;
}

.result-title {
  font-size: 15px;
  font-weight: 600;
  color: #2C3E50;
  margin-bottom: 8px;
  padding-left: 8px;
  border-left: 3px solid #005B96;
}

.result-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  position: relative;

  &.clickable {
    cursor: pointer;
    transition: all 0.3s;

    &:active {
      transform: scale(0.98);
      background: #F5F7FA;
    }
  }

  .result-arrow {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: #BDC3C7;
  }
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-right: 24px;
}

.result-name {
  font-size: 14px;
  font-weight: 500;
  color: #2C3E50;
}

.result-body {
  .result-label {
    font-size: 12px;
    color: #7F8C8D;
    margin-bottom: 4px;
  }
  .result-text {
    font-size: 13px;
    color: #2C3E50;
    line-height: 1.6;
  }
}

/* ===== AI 分诊样式 ===== */
.triage-section {
  margin-top: 16px;
}

.triage-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;

  .divider-line {
    flex: 1;
    height: 1px;
    background: #E0E0E0;
  }

  .divider-text {
    font-size: 14px;
    font-weight: 600;
    color: #005B96;
    white-space: nowrap;
  }
}

.triage-card {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #E8F4FD 0%, #F0F7FF 100%);
  border-radius: 12px;
  padding: 14px 16px;
  border: 1px solid #B3D9F7;
  cursor: pointer;
  transition: all 0.3s;

  &:active {
    transform: scale(0.98);
  }

  .triage-icon {
    font-size: 32px;
    margin-right: 12px;
  }

  .triage-content {
    flex: 1;

    .triage-title {
      font-size: 15px;
      font-weight: 600;
      color: #005B96;
    }

    .triage-desc {
      font-size: 13px;
      color: #5C6B7A;

      .triage-done {
        color: #27AE60;
        margin-left: 8px;
      }
    }
  }

  .triage-arrow {
    color: #005B96;
    font-size: 18px;
  }
}

.drug-item {
  background: #F5F7FA;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  position: relative;

  .drug-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
  }

  .drug-name {
    font-size: 14px;
    font-weight: 500;
    color: #2C3E50;
  }

  .drug-price {
    font-size: 14px;
    color: #E76F51;
    font-weight: 600;
  }

  .drug-detail {
    font-size: 12px;
    color: #7F8C8D;
  }

  .delete-icon {
    position: absolute;
    right: 8px;
    top: 8px;
    color: #BDC3C7;
    font-size: 16px;
    cursor: pointer;
  }
}

.total-price {
  text-align: right;
  font-size: 14px;
  color: #2C3E50;
  margin-top: 8px;

  .price {
    font-size: 18px;
    font-weight: 700;
    color: #E76F51;
  }
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #BDC3C7;
}

.empty-mini {
  text-align: center;
  padding: 20px 0;
  color: #BDC3C7;
  font-size: 13px;
}

.drug-picker {
  padding: 16px;

  .drug-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #F5F5F5;
    cursor: pointer;

    &:last-child {
      border-bottom: none;
    }

    .drug-option-name {
      font-size: 14px;
      color: #2C3E50;
    }

    .drug-option-price {
      font-size: 14px;
      color: #E76F51;
      font-weight: 600;
    }
  }
}
</style>