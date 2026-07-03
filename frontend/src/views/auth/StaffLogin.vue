<!-- src/views/auth/StaffLogin.vue -->
<template>
  <div class="staff-login-page">
    <div class="login-wrapper">
      <!-- 左侧品牌区 -->
      <div class="brand-section">
        <div class="brand-content">
          <img src="@/assets/logo.svg" alt="logo" class="brand-logo" />
          <h1 class="brand-title">智慧云脑诊疗平台</h1>
          <p class="brand-subtitle">AI赋能，智慧医疗</p>
          <div class="brand-features">
            <div class="feature-item">
              <el-icon><FirstAidKit /></el-icon>
              <span>智能辅助诊断</span>
            </div>
            <div class="feature-item">
              <el-icon><Calendar /></el-icon>
              <span>AI智能排班</span>
            </div>
            <div class="feature-item">
              <el-icon><DataAnalysis /></el-icon>
              <span>数据驱动决策</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录区 -->
      <div class="form-section">
        <div class="form-container">
          <div class="form-header">
            <h2 class="form-title">欢迎登录</h2>
            <p class="form-subtitle">医生 / 管理员工作台</p>
          </div>

          <!-- 角色切换 -->
          <div class="role-switch">
            <div
                v-for="r in staffRoles"
                :key="r.value"
                :class="['role-btn', { active: staffRole === r.value }]"
                @click="staffRole = r.value"
            >
              <el-icon v-if="r.value === 'DOCTOR'"><FirstAidKit /></el-icon>
              <el-icon v-else><Setting /></el-icon>
              {{ r.label }}
            </div>
          </div>

          <!-- 登录方式切换 -->
          <div class="login-type-tabs">
            <div
                :class="['type-tab', { active: loginType === 'password' }]"
                @click="loginType = 'password'"
            >
              密码登录
            </div>
            <div
                :class="['type-tab', { active: loginType === 'code' }]"
                @click="loginType = 'code'"
            >
              验证码登录
            </div>
          </div>

          <!-- 密码登录 -->
          <el-form
              v-if="loginType === 'password'"
              ref="pwdFormRef"
              :model="pwdForm"
              :rules="pwdRules"
              @keyup.enter="handlePwdLogin"
          >
            <el-form-item prop="username">
              <el-input
                  v-model="pwdForm.username"
                  placeholder="请输入用户名"
                  :prefix-icon="User"
                  size="large"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                  v-model="pwdForm.password"
                  type="password"
                  placeholder="请输入密码"
                  :prefix-icon="Lock"
                  size="large"
                  show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button
                  type="primary"
                  size="large"
                  class="login-btn"
                  :loading="loading"
                  @click="handlePwdLogin"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 验证码登录 -->
          <el-form
              v-else
              ref="codeFormRef"
              :model="codeForm"
              :rules="codeRules"
              @keyup.enter="handleCodeLogin"
          >
            <el-form-item prop="phone">
              <el-input
                  v-model="codeForm.phone"
                  placeholder="请输入手机号"
                  :prefix-icon="Phone"
                  size="large"
              />
            </el-form-item>
            <el-form-item prop="code">
              <div class="code-input-row">
                <el-input
                    v-model="codeForm.code"
                    placeholder="请输入验证码"
                    :prefix-icon="Key"
                    size="large"
                    class="code-input"
                />
                <el-button
                    :disabled="countdown > 0"
                    class="send-code-btn"
                    @click="handleSendCode"
                >
                  {{ countdown > 0 ? `${countdown}秒后重试` : '获取验证码' }}
                </el-button>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button
                  type="primary"
                  size="large"
                  class="login-btn"
                  :loading="loading"
                  @click="handleCodeLogin"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 测试账号 -->
          <div v-if="isDev" class="test-accounts">
            <el-divider>测试账号</el-divider>
            <div class="test-list">
              <el-tag
                  v-for="acc in testAccounts"
                  :key="acc.role"
                  class="test-tag"
                  @click="fillTestAccount(acc)"
              >
                {{ acc.label }}：{{ acc.username }} / {{ acc.password }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Phone, Key, FirstAidKit, Setting, Calendar, DataAnalysis } from '@element-plus/icons-vue'
import { login, authSendCode, loginByCode } from '@/api'
import type { LoginRequestDTO, LoginResponseVO } from '@/api/model'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const isDev = import.meta.env.DEV
const loading = ref(false)
const countdown = ref(0)
const loginType = ref<'password' | 'code'>('password')
const staffRole = ref<'DOCTOR' | 'ADMIN'>('DOCTOR')

const staffRoles = [
  { label: '医生登录', value: 'DOCTOR' as const },
  { label: '管理员登录', value: 'ADMIN' as const }
]

const testAccounts = [
  { label: '医生', role: 'DOCTOR', username: 'doctor', password: '123456' },
  { label: '管理员', role: 'ADMIN', username: 'admin', password: '123456' }
]

// 密码登录
const pwdFormRef = ref()
const pwdForm = reactive({
  username: '',
  password: ''
})
const pwdRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 验证码登录
const codeFormRef = ref()
const codeForm = reactive({
  phone: '',
  code: ''
})
const codeRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

