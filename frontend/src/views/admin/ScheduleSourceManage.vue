<template>
  <div class="schedule-page">
    <section class="panel">
      <h2>新增号源</h2>
      <el-form :model="form" label-width="86px" class="source-form">
        <el-form-item label="医生ID">
          <el-input-number v-model="form.doctorId" :min="1" />
        </el-form-item>
        <el-form-item label="科室ID">
          <el-input-number v-model="form.deptId" :min="1" />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="form.scheduleDate" value-format="YYYY-MM-DD" type="date" />
        </el-form-item>
        <el-form-item label="午别">
          <el-select v-model="form.noon">
            <el-option label="上午" value="AM" />
            <el-option label="下午" value="PM" />
          </el-select>
        </el-form-item>
        <el-form-item label="号源数">
          <el-input-number v-model="form.registQuota" :min="0" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="createSource">创建号源</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="panel">
      <div class="toolbar">
        <el-input v-model.number="query.deptId" clearable placeholder="科室ID" style="width: 130px" />
        <el-input v-model.number="query.doctorId" clearable placeholder="医生ID" style="width: 130px" />
        <el-date-picker v-model="dateRange" value-format="YYYY-MM-DD" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" />
        <el-button type="primary" :loading="loading" @click="loadSources">查询</el-button>
      </div>

      <el-table :data="sources" stripe border v-loading="loading">
        <el-table-column prop="scheduleId" label="号源ID" width="90" />
        <el-table-column prop="doctorName" label="医生" min-width="120" />
        <el-table-column prop="deptName" label="科室" min-width="140" />
        <el-table-column prop="scheduleDate" label="日期" width="120" />
        <el-table-column prop="noon" label="午别" width="80">
          <template #default="{ row }">{{ row.noon === 'AM' ? '上午' : '下午' }}</template>
        </el-table-column>
        <el-table-column prop="registQuota" label="号源" width="90" />
        <el-table-column prop="scheduleStatus" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.scheduleStatus === 'NORMAL' ? 'success' : 'warning'">
              {{ row.scheduleStatus === 'NORMAL' ? '可挂号' : '已停诊' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sourceType" label="来源" width="100" />
        <el-table-column label="操作" width="270" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openQuota(row)">改号源</el-button>
            <el-button size="small" type="warning" :disabled="row.scheduleStatus !== 'NORMAL'" @click="suspend(row)">停诊</el-button>
            <el-button size="small" type="success" :disabled="row.scheduleStatus === 'NORMAL'" @click="resume(row)">恢复</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="quotaDialog.visible" title="调整号源" width="360px">
      <el-input-number v-model="quotaDialog.registQuota" :min="0" />
      <template #footer>
        <el-button @click="quotaDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="saveQuota">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createScheduleSource,
  getScheduleSources,
  resumeScheduleSource,
  suspendScheduleSource,
  updateScheduleQuota,
  type ScheduleSourceVO,
} from '@/api'

const today = new Date().toISOString().slice(0, 10)
const loading = ref(false)
const saving = ref(false)
const sources = ref<ScheduleSourceVO[]>([])
const dateRange = ref<[string, string]>([today, today])
const query = reactive({ deptId: undefined as number | undefined, doctorId: undefined as number | undefined })
const form = reactive({
  doctorId: 1,
  deptId: 1,
  scheduleDate: today,
  noon: 'AM',
  registQuota: 30,
  sourceType: 'MANUAL',
})
const quotaDialog = reactive({ visible: false, scheduleId: 0, registQuota: 0 })

const loadSources = async () => {
  loading.value = true
  try {
    const res: any = await getScheduleSources({
      pageNum: 1,
      pageSize: 100,
      deptId: query.deptId || undefined,
      doctorId: query.doctorId || undefined,
      startDate: dateRange.value?.[0],
      endDate: dateRange.value?.[1],
    })
    sources.value = res.records || []
  } finally {
    loading.value = false
  }
}

const createSource = async () => {
  saving.value = true
  try {
    await createScheduleSource(form)
    ElMessage.success('号源已创建')
    await loadSources()
  } finally {
    saving.value = false
  }
}

const openQuota = (row: ScheduleSourceVO) => {
  quotaDialog.visible = true
  quotaDialog.scheduleId = row.scheduleId!
  quotaDialog.registQuota = row.registQuota || 0
}

const saveQuota = async () => {
  await updateScheduleQuota(quotaDialog.scheduleId, { registQuota: quotaDialog.registQuota })
  quotaDialog.visible = false
  ElMessage.success('号源数已更新')
  await loadSources()
}

const suspend = async (row: ScheduleSourceVO) => {
  await suspendScheduleSource(row.scheduleId!, { reason: '管理员停诊' })
  ElMessage.success('号源已停诊')
  await loadSources()
}

const resume = async (row: ScheduleSourceVO) => {
  await resumeScheduleSource(row.scheduleId!, { reason: '管理员恢复接诊' })
  ElMessage.success('号源已恢复')
  await loadSources()
}

onMounted(loadSources)
</script>

<style scoped>
.schedule-page {
  padding: 16px;
  display: grid;
  gap: 16px;
}
.panel {
  background: #fff;
  border: 1px solid #e6e8eb;
  border-radius: 8px;
  padding: 16px;
}
.panel h2 {
  margin: 0 0 12px;
  font-size: 18px;
}
.source-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0 12px;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 14px;
}
</style>
