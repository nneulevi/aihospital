<!-- src/views/patient/PhysicalExam.vue -->
<template>
  <div class="physical-exam-page">
    <van-nav-bar title="健康体检" fixed placeholder left-arrow @click-left="() => router.back()" />

    <div class="package-banner">
      <div class="banner-title">🏥 健康体检套餐</div>
      <div class="banner-desc">专业体检，守护您的健康</div>
    </div>

    <div
        v-for="pkg in packages"
        :key="pkg.id"
        class="package-card"
        @click="selectPackage(pkg)"
    >
      <div class="package-header">
        <div class="package-name">{{ pkg.name }}</div>
        <div class="package-price">¥{{ pkg.price }}</div>
      </div>
      <div class="package-desc">{{ pkg.desc }}</div>
      <div class="package-items">
        <span v-for="item in pkg.items.slice(0, 5)" :key="item" class="item-tag">
          {{ item }}
        </span>
        <span v-if="pkg.items.length > 5" class="item-tag more">
          +{{ pkg.items.length - 5 }}
        </span>
      </div>
      <div class="package-footer">
        <span class="package-time">⏰ {{ pkg.duration }}</span>
        <van-button size="small" type="primary" round @click.stop="bookPackage(pkg)">
          立即预约
        </van-button>
      </div>
    </div>

    <!-- 预约弹窗 -->
    <van-action-sheet v-model:show="showBooking" title="体检预约">
      <div class="booking-form">
        <van-form @submit="submitBooking">
          <van-field
              v-model="bookingForm.packageName"
              label="套餐"
              readonly
          />
          <van-field
              v-model="bookingForm.patientName"
              label="就诊人"
              placeholder="请选择就诊人"
              readonly
              is-link
              @click="showPatientPicker = true"
          />
          <van-field
              v-model="bookingForm.visitDate"
              label="预约日期"
              placeholder="请选择日期"
              readonly
              is-link
              @click="showDatePicker = true"
          />
          <van-field
              v-model="bookingForm.phone"
              label="手机号"
              placeholder="请输入手机号"
              :rules="[{ required: true, message: '请填写手机号' }]"
          />
          <div class="form-actions">
            <van-button plain round @click="showBooking = false">取消</van-button>
            <van-button type="primary" round native-type="submit">确认预约</van-button>
          </div>
        </van-form>
      </div>
    </van-action-sheet>

    <!-- 就诊人选择 -->
    <van-action-sheet v-model:show="showPatientPicker" title="选择就诊人">
      <div class="picker-list">
        <div
            v-for="patient in patients"
            :key="patient.id"
            class="picker-item"
            @click="selectPatient(patient)"
        >
          {{ patient.name }}
          <span class="picker-sub">{{ patient.caseNumber }}</span>
        </div>
      </div>
    </van-action-sheet>

    <!-- 日期选择 -->
    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-picker
          :columns="dateColumns"
          title="选择预约日期"
          @confirm="onDateConfirm"
          @cancel="showDatePicker = false"
      />
    </van-popup>

    <!-- 预约成功 -->
    <van-dialog
        v-model:show="showSuccess"
        title="🎉 预约成功"
        :show-cancel-button="false"
        confirm-button-text="完成"
        @confirm="showSuccess = false"
    >
      <div class="success-content">
        <div class="success-icon">
          <van-icon name="checked" size="48" color="#4CAF50" />
        </div>
        <p>体检预约已提交</p>
        <div class="success-info">
          <div class="info-row">
            <span>套餐</span>
            <span>{{ bookingForm.packageName }}</span>
          </div>
          <div class="info-row">
            <span>日期</span>
            <span>{{ bookingForm.visitDate }}</span>
          </div>
        </div>
        <div class="success-tip">请携带身份证按时到院体检</div>
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()

const packages = ref([
  {
    id: 1,
    name: '基础体检套餐',
    price: 388,
    desc: '适合日常健康检查，包含常规项目',
    items: ['身高体重', '血压', '血常规', '尿常规', '心电图', '胸透'],
    duration: '约1小时'
  },
  {
    id: 2,
    name: '标准体检套餐',
    price: 688,
    desc: '全面健康评估，适合中青年人群',
    items: ['基础套餐全部', '肝功能', '肾功能', '血脂', '血糖', '腹部彩超', '幽门螺杆菌检测'],
    duration: '约2小时'
  },
  {
    id: 3,
    name: '高端体检套餐',
    price: 1288,
    desc: '深度全面检查，适合中老年及高风险人群',
    items: ['标准套餐全部', '头部CT', '心脏彩超', '颈动脉彩超', '骨密度', '肿瘤标志物', '甲状腺功能'],
    duration: '约3小时'
  },
  {
    id: 4,
    name: '女性专属套餐',
    price: 988,
    desc: '专为女性设计，关注女性健康',
    items: ['标准套餐全部', '乳腺彩超', '妇科检查', 'HPV筛查', '甲状腺彩超'],
    duration: '约2.5小时'
  }
])

