<!-- src/views/doctor/PatientVisit.vue -->
<template>
  <div class="patient-visit">
    <div class="patient-card-top">
      <div class="info-row">
        <span class="name">{{ patientName }}</span>
        <span class="gender">{{ patientInfo.gender }}</span>
        <span class="age">{{ patientInfo.age }}岁</span>
        <van-tag type="primary" class="status-tag">就诊中</van-tag>
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

      <!-- 检查检验 -->
      <van-tab title="检查检验" name="check">
        <div class="tab-panel">
          <div class="list-card">
            <div class="card-title">📋 已开项目</div>
            <div v-if="orderedItems.length === 0" class="empty-mini">暂无已开项目</div>
            <div v-for="(item, idx) in orderedItems" :key="idx" class="ordered-item">
              <div class="item-main">
                <van-tag :type="item.type === 'CHECK' ? 'primary' : item.type === 'INSPECTION' ? 'warning' : 'success'">
                  {{ item.type === 'CHECK' ? '检查' : item.type === 'INSPECTION' ? '检验' : '处置' }}
                </van-tag>
                <span class="item-name">{{ item.name }}</span>
                <span class="item-price" v-if="item.price">¥{{ item.price }}</span>
                <van-icon name="cross" class="delete-icon" @click.stop="removeOrderItem(idx)" />
              </div>
              <div class="item-sub">{{ item.position }}</div>
            </div>
            <div v-if="orderedItems.length > 0" class="total-price">
              合计：<span class="price">¥{{ orderTotal.toFixed(2) }}</span>
            </div>
          </div>

          <div class="form-card">
            <div class="card-title">➕ 添加项目</div>
            <div class="type-selector">
              <van-button size="small" :type="currentType === 'CHECK' ? 'primary' : 'default'" @click="currentType = 'CHECK'">检查</van-button>
              <van-button size="small" :type="currentType === 'INSPECTION' ? 'primary' : 'default'" @click="currentType = 'INSPECTION'">检验</van-button>
              <van-button size="small" :type="currentType === 'DISPOSAL' ? 'primary' : 'default'" @click="currentType = 'DISPOSAL'">处置</van-button>
            </div>
            <van-button type="primary" block round @click="showTechPicker = true" class="action-btn">
              选择{{ currentType === 'CHECK' ? '检查' : currentType === 'INSPECTION' ? '检验' : '处置' }}项目
            </van-button>
          </div>

          <van-button type="primary" block round :loading="savingOrders" @click="submitOrders" class="action-btn">
            提交申请
          </van-button>
        </div>
      </van-tab>

      <!-- 结果查看 -->
      <van-tab title="结果" name="result">
        <div class="tab-panel">
          <van-button type="primary" block round @click="loadResults" class="action-btn" :loading="loadingResults">
            刷新结果
          </van-button>

          <div v-if="checkResults.checkRequests && checkResults.checkRequests.length > 0" class="result-group">
            <div class="result-title">🔬 检查结果</div>
            <div v-for="r in checkResults.checkRequests" :key="r.id" class="result-card clickable" @click="goToResultDetail('check', r.id)">
              <div class="result-header">
                <span class="result-name">{{ r.checkInfo }}</span>
                <van-tag :type="r.checkState === 'COMPLETED' || r.checkState === 'REPORTED' ? 'success' : 'warning'">
                  {{ getStateText(r.checkState) }}
                </van-tag>
              </div>
              <div v-if="r.checkResult" class="result-body">
                <div class="result-label">检查所见：</div>
                <div class="result-text">{{ r.checkResult }}</div>
              </div>
              <div class="result-arrow" v-if="r.checkState === 'COMPLETED' || r.checkState === 'REPORTED'">
                <van-icon name="arrow" />
              </div>
            </div>
          </div>

          <div v-if="checkResults.inspectionRequests && checkResults.inspectionRequests.length > 0" class="result-group">
            <div class="result-title">🧪 检验结果</div>
            <div v-for="r in checkResults.inspectionRequests" :key="r.id" class="result-card clickable" @click="goToResultDetail('inspection', r.id)">
              <div class="result-header">
                <span class="result-name">{{ r.inspectionInfo }}</span>
                <van-tag :type="r.inspectionState === 'COMPLETED' || r.inspectionState === 'REPORTED' ? 'success' : 'warning'">
                  {{ getStateText(r.inspectionState) }}
                </van-tag>
              </div>
              <div v-if="r.inspectionResult" class="result-body">
                <div class="result-text">{{ r.inspectionResult }}</div>
              </div>
              <div class="result-arrow" v-if="r.inspectionState === 'COMPLETED' || r.inspectionState === 'REPORTED'">
                <van-icon name="arrow" />
              </div>
            </div>
          </div>

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
              <van-field v-model="diseaseIdsText" label="疾病编码" placeholder="如：2,3（逗号分隔）" />
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
          <!-- 已选药品列表 -->
          <div class="list-card">
            <div class="card-title">💊 处方药品</div>
            <div v-if="prescriptionItems.length === 0" class="empty-mini">暂无药品</div>
            <div v-for="(item, idx) in prescriptionItems" :key="idx" class="drug-item">
              <div class="drug-header">
                <span class="drug-name">{{ item.drugName }}</span>
                <span class="drug-price">¥{{ (item.drugPrice * item.drugNumber).toFixed(2) }}</span>
              </div>
              <div class="drug-detail">
                {{ item.usageRoute }} | {{ item.frequency }} | {{ item.dosage }} | {{ item.singleDose }} | {{ item.useDays }}天 | ×{{ item.drugNumber }}
              </div>
              <van-icon name="cross" class="delete-icon" @click="removeDrug(idx)" />
            </div>
            <div v-if="prescriptionItems.length > 0" class="total-price">
              合计：<span class="price">¥{{ prescriptionTotal.toFixed(2) }}</span>
            </div>
          </div>

          <!-- 药品搜索和列表 - 参考 DrugManage.vue 风格 -->
          <div class="form-card">
            <div class="card-title">🔍 选择药品</div>

            <!-- 搜索框 -->
            <div class="search-bar">
              <van-search
                  v-model="drugKeyword"
                  placeholder="搜索药品名称/编码/厂家"
                  shape="round"
                  background="transparent"
                  @search="onDrugSearch"
                  @clear="onDrugClear"
              />
            </div>

            <!-- 药品列表 -->
            <div class="inventory-list">
              <div
                  v-for="drug in displayDrugList"
                  :key="drug.drugId"
                  class="drug-card"
                  :class="{ 'low-stock': (drug.stockNum || 0) <= 10 }"
                  @click="selectDrug(drug)"
              >
                <div class="drug-header">
                  <div class="drug-name">{{ drug.drugName }}</div>
                  <div class="drug-tags">
                    <van-tag v-if="(drug.stockNum || 0) <= 0" type="danger">无库存</van-tag>
                    <van-tag v-else-if="(drug.stockNum || 0) <= 10" type="danger">库存不足</van-tag>
                    <van-tag v-else type="primary">有货</van-tag>
                  </div>
                </div>
                <div class="drug-info">
                  <div class="info-row"><span class="label">编码</span><span class="value">{{ drug.drugCode || '-' }}</span></div>
                  <div class="info-row"><span class="label">规格</span><span class="value">{{ drug.drugFormat || '-' }}</span></div>
                  <div class="info-row"><span class="label">单位</span><span class="value">{{ drug.drugUnit || '-' }}</span></div>
                  <div class="info-row"><span class="label">库存</span><span class="value" :class="(drug.stockNum || 0) <= 10 ? 'warning' : ''">{{ drug.stockNum || 0 }}</span></div>
                  <div class="info-row"><span class="label">单价</span><span class="value">¥{{ (drug.drugPrice || 0).toFixed(2) }}</span></div>
                  <div class="info-row"><span class="label">厂家</span><span class="value">{{ drug.manufacturer || '-' }}</span></div>
                </div>
                <div class="drug-footer">
                  <span class="select-btn">点击选择</span>
                </div>
              </div>
              <div v-if="filteredDrugList.length === 0" class="empty-state">
                <van-icon name="medal-o" size="48" color="#C4B8A8" />
                <p>{{ drugKeyword ? '未找到匹配药品' : '暂无药品数据' }}</p>
              </div>
            </div>

            <!-- 分页 -->
            <div v-if="filteredDrugList.length > pageSize" class="pagination">
              <van-button size="small" :disabled="currentPage === 1" @click="currentPage--">上一页</van-button>
              <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
              <van-button size="small" :disabled="currentPage === totalPages" @click="currentPage++">下一页</van-button>
            </div>
          </div>

          <!-- 添加药品表单 -->
          <div class="form-card" v-if="selectedDrugInfo">
            <div class="card-title">📝 填写处方信息</div>

            <!-- 选中药品信息 -->
            <div class="selected-drug-info">
              <div class="drug-info-grid">
                <div class="info-item">
                  <span class="info-label">药品</span>
                  <span class="info-value highlight">{{ selectedDrugInfo.drugName }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">单价</span>
                  <span class="info-value price">¥{{ (selectedDrugInfo.drugPrice || 0).toFixed(2) }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">库存</span>
                  <span class="info-value" :class="{ warning: (selectedDrugInfo.stockNum || 0) <= 10 }">
                    {{ selectedDrugInfo.stockNum || 0 }}
                  </span>
                </div>
                <div class="info-item">
                  <span class="info-label">规格</span>
                  <span class="info-value">{{ selectedDrugInfo.drugFormat || '-' }}</span>
                </div>
              </div>
            </div>

            <van-field v-model="drugForm.usageRoute" label="用法" placeholder="如：口服" />
            <van-field v-model="drugForm.frequency" label="频次" placeholder="如：每日三次" />
            <van-field v-model="drugForm.dosage" label="剂量" placeholder="如：100mg" />
            <van-field v-model="drugForm.singleDose" label="单次用量" placeholder="如：1片" />
            <van-field v-model="drugForm.useDays" label="天数" type="digit" placeholder="1-90" />
            <van-field v-model="drugForm.drugNumber" label="数量" type="digit" placeholder="1-999" />

            <div class="form-actions">
              <van-button type="default" size="small" @click="cancelSelectDrug">取消</van-button>
              <van-button type="primary" size="small" round @click="addDrug" :disabled="!drugForm.drugName">
                加入处方
              </van-button>
            </div>
          </div>

          <van-button type="primary" block round :loading="savingRx" @click="submitPrescription" class="action-btn" :disabled="prescriptionItems.length === 0">
            提交处方
          </van-button>
        </div>
      </van-tab>
    </van-tabs>

    <!-- 检查/检验/处置 项目选择弹窗 -->
    <van-popup v-model:show="showTechPicker" position="bottom" round :style="{ height: '70%' }">
      <div class="picker-header">
        <span>选择{{ currentType === 'CHECK' ? '检查' : currentType === 'INSPECTION' ? '检验' : '处置' }}项目</span>
        <van-icon name="cross" @click="showTechPicker = false" />
      </div>
      <div class="tech-list">
        <div v-for="tech in filteredTechList" :key="tech.id" class="tech-option" @click="addTechItem(tech)">
          <div class="tech-info">
            <div class="tech-name">{{ tech.name }}</div>
            <div class="tech-detail">{{ tech.bodyPart }} | {{ tech.typeName }}</div>
          </div>
          <div class="tech-price">¥{{ tech.price }}</div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { useUserStore } from '@/stores/user'
import {
  saveMedicalRecord,
  createCheckRequest,
  createInspectionRequest,
  createDisposalRequest,
  getCheckResults,
  getCheckResultDetail,
  confirmDiagnosis,
  receiveDiagnosis,
  createPrescription,
  getDrugInventory,  // ✅ 改用 getDrugInventory
  getCheckList,
  getInspectionList,
  getMedicalRecord,
  getOrdersByRegisterId,
  getPrescriptionsByRegisterId,
  getDiagnosis
} from '@/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const registerId = ref(Number(route.query.registerId) || 0)
const patientName = ref(route.query.name as string || '患者')
const doctorId = computed(() => userStore.doctorId || 0)

const visitTab = ref('record')
const hasDraft = ref(false)

const patientInfo = ref({
  gender: '男',
  age: 35,
  caseNumber: ''
})

// ===== 加载已有数据 =====
const loadExistingData = async () => {
  try {
    const [record, orders, prescriptions, diagnosis] = await Promise.all([
      getMedicalRecord(registerId.value).catch(() => null),
      getOrdersByRegisterId(registerId.value).catch(() => null),
      getPrescriptionsByRegisterId(registerId.value).catch(() => null),
      getDiagnosis(registerId.value).catch(() => null)
    ])

    if (record) {
      recordForm.value = {
        registerId: registerId.value,
        readme: record.readme || '',
        present: record.present || '',
        presentTreat: record.presentTreat || '',
        history: record.history || '',
        allergy: record.allergy || '',
        physique: record.physique || '',
        proposal: record.proposal || '',
        careful: record.careful || '',
        diagnosis: record.diagnosis || ''
      }
    }

    if (orders) {
      const checks = (orders.checkRequests || []).map((r: any) => ({
        type: 'CHECK',
        medicalTechnologyId: r.medicalTechnologyId,
        name: r.checkInfo,
        position: r.checkPosition,
        price: null
      }))
      const inspections = (orders.inspectionRequests || []).map((r: any) => ({
        type: 'INSPECTION',
        medicalTechnologyId: r.medicalTechnologyId,
        name: r.inspectionInfo,
        position: r.inspectionPosition,
        price: null
      }))
      const disposals = (orders.disposalRequests || []).map((r: any) => ({
        type: 'DISPOSAL',
        medicalTechnologyId: r.medicalTechnologyId,
        name: r.disposalInfo,
        position: r.disposalPosition,
        price: null
      }))
      orderedItems.value = [...checks, ...inspections, ...disposals]
    }

    if (prescriptions && prescriptions.length > 0) {
      console.log('已有处方:', prescriptions)
    }

    if (diagnosis) {
      confirmForm.value.diagnosis = diagnosis.diagnosis || ''
      confirmForm.value.cure = diagnosis.cure || ''
      if (diagnosis.diseaseIds && diagnosis.diseaseIds.length > 0) {
        diseaseIdsText.value = diagnosis.diseaseIds.join(',')
      }
    }
  } catch (e) {
    console.error('加载已有数据失败', e)
  }
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
    await saveMedicalRecord({
      registerId: registerId.value,
      readme: recordForm.value.readme,
      present: recordForm.value.present,
      presentTreat: recordForm.value.presentTreat,
      history: recordForm.value.history,
      allergy: recordForm.value.allergy,
      physique: recordForm.value.physique,
      proposal: recordForm.value.proposal,
      careful: recordForm.value.careful,
      diagnosis: recordForm.value.diagnosis
    })
    showToast('病历保存成功')
    clearDraft()
  } catch (e: any) {
    showToast('保存失败: ' + (e.message || '未知错误'))
  } finally {
    savingRecord.value = false
  }
}

// ===== 检查检验处置 =====
const orderedItems = ref<any[]>([])
const currentType = ref<'CHECK' | 'INSPECTION' | 'DISPOSAL'>('CHECK')
const savingOrders = ref(false)
const showTechPicker = ref(false)
const techList = ref<any[]>([])

const loadTechList = async () => {
  try {
    const [checks, inspections] = await Promise.all([
      getCheckList(),
      getInspectionList()
    ])
    techList.value = [
      ...(checks || []).map((t: any) => ({ ...t, type: 'CHECK' })),
      ...(inspections || []).map((t: any) => ({ ...t, type: 'INSPECTION' }))
    ]
  } catch (e) {
    console.error('加载医疗项目失败', e)
  }
}

const filteredTechList = computed(() => {
  return techList.value.filter(t => t.type === currentType.value)
})

const addTechItem = (tech: any) => {
  const baseItem = {
    medicalTechnologyId: tech.id,
    name: tech.name,
    price: tech.price,
    position: tech.bodyPart
  }

  if (currentType.value === 'CHECK') {
    orderedItems.value.push({
      type: 'CHECK',
      ...baseItem,
      checkInfo: tech.name,
      checkPosition: tech.bodyPart
    })
  } else if (currentType.value === 'INSPECTION') {
    orderedItems.value.push({
      type: 'INSPECTION',
      ...baseItem,
      inspectionInfo: tech.name,
      inspectionPosition: tech.bodyPart
    })
  } else {
    orderedItems.value.push({
      type: 'DISPOSAL',
      ...baseItem,
      disposalInfo: tech.name,
      disposalPosition: tech.bodyPart
    })
  }
  showTechPicker.value = false
  saveDraft()
  showToast('已添加')
}

const removeOrderItem = (idx: number) => {
  orderedItems.value.splice(idx, 1)
  saveDraft()
}

const orderTotal = computed(() => {
  return orderedItems.value.reduce((sum, item) => sum + (item.price || 0), 0)
})

const submitOrders = async () => {
  if (orderedItems.value.length === 0) {
    showToast('请先添加项目')
    return
  }
  savingOrders.value = true
  try {
    const checkItems = orderedItems.value.filter(i => i.type === 'CHECK')
    const inspectionItems = orderedItems.value.filter(i => i.type === 'INSPECTION')
    const disposalItems = orderedItems.value.filter(i => i.type === 'DISPOSAL')

    const promises: Promise<any>[] = []
    if (checkItems.length > 0) {
      promises.push(createCheckRequest({
        registerId: registerId.value,
        items: checkItems.map(i => ({
          medicalTechnologyId: i.medicalTechnologyId,
          checkInfo: i.checkInfo,
          checkPosition: i.checkPosition
        }))
      }))
    }
    if (inspectionItems.length > 0) {
      promises.push(createInspectionRequest({
        registerId: registerId.value,
        items: inspectionItems.map(i => ({
          medicalTechnologyId: i.medicalTechnologyId,
          inspectionInfo: i.inspectionInfo,
          inspectionPosition: i.inspectionPosition
        }))
      }))
    }
    if (disposalItems.length > 0) {
      promises.push(createDisposalRequest({
        registerId: registerId.value,
        items: disposalItems.map(i => ({
          medicalTechnologyId: i.medicalTechnologyId,
          disposalInfo: i.disposalInfo,
          disposalPosition: i.disposalPosition
        }))
      }))
    }

    await Promise.all(promises)
    showToast('申请提交成功')
    orderedItems.value = []
    clearDraft()
  } catch (e: any) {
    showToast('提交失败: ' + (e.message || '未知错误'))
  } finally {
    savingOrders.value = false
  }
}

// ===== 结果查看 =====
const checkResults = ref<any>({})
const loadingResults = ref(false)

const getStateText = (state?: string) => {
  const map: Record<string, string> = {
    'CREATED': '待执行',
    'ASSIGNED': '已分配',
    'BOOKED': '已预约',
    'COMPLETED': '已完成',
    'REPORTED': '已出报告'
  }
  return map[state || ''] || state || '未知'
}

const hasAnyResult = computed(() => {
  return (checkResults.value.checkRequests?.length > 0) ||
      (checkResults.value.inspectionRequests?.length > 0)
})

const totalDoneResults = computed(() => {
  let count = 0
  const checks = checkResults.value.checkRequests || []
  const inspections = checkResults.value.inspectionRequests || []
  checks.forEach((r: any) => {
    if (r.checkState === 'COMPLETED' || r.checkState === 'REPORTED') count++
  })
  inspections.forEach((r: any) => {
    if (r.inspectionState === 'COMPLETED' || r.inspectionState === 'REPORTED') count++
  })
  return count
})

const loadResults = async () => {
  loadingResults.value = true
  showLoadingToast({ message: '加载中...', forbidClick: true })
  try {
    const res = await getCheckResults(registerId.value)
    checkResults.value = {
      checkRequests: res.checkRequests || [],
      inspectionRequests: res.inspectionRequests || []
    }
    closeToast()
  } catch (e: any) {
    closeToast()
    showToast('加载失败: ' + (e.message || '未知错误'))
  } finally {
    loadingResults.value = false
  }
}

// ===== 确诊 =====
const confirmForm = ref({
  registerId: registerId.value,
  diagnosis: '',
  cure: '',
  diseaseIds: [] as number[]
})
const diseaseIdsText = ref('')
const confirming = ref(false)

const submitConfirm = async () => {
  if (!confirmForm.value.diagnosis) {
    showToast('请填写诊断')
    return
  }
  confirming.value = true
  try {
    const diseaseIds = diseaseIdsText.value
        .split(/[,，]/)
        .map(s => parseInt(s.trim()))
        .filter(n => !isNaN(n))

    await receiveDiagnosis({
      registerId: registerId.value,
      diagnosis: confirmForm.value.diagnosis,
      cure: confirmForm.value.cure,
      diseaseIds: diseaseIds.length > 0 ? diseaseIds : undefined
    })
    showToast('确诊成功')
    clearDraft()
  } catch (e: any) {
    showToast('确诊失败: ' + (e.message || '未知错误'))
  } finally {
    confirming.value = false
  }
}

// ===== 处方 - 参考 DrugManage.vue 风格 =====
const prescriptionItems = ref<any[]>([])
const allDrugList = ref<any[]>([])
const drugKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const selectedDrugInfo = ref<any>(null)

// 药品表单
const drugForm = ref({
  drugId: 0,
  drugName: '',
  usageRoute: '口服',
  frequency: '每日一次',
  dosage: '',
  singleDose: '1片',
  useDays: 7,
  drugNumber: 1,
  drugPrice: 0
})

// 过滤后的药品列表
const filteredDrugList = computed(() => {
  const kw = drugKeyword.value.trim().toLowerCase()
  if (!kw) return allDrugList.value
  return allDrugList.value.filter(drug =>
      drug.drugName?.toLowerCase().includes(kw) ||
      drug.drugCode?.toLowerCase().includes(kw) ||
      drug.manufacturer?.toLowerCase().includes(kw)
  )
})

// 当前页显示的药品
const displayDrugList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredDrugList.value.slice(start, end)
})