// 发送验证码
const handleSendCode = async () => {
  if (!codeForm.phone || !/^1[3-9]\d{9}$/.test(codeForm.phone)) {
    ElMessage.warning('请填写正确的手机号')
    return
  }
  try {
    await authSendCode({
      phone: codeForm.phone,
      codeType: `${staffRole.value}_LOGIN`
    } as any)
    ElMessage.success('验证码已发送')
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (error: any) {
    ElMessage.error(error.message || '发送失败')
  }
}

// 填充测试账号
const fillTestAccount = (acc: any) => {
  pwdForm.username = acc.username
  pwdForm.password = acc.password
  staffRole.value = acc.role
  loginType.value = 'password'
}

// ===== 处理登录响应 =====
const handleLoginResponse = (res: LoginResponseVO, roleType: 'DOCTOR' | 'ADMIN') => {
  console.log('[StaffLogin] 登录响应:', res)

  if (!res.token) {
    ElMessage.error('登录失败：未获取到token')
    return
  }

  // 从后端返回的数据中提取字段
  const responseData = res as any

  // 员工ID：从 id 字段获取（医生有值，管理员可能为null）
  const employeeId = responseData.id || responseData.employeeId || null
  // 科室ID：从 deptId 字段获取（医生有值，管理员为null）
  const deptId = responseData.deptId || responseData.departmentId || null
  // 角色类型
  const finalRoleType = responseData.roleType || roleType
  // 真实姓名
  const realname = responseData.realname || responseData.realName || ''

  console.log('[StaffLogin] 提取的数据:', {
    employeeId,
    deptId,
    roleType: finalRoleType,
    realname
  })

  // 构建用户信息
  const userInfo = {
    employeeId: employeeId,
    id: employeeId,  // 兼容 id 字段
    realname: realname,
    roleType: finalRoleType,
    deptId: deptId
  }

  // 登录到 store
  userStore.login(res.token, userInfo)

  console.log('[StaffLogin] 登录后 userStore.doctorId:', userStore.doctorId)
  console.log('[StaffLogin] 登录后 userStore.userInfo:', userStore.userInfo)

  ElMessage.success('登录成功')

  // 根据角色跳转
  if (finalRoleType === 'ADMIN') {
    router.push('/admin')
  } else {
    router.push('/doctor')
  }
}

// ===== 密码登录 =====
const handlePwdLogin = async () => {
  const valid = await pwdFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const params: LoginRequestDTO = {
      username: pwdForm.username,
      password: pwdForm.password,
      loginType: staffRole.value
    }
    const res: LoginResponseVO = await login(params)
    handleLoginResponse(res, staffRole.value)
  } catch (error: any) {
    console.error('[StaffLogin] 登录失败:', error)
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}

// ===== 验证码登录 =====
const handleCodeLogin = async () => {
  const valid = await codeFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res: LoginResponseVO = await loginByCode({
      phone: codeForm.phone,
      verifyCode: codeForm.code,
      loginType: staffRole.value
    } as any)
    handleLoginResponse(res, staffRole.value)
  } catch (error: any) {
    console.error('[StaffLogin] 登录失败:', error)
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.staff-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-wrapper {
  display: flex;
  width: 900px;
  min-height: 520px;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.brand-section {
  width: 380px;
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: white;

  .brand-logo {
    width: 64px;
    height: 64px;
    margin-bottom: 24px;
  }

  .brand-title {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
  }

  .brand-subtitle {
    font-size: 14px;
    opacity: 0.8;
    margin-bottom: 40px;
  }

  .brand-features {
    .feature-item {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      font-size: 14px;
      opacity: 0.9;

      .el-icon {
        font-size: 20px;
      }
    }
  }
}

.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;

  .form-container {
    width: 100%;
    max-width: 320px;
  }

  .form-header {
    text-align: center;
    margin-bottom: 32px;

    .form-title {
      font-size: 24px;
      font-weight: 600;
      color: #1f2937;
      margin-bottom: 8px;
    }

    .form-subtitle {
      font-size: 14px;
      color: #6b7280;
    }
  }
}

.role-switch {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;

  .role-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 14px;
    color: #6b7280;

    &:hover {
      border-color: #3b82f6;
      color: #3b82f6;
    }

    &.active {
      background: #3b82f6;
      border-color: #3b82f6;
      color: white;
    }

    .el-icon {
      font-size: 18px;
    }
  }
}

.login-type-tabs {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;

  .type-tab {
    padding-bottom: 12px;
    font-size: 14px;
    color: #6b7280;
    cursor: pointer;
    position: relative;
    transition: color 0.2s;

    &:hover {
      color: #3b82f6;
    }

    &.active {
      color: #3b82f6;
      font-weight: 500;

      &::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        right: 0;
        height: 2px;
        background: #3b82f6;
      }
    }
  }
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.code-input-row {
  display: flex;
  gap: 12px;

  .code-input {
    flex: 1;
  }

  .send-code-btn {
    width: 120px;
    height: 40px;
  }
}

.test-accounts {
  margin-top: 24px;

  .test-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }

  .test-tag {
    cursor: pointer;
  }
}
</style>