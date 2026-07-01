<!-- src/views/patient/PatientManager.vue -->
<template>
  <div class="patient-manager">
    <van-nav-bar title="就诊人管理" fixed placeholder left-arrow @click-left="() => router.back()" />

    <!-- 就诊人列表 -->
    <div class="patient-list">
      <div
          v-for="patient in patients"
          :key="patient.id"
          class="patient-card"
          :class="{ active: patient.isDefault }"
      >
        <div class="patient-avatar">
          <van-icon name="user-circle-o" size="44" color="#4CAF50" />
        </div>

        <div class="patient-detail">
          <div class="patient-name">
            {{ patient.realName }}
            <span class="patient-relation" v-if="patient.relation">
              {{ patient.relation }}
            </span>
            <van-tag v-if="patient.isDefault" type="success" size="mini">默认</van-tag>
          </div>
          <div class="patient-meta">
            <!-- ✅ 数据库存的是中文 "男"/"女"，直接显示 -->
            <span>{{ patient.gender || '未知' }}</span>
            <span>{{ patient.age || '--' }}岁</span>
            <span>病历号：{{ patient.caseNumber || '--' }}</span>
          </div>
          <div class="patient-phone">
            <van-icon name="phone-o" /> {{ patient.phone || '--' }}
          </div>
          <div class="patient-id-card">
            <van-icon name="idcard-o" /> {{ maskIdCard(patient.cardNumber) }}
          </div>
        </div>

        <div class="patient-actions">
          <van-button
              v-if="!patient.isDefault"
              size="small"
              type="primary"
              plain
              round
              @click="setDefault(patient)"
          >
            设为默认
          </van-button>
          <van-button
              size="small"
              plain
              round
              @click="editPatient(patient)"
          >
            编辑
          </van-button>
          <van-button
              size="small"
              plain
              type="danger"
              round
              :disabled="patient.isDefault"
              @click="deletePatient(patient)"
          >
            删除
          </van-button>
        </div>
      </div>
    </div>

    <!-- 添加按钮 -->
    <div class="add-btn-wrapper">
      <van-button type="primary" round block @click="openAddForm">
        <van-icon name="plus" /> 添加就诊人
      </van-button>
    </div>

    <!-- ===== 添加/编辑就诊人弹窗 ===== -->
    <van-action-sheet v-model:show="showAddSheet" :title="isEditMode ? '编辑就诊人' : '添加就诊人'" close-on-click-action>
      <div class="add-form">
        <van-form ref="formRef" @submit="submitPatient">
          <van-field
              v-model="formData.realName"
              name="realName"
              label="姓名"
              placeholder="请输入真实姓名（必填）"
              :rules="[{ required: true, message: '请填写姓名' }]"
          />
          <van-field
              v-model="formData.gender"
              name="gender"
              label="性别"
              placeholder="请选择性别"
              readonly
              is-link
              :rules="[{ required: true, message: '请选择性别' }]"
              @click="showGenderPicker = true"
          />
          <van-field
              v-model="formData.cardNumber"
              name="cardNumber"
              label="身份证号"
              placeholder="请输入18位身份证号"
              :rules="[
                { required: true, message: '请填写身份证号' },
                { pattern: /^\d{17}[\dXx]$/, message: '身份证号格式不正确' }
              ]"
              @input="onCardNumberChange"
          />
          <van-field
              v-model="formData.phone"
              name="phone"
              label="手机号"
              placeholder="请输入手机号"
              :rules="[
                { required: true, message: '请填写手机号' },
                { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' }
              ]"
          />
          <van-field
              v-model="formData.code"
              name="code"
              label="验证码"
              placeholder="请输入短信验证码"
              :rules="[{ required: true, message: '请填写验证码' }]"
          >
            <template #button>
              <van-button
                  size="small"
                  type="primary"
                  :disabled="countdown > 0"
                  @click="onSendCode"
              >
                {{ countdown > 0 ? `${countdown}秒` : '获取验证码' }}
              </van-button>
            </template>
          </van-field>

          <van-field
              name="birthdate"
              label="出生日期"
              placeholder="选填，可从身份证自动解析"
          >
            <template #input>
              <input
                  type="date"
                  v-model="formData.birthdate"
                  class="native-date-input"
                  :max="maxDateStr"
              />
            </template>
          </van-field>

          <van-field
              v-model="formData.relation"
              name="relation"
              label="关系"
              placeholder="如：本人、父亲、母亲、子女"
              readonly
              is-link
              @click="showRelationPicker = true"
          />
          <van-field
              v-model="formData.homeAddress"
              name="homeAddress"
              label="家庭地址"
              placeholder="选填"
          />

          <div class="form-actions">
            <van-button plain round @click="closeForm">取消</van-button>
            <van-button type="primary" round native-type="submit" :loading="submitting">
              {{ isEditMode ? '保存修改' : '确认添加' }}
            </van-button>
          </div>
        </van-form>
      </div>
    </van-action-sheet>

    <!-- ===== 性别选择器 ===== -->
    <van-action-sheet v-model:show="showGenderPicker" title="选择性别">
      <div class="picker-options">
        <div class="picker-option" @click="selectGender('男')">男</div>
        <div class="picker-option" @click="selectGender('女')">女</div>
      </div>
    </van-action-sheet>

    <!-- ===== 关系选择器 ===== -->
    <van-action-sheet v-model:show="showRelationPicker" title="选择关系">
      <div class="picker-options">
        <div
            v-for="rel in relationOptions"
            :key="rel"
            class="picker-option"
            @click="selectRelation(rel)"
        >
          {{ rel }}
        </div>
      </div>
    </van-action-sheet>

    <!-- ===== 删除确认弹窗 ===== -->
    <van-dialog
        v-model:show="showDeleteDialog"
        title="确认删除"
        message="确定要删除该就诊人吗？"
        show-cancel-button
        confirm-button-color="#E76F51"
        @confirm="confirmDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import dayjs from 'dayjs'
