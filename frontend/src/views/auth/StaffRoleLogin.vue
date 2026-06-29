<template>
  <div class="login-page">
    <section class="brand">
      <h1>智慧云脑诊疗平台</h1>
      <p>医生、医技、药房、管理员统一工作入口</p>
    </section>

    <section class="login-panel">
      <h2>员工登录</h2>
      <div class="role-grid">
        <button
          v-for="role in staffRoles"
          :key="role.value"
          :class="{ active: staffRole === role.value }"
          @click="selectRole(role)"
        >
          {{ role.label }}
        </button>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" show-password size="large" />
        </el-form-item>
        <el-button type="primary" size="large" class="submit" :loading="loading" @click="handleLogin">
          登录
        </el-button>
      </el-form>

      <div v-if="isDev" class="demo">
        <button v-for="account in demoAccounts" :key="account.role" @click="fillDemo(account)">
          {{ account.label }}：{{ account.username }} / {{ account.password }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api'
import { useUserStore } from '@/stores/user'

type StaffRole = 'DOCTOR' | 'ADMIN' | 'MEDICAL_TECH' | 'PHARMACIST'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const isDev = import.meta.env.DEV
const staffRole = ref<StaffRole>('DOCTOR')
const form = reactive({ username: 'doctor', password: '123456' })

const staffRoles: Array<{ label: string; value: StaffRole; username: string }> = [
  { label: '医生', value: 'DOCTOR', username: 'doctor' },
  { label: '管理员', value: 'ADMIN', username: 'admin' },
  { label: '医技', value: 'MEDICAL_TECH', username: 'medicaltech' },
  { label: '药师', value: 'PHARMACIST', username: 'pharmacist' },
]
const demoAccounts = staffRoles.map((role) => ({ ...role, role: role.value, password: '123456' }))
const homeByRole: Record<StaffRole, string> = {
  DOCTOR: '/doctor',
  ADMIN: '/admin',
  MEDICAL_TECH: '/medical-tech',
  PHARMACIST: '/drugstore',
}
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const selectRole = (role: { value: StaffRole; username: string }) => {
  staffRole.value = role.value
  form.username = role.username
  form.password = '123456'
}

const fillDemo = (account: any) => {
  staffRole.value = account.role
  form.username = account.username
  form.password = account.password
}

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res: any = await login({
      username: form.username,
      password: form.password,
      loginType: staffRole.value,
    })
    const data = res.data || res
    userStore.login(data.token, {
      employeeId: data.employeeId,
      realname: data.realname,
      roleType: data.roleType,
      deptId: data.deptId,
    })
    ElMessage.success('登录成功')
    router.push((route.query.redirect as string) || homeByRole[data.roleType as StaffRole] || '/auth/login')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(320px, 1fr) minmax(360px, 460px);
  background: #eef3f8;
}
.brand {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 64px;
  background: #123d5f;
  color: #fff;
}
.brand h1 {
  font-size: 34px;
  margin: 0 0 14px;
}
.brand p {
  margin: 0;
  opacity: 0.82;
}
.login-panel {
  align-self: center;
  margin: 24px;
  padding: 28px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 18px 48px rgba(16, 42, 67, 0.12);
}
.login-panel h2 {
  margin: 0 0 18px;
  font-size: 24px;
}
.role-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 18px;
}
.role-grid button,
.demo button {
  border: 1px solid #d7dde5;
  background: #fff;
  border-radius: 6px;
  padding: 10px;
  cursor: pointer;
}
.role-grid button.active {
  border-color: #1f6fb2;
  color: #1f6fb2;
  background: #eef6fd;
}
.submit {
  width: 100%;
}
.demo {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-top: 18px;
}
@media (max-width: 780px) {
  .login-page {
    grid-template-columns: 1fr;
  }
  .brand {
    padding: 34px 24px;
  }
}
</style>
