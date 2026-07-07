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
      <div
        v-if="historyFeedback"
        class="history-feedback"
        :class="{ 'history-feedback--error': historyFeedbackType === 'error' }"
        role="status"
      >
        {{ historyFeedback }}
      </div>
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
    <van-empty v-else-if="hasQueriedHistory" description="暂无历史排班" />

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
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import dayjs from 'dayjs'
import { getAdminDepartments, scheduleGenerate, getResults } from '@/api'
import type { DailySchedule, ScheduleGenerateRequestDTO, ScheduleResultVO } from '@/api/model'

const selectedDeptId = ref<number | null>(null)
const selectedDeptName = ref('')
const startDate = ref(dayjs().format('YYYY-MM-DD'))
const endDate = ref(dayjs().add(6, 'day').format('YYYY-MM-DD'))
const ruleConfig = ref('')
const generating = ref(false)
const historyLoading = ref(false)
const hasGenerated = ref(false)
const hasQueriedHistory = ref(false)
const scheduleResult = ref<DailySchedule[]>([])
const historyResults = ref<ScheduleResultVO[]>([])
const historyFeedback = ref('')
const historyFeedbackType = ref<'info' | 'error'>('info')

const showDeptPicker = ref(false)
const showStartDatePicker = ref(false)
const showEndDatePicker = ref(false)
const startDateValue = ref([dayjs().format('YYYY'), dayjs().format('MM'), dayjs().format('DD')])
const endDateValue = ref([dayjs().add(6, 'day').format('YYYY'), dayjs().add(6, 'day').format('MM'), dayjs().add(6, 'day').format('DD')])

const deptColumns = ref<Array<{ text: string; value: number }>>([])

const setPageFeedback = (message: string, type: 'info' | 'error' = 'info') => {
  historyFeedbackType.value = type
  historyFeedback.value = message
}

const loadDepartments = async () => {
  try {
    const res = await getAdminDepartments()
    const source = (res.data || res || []) as any[]
    const seen = new Set<string>()
    const devMarkers = ['Extended', 'User Logic', '项目验收', '验收', '测试']
    deptColumns.value = source
      .filter((dept) => {
        const id = Number(dept.deptId || dept.id)
        const name = String(dept.deptName || dept.name || '').trim()
        if (!id || !name || devMarkers.some((marker) => name.includes(marker))) return false
        if (seen.has(name)) return false
        seen.add(name)
        return true
      })
      .map((dept) => ({
        text: dept.deptName || dept.name || `科室${dept.deptId || dept.id}`,
        value: Number(dept.deptId || dept.id),
      }))
    if (!selectedDeptId.value && deptColumns.value.length) {
      selectedDeptId.value = deptColumns.value[0].value
      selectedDeptName.value = deptColumns.value[0].text
    }
  } catch {
    showToast('科室列表加载失败')
    deptColumns.value = []
  }
}

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
    setPageFeedback('请填写完整排班条件。', 'error')
    return
  }
  if (dayjs(endDate.value).isBefore(dayjs(startDate.value))) {
    setPageFeedback('结束日期不能早于开始日期。', 'error')
    return
  }

  generating.value = true
  setPageFeedback('正在生成排班...')
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
    if (scheduleResult.value.length === 0) {
      setPageFeedback('当前科室暂无可生成的排班结果，请先维护医生信息或选择其他科室。', 'error')
      return
    }
    setPageFeedback(`排班生成成功，已生成 ${scheduleResult.value.length} 天排班。`)
  } catch {
    setPageFeedback('排班生成失败，请稍后重试。', 'error')
  } finally {
    generating.value = false
  }
}

const loadScheduleHistory = async () => {
  if (!selectedDeptId.value) {
    setPageFeedback('请先选择科室后再查询历史排班。', 'error')
    return
  }
  historyLoading.value = true
  hasQueriedHistory.value = false
  setPageFeedback('正在查询历史排班...')
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
    hasQueriedHistory.value = true
    setPageFeedback(historyResults.value.length
      ? `已查询到 ${historyResults.value.length} 条历史排班。`
      : '当前筛选条件下暂无历史排班。')
  } catch {
    setPageFeedback('历史排班加载失败，请稍后重试。', 'error')
  } finally {
    historyLoading.value = false
  }
}

const formatDate = (date?: string) => date ? dayjs(date).format('YYYY-MM-DD') : '--'

onMounted(loadDepartments)
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
.history-feedback {
  padding: 9px 12px;
  color: #0f766e;
  font-size: 14px;
  line-height: 1.45;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
}
.history-feedback--error {
  color: #b42318;
  background: #fff1f3;
  border-color: #fecdd3;
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