import { list, authRegister, switchPatient, patientSendCode } from '@/api'
import { useUserStore } from '@/stores/user'
import type { PatientListVO, PatientAuthRegisterRequestDTO } from '@/api/model'

const router = useRouter()
const userStore = useUserStore()

// ============ 状态 ============
const patients = ref<PatientListVO[]>([])
const formRef = ref<any>(null)
const submitting = ref(false)
const isEditMode = ref(false)
const editingId = ref<number | null>(null)
const countdown = ref(0)

const showAddSheet = ref(false)
const showGenderPicker = ref(false)
const showRelationPicker = ref(false)
const showDeleteDialog = ref(false)

const deleteTarget = ref<PatientListVO | null>(null)

const formData = ref<PatientAuthRegisterRequestDTO & { relation?: string }>({
  realName: '',
  cardNumber: '',
  phone: '',
  code: '',
  gender: '男',  // ✅ 默认改为中文
  birthdate: '',
  homeAddress: '',
  relation: ''
})

const relationOptions = ['本人', '父亲', '母亲', '儿子', '女儿', '配偶', '其他']

// ✅ 最大日期（今天）
const maxDateStr = computed(() => dayjs().format('YYYY-MM-DD'))

// ============ 工具方法 ============

const maskIdCard = (cardNumber?: string) => {
  if (!cardNumber) return '--'
  if (cardNumber.length === 18) {
    return cardNumber.substring(0, 6) + '********' + cardNumber.substring(14)
  }
  return cardNumber
}

// 从身份证提取出生日期
const extractBirthdateFromCard = (cardNumber: string): string | null => {
  if (!cardNumber || cardNumber.length !== 18) return null
  const year = cardNumber.substring(6, 10)
  const month = cardNumber.substring(10, 12)
  const day = cardNumber.substring(12, 14)
  return `${year}-${month}-${day}`
}

// 从身份证提取性别（返回中文）
const extractGenderFromCard = (cardNumber: string): string | null => {
  if (!cardNumber || cardNumber.length !== 18) return null
  const genderCode = parseInt(cardNumber.substring(16, 17))
  return genderCode % 2 === 1 ? '男' : '女'
}

