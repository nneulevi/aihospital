<template>
  <div class="admin-page">
    <div class="page-card">
      <div class="page-title">人员新增</div>
      <div class="page-subtitle">用于录入医生、医技、药房和收费人员的基础信息，提交后进入管理员审核流程。</div>

      <van-form @submit="submit">
        <van-field v-model="form.name" label="姓名" placeholder="请输入姓名" :rules="[{ required: true, message: '请填写姓名' }]" />
        <van-field v-model="form.account" label="账号" placeholder="用于登录系统" :rules="[{ required: true, message: '请填写账号' }]" />
        <van-field name="role" label="角色">
          <template #input>
            <van-radio-group v-model="form.role" direction="horizontal">
              <van-radio name="DOCTOR">医生</van-radio>
              <van-radio name="MEDICAL_TECH">医技</van-radio>
              <van-radio name="DRUGSTORE">药房</van-radio>
              <van-radio name="ADMIN">管理员</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <van-field v-model.number="form.deptId" label="科室ID" type="digit" placeholder="默认 1" />
        <van-field v-model="form.titleLevel" label="职称" placeholder="如 主治医师 / 技师 / 药师" />
        <van-field v-model="form.phone" label="手机号" placeholder="用于院内联系" />
        <van-field v-model="form.note" label="备注" type="textarea" rows="3" placeholder="资质、排班或权限说明" />
        <van-button block round type="primary" native-type="submit" :loading="loading">保存人员</van-button>
      </van-form>

      <div v-if="createdStaff" class="created-card">
        <div class="created-title">已保存</div>
        <div>员工 ID：{{ createdStaff.staffId }}</div>
        <div>登录账号：{{ createdStaff.account }}</div>
        <div>角色：{{ formatRole(createdStaff.role) }}</div>
      </div>
    </div>

    <div class="page-card staff-list-card">
      <div class="list-header">
        <div>
          <div class="page-title">人员列表</div>
          <div class="page-subtitle">当前启用的医生、医技、药房与管理员账号。</div>
        </div>
        <van-button size="small" plain type="primary" :loading="listLoading" @click="loadEmployees">刷新</van-button>
      </div>
      <article v-for="item in employees" :key="item.employeeId" class="staff-card">
        <div>
          <strong>{{ item.realname }}</strong>
          <span>{{ item.deptName || '未分配科室' }} · {{ item.titleLevel || formatRole(item.roleType) }}</span>
        </div>
        <van-tag type="primary">{{ formatRole(item.roleType) }}</van-tag>
      </article>
      <van-empty v-if="!listLoading && employees.length === 0" description="暂无人员数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { showToast } from 'vant'
import { createStaff, getAdminEmployees, type EmployeeListItemVO, type StaffCreateResponse } from '@/api'

const form = reactive({
  deptId: 1,
  name: '',
  account: '',
  role: 'DOCTOR',
  titleLevel: '',
  phone: '',
  note: ''
})
const loading = ref(false)
const createdStaff = ref<StaffCreateResponse | null>(null)
const listLoading = ref(false)
const employees = ref<EmployeeListItemVO[]>([])

const submit = async () => {
  loading.value = true
  try {
    const res = await createStaff(form)
    createdStaff.value = (res.data || res) as StaffCreateResponse
    showToast('人员已保存')
    await loadEmployees()
  } finally {
    loading.value = false
  }
}

const loadEmployees = async () => {
  listLoading.value = true
  try {
    const res = await getAdminEmployees()
    employees.value = (res.data || res || []) as EmployeeListItemVO[]
  } catch {
    showToast('人员列表加载失败')
  } finally {
    listLoading.value = false
  }
}

const formatRole = (role?: string) => {
  const map: Record<string, string> = {
    DOCTOR: '医生',
    MEDICAL_TECH: '医技',
    PHARMACIST: '药房',
    ADMIN: '管理员'
  }
  return role ? map[role] || role : '--'
}

onMounted(loadEmployees)
</script>

<style lang="scss" scoped>
.admin-page {
  padding: 12px;
}
.page-card,
.tip-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}
.page-subtitle {
  margin: 8px 0 18px;
  color: #64748b;
  line-height: 1.6;
}
.created-card {
  margin-top: 12px;
  background: #f8fbff;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  padding: 12px;
  color: #1f2937;
  line-height: 1.8;
}
.created-title {
  font-weight: 700;
  color: #1677ff;
}
.staff-list-card {
  margin-top: 12px;
}
.list-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}
.staff-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 0;
  border-top: 1px solid #eef2f7;
}
.staff-card strong,
.staff-card span {
  display: block;
}
.staff-card span {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}
</style>