// 总页数
const totalPages = computed(() =>
    Math.ceil(filteredDrugList.value.length / pageSize.value) || 1
)

// 搜索
const onDrugSearch = () => {
  currentPage.value = 1
}

const onDrugClear = () => {
  drugKeyword.value = ''
  currentPage.value = 1
}

// 加载药品 - 参考 DrugManage.vue 的 loadInventory
const loadDrugInventory = async () => {
  showLoadingToast({ message: '加载药品...', forbidClick: true })
  try {
    const allDrugs: any[] = []
    let page = 1
    let total = 1

    while (allDrugs.length < total) {
      const res = await getDrugInventory({
        pageNum: page,
        pageSize: 50
      })
      const records = res.records || []
      allDrugs.push(...records)
      total = res.total || 0
      if (records.length === 0) break
      page++
    }

    allDrugList.value = allDrugs
    console.log('[PatientVisit] 加载药品成功，共', allDrugList.value.length, '种')
    closeToast()
  } catch (e) {
    console.error('[PatientVisit] 加载药品失败', e)
    closeToast()
    showToast('加载药品失败')
  }
}

// 选择药品
const selectDrug = (drug: any) => {
  if ((drug.stockNum || 0) <= 0) {
    showToast('该药品库存不足')
    return
  }

  selectedDrugInfo.value = drug
  drugForm.value = {
    drugId: drug.drugId,
    drugName: drug.drugName,
    drugPrice: drug.drugPrice || 0,
    usageRoute: '口服',
    frequency: '每日一次',
    dosage: drug.drugDosage || drug.dosage || '',
    singleDose: '1片',
    useDays: 7,
    drugNumber: 1
  }

  // 滚动到表单位置
  setTimeout(() => {
    document.querySelector('.form-card:last-child')?.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    })
  }, 100)
}

