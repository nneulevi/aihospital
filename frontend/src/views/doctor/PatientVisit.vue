<!-- src/views/doctor/PatientVisit.vue -->
<template>
  <div class="patient-visit">
    <van-nav-bar
        :title="patientName || '患者诊疗'"
        fixed
        placeholder
        left-arrow
        @click-left="() => router.back()"
    >
      <template #right>
        <van-tag type="primary" size="medium">就诊中</van-tag>
      </template>
    </van-nav-bar>

    <!-- 患者信息卡片 -->
    <div class="patient-card-top">
      <div class="info-row">
        <span class="name">{{ patientName }}</span>
        <span class="gender">{{ patientInfo.gender }}</span>
        <span class="age">{{ patientInfo.age }}岁</span>
      </div>
      <div class="info-row sub">
        <span>病历号: {{ patientInfo.caseNumber }}</span>
        <span>挂号ID: {{ registerId }}</span>
      </div>
      <van-button
        class="return-waiting-btn"
        plain
        round
        size="small"
        type="primary"
        :loading="returningWaiting"
        @click="returnWaiting"
      >
        退回候诊
      </van-button>
    </div>

    <!-- 诊疗流程 Tab -->
    <van-tabs v-model:active="visitTab" class="visit-tabs" sticky offset-top="96">
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

          <van-button type="warning" block round :loading="aiLoading" @click="getAiSuggestion" class="action-btn">
            🤖 AI 诊断建议
          </van-button>
          <div v-if="aiStreamStatus" class="ai-stream-status">
            {{ aiStreamStatus }}
          </div>
          <div v-if="aiStreamText" class="ai-stream-text">
            {{ aiStreamText }}
          </div>

          <div v-if="aiSuggestions.length > 0" class="ai-card">
            <div class="ai-title-row">
              <div>
                <div class="ai-title">AI 诊断建议</div>
                <p>结合当前病历要点生成，医生可采纳后继续编辑。</p>
              </div>
              <van-tag type="primary">{{ aiSuggestions.length }} 条建议</van-tag>
            </div>
            <div v-for="(s, idx) in aiSuggestions" :key="idx" class="suggestion-item">
              <div class="suggestion-header">
                <div>
                  <span class="disease-name">{{ s.diseaseName }}</span>
                  <div class="suggestion-evidence">{{ s.evidence || '暂无证据说明' }}</div>
                </div>
                <van-tag :type="suggestionTagType(s.confidence)">
                  {{ suggestionConfidencePercent(s.confidence) }}%
                </van-tag>
              </div>
              <div class="suggestion-meter" aria-label="AI 诊断置信度">
                <div
                  class="suggestion-meter-fill"
                  :style="{ width: `${suggestionConfidencePercent(s.confidence)}%` }"
                ></div>
              </div>
              <div class="suggestion-actions">
                <span>建议复核主诉、体征和检查结果后确认</span>
                <van-button size="small" type="primary" plain @click="adoptSuggestion(s)">采纳</van-button>
              </div>
            </div>
          </div>
        </div>
      </van-tab>

      <!-- 检查/检验 -->
      <van-tab title="检查检验" name="check">
        <div class="tab-panel">
          <!-- 已开项目 -->
          <div class="list-card">
            <div class="card-title">📋 已开项目</div>
            <div v-if="existingOrders.length === 0 && orderedItems.length === 0" class="empty-mini">暂无已开项目</div>
            <div v-for="item in existingOrders" :key="item.key" class="ordered-item existing">
              <div class="item-main">
                <van-tag :type="item.type === 'CHECK' ? 'primary' : item.type === 'INSPECTION' ? 'warning' : 'success'">
                  {{ item.type === 'CHECK' ? '检查' : item.type === 'INSPECTION' ? '检验' : '处置' }}
                </van-tag>
                <span class="item-name">{{ item.name }}</span>
                <van-tag plain>{{ item.stateName }}</van-tag>
              </div>
              <div class="item-sub">{{ item.position }}</div>
            </div>
            <div v-for="(item, idx) in orderedItems" :key="`draft-${idx}`" class="ordered-item">
              <div class="item-main">
                <van-tag :type="item.type === 'CHECK' ? 'primary' : item.type === 'INSPECTION' ? 'warning' : 'success'">
                  {{ item.type === 'CHECK' ? '检查' : item.type === 'INSPECTION' ? '检验' : '处置' }}
                </van-tag>
                <span class="item-name">{{ item.name }}</span>
                <van-tag plain type="warning">待提交</van-tag>
              </div>
              <div class="item-sub">{{ item.position }}</div>
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
            <div v-for="r in checkResults.checkRequests" :key="r.id" class="result-card">
              <div class="result-header">
                <span class="result-name">{{ r.checkInfo }}</span>
                <van-tag :type="r.checkState === 'DONE' ? 'success' : 'warning'">
                  {{ r.checkState === 'DONE' ? '已出结果' : '待执行' }}
                </van-tag>
              </div>
              <div v-if="r.checkResult" class="result-body">
                <div class="result-label">检查所见：</div>
                <div class="result-text">{{ r.checkResult }}</div>
              </div>
              <div v-if="r.checkRemark" class="result-body">
                <div class="result-label">备注：</div>
                <div class="result-text">{{ r.checkRemark }}</div>
              </div>
            </div>
          </div>

          <div v-if="checkResults.inspectionRequests && checkResults.inspectionRequests.length > 0" class="result-group">
            <div class="result-title">🧪 检验结果</div>
            <div v-for="r in checkResults.inspectionRequests" :key="r.id" class="result-card">
              <div class="result-header">
                <span class="result-name">{{ r.inspectionInfo }}</span>
                <van-tag :type="r.inspectionState === 'DONE' ? 'success' : 'warning'">
                  {{ r.inspectionState === 'DONE' ? '已出结果' : '待执行' }}
                </van-tag>
              </div>
              <div v-if="r.inspectionResult" class="result-body">
                <div class="result-text">{{ r.inspectionResult }}</div>
              </div>
            </div>
          </div>

          <div v-if="checkResults.disposalRequests && checkResults.disposalRequests.length > 0" class="result-group">
            <div class="result-title">🩹 处置记录</div>
            <div v-for="r in checkResults.disposalRequests" :key="r.id" class="result-card">
              <div class="result-header">
                <span class="result-name">{{ r.disposalInfo }}</span>
                <van-tag :type="r.disposalState === 'DONE' ? 'success' : 'warning'">
                  {{ r.disposalState === 'DONE' ? '已完成' : '待执行' }}
                </van-tag>
              </div>
            </div>
          </div>

          <!-- AI 影像识别与报告 -->
          <div class="ai-report-card">
            <div class="ai-report-title-row">
              <div>
                <div class="ai-report-title">AI 影像识别与报告生成</div>
                <p>上传头部 CT 后执行伪影评估、影像识别与报告草稿生成。</p>
              </div>
              <van-icon name="scan" />
            </div>
            <van-cell-group inset>
              <van-field
                  v-model="aiImageForm.checkRequestId"
                  label="检查申请ID"
                  type="digit"
                  placeholder="选择或输入检查申请ID"
              />
              <van-field
                  v-model="aiImageForm.imageFileId"
                  label="影像文件ID"
                  type="digit"
                  placeholder="上传后自动填入，也可手动输入"
              />
              <van-field
                  v-model="reportForm.reportType"
                  label="报告类型"
                  placeholder="如：HEAD_CT"
              />
              <div class="upload-row">
                <input type="file" accept=".dcm,.nii,.nii.gz,.nrrd,.png,.jpg,.jpeg" @change="onImageFileChange" />
                <van-button size="small" type="primary" :loading="uploadingImage" @click="uploadImageFile">
                  上传影像
                </van-button>
              </div>
            </van-cell-group>
            <div class="ai-actions">
              <van-button type="primary" round :loading="analyzingImage" @click="analyzeImage">
                AI识别
              </van-button>
              <van-button type="success" round :loading="generatingReport" @click="generateAiReport">
                生成报告
              </van-button>
            </div>
            <div v-if="imageAnalysis" class="ai-report-content">
              <div class="analysis-summary-grid">
                <div class="analysis-summary-item">
                  <span>出血阳性概率</span>
                  <strong>{{ formatConfidence(positiveProbability) }}</strong>
                </div>
                <div class="analysis-summary-item">
                  <span>分析可靠性</span>
                  <strong>{{ analysisReliabilityText }}</strong>
                </div>
              </div>
              <div class="analysis-text-block">
                <strong>影像所见</strong>
                <p>{{ imageAnalysis.findings || '暂无' }}</p>
              </div>
              <div class="analysis-text-block">
                <strong>AI结论</strong>
                <p>{{ imageAnalysis.conclusion || '暂无' }}</p>
              </div>
              <div v-if="previewUrlList.length" class="preview-panel">
                <div class="preview-title">影像可视化输出</div>
                <div class="preview-grid">
                  <div v-for="item in previewUrlList" :key="item.label" class="preview-item">
                    <img :src="item.url" :alt="`${item.label}预览图`" />
                    <span>{{ item.label }}</span>
                  </div>
                </div>
              </div>
              <div v-if="positiveProbability !== undefined && positiveProbability !== null" class="confidence-panel">
                <div class="confidence-header">
                  <span>颅内出血阳性概率</span>
                  <strong>{{ imageConfidencePercent }}%</strong>
                </div>
                <div class="confidence-bar" role="progressbar" :aria-valuenow="imageConfidencePercent" aria-valuemin="0" aria-valuemax="100">
                  <div class="confidence-fill" :style="{ width: `${imageConfidencePercent}%`, background: confidenceColor }"></div>
                </div>
                <div class="confidence-note">
                  {{ confidenceInterpretation }}
                </div>
              </div>
              <div v-if="subtypeProbabilityList.length" class="subtype-panel">
                <div class="subtype-title">出血亚型概率</div>
                <div class="subtype-list">
                  <div v-for="item in subtypeProbabilityList" :key="item.key" class="subtype-row">
                    <span>{{ item.label }}</span>
                    <div class="subtype-meter">
                      <div class="subtype-meter-fill" :style="{ width: `${item.percent}%` }"></div>
                    </div>
                    <strong>{{ item.percent }}%</strong>
                  </div>
                </div>
              </div>
              <div v-if="imageAnalysis.aiImagingStatus" class="ai-status-panel">
                <div class="ai-status-header">
                  <span>链路状态</span>
                  <van-tag :type="aiWorkflowReady ? 'success' : 'warning'">
                    {{ formatProjectUseStatus(readStatusField(aiStatus, 'projectUseStatus', 'project_use_status')) }}
                  </van-tag>
                </div>
                <div class="ai-status-grid">
                  <div>
                    <span class="status-label">伪影模型</span>
                    <strong>{{ readStatusField(qualityControlModel, 'modelName', 'model_name') || '--' }}</strong>
                  </div>
                  <div>
                    <span class="status-label">校正状态</span>
                    <strong>{{ formatReductionStatus(readStatusField(artifactReduction, 'status', 'status')) }}</strong>
                  </div>
                  <div>
                    <span class="status-label">病灶模型</span>
                    <strong>{{ readStatusField(lesionModel, 'modelName', 'model_name') || '--' }}</strong>
                  </div>
                  <div>
                    <span class="status-label">输出类型</span>
                    <strong>{{ readStatusField(lesionModel, 'taskType', 'task_type') === 'segmentation' ? '分割' : '分类' }}</strong>
                  </div>
                </div>
                <div v-if="aiStatus.limitations?.length" class="status-limitations">
                  {{ aiStatus.limitations.join(' / ') }}
                </div>
              </div>
              <div v-if="modelLimitationsList.length" class="analysis-text-block">
                <strong>模型限制与复核重点</strong>
                <p v-for="item in modelLimitationsList" :key="item">{{ item }}</p>
              </div>
              <div v-if="imageAnalysis.annotations?.length" class="annotation-list">
                <div v-for="(annotation, idx) in imageAnalysis.annotations" :key="idx" class="annotation-item">
                  <span>{{ annotation.label || '标注' }}</span>
                  <small>x={{ annotation.x ?? 0 }}，y={{ annotation.y ?? 0 }}，w={{ annotation.width ?? 0 }}，h={{ annotation.height ?? 0 }}</small>
                </div>
              </div>
            </div>
            <div v-if="aiReport" class="ai-report-content">
              <div class="report-meta-grid">
                <div>
                  <span>报告ID</span>
                  <strong>{{ aiReport.reportId || '--' }}</strong>
                </div>
                <div>
                  <span>状态</span>
                  <strong>{{ aiReport.status || '--' }}</strong>
                </div>
              </div>
              <p class="report-text">{{ aiReport.reportContent || '暂无报告内容' }}</p>
            </div>
          </div>

          <div v-if="!hasAnyResult && !imageAnalysis && !aiReport" class="empty-state">
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
              <van-field v-model="diseaseIdsText" label="疾病编码" placeholder="如：1,2,3（逗号分隔）" />
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
          <div class="list-card">
            <div class="card-title">📄 已开处方</div>
            <div v-if="existingPrescriptions.length === 0" class="empty-mini">暂无已开处方</div>
            <div v-for="item in existingPrescriptions" :key="item.id" class="drug-item">
              <div class="drug-header">
                <span class="drug-name">{{ item.prescriptionNo || `处方 ${item.id}` }}</span>
                <span class="drug-price">¥{{ Number(item.totalAmount || 0).toFixed(2) }}</span>
              </div>
              <div class="drug-detail">
                状态：{{ item.prescriptionStatus || 'CREATED' }} | 开立时间：{{ item.creationTime || '-' }}
              </div>
            </div>
          </div>

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
                {{ item.usageRoute }} | {{ item.frequency }} | {{ item.dosage }} | {{ item.useDays }}天 | ×{{ item.drugNumber }}
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

    <van-action-sheet v-model:show="showDrugPicker" title="选择药品">
      <div class="drug-picker-list">
        <button
          v-for="option in drugOptions"
          :key="option.value"
          type="button"
          class="drug-picker-option"
          @click="selectDrug(option)"
        >
          <span>{{ option.text }}</span>
          <strong>¥{{ option.price.toFixed(2) }}</strong>
        </button>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { useUserStore } from '@/stores/user'
