<template>
  <div class="ai-schedule">
    <section class="filter-panel">
      <van-cell title="科室" :value="selectedDeptName || '请选择科室'" is-link @click="showDeptPicker = true" />
      <van-cell title="开始日期" :value="startDate || '请选择'" is-link @click="showStartDatePicker = true" />
      <van-cell title="结束日期" :value="endDate || '请选择'" is-link @click="showEndDatePicker = true" />
      <van-field
        v-model="ruleConfig"
        label="排班规则"
        autosize
        type="textarea"
        rows="2"
        placeholder="例如：均衡上午/下午班，避免连续高负荷门诊"
      />
      <van-button type="primary" block round :loading="generating" @click="generateSchedule">
        AI生成排班
      </van-button>
      <van-button plain type="primary" block round :loading="historyLoading" @click="loadScheduleHistory">
        查询历史排班
      </van-button>
    </section>

    <section v-if="scheduleResult.length" class="result-section">
      <div class="section-title">排班结果</div>
      <article v-for="day in scheduleResult" :key="day.date" class="day-card">
        <header>{{ formatDate(day.date) }}</header>
        <div class="shift-block">
          <div class="shift-title">上午</div>
          <div v-if="day.morning?.length" class="shift-list">
            <div v-for="shift in day.morning" :key="`${day.date}-m-${shift.employeeId}`" class="shift-item">
              <span>{{ shift.employeeName || '未命名医生' }}</span>
              <span>号源 {{ shift.quota ?? 0 }}</span>
            </div>
          </div>
          <van-empty v-else image-size="48" description="休息" />
        </div>
        <div class="shift-block">
          <div class="shift-title">下午</div>
          <div v-if="day.afternoon?.length" class="shift-list">
            <div v-for="shift in day.afternoon" :key="`${day.date}-a-${shift.employeeId}`" class="shift-item">
              <span>{{ shift.employeeName || '未命名医生' }}</span>
              <span>号源 {{ shift.quota ?? 0 }}</span>
            </div>
          </div>
          <van-empty v-else image-size="48" description="休息" />
        </div>
      </article>
    </section>

    <van-empty v-else-if="hasGenerated" description="暂无排班结果" />

    <section v-if="historyResults.length" class="result-section">
      <div class="section-title">历史排班</div>
      <article v-for="item in historyResults" :key="`${item.scheduleDate}-${item.doctorId}-${item.shiftType}`" class="history-card">
        <div class="history-main">
          <strong>{{ item.doctorName || `医生${item.doctorId || ''}` }}</strong>
          <van-tag type="primary">{{ item.shiftType || '--' }}</van-tag>
        </div>
        <div class="history-sub">
          <span>{{ formatDate(item.scheduleDate) }}</span>
          <span>号源 {{ item.registQuota ?? 0 }}</span>
        </div>
      </article>
    </section>

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
import dayjs from 'dayjs'
import { scheduleGenerate, getResults } from '@/api'
import type { DailySchedule, ScheduleGenerateRequestDTO, ScheduleResultVO } from '@/api/model'

const selectedDeptId = ref<number | null>(null)
const selectedDeptName = ref('')
const startDate = ref('')
const endDate = ref('')
const ruleConfig = ref('')
const generating = ref(false)
const historyLoading = ref(false)
const hasGenerated = ref(false)
const scheduleResult = ref<DailySchedule[]>([])
const historyResults = ref<ScheduleResultVO[]>([])

const showDeptPicker = ref(false)
const showStartDatePicker = ref(false)
const showEndDatePicker = ref(false)
const startDateValue = ref([dayjs().format('YYYY'), dayjs().format('MM'), dayjs().format('DD')])
const endDateValue = ref([dayjs().add(6, 'day').format('YYYY'), dayjs().add(6, 'day').format('MM'), dayjs().add(6, 'day').format('DD')])

const deptColumns = [
  { text: '神经内科', value: 1 },
  { text: '呼吸内科', value: 2 },
  { text: '消化内科', value: 3 },
  { text: '心血管内科', value: 4 },
  { text: '骨科', value: 5 }
]

const onDeptConfirm = ({ selectedOptions }: any) => {
  selectedDeptName.value = selectedOptions?.[0]?.text || ''
  selectedDeptId.value = Number(selectedOptions?.[0]?.value || 0)
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
    showToast('请填写完整排班条件')
    return
  }
  if (dayjs(endDate.value).isBefore(dayjs(startDate.value))) {
    showToast('结束日期不能早于开始日期')
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
    const res = await scheduleGenerate(dto)
    const data = res.data || res
    scheduleResult.value = data.results || []
    hasGenerated.value = true
    showToast('排班生成成功')
  } catch {
    showToast('排班生成失败')
  } finally {
    generating.value = false
  }
}

const loadScheduleHistory = async () => {
  if (!selectedDeptId.value) {
    showToast('请先选择科室')
    return
  }
  historyLoading.value = true
  try {
    const res = await getResults({
      query: {
        deptId: selectedDeptId.value,
        startDate: startDate.value || undefined,
        endDate: endDate.value || undefined,
        pageNum: 1,
        pageSize: 50
      }
    })
    const data = res.data || res
    historyResults.value = data.records || []
    showToast(historyResults.value.length ? '历史排班加载完成' : '暂无历史排班')
  } catch {
    showToast('历史排班加载失败')
  } finally {
    historyLoading.value = false
  }
}

const formatDate = (date?: string) => date ? dayjs(date).format('YYYY-MM-DD') : '--'
</script>

<style lang="scss" scoped>
.ai-schedule {
  min-height: 100vh;
  padding: 12px;
  background: #f7f8fa;
}
.filter-panel {
  display: grid;
  gap: 10px;
  padding: 12px;
  background: #fff;
  border: 1px solid #eef0f3;
  border-radius: 8px;
}
.result-section {
  margin-top: 14px;
}
.section-title {
  margin: 6px 0 10px;
  font-size: 16px;
  font-weight: 600;
  color: #263238;
}
.day-card {
  margin-bottom: 12px;
  padding: 12px;
  background: #fff;
  border: 1px solid #eef0f3;
  border-radius: 8px;
}
.day-card header {
  margin-bottom: 10px;
  font-weight: 600;
  color: #263238;
}
.shift-block + .shift-block {
  margin-top: 12px;
}
.shift-title {
  margin-bottom: 8px;
  color: #697386;
}
.shift-list {
  display: grid;
  gap: 8px;
}
.shift-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 6px;
  color: #263238;
}
.history-card {
  margin-bottom: 8px;
  padding: 12px;
  background: #fff;
  border: 1px solid #eef0f3;
  border-radius: 8px;
}
.history-main,
.history-sub {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}
.history-main {
  margin-bottom: 8px;
  color: #263238;
}
.history-sub {
  font-size: 13px;
  color: #697386;
}
</style>