// 取消选择
const cancelSelectDrug = () => {
  selectedDrugInfo.value = null
  drugForm.value = {
    drugId: 0,
    drugName: '',
    usageRoute: '口服',
    frequency: '每日一次',
    dosage: '',
    singleDose: '1片',
    useDays: 7,
    drugNumber: 1,
    drugPrice: 0
  }
}

// 添加药品到处方
const addDrug = () => {
  if (!drugForm.value.drugName) {
    showToast('请先选择药品')
    return
  }

  const drug = allDrugList.value.find(d => d.drugId === drugForm.value.drugId)
  if (drug && (drug.stockNum || 0) < (drugForm.value.drugNumber || 1)) {
    showToast(`库存不足，当前库存: ${drug.stockNum}`)
    return
  }

  const existing = prescriptionItems.value.find(item => item.drugId === drugForm.value.drugId)
  if (existing) {
    showToast('该药品已添加，请勿重复添加')
    return
  }

  prescriptionItems.value.push({ ...drugForm.value })

  // 重置表单
  cancelSelectDrug()
  showToast('已添加')
  saveDraft()
}

// 移除药品
const removeDrug = (idx: number) => {
  prescriptionItems.value.splice(idx, 1)
  saveDraft()
}

// 处方合计
const prescriptionTotal = computed(() => {
  return prescriptionItems.value.reduce((sum, item) => sum + ((item.drugPrice || 0) * (item.drugNumber || 1)), 0)
})