// ============ 发送验证码 ============
const onSendCode = async () => {
  if (!formData.value.phone || !/^1[3-9]\d{9}$/.test(formData.value.phone)) {
    showToast('请填写正确的手机号')
    return
  }

  try {
    await patientSendCode({
      phone: formData.value.phone,
      codeType: 'REGISTER'
    })
    showToast('验证码已发送')
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (error: any) {
    showToast(error.message || '发送失败')
  }
}

// ============ 加载就诊人列表 ============

const loadPatients = async () => {
  try {
    const res = await list() as PatientListVO[]
    patients.value = res || []
  } catch {
    showToast('加载就诊人列表失败')
  }
}

// ============ 设为默认（切换就诊人） ============

const setDefault = async (patient: PatientListVO) => {
  try {
    await switchPatient({ patientId: patient.id! })
    // 更新 store 中的当前患者信息
    userStore.setCurrentPatient?.({
      patientId: patient.id!,
      realName: patient.realName,
      caseNumber: patient.caseNumber,
      gender: patient.gender,
      age: patient.age,
      phone: patient.phone
    })
    await loadPatients()
    showSuccessToast('已切换')
  } catch {
    showToast('操作失败')
  }
}

// ============ 编辑 ============

const editPatient = (patient: PatientListVO) => {
  isEditMode.value = true
  editingId.value = patient.id!
  formData.value = {
    realName: patient.realName || '',
    cardNumber: patient.cardNumber || '',
    phone: patient.phone || '',
    code: '',
    gender: patient.gender || '男',
    birthdate: patient.birthdate || '',
    homeAddress: patient.homeAddress || '',
    relation: patient.relation || ''
  }
  showAddSheet.value = true
}

// ============ 删除 ============

const deletePatient = (patient: PatientListVO) => {
  if (patient.isDefault) {
    showToast('不能删除默认就诊人')
    return
  }
  deleteTarget.value = patient
  showDeleteDialog.value = true
}

const confirmDelete = async () => {
  if (!deleteTarget.value) return

  try {
    // TODO: 调用删除 API
    patients.value = patients.value.filter(p => p.id !== deleteTarget.value?.id)
    showSuccessToast('删除成功')
  } catch {
    showToast('删除失败')
  } finally {
    deleteTarget.value = null
    showDeleteDialog.value = false
  }
}

// ============ 表单操作 ============

const openAddForm = () => {
  isEditMode.value = false
  editingId.value = null
  countdown.value = 0
  formData.value = {
    realName: '',
    cardNumber: '',
    phone: '',
    code: '',
    gender: '男',  // ✅ 默认男
    birthdate: '',
    homeAddress: '',
    relation: ''
  }
  showAddSheet.value = true
}

const selectGender = (gender: string) => {
  formData.value.gender = gender
  showGenderPicker.value = false
}

const selectRelation = (relation: string) => {
  formData.value.relation = relation
  showRelationPicker.value = false
}

const onCardNumberChange = () => {
  const card = formData.value.cardNumber
  if (card && card.length === 18) {
    const birthdate = extractBirthdateFromCard(card)
    if (birthdate && !formData.value.birthdate) {
      formData.value.birthdate = birthdate
    }
    const gender = extractGenderFromCard(card)
    if (gender) {
      formData.value.gender = gender
    }
  }
}

// ============ 提交表单 ============

const submitPatient = async () => {
  if (!formData.value.realName) { showToast('请填写姓名'); return }
  if (!formData.value.cardNumber) { showToast('请填写身份证号'); return }
  if (!formData.value.phone) { showToast('请填写手机号'); return }
  if (!formData.value.code) { showToast('请填写验证码'); return }

  submitting.value = true

  try {
    const params: PatientAuthRegisterRequestDTO = {
      realName: formData.value.realName,
      cardNumber: formData.value.cardNumber,
      phone: formData.value.phone,
      code: formData.value.code,
      gender: formData.value.gender,
      birthdate: formData.value.birthdate,
      homeAddress: formData.value.homeAddress
    }

    const res = await authRegister(params)

    await loadPatients()

    if (res?.patientId) {
      userStore.setCurrentPatient?.({
        patientId: res.patientId,
        realName: formData.value.realName,
        caseNumber: res.caseNumber,
        gender: formData.value.gender,
        phone: formData.value.phone
      })
    }

    showSuccessToast(res?.isNewPatient ? '添加成功' : '就诊人已存在，已自动切换')
    closeForm()
  } catch (error: any) {
    showToast(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const closeForm = () => {
  showAddSheet.value = false
  isEditMode.value = false
  editingId.value = null
  countdown.value = 0
  formData.value = {
    realName: '',
    cardNumber: '',
    phone: '',
    code: '',
    gender: '男',
    birthdate: '',
    homeAddress: '',
    relation: ''
  }
}

// ============ 生命周期 ============

onMounted(() => {
  loadPatients()
})
</script>

<style lang="scss" scoped>
.patient-manager {
  min-height: 100vh;
  background: #F5F7FA;
  padding-bottom: 80px;
}

.patient-list {
  padding: 12px 16px;
}

.patient-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: all 0.2s;

  &.active {
    border-left: 4px solid #4CAF50;
  }

  .patient-detail {
    flex: 1;
    margin-bottom: 12px;

    .patient-name {
      font-size: 18px;
      font-weight: 600;
      color: #1A1A2E;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;

      .patient-relation {
        font-size: 12px;
        color: #4CAF50;
        background: #E8F5E9;
        padding: 0 10px;
        border-radius: 10px;
        font-weight: 400;
      }
    }

    .patient-meta {
      font-size: 14px;
      color: #6B6B7E;
      display: flex;
      gap: 16px;
      margin: 6px 0;
    }

    .patient-phone,
    .patient-id-card {
      font-size: 14px;
      color: #6B6B7E;
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 2px;
    }
  }

  .patient-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    padding-top: 12px;
    border-top: 1px solid #F0F0F0;

    .van-button {
      font-size: 12px;
      height: 28px;
      padding: 0 12px;
    }
  }
}

.add-btn-wrapper {
  padding: 0 16px 20px;
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
    height: 48px;
  }
}

.add-form {
  padding: 16px 16px 24px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding: 0 12px;

  .van-button {
    flex: 1;
    height: 44px;
  }
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
  }
}

.picker-options {
  padding: 8px 0 20px;
}

.picker-option {
  padding: 14px 20px;
  text-align: center;
  font-size: 16px;
  color: #1A1A2E;
  border-bottom: 1px solid #F0F0F0;
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: #F5F7FA;
  }
  &:last-child {
    border-bottom: none;
  }
  &:active {
    background: #E8E8E8;
  }
}

.native-date-input {
  border: none;
  outline: none;
  font-size: 14px;
  color: #1A1A2E;
  background: transparent;
  width: 100%;
  padding: 4px 0;
  font-family: inherit;
}
</style>