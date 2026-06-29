<template>
  <section class="workspace">
    <div class="toolbar">
      <el-segmented v-model="query.state" :options="stateOptions" @change="loadTasks" />
      <el-select v-model="query.itemType" clearable placeholder="项目类型" style="width: 150px" @change="loadTasks">
        <el-option label="检查" value="CHECK" />
        <el-option label="检验" value="INSPECTION" />
        <el-option label="处置" value="DISPOSAL" />
      </el-select>
      <el-input v-model.number="query.registerId" clearable placeholder="挂号ID" style="width: 140px" @keyup.enter="loadTasks" />
      <el-button type="primary" :loading="loading" @click="loadTasks">刷新</el-button>
    </div>

    <el-table :data="tasks" stripe border v-loading="loading">
      <el-table-column prop="itemType" label="类型" width="110" />
      <el-table-column prop="itemId" label="项目ID" width="90" />
      <el-table-column prop="registerId" label="挂号ID" width="90" />
      <el-table-column prop="patientName" label="患者" min-width="120" />
      <el-table-column prop="projectName" label="项目" min-width="160" />
      <el-table-column prop="projectPosition" label="部位" min-width="100" />
      <el-table-column prop="state" label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="stateTag(row.state)">{{ stateText(row.state) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="result" label="结果" min-width="220" show-overflow-tooltip />
      <el-table-column label="报告录入" min-width="240">
        <template #default="{ row }">
          <el-input v-model="resultDrafts[taskKey(row)]" placeholder="录入检查/检验/处置结果" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :disabled="row.state !== 'CHARGED'" @click="executeTask(row)">执行</el-button>
          <el-button size="small" type="primary" :disabled="!canReport(row)" @click="reportTask(row)">报告</el-button>
          <el-button size="small" type="success" :disabled="!row.result" @click="interpretTask(row)">AI解读</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="interpretVisible" title="AI 辅助解读" width="560px">
      <p class="interpret-title">摘要</p>
      <p>{{ interpretation.summary }}</p>
      <p class="interpret-title">建议</p>
      <p>{{ interpretation.suggestion }}</p>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  executeMedicalTechTask,
  getMedicalTechTasks,
  interpretMedicalTechTask,
  reportMedicalTechTask,
  type MedicalTechInterpretationVO,
  type MedicalTechTaskVO,
} from '@/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const loading = ref(false)
const tasks = ref<MedicalTechTaskVO[]>([])
const resultDrafts = reactive<Record<string, string>>({})
const interpretVisible = ref(false)
const interpretation = reactive<MedicalTechInterpretationVO>({})
const query = reactive({
  state: 'CHARGED',
  itemType: '',
  registerId: undefined as number | undefined,
})

const stateOptions = [
  { label: '待执行', value: 'CHARGED' },
  { label: '执行中', value: 'EXECUTING' },
  { label: '已完成', value: 'COMPLETED' },
]

const taskKey = (row: MedicalTechTaskVO) => `${row.itemType}-${row.itemId}`
const canReport = (row: MedicalTechTaskVO) => row.state === 'EXECUTING' || row.state === 'COMPLETED'
const stateText = (state?: string) => ({ CHARGED: '待执行', EXECUTING: '执行中', COMPLETED: '已完成' }[state || ''] || state || '-')
const stateTag = (state?: string) => state === 'COMPLETED' ? 'success' : state === 'EXECUTING' ? 'warning' : 'info'

const loadTasks = async () => {
  loading.value = true
  try {
    const res: any = await getMedicalTechTasks({
      pageNum: 1,
      pageSize: 100,
      state: query.state || undefined,
      itemType: query.itemType || undefined,
      registerId: query.registerId || undefined,
    })
    tasks.value = res.records || []
  } finally {
    loading.value = false
  }
}

const executeTask = async (row: MedicalTechTaskVO) => {
  await executeMedicalTechTask(row.itemType!, row.itemId!, {
    executorId: userStore.userId,
    remark: '医技工作台执行',
  })
  ElMessage.success('项目已进入执行中')
  await loadTasks()
}

const reportTask = async (row: MedicalTechTaskVO) => {
  const result = resultDrafts[taskKey(row)] || row.result
  if (!result) {
    ElMessage.warning('请先录入结果')
    return
  }
  await reportMedicalTechTask(row.itemType!, row.itemId!, {
    reporterId: userStore.userId,
    result,
    remark: '医技工作台报告录入',
  })
  ElMessage.success('报告已保存')
  await loadTasks()
}

const interpretTask = async (row: MedicalTechTaskVO) => {
  const res: any = await interpretMedicalTechTask(row.itemType!, row.itemId!)
  Object.assign(interpretation, res.data || res)
  interpretVisible.value = true
}

onMounted(loadTasks)
</script>

<style scoped>
.workspace {
  display: grid;
  gap: 16px;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}
.interpret-title {
  margin: 14px 0 6px;
  font-weight: 700;
}
</style>