const savingRx = ref(false)

// 提交处方
const submitPrescription = async () => {
  if (prescriptionItems.value.length === 0) {
    showToast('处方不能为空')
    return
  }
  savingRx.value = true
  try {
    await createPrescription({
      registerId: registerId.value,
      doctorId: doctorId.value,
      items: prescriptionItems.value.map(item => ({
        drugId: item.drugId,
        usageRoute: item.usageRoute,
        frequency: item.frequency,
        dosage: item.dosage,
        singleDose: item.singleDose,
        useDays: item.useDays,
        drugNumber: item.drugNumber
      }))
    })
    showToast('处方提交成功')
    prescriptionItems.value = []
    selectedDrugInfo.value = null
    clearDraft()
  } catch (e: any) {
    showToast('提交失败: ' + (e.message || '未知错误'))
  } finally {
    savingRx.value = false
  }
}

// ===== 草稿保存 =====
const saveDraft = () => {
  const draft = {
    registerId: registerId.value,
    recordForm: recordForm.value,
    orderedItems: orderedItems.value,
    prescriptionItems: prescriptionItems.value,
    confirmForm: confirmForm.value,
    diseaseIdsText: diseaseIdsText.value,
    timestamp: Date.now()
  }
  localStorage.setItem(`draft_${registerId.value}`, JSON.stringify(draft))
  hasDraft.value = true
}