import {
  saveMedicalRecord, suggest, diagnosisSuggestStream, createCheckRequest, createInspectionRequest,
  createDisposalRequest, getCheckResults, confirmDiagnosis, createPrescription,
  upload, analyze, reportGenerate, getPatientDetail, returnPatientToWaiting,
  getMedicalRecord, getOrdersByRegisterId, getPrescriptionsByRegisterId, getDiagnosis
} from '@/api'
import type {
  MedicalRecordSaveRequestDTO, DiagnosisSuggestRequestDTO, DiagnosisSuggestResponseVO,
  CheckRequestCreateDTO, CheckItemDTO, InspectionRequestCreateDTO, InspectionItemDTO,
  DisposalRequestCreateDTO, DisposalItemDTO, CheckResultVO, DiagnosisConfirmRequestDTO,
  PrescriptionCreateDTO, PrescriptionItemDTO, ImageAnalyzeResponseVO, ReportGenerateResponseVO,
  DoctorPatientListVO
} from '@/api/model'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const registerId = ref(Number(route.query.registerId) || 0)
const patientName = ref(route.query.name as string || '患者')

const visitTab = ref('record')
const returningWaiting = ref(false)

// 患者信息
const patientInfo = ref({
  gender: '男',
  age: 35,
  caseNumber: 'HN202600006'
})

