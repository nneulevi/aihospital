<!-- src/views/admin/AISchedule.vue -->
<template>
  <div class="ai-schedule">
    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-label">科室</div>
        <div class="filter-value" @click="showDeptPicker = true">
          {{ selectedDeptName || '请选择科室' }}
          <van-icon name="arrow" />
        </div>
      </div>
      <div class="filter-row">
        <div class="filter-label">开始日期</div>
        <div class="filter-value" @click="showStartDatePicker = true">
          {{ startDate || '请选择' }}
          <van-icon name="arrow" />
        </div>
      </div>
      <div class="filter-row">
        <div class="filter-label">结束日期</div>
        <div class="filter-value" @click="showEndDatePicker = true">
          {{ endDate || '请选择' }}
          <van-icon name="arrow" />
        </div>
      </div>
      <div class="filter-row">
        <div class="filter-label">排班规则</div>
        <van-field v-model="ruleConfig" placeholder="例如：避开节假日，均衡工作量" />
      </div>
      <van-button type="primary" block round :loading="generating" @click="generateSchedule" class="generate-btn">
        🤖 AI生成排班
      </van-button>
    </div>

    <div v-if="scheduleResult.length > 0" class="result-section">
      <div class="section-title">排班结果</div>
      <div v-for="day in scheduleResult" :key="day.date" class="day-card">
        <div class="day-header">{{ formatDate(day.date) }}</div>
        <div class="shift-section">
          <div class="shift-title">🌅 上午</div>
          <div class="shift-list">
            <div v-for="s in day.morning" :key="s.employeeId" class="shift-item">
              <span class="doctor-name">{{ s.employeeName }}</span>
              <span class="quota">号源 {{ s.quota }}</span>
            </div>
            <div v-if="!day.morning || day.morning.length === 0" class="empty-shift">休息</div>
          </div>
        </div>
        <div class="shift-section">
          <div class="shift-title">🌇 下午</div>
          <div class="shift-list">
            <div v-for="s in day.afternoon" :key="s.employeeId" class="shift-item">
              <span class="doctor-name">{{ s.employeeName }}</span>
              <span class="quota">号源 {{ s.quota }}</span>
            </div>
            <div v-if="!day.afternoon || day.afternoon.length === 0" class="empty-shift">休息</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="hasGenerated" class="empty-result">
      <van-icon name="calendar-o" size="48" color="#C4B8A8" />
      <p>暂无排班数据</p>
    </div>

    <van-popup v-model:show="showDeptPicker" position="bottom">
      <van-picker :columns="deptColumns" @confirm="onDeptConfirm" @cancel="showDeptPicker = false" />
    </van-popup>
    <van-popup v-model:show="showStartDatePicker" position="bottom">
      <van-date-picker v-model="startDateValue" @confirm="onStartDateConfirm" @cancel="showStartDatePicker = false" />
    </van-popup>
    <van-popup v-model:show="showEndDatePicker" position="bottom">
      <van-date-picker v-model="endDateValue" @confirm="onEndDateConfirm" @cancel="showEndDatePicker = false" />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'

// ========== 真实 API（启用时取消注释） ==========
// import { scheduleGenerate, getResults } from '@/api'
// import type { ScheduleGenerateRequestDTO, ScheduleGenerateResponseVO, DailySchedule } from '@/api/model'

// ========== 模拟 API ==========
import type { ScheduleGenerateRequestDTO, ScheduleGenerateResponseVO, DailySchedule } from '@/api/model'
import dayjs from 'dayjs'

const mockScheduleGenerate = async (dto: ScheduleGenerateRequestDTO): Promise<ScheduleGenerateResponseVO> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const results: DailySchedule[] = []
      const start = dayjs(dto.startDate)
      const end = dayjs(dto.endDate)
      const diff = end.diff(start, 'day') + 1

      for (let i = 0; i < diff; i++) {
        const date = start.add(i, 'day').format('YYYY-MM-DD')
        results.push({
          date,
          morning: [
            { employeeId: 1, employeeName: '张敏', quota: 20, shiftType: 'MORNING' },
            { employeeId: 2, employeeName: '李华', quota: 15, shiftType: 'MORNING' }
          ],
          afternoon: [
            { employeeId: 1, employeeName: '张敏', quota: 15, shiftType: 'AFTERNOON' },
            { employeeId: 3, employeeName: '王强', quota: 20, shiftType: 'AFTERNOON' }
          ]
        })
      }
      resolve({ scheduleRuleId: 1, results })
    }, 1000)
  })
}

