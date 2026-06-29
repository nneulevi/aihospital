<!-- src/views/admin/StaffCreate.vue -->
<template>
  <div class="staff-create">
    <div class="page-header">
      <van-icon name="arrow-left" @click="goBack" />
      <span class="title">👤 创建职员档案</span>
    </div>

    <div class="form-card">
      <van-form ref="formRef" @submit="onSubmit">
        <div class="section-title">基本信息</div>

        <van-field
            v-model="form.realname"
            name="realname"
            label="姓名"
            placeholder="请输入姓名"
            :rules="[{ required: true, message: '请输入姓名' }]"
        />

        <van-field
            v-model="form.phone"
            name="phone"
            label="手机号"
            placeholder="请输入手机号"
            :rules="[{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确手机号' }]"
        />

        <van-field
            v-model="form.password"
            name="password"
            label="密码"
            type="password"
            placeholder="默认密码：123456"
        />

        <div class="section-title">角色权限</div>

        <van-field name="roleType" label="角色类型">
          <template #input>
            <van-radio-group v-model="form.roleType" direction="horizontal">
              <van-radio name="DOCTOR">👨‍⚕️ 医生</van-radio>
              <van-radio name="ADMIN">🔧 管理员</van-radio>
            </van-radio-group>
          </template>
        </van-field>

        <!-- 医生专属字段 -->
        <template v-if="form.roleType === 'DOCTOR'">
          <van-field name="deptmentId" label="所属科室">
            <template #input>
              <van-dropdown-menu>
                <van-dropdown-item v-model="form.deptmentId" :options="deptOptions" />
              </van-dropdown-menu>
            </template>
          </van-field>

          <van-field
              v-model="form.titleLevel"
              label="职称"
              placeholder="如：主任医师、副主任医师"
          />
        </template>

        <div class="section-title">账户状态</div>

        <van-field name="enabled" label="启用状态">
          <template #input>
            <van-switch v-model="form.enabled" size="22" active-color="#27AE60" />
          </template>
        </van-field>

        <div style="margin-top: 20px; display: flex; gap: 12px;">
          <van-button type="default" round block @click="goBack">取消</van-button>
          <van-button type="primary" round block native-type="submit" :loading="submitting">
            创建档案
          </van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import type { FormInstance } from 'vant'
import { listDepartments, createEmployee } from '@/api'
import type { Department } from '@/api/model'

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const deptOptions = ref<{ text: string; value: number }[]>([])

const form = ref({
  realname: '',
  phone: '',
  password: '123456',
  roleType: 'DOCTOR' as 'DOCTOR' | 'ADMIN',
  deptmentId: undefined as number | undefined,
  titleLevel: '',
  enabled: true
})

const loadDepts = async () => {
  try {
    const res = await listDepartments()
    deptOptions.value = (res as Department[]).map(d => ({
      text: d.deptName,
      value: d.id
    }))
    if (deptOptions.value.length > 0) {
      form.value.deptmentId = deptOptions.value[0].value
    }
  } catch {
    // 降级使用硬编码
    deptOptions.value = [
      { text: '呼吸内科', value: 1 },
      { text: '心血管内科', value: 2 },
      { text: '消化内科', value: 3 },
      { text: '神经内科', value: 4 },
      { text: '骨科', value: 5 },
      { text: '妇产科', value: 6 },
      { text: '儿科', value: 7 }
    ]
  }
}

const onSubmit = async () => {
  submitting.value = true
  try {
    const payload = {
      realname: form.value.realname,
      phone: form.value.phone,
      password: form.value.password || '123456',
      roleType: form.value.roleType,
      deptmentId: form.value.roleType === 'DOCTOR' ? form.value.deptmentId : null,
      titleLevel: form.value.titleLevel || null,
      enabled: form.value.enabled
    }
    await createEmployee(payload)
    showToast('✅ 职员档案创建成功')
    setTimeout(() => router.push('/admin'), 500)
  } catch {
    showToast('创建失败，请重试')
  } finally {
    submitting.value = false
  }
}

const goBack = () => router.back()

onMounted(loadDepts)
</script>

<style lang="scss" scoped>
/* 保持不变 */
.staff-create {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 12px;
  padding-bottom: 20px;
}
.page-header {
  display: flex;
  align-items: center;
  background: white;
  padding: 14px 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  .van-icon {
    font-size: 22px;
    cursor: pointer;
    color: #2C3E50;
  }
  .title {
    flex: 1;
    margin-left: 12px;
    font-size: 17px;
    font-weight: 600;
    color: #2C3E50;
  }
}
.form-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #2C3E50;
  padding: 12px 0 8px 0;
  border-bottom: 2px solid #F4A261;
  margin-bottom: 8px;
  &:first-of-type { padding-top: 0; }
}
:deep(.van-field) {
  padding: 10px 0;
  border-bottom: 1px solid #F5F5F5;
  &:last-of-type { border-bottom: none; }
}
:deep(.van-radio-group) .van-radio { margin-right: 20px; }
</style>