const loadPatientDetail = async () => {
  if (!registerId.value) return
  try {
    const res = await getPatientDetail(registerId.value)
    const data = (res.data || res) as DoctorPatientListVO
    patientName.value = data.patientName || patientName.value
    patientInfo.value = {
      gender: data.gender || patientInfo.value.gender,
      age: data.age ?? patientInfo.value.age,
      caseNumber: data.caseNumber || patientInfo.value.caseNumber
    }
  } catch {
    showToast('患者详情加载失败')
  }
}

// 病历
const recordForm = ref<MedicalRecordSaveRequestDTO>({
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
const aiLoading = ref(false)
const aiStreamStatus = ref('')
const aiStreamText = ref('')
const aiSuggestions = ref<any[]>([])

const saveRecord = async () => {
  savingRecord.value = true
  try {
    await saveMedicalRecord({ ...recordForm.value, registerId: registerId.value })
    showToast('病历保存成功')
  } catch {
    showToast('保存失败')
  } finally {
    savingRecord.value = false
  }
}

const getAiSuggestion = async () => {
  aiLoading.value = true
  aiStreamStatus.value = '正在建立 AI 流式连接...'
  aiStreamText.value = ''
  try {
    let finalPayload: any = null
    await diagnosisSuggestStream({
      medicalRecordId: registerId.value,
      symptoms: recordForm.value.readme,
      history: recordForm.value.history,
      physique: recordForm.value.physique
    }, {
      onEvent: ({ event, data }) => {
        if (event === 'memory_loaded' || event === 'rag_retrieved' || event === 'llm_generating') {
          aiStreamStatus.value = data?.message || aiStreamStatus.value
        } else if (event === 'delta') {
          aiStreamText.value += data?.text || ''
        }
      },
      onFinal: (data) => {
        finalPayload = data?.data || data
      },
      onError: (data) => {
        throw new Error(data?.message || 'AI建议获取失败')
      },
    })
    if (!finalPayload) {
      throw new Error('AI流式响应缺少最终结果')
    }
    aiSuggestions.value = finalPayload?.suggestions || []
  } catch {
    try {
      aiStreamStatus.value = '流式连接不可用，正在切换普通分析...'
      const res = await suggest({
        medicalRecordId: registerId.value,
        symptoms: recordForm.value.readme,
        history: recordForm.value.history,
        physique: recordForm.value.physique
      })
      aiSuggestions.value = res.data?.suggestions || []
    } catch {
      showToast('AI建议获取失败')
    }
  } finally {
    aiStreamStatus.value = ''
    aiStreamText.value = ''
    aiLoading.value = false
  }
}

const returnWaiting = async () => {
  if (!registerId.value) {
    showToast('缺少挂号ID')
    return
  }
  returningWaiting.value = true
  try {
    await returnPatientToWaiting(registerId.value)
    showToast('已退回候诊队列')
    router.replace('/doctor')
  } catch {
    showToast('退回候诊失败')
  } finally {
    returningWaiting.value = false
  }
}

const adoptSuggestion = (s: any) => {
  recordForm.value.diagnosis = s.diseaseName
  showToast(`已采纳：${s.diseaseName}`)
}

const suggestionConfidencePercent = (confidence?: number) => {
  if (confidence === undefined || confidence === null) return 0
  return Math.max(0, Math.min(100, Math.round(confidence * 100)))
}

const suggestionTagType = (confidence?: number) => {
  const percent = suggestionConfidencePercent(confidence)
  if (percent >= 75) return 'success'
  if (percent >= 45) return 'warning'
  return 'default'
}

// 检查/检验/处置
const orderedItems = ref<any[]>([])
const existingOrders = ref<any[]>([])
const newCheck = ref<CheckItemDTO>({ medicalTechnologyId: 1, checkInfo: '', checkPosition: '' })
const newInspection = ref<InspectionItemDTO>({ medicalTechnologyId: 4, inspectionInfo: '', inspectionPosition: '' })
const newDisposal = ref<DisposalItemDTO>({ medicalTechnologyId: 6, disposalInfo: '', disposalPosition: '' })
const savingOrders = ref(false)

const addCheck = () => {
  if (!newCheck.value.checkInfo?.trim()) { showToast('请填写检查项目'); return }
  if (!newCheck.value.checkPosition?.trim()) { showToast('请填写检查部位'); return }
  orderedItems.value.push({ type: 'CHECK', ...newCheck.value })
  newCheck.value = { medicalTechnologyId: 1, checkInfo: '', checkPosition: '' }
  showToast('已添加检查')
}

const addInspection = () => {
  if (!newInspection.value.inspectionInfo?.trim()) { showToast('请填写检验项目'); return }
  if (!newInspection.value.inspectionPosition?.trim()) { showToast('请填写检验样本'); return }
  orderedItems.value.push({ type: 'INSPECTION', ...newInspection.value })
  newInspection.value = { medicalTechnologyId: 4, inspectionInfo: '', inspectionPosition: '' }
  showToast('已添加检验')
}

const addDisposal = () => {
  if (!newDisposal.value.disposalInfo?.trim()) { showToast('请填写处置项目'); return }
  if (!newDisposal.value.disposalPosition?.trim()) { showToast('请填写处置部位'); return }
  orderedItems.value.push({ type: 'DISPOSAL', ...newDisposal.value })
  newDisposal.value = { medicalTechnologyId: 6, disposalInfo: '', disposalPosition: '' }
  showToast('已添加处置')
}

const submitOrders = async () => {
  const checks = orderedItems.value.filter(i => i.type === 'CHECK')
  const inspections = orderedItems.value.filter(i => i.type === 'INSPECTION')
  const disposals = orderedItems.value.filter(i => i.type === 'DISPOSAL')
  if (checks.length + inspections.length + disposals.length === 0) {
    showToast('请先添加检查、检验或处置项目')
    return
  }

  savingOrders.value = true
  try {
    if (checks.length > 0) {
      await createCheckRequest({ registerId: registerId.value, items: checks.map(c => ({ medicalTechnologyId: c.medicalTechnologyId, checkInfo: c.checkInfo, checkPosition: c.checkPosition })) })
    }
    if (inspections.length > 0) {
      await createInspectionRequest({ registerId: registerId.value, items: inspections.map(c => ({ medicalTechnologyId: c.medicalTechnologyId, inspectionInfo: c.inspectionInfo, inspectionPosition: c.inspectionPosition })) })
    }
    if (disposals.length > 0) {
      await createDisposalRequest({ registerId: registerId.value, items: disposals.map(c => ({ medicalTechnologyId: c.medicalTechnologyId, disposalInfo: c.disposalInfo, disposalPosition: c.disposalPosition })) })
    }
    showToast('申请提交成功')
    orderedItems.value = []
    await loadExistingOrders()
  } catch {
    showToast('提交失败')
  } finally {
    savingOrders.value = false
  }
}

// 结果查看
const checkResults = ref<CheckResultVO>({})
const selectedImageFile = ref<File | null>(null)
const uploadingImage = ref(false)
const analyzingImage = ref(false)
const generatingReport = ref(false)
const imageAnalysis = ref<ImageAnalyzeResponseVO | null>(null)
const aiReport = ref<ReportGenerateResponseVO | null>(null)
const aiImageForm = ref({
  checkRequestId: '',
  imageFileId: ''
})
const reportForm = ref({
  reportType: 'HEAD_CT'
})
const hasAnyResult = computed(() => {
  return (checkResults.value.checkRequests && checkResults.value.checkRequests.length > 0) ||
      (checkResults.value.inspectionRequests && checkResults.value.inspectionRequests.length > 0) ||
      (checkResults.value.disposalRequests && checkResults.value.disposalRequests.length > 0)
})

const loadResults = async () => {
  showLoadingToast({ message: '加载中...', forbidClick: true })
  try {
    const res = await getCheckResults(registerId.value)
    checkResults.value = res.data || {}
    existingOrders.value = mapExistingOrders(checkResults.value)
    closeToast()
  } catch {
    closeToast()
    showToast('加载失败')
  }
}

const onImageFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  selectedImageFile.value = target.files?.[0] || null
}

const getEffectiveCheckRequestId = () => {
  const manualId = Number(aiImageForm.value.checkRequestId)
  if (manualId) return manualId
  const firstCheckId = checkResults.value.checkRequests?.[0]?.id
  if (firstCheckId) {
    aiImageForm.value.checkRequestId = String(firstCheckId)
    return firstCheckId
  }
  return 0
}

const uploadImageFile = async () => {
  const checkRequestId = getEffectiveCheckRequestId()
  if (!checkRequestId) {
    showToast('请先填写或查询检查申请ID')
    return
  }
  if (!selectedImageFile.value) {
    showToast('请选择影像文件')
    return
  }

  uploadingImage.value = true
  try {
    const res = await upload(
      { file: selectedImageFile.value },
      { checkRequestId, registerId: registerId.value },
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    const data = res.data || res
    const uploadedId =
      data?.imageFileId ??
      data?.id ??
      (typeof data === 'string' ? tryParseImageFileId(data) : undefined)
    if (!uploadedId) {
      throw new Error('missing imageFileId')
    }
    aiImageForm.value.imageFileId = String(uploadedId)
    showToast('影像上传成功')
  } catch {
    showToast('影像上传失败')
  } finally {
    uploadingImage.value = false
  }
}

const tryParseImageFileId = (value: string) => {
  try {
    const parsed = JSON.parse(value)
    return parsed?.imageFileId ?? parsed?.id
  } catch {
    return Number(value) || undefined
  }
}

const analyzeImage = async () => {
  const checkRequestId = getEffectiveCheckRequestId()
  const imageFileId = Number(aiImageForm.value.imageFileId)
  if (!checkRequestId || !imageFileId) {
    showToast('请填写检查申请ID和影像文件ID')
    return
  }

  analyzingImage.value = true
  try {
    const res = await analyze({ checkRequestId, imageFileId })
    imageAnalysis.value = (res.data || res) as ImageAnalyzeResponseVO
    showToast('AI识别完成')
  } catch {
    showToast('AI识别失败')
  } finally {
    analyzingImage.value = false
  }
}

const generateAiReport = async () => {
  const checkRequestId = getEffectiveCheckRequestId()
  if (!checkRequestId) {
    showToast('请先填写或查询检查申请ID')
    return
  }

  generatingReport.value = true
  try {
    const rawData = imageAnalysis.value
      ? JSON.stringify({
        findings: imageAnalysis.value.findings,
        conclusion: imageAnalysis.value.conclusion,
        confidence: imageAnalysis.value.confidence,
        positiveProbability: imageAnalysis.value.positiveProbability,
        subtypeProbabilities: imageAnalysis.value.subtypeProbabilities,
        analysisReliability: imageAnalysis.value.analysisReliability,
        modelLimitations: imageAnalysis.value.modelLimitations,
        annotations: imageAnalysis.value.annotations,
        aiImagingStatus: imageAnalysis.value.aiImagingStatus
      })
      : undefined
    const res = await reportGenerate({
      checkRequestId,
      reportType: reportForm.value.reportType || 'HEAD_CT',
      rawData
    })
    aiReport.value = (res.data || res) as ReportGenerateResponseVO
    showToast('AI报告生成成功')
  } catch {
    showToast('AI报告生成失败')
  } finally {
    generatingReport.value = false
  }
}

const formatConfidence = (confidence?: number) => {
  if (confidence === undefined || confidence === null) return '--'
  return `${Math.round(confidence * 100)}%`
}

const imageConfidencePercent = computed(() => {
  const confidence = positiveProbability.value
  if (confidence === undefined || confidence === null) return 0
  return Math.max(0, Math.min(100, Math.round(confidence * 100)))
})

const confidenceColor = computed(() => {
  if (imageConfidencePercent.value >= 75) return '#E76F51'
  if (imageConfidencePercent.value >= 45) return '#F4A261'
  return '#2A9D8F'
})

const confidenceInterpretation = computed(() => {
  if (imageConfidencePercent.value >= 75) return '模型提示较高出血阳性概率，建议医生重点核对对应层面、窗宽窗位和原始图像。'
  if (imageConfidencePercent.value >= 45) return '模型提示中等出血阳性概率，需结合伪影影响、相邻层面和临床资料复核。'
  return '当前模型未提示明确颅内出血阳性倾向；低概率不等同于图像分析失败，仍需医生结合原始影像确认。'
})

const aiStatus = computed<Record<string, any>>(() => imageAnalysis.value?.aiImagingStatus || {})
const qualityControlModel = computed<Record<string, any>>(() => aiStatus.value.qualityControlModel || aiStatus.value.quality_control_model || {})
const artifactReduction = computed<Record<string, any>>(() => aiStatus.value.artifactReduction || aiStatus.value.artifact_reduction || {})
const lesionModel = computed<Record<string, any>>(() => aiStatus.value.lesionModel || aiStatus.value.lesion_model || {})
const aiWorkflowReady = computed(() => Boolean(aiStatus.value.workflowReady ?? aiStatus.value.workflow_ready))
const positiveProbability = computed(() => imageAnalysis.value?.positiveProbability ?? imageAnalysis.value?.confidence)
const analysisReliabilityText = computed(() => imageAnalysis.value?.analysisReliability || (imageAnalysis.value?.aiImagingStatus ? '链路完整，按结构化结果解释' : '基础结果'))
const subtypeLabels: Record<string, string> = {
  any: '任意出血',
  epidural: '硬膜外出血',
  intraparenchymal: '脑实质内出血',
  intraventricular: '脑室内出血',
  subarachnoid: '蛛网膜下腔出血',
  subdural: '硬膜下出血'
}
const subtypeProbabilityList = computed(() => {
  const probs = ((imageAnalysis.value as any)?.subtypeProbabilities || (imageAnalysis.value as any)?.subtype_probabilities || {}) as Record<string, number>
  return Object.entries(probs)
    .map(([key, value]) => ({
      key,
      label: subtypeLabels[key] || key,
      percent: Math.max(0, Math.min(100, Math.round(Number(value || 0) * 100)))
    }))
    .sort((a, b) => (a.key === 'any' ? -1 : b.key === 'any' ? 1 : b.percent - a.percent))
})
const modelLimitationsList = computed(() => {
  const items = [
    ...(((imageAnalysis.value as any)?.modelLimitations || (imageAnalysis.value as any)?.model_limitations || []) as string[]),
    ...((aiStatus.value.limitations || []) as string[])
  ]
  return Array.from(new Set(items.filter(Boolean)))
})
const previewUrlList = computed(() => {
  const urls = ((imageAnalysis.value as any)?.previewUrls || (imageAnalysis.value as any)?.preview_urls || {}) as Record<string, string>
  const labels: Record<string, string> = {
    axial: '轴位',
    coronal: '冠状位',
    sagittal: '矢状位',
    quality_axial: '质控轴位',
    quality_coronal: '质控冠状位',
    quality_sagittal: '质控矢状位',
    lesion_axial: '病灶轴位',
    lesion_coronal: '病灶冠状位',
    lesion_sagittal: '病灶矢状位'
  }
  return Object.entries(urls)
    .filter(([, url]) => Boolean(url))
    .map(([key, url]) => ({ label: labels[key] || key, url }))
})

const readStatusField = (source: Record<string, any>, camelKey: string, snakeKey: string) => {
  return source?.[camelKey] ?? source?.[snakeKey]
}

const formatProjectUseStatus = (status?: string) => {
  if (status === 'ready_for_project_demo') return '项目链路可用'
  if (String(status || '').toLowerCase().includes('demo')) return '影像辅助分析'
  if (status === 'degraded_for_project_demo') return '链路受限'
  return status || '--'
}

const formatReductionStatus = (status?: string) => {
  if (status === 'executable') return '已执行校正'
  if (status === 'registered_not_executable') return '已登记未执行'
  if (status === 'not_configured') return '未配置'
  return status || '--'
}

// 确诊
const confirmForm = ref<DiagnosisConfirmRequestDTO>({
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
    const ids = diseaseIdsText.value.split(',').filter(s => s).map(Number)
    await confirmDiagnosis({ ...confirmForm.value, registerId: registerId.value, diseaseIds: ids })
    showToast('确诊成功')
    await loadExistingDiagnosis()
  } catch {
    showToast('确诊失败')
  } finally {
    confirming.value = false
  }
}

// 处方
const prescriptionItems = ref<any[]>([])
const existingPrescriptions = ref<any[]>([])
const newDrug = ref<any>({ drugName: '', usageRoute: '', frequency: '', dosage: '', singleDose: '', useDays: 1, drugNumber: 1, drugPrice: 0 })
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

type DrugOption = typeof drugOptions[number]

const selectDrug = (option: DrugOption) => {
  newDrug.value.drugId = option.value
  newDrug.value.drugName = option.text
  newDrug.value.drugPrice = option.price
  showDrugPicker.value = false
}

const addDrug = () => {
  if (!newDrug.value.drugName) { showToast('请选择药品'); return }
  prescriptionItems.value.push({ ...newDrug.value })
  newDrug.value = { drugName: '', usageRoute: '', frequency: '', dosage: '', singleDose: '', useDays: 1, drugNumber: 1, drugPrice: 0 }
  showToast('已添加')
}

const removeDrug = (idx: number) => {
  prescriptionItems.value.splice(idx, 1)
}

const prescriptionTotal = computed(() => {
  return prescriptionItems.value.reduce((sum, item) => sum + ((item.drugPrice || 0) * (item.drugNumber || 1)), 0)
})

const submitPrescription = async () => {
  if (prescriptionItems.value.length === 0) { showToast('处方不能为空'); return }
  savingRx.value = true
  try {
    const items: PrescriptionItemDTO[] = prescriptionItems.value.map((d: any) => ({
      drugId: d.drugId || 1,
      usageRoute: d.usageRoute,
      frequency: d.frequency,
      dosage: d.dosage,
      singleDose: d.singleDose,
      useDays: Number(d.useDays),
      drugNumber: Number(d.drugNumber)
    }))
    await createPrescription({ registerId: registerId.value, doctorId: userStore.doctorId || 1, items })
    showToast('处方提交成功')
    prescriptionItems.value = []
    await loadExistingPrescriptions()
  } catch {
    showToast('提交失败')
  } finally {
    savingRx.value = false
  }
}

const formatOrderStateName = (state?: string) => {
  if (state === 'CREATED') return '待缴费'
  if (state === 'CHARGED' || state === 'PAID') return '已缴费'
  if (state === 'EXECUTING') return '执行中'
  if (state === 'COMPLETED' || state === 'DONE') return '已完成'
  if (state === 'REFUNDED') return '已退费'
  if (state === 'CANCELLED') return '已取消'
  return state || '处理中'
}

const mapExistingOrders = (data: CheckResultVO | any) => {
  const result: any[] = []
  for (const item of data?.checkRequests || []) {
    result.push({
      key: `CHECK-${item.id}`,
      type: 'CHECK',
      name: item.checkInfo || '检查项目',
      position: item.checkPosition || '-',
      stateName: formatOrderStateName(item.checkState)
    })
  }
  for (const item of data?.inspectionRequests || []) {
    result.push({
      key: `INSPECTION-${item.id}`,
      type: 'INSPECTION',
      name: item.inspectionInfo || '检验项目',
      position: item.inspectionPosition || '-',
      stateName: formatOrderStateName(item.inspectionState)
    })
  }
  for (const item of data?.disposalRequests || []) {
    result.push({
      key: `DISPOSAL-${item.id}`,
      type: 'DISPOSAL',
      name: item.disposalInfo || '处置项目',
      position: item.disposalPosition || '-',
      stateName: formatOrderStateName(item.disposalState)
    })
  }
  return result
}

const loadExistingRecord = async () => {
  const res = await getMedicalRecord(registerId.value).catch(() => undefined)
  const data = res?.data || res
  if (!data) return
  recordForm.value = {
    ...recordForm.value,
    ...data,
    registerId: registerId.value
  }
}

const loadExistingOrders = async () => {
  const res = await getOrdersByRegisterId(registerId.value).catch(() => undefined)
  const data = (res?.data || res || {}) as CheckResultVO
  checkResults.value = data
  existingOrders.value = mapExistingOrders(data)
}

const loadExistingPrescriptions = async () => {
  const res = await getPrescriptionsByRegisterId(registerId.value).catch(() => undefined)
  existingPrescriptions.value = (res?.data || res || []) as any[]
}

const loadExistingDiagnosis = async () => {
  const res = await getDiagnosis(registerId.value).catch(() => undefined)
  const data = res?.data || res
  if (!data) return
  confirmForm.value = {
    ...confirmForm.value,
    ...data,
    registerId: registerId.value
  }
  diseaseIdsText.value = Array.isArray(data.diseaseIds) ? data.diseaseIds.join(',') : ''
}

const loadExistingVisitData = async () => {
  if (!registerId.value) return
  await loadExistingRecord()
  await loadExistingOrders()
  await loadExistingPrescriptions()
  await loadExistingDiagnosis()
}

onMounted(() => {
  if (route.query.name) patientName.value = route.query.name as string
  loadPatientDetail()
  loadExistingVisitData()
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
  }
  .name {
    font-size: 18px;
    font-weight: 600;
    color: #5C4B3A;
  }
  .gender, .age {
    font-size: 13px;
    color: #8B7A6B;
    background: #F5F5F5;
    padding: 2px 8px;
    border-radius: 4px;
  }
  .return-waiting-btn {
    margin-top: 10px;
  }
}
.visit-tabs :deep(.van-tabs__line) {
  background-color: #5E60CE;
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
  color: #5C4B3A;
  margin-bottom: 12px;
}
.action-btn {
  margin-bottom: 12px;
  height: 44px;
}
.ai-stream-status {
  margin: -2px 0 12px;
  padding: 10px 12px;
  border: 1px solid rgba(244, 162, 97, 0.28);
  border-radius: 8px;
  background: #fff8ed;
  color: #a45d20;
  font-size: 13px;
  line-height: 1.5;
}
.ai-stream-text {
  margin: -4px 0 12px;
  padding: 12px;
  max-height: 180px;
  overflow-y: auto;
  border: 1px solid rgba(42, 157, 143, 0.22);
  border-radius: 8px;
  background: #f7fffd;
  color: #2f5d56;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.ai-card {
  background: linear-gradient(135deg, rgba(94, 96, 206, 0.09) 0%, rgba(42, 157, 143, 0.06) 100%);
  border: 1px solid rgba(94, 96, 206, 0.18);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
.ai-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  p {
    margin: 4px 0 0;
    color: #687789;
    font-size: 12px;
    line-height: 1.5;
  }
}
.ai-title {
  font-size: 15px;
  font-weight: 600;
  color: #5E60CE;
}
.suggestion-item {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}
.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 8px;
}
.disease-name {
  font-size: 14px;
  font-weight: 500;
  color: #5C4B3A;
}
.suggestion-evidence {
  font-size: 13px;
  color: #8B7A6B;
  line-height: 1.5;
  margin-top: 5px;
}
.suggestion-meter {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: #eef1f6;
  margin-bottom: 10px;
}
.suggestion-meter-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #5E60CE, #2A9D8F);
  transition: width 0.25s ease;
}
.suggestion-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #687789;
  font-size: 12px;
  line-height: 1.5;
}
.ordered-item {
  background: #F5F7FA;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  .item-main {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }
  .item-name {
    font-size: 14px;
    color: #5C4B3A;
  }
  .item-sub {
    font-size: 12px;
    color: #8B7A6B;
  }
}
.result-group {
  margin-bottom: 16px;
}
.result-title {
  font-size: 15px;
  font-weight: 600;
  color: #5C4B3A;
  margin-bottom: 8px;
  padding-left: 8px;
  border-left: 3px solid #5E60CE;
}
.result-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.result-name {
  font-size: 14px;
  font-weight: 500;
  color: #5C4B3A;
}
.result-body {
  .result-label {
    font-size: 12px;
    color: #8B7A6B;
    margin-bottom: 4px;
  }
  .result-text {
    font-size: 13px;
    color: #5C4B3A;
    line-height: 1.6;
  }
}
.ai-report-card {
  background: linear-gradient(180deg, #fffaf3 0%, #ffffff 100%);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #F4A261;
}
.ai-report-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 12px;
  p {
    margin: 4px 0 0;
    color: #8B7A6B;
    font-size: 12px;
    line-height: 1.5;
  }
  :deep(.van-icon) {
    flex: 0 0 auto;
    width: 40px;
    height: 40px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: #fff1df;
    color: #F4A261;
    font-size: 24px;
  }
}
.ai-report-title {
  font-size: 15px;
  font-weight: 600;
  color: #F4A261;
}
.ai-report-content {
  font-size: 13px;
  color: #5C4B3A;
  line-height: 1.8;
  margin-bottom: 12px;
}
.analysis-summary-grid,
.report-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}
.analysis-summary-item,
.report-meta-grid div {
  min-width: 0;
  padding: 10px;
  border-radius: 8px;
  background: #FFF9F0;
  border: 1px solid #F7D6A3;
  span {
    display: block;
    color: #8B7A6B;
    font-size: 11px;
  }
  strong {
    display: block;
    margin-top: 4px;
    color: #3D342C;
    font-size: 14px;
    overflow-wrap: anywhere;
  }
}
.analysis-text-block {
  padding: 10px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #F0E3D1;
  margin-bottom: 8px;
  strong {
    display: block;
    color: #3D342C;
    font-size: 13px;
    margin-bottom: 4px;
  }
  p {
    margin: 0;
    color: #5C4B3A;
    line-height: 1.65;
  }
}
.preview-panel {
  margin: 10px 0;
  padding: 10px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #dce6ef;
}
.preview-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 10px;
}
.preview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.preview-item {
  min-width: 0;
  display: grid;
  gap: 6px;
  span {
    text-align: center;
    font-size: 12px;
    color: #64748b;
  }
  img {
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: contain;
    border-radius: 6px;
    border: 1px solid #d8e0e8;
    background: #111827;
  }
}
.ai-status-panel {
  background: #fff;
  border: 1px solid #F7D6A3;
  border-radius: 8px;
  padding: 10px;
  margin: 10px 0;
}
.confidence-panel {
  background: #fff;
  border: 1px solid #E8DCC8;
  border-radius: 8px;
  padding: 10px;
  margin: 10px 0;
}
.confidence-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #5C4B3A;
  margin-bottom: 8px;
  strong {
    color: #3D342C;
    font-size: 16px;
  }
}
.confidence-bar {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #EFE7DD;
}
.confidence-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.25s ease;
}
.confidence-note {
  margin-top: 8px;
  color: #8B7A6B;
  font-size: 12px;
  line-height: 1.5;
}
.subtype-panel {
  margin: 10px 0;
  padding: 10px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #F0E3D1;
}
.subtype-title {
  font-size: 13px;
  font-weight: 600;
  color: #3D342C;
  margin-bottom: 10px;
}
.subtype-list {
  display: grid;
  gap: 8px;
}
.subtype-row {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr) 42px;
  align-items: center;
  gap: 10px;
  color: #5C4B3A;
  font-size: 12px;
  strong {
    text-align: right;
    color: #3D342C;
  }
}
.subtype-meter {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf2f7;
}
.subtype-meter-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #2A9D8F, #F4A261);
}
.ai-status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: #5C4B3A;
  margin-bottom: 8px;
}
.ai-status-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  div {
    min-width: 0;
    background: #FFF9F0;
    border-radius: 6px;
    padding: 8px;
  }
  strong {
    display: block;
    font-size: 12px;
    color: #3D342C;
    overflow-wrap: anywhere;
  }
}
.status-label {
  display: block;
  font-size: 11px;
  color: #8B7A6B;
  margin-bottom: 3px;
}
.status-limitations {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #F7D6A3;
  font-size: 11px;
  color: #8B7A6B;
  overflow-wrap: anywhere;
}
@media (max-width: 640px) {
  .preview-grid {
    grid-template-columns: 1fr;
  }
}
.upload-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  input {
    min-width: 0;
    flex: 1;
  }
}
.ai-actions {
  display: flex;
  gap: 10px;
  padding: 12px 0;
  .van-button {
    flex: 1;
  }
}
.annotation-list {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}
.annotation-item {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 9px;
  background: white;
  border-radius: 6px;
  font-size: 12px;
  color: #5C4B3A;
  span {
    font-weight: 600;
  }
  small {
    color: #8B7A6B;
    overflow-wrap: anywhere;
  }
}
.report-text {
  padding: 10px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #F0E3D1;
  white-space: pre-wrap;
}
.ai-report-footer {
  display: flex;
  gap: 12px;
}
.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #C4B8A8;
}
.empty-mini {
  text-align: center;
  padding: 20px 0;
  color: #C4B8A8;
  font-size: 13px;
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
    color: #5C4B3A;
  }
  .drug-price {
    font-size: 14px;
    color: #E76F51;
    font-weight: 600;
  }
  .drug-detail {
    font-size: 12px;
    color: #8B7A6B;
  }
  .delete-icon {
    position: absolute;
    right: 8px;
    top: 8px;
    color: #C4B8A8;
    font-size: 16px;
  }
}
.total-price {
  text-align: right;
  font-size: 14px;
  color: #5C4B3A;
  margin-top: 8px;
  .price {
    font-size: 18px;
    font-weight: 700;
    color: #E76F51;
  }
}
.drug-picker-list {
  padding: 8px 16px 20px;
  background: #fff;
}
.drug-picker-option {
  width: 100%;
  border: 0;
  border-bottom: 1px solid #F0E3D1;
  background: #fff;
  padding: 14px 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #3D342C;
  font-size: 14px;
  text-align: left;
  span {
    min-width: 0;
    overflow-wrap: anywhere;
  }
  strong {
    flex: 0 0 auto;
    color: #E76F51;
    font-weight: 700;
  }
}
</style>