const loadDraft = () => {
  const key = `draft_${registerId.value}`
  const saved = localStorage.getItem(key)
  if (saved) {
    try {
      const draft = JSON.parse(saved)
      if (draft.recordForm) recordForm.value = draft.recordForm
      if (draft.orderedItems) orderedItems.value = draft.orderedItems
      if (draft.prescriptionItems) prescriptionItems.value = draft.prescriptionItems
      if (draft.confirmForm) confirmForm.value = draft.confirmForm
      if (draft.diseaseIdsText) diseaseIdsText.value = draft.diseaseIdsText
      hasDraft.value = true
    } catch (e) {
      console.error('加载草稿失败', e)
    }
  }
}

const clearDraft = () => {
  localStorage.removeItem(`draft_${registerId.value}`)
  hasDraft.value = false
}

// ===== 跳转 =====
const goBack = () => {
  saveDraft()
  router.push('/doctor')
}

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

const hasTriageResult = ref(false)
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

const onTabChange = () => {
  saveDraft()
  if (visitTab.value === 'result') {
    loadResults()
  }
}

// ===== 生命周期 =====
onMounted(() => {
  if (!userStore.isLoggedIn || !userStore.doctorId) {
    showToast('请先登录')
    router.push('/auth/login')
    return
  }
  loadDraft()
  loadExistingData()
  loadTechList()
  loadDrugInventory()  // ✅ 使用 getDrugInventory
})