const patients = [
  { id: 1, name: '张明', caseNumber: 'HN202600001' },
  { id: 2, name: '张秀兰', caseNumber: 'HN202600002' }
]

const showBooking = ref(false)
const showPatientPicker = ref(false)
const showDatePicker = ref(false)
const showSuccess = ref(false)

const bookingForm = ref({
  packageName: '',
  patientName: '',
  visitDate: '',
  phone: ''
})

const dateColumns = computed(() => {
  const columns = []
  for (let i = 0; i < 30; i++) {
    const date = dayjs().add(i, 'day')
    columns.push({
      text: date.format('YYYY年MM月DD日 (ddd)'),
      value: date.format('YYYY-MM-DD')
    })
  }
  return columns
})

const selectPackage = (pkg: any) => {
  bookingForm.value.packageName = pkg.name
  bookingForm.value.patientName = patients[0]?.name || ''
  bookingForm.value.phone = '13912345678'
  showBooking.value = true
}

const selectPatient = (patient: any) => {
  bookingForm.value.patientName = patient.name
  showPatientPicker.value = false
}

const onDateConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  if (selectedValues && selectedValues.length > 0) {
    bookingForm.value.visitDate = selectedValues[0]
  }
  showDatePicker.value = false
}

const submitBooking = () => {
  if (!bookingForm.value.visitDate) {
    showToast('请选择预约日期')
    return
  }
  showBooking.value = false
  showSuccess.value = true
}

const bookPackage = (pkg: any) => {
  selectPackage(pkg)
}
</script>

<style lang="scss" scoped>
.physical-exam-page {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 0 16px 20px;
}

.package-banner {
  background: linear-gradient(135deg, #2196F3 0%, #1565C0 100%);
  margin: 12px -16px 16px;
  padding: 20px 24px;
  color: white;
  .banner-title { font-size: 20px; font-weight: 600; }
  .banner-desc { font-size: 14px; opacity: 0.85; }
}

.package-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  &:active { transform: scale(0.98); }
}

.package-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  .package-name { font-size: 17px; font-weight: 600; color: #1A1A2E; }
  .package-price { font-size: 20px; font-weight: 700; color: #E76F51; }
}

.package-desc {
  font-size: 14px;
  color: #6B6B7E;
  margin-bottom: 8px;
}

.package-items {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
  .item-tag {
    font-size: 12px;
    color: #6B6B7E;
    background: #F5F7FA;
    padding: 2px 10px;
    border-radius: 10px;
    &.more { background: #E8E8E8; }
  }
}

.package-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #F0F0F0;
  .package-time { font-size: 13px; color: #C4C4D6; }
  .van-button--primary {
    background: #4CAF50;
    border-color: #4CAF50;
  }
}

.booking-form {
  padding: 16px 16px 24px;
  .form-actions {
    display: flex;
    gap: 12px;
    margin-top: 16px;
    .van-button { flex: 1; height: 44px; }
    .van-button--primary {
      background: #4CAF50;
      border-color: #4CAF50;
    }
  }
}

.picker-list {
  padding: 8px 16px 20px;
}
.picker-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  &:active { background: #F5F7FA; }
  .picker-sub { font-size: 12px; color: #6B6B7E; margin-left: 8px; }
}

.success-content {
  text-align: center;
  padding: 16px 0;
  .success-icon { margin-bottom: 12px; }
  p { font-size: 16px; color: #1A1A2E; margin-bottom: 12px; }
  .success-info {
    text-align: left;
    background: #F5F7FA;
    border-radius: 8px;
    padding: 10px 14px;
    .info-row {
      display: flex;
      justify-content: space-between;
      padding: 4px 0;
      font-size: 14px;
      color: #6B6B7E;
    }
  }
  .success-tip {
    margin-top: 12px;
    font-size: 13px;
    color: #4CAF50;
    background: #E8F5E9;
    padding: 8px;
    border-radius: 6px;
  }
}
</style>