const selectedDeptId = ref<number | null>(null)
const selectedDeptName = ref('')
const startDate = ref('')
const endDate = ref('')
const ruleConfig = ref('')
const generating = ref(false)
const hasGenerated = ref(false)
const scheduleResult = ref<DailySchedule[]>([])

const showDeptPicker = ref(false)
const showStartDatePicker = ref(false)
const showEndDatePicker = ref(false)
const startDateValue = ref(['2026', '06', '20'])
const endDateValue = ref(['2026', '06', '26'])

const deptColumns = [
  { text: '神经内科', value: 1 },
  { text: '呼吸内科', value: 2 },
  { text: '消化内科', value: 3 },
  { text: '心血管内科', value: 4 },
  { text: '骨科', value: 5 }
]

const onDeptConfirm = ({ selectedOptions }: any) => {
  selectedDeptName.value = selectedOptions[0].text
  selectedDeptId.value = selectedOptions[0].value
  showDeptPicker.value = false
}

const onStartDateConfirm = ({ selectedValues }: any) => {
  startDate.value = selectedValues.join('-')
  startDateValue.value = selectedValues
  showStartDatePicker.value = false
}

const onEndDateConfirm = ({ selectedValues }: any) => {
  endDate.value = selectedValues.join('-')
  endDateValue.value = selectedValues
  showEndDatePicker.value = false
}

const generateSchedule = async () => {
  if (!selectedDeptId.value || !startDate.value || !endDate.value) {
    showToast('请填写完整信息')
    return
  }
  generating.value = true
  try {
    const dto: ScheduleGenerateRequestDTO = {
      deptId: selectedDeptId.value,
      startDate: startDate.value,
      endDate: endDate.value,
      ruleConfig: ruleConfig.value
    }
    const res = await mockScheduleGenerate(dto)
    scheduleResult.value = res.results || []
    hasGenerated.value = true
    showToast('排班生成成功')
  } catch {
    showToast('生成失败')
  } finally {
    generating.value = false
  }
}

const formatDate = (date?: string) => date ? dayjs(date).format('MM月DD日 dddd') : ''
</script>

<style lang="scss" scoped>
.ai-schedule {
  padding: 12px;
  padding-bottom: 20px;
}
.filter-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}
.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #F5F5F5;
  &:last-child {
    border-bottom: none;
  }
}
.filter-label {
  font-size: 14px;
  color: #5C4B3A;
  font-weight: 500;
}
.filter-value {
  font-size: 14px;
  color: #8B7A6B;
  display: flex;
  align-items: center;
  gap: 4px;
}
.generate-btn {
  margin-top: 16px;
  background: #5E60CE;
  border-color: #5E60CE;
  height: 44px;
}
.result-section {
  margin-top: 8px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #5C4B3A;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #F4A261;
}
.day-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.day-header {
  font-size: 16px;
  font-weight: 600;
  color: #5C4B3A;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #F5F5F5;
}
.shift-section {
  margin-bottom: 12px;
  &:last-child {
    margin-bottom: 0;
  }
}
.shift-title {
  font-size: 13px;
  color: #8B7A6B;
  margin-bottom: 8px;
}
.shift-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.shift-item {
  background: #FFF9F0;
  border-radius: 8px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.doctor-name {
  font-size: 14px;
  color: #5C4B3A;
  font-weight: 500;
}
.quota {
  font-size: 12px;
  color: #F4A261;
  background: white;
  padding: 2px 6px;
  border-radius: 4px;
}
.empty-shift {
  font-size: 13px;
  color: #C4B8A8;
  padding: 8px 0;
}
.empty-result {
  text-align: center;
  padding: 60px 0;
  color: #C4B8A8;
}
</style>