onBeforeUnmount(() => {
  saveDraft()
})
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

.type-selector {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
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

    .item-name {
      flex: 1;
      font-size: 14px;
      color: #2C3E50;
    }

    .item-price {
      color: #E76F51;
      font-weight: 600;
    }

    .delete-icon {
      color: #E74C3C;
      font-size: 16px;
      cursor: pointer;
    }
  }

  .item-sub {
    font-size: 12px;
    color: #7F8C8D;
    margin-top: 4px;
  }
}

.total-price {
  text-align: right;
  font-size: 14px;
  color: #2C3E50;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #E0E0E0;

  .price {
    font-size: 18px;
    font-weight: 700;
    color: #E76F51;
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

/* ===== 药品样式 - 参考 DrugManage.vue ===== */

// 已选药品
.drug-item {
  background: #F5F7FA;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  position: relative;
  border-left: 3px solid #005B96;

  .drug-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;

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

    &:hover {
      color: #E74C3C;
    }
  }
}

.picker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #F0F0F0;
}

.tech-list {
  padding: 8px;
  height: calc(100% - 60px);
  overflow-y: auto;
}

.tech-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #F5F5F5;
  cursor: pointer;

  &:active {
    background: #F5F7FA;
  }

  .tech-info {
    flex: 1;

    .tech-name {
      font-size: 14px;
      color: #2C3E50;
      font-weight: 500;
    }

    .tech-detail {
      font-size: 12px;
      color: #7F8C8D;
      margin-top: 2px;
    }
  }

  .tech-price {
    font-size: 14px;
    color: #E76F51;
    font-weight: 600;
  }
}

/* ===== 药品列表样式 - 完全参考 DrugManage.vue ===== */
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
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

  &.low-stock {
    border-left: 3px solid #E76F51;
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

    .drug-tags {
      display: flex;
      gap: 4px;
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

  .drug-footer {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid #F0F0F0;
    text-align: right;

    .select-btn {
      font-size: 13px;
      color: #005B96;
      font-weight: 500;
    }
  }
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #C4B8A8;
}

.empty-mini {
  text-align: center;
  padding: 20px 0;
  color: #BDC3C7;
  font-size: 13px;
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

/* ===== 选中药品信息展示 ===== */
.selected-drug-info {
  background: #F5F9FF;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #D4E8F7;

  .drug-info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4px 16px;

    .info-item {
      display: flex;
      justify-content: space-between;
      padding: 2px 0;

      .info-label {
        font-size: 12px;
        color: #8B7A6B;
      }

      .info-value {
        font-size: 13px;
        color: #2C3E50;
        font-weight: 500;

        &.highlight {
          color: #005B96;
          font-weight: 600;
        }

        &.warning {
          color: #E76F51;
        }

        &.price {
          color: #E76F51;
          font-weight: 700;
        }
      }
    }
  }
}

/* ===== 表单操作按钮 ===== */
.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>