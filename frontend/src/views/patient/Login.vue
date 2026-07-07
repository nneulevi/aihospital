<!-- src/views/patient/Login.vue -->
<template>
  <div class="login-page">
    <div class="login-container">
      <div class="logo-area">
        <img src="@/assets/logo.svg" alt="logo" class="logo" />
        <h1 class="title">智慧云脑诊疗平台</h1>
        <p class="subtitle">AI赋能，智慧医疗</p>
      </div>

      <div class="form-area">
        <van-tabs v-model:active="activeTab" animated>
          <!-- 密码登录（老患者/员工） -->
          <van-tab title="密码登录" name="password">
            <van-form @submit="onPasswordLogin">
              <van-cell-group inset>
                <van-field
                    v-model="loginForm.username"
                    name="username"
                    label="用户名"
                    placeholder="请输入用户名/手机号"
                    :rules="[{ required: true, message: '请填写用户名' }]"
                />
                <van-field
                    v-model="loginForm.password"
                    type="password"
                    name="password"
                    label="密码"
                    placeholder="请输入密码"
                    :rules="[{ required: true, message: '请填写密码' }]"
                />
              </van-cell-group>
              <div class="submit-btn">
                <van-button round block type="primary" native-type="submit" :loading="loading">
                  登录
                </van-button>
              </div>
            </van-form>
          </van-tab>

          <!-- 验证码登录（患者首次登录/注册） -->
          <van-tab title="验证码登录" name="code">
            <van-form @submit="onCodeLogin">
              <van-cell-group inset>
                <van-field
                    v-model="codeForm.realName"
                    name="realName"
                    label="姓名"
                    placeholder="请输入真实姓名"
                    :rules="[{ required: true, message: '请填写姓名' }]"
                />
                <van-field
                    v-model="codeForm.cardNumber"
                    name="cardNumber"
                    label="身份证号"
                    placeholder="请输入18位身份证号"
                    :rules="[
                      { required: true, message: '请填写身份证号' },
                      { pattern: /^\d{17}[\dXx]$/, message: '身份证号格式不正确' }
                    ]"
                />
                <van-field
                    v-model="codeForm.phone"
                    name="phone"
                    label="手机号"
                    placeholder="请输入手机号"
                    :rules="[
                      { required: true, message: '请填写手机号' },
                      { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' }
                    ]"
                />
                <van-field
                    v-model="codeForm.code"
                    name="code"
                    label="验证码"
                    placeholder="请输入验证码"
                    :rules="[{ required: true, message: '请填写验证码' }]"
                >
                  <template #button>
                    <van-button
                        size="small"
                        type="primary"
                        :disabled="countdown > 0"
                        @click="onSendCode"
                    >
                      {{ countdown > 0 ? `${countdown}秒后重试` : '获取验证码' }}
                    </van-button>
                  </template>
                </van-field>
                <!-- 可选字段 -->
                <van-field
                    v-model="codeForm.gender"
                    name="gender"
                    label="性别"
                    placeholder="选填"
                />
                <van-field
                    v-model="codeForm.birthdate"
                    name="birthdate"
                    label="出生日期"
                    placeholder="选填，如 1990-01-01"
                />
                <van-field
                    v-model="codeForm.homeAddress"
                    name="homeAddress"
                    label="家庭地址"
                    placeholder="选填"
                />
              </van-cell-group>
              <div class="submit-btn">
                <van-button round block type="primary" native-type="submit" :loading="loading">
                  {{ isNewPatient ? '注册并登录' : '登录' }}
                </van-button>
              </div>
            </van-form>
          </van-tab>
        </van-tabs>

        <div class="test-accounts" v-if="isDev">
          <div class="test-title">测试账号</div>
          <div class="test-item" @click="fillTestAccount('patient')">
            👤 患者端：13800001111 / 123456
          </div>
          <div class="test-item" @click="fillTestAccount('doctor')">
            👨‍⚕️ 医生端：doctor / 123456
          </div>
          <div class="test-item" @click="fillTestAccount('admin')">
            🔧 管理员端：admin / 123456
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { login, authRegister, patientSendCode } from '@/api'
import type {
  LoginRequestDTO,
  LoginResponseVO,
  PatientAuthRegisterRequestDTO,
  PatientLoginResponseVO,
  SendCodeRequestDTO
} from '@/api/model'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isDev = import.meta.env.DEV
const activeTab = ref('password')
const loading = ref(false)
const countdown = ref(0)
const isNewPatient = ref(false)

const loginForm = reactive({ username: '', password: '' })

const codeForm = reactive<PatientAuthRegisterRequestDTO>({
  realName: '',
  cardNumber: '',
  phone: '',
  code: '',
  gender: '',
  birthdate: '',
  homeAddress: ''
})

const onSendCode = async () => {
  if (!codeForm.phone || !/^1[3-9]\d{9}$/.test(codeForm.phone)) {
    showToast('请填写正确的手机号')
    return
  }
  try {
    const params: SendCodeRequestDTO = {
      phone: codeForm.phone,
      codeType: 'REGISTER'
    }
    await patientSendCode(params)
    showToast('验证码已发送')
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (error: any) {
    showToast(error.message || '发送失败')
  }
}

const fillTestAccount = (role: string) => {
  if (role === 'patient') {
    loginForm.username = '13800001111'
    loginForm.password = '123456'
    activeTab.value = 'password'
    return
  }
  if (role === 'doctor') {
    loginForm.username = 'doctor'
    loginForm.password = '123456'
    activeTab.value = 'password'
    return
  }
  if (role === 'admin') {
    loginForm.username = 'admin'
    loginForm.password = '123456'
    activeTab.value = 'password'
  }
}

const inferPasswordLoginType = (): 'PATIENT' | 'DOCTOR' | 'ADMIN' => {
  const account = loginForm.username.trim().toLowerCase()
  if (account === 'doctor') return 'DOCTOR'
  if (account === 'admin') return 'ADMIN'
  return 'PATIENT'
}

const getHomePath = (roleType?: string) => {
  if (roleType === 'DOCTOR') return '/doctor'
  if (roleType === 'ADMIN') return '/admin'
  return '/patient'
}

const onPasswordLogin = async () => {
  loading.value = true
  try {
    const loginType = inferPasswordLoginType()
    const params: LoginRequestDTO = {
      username: loginForm.username,
      password: loginForm.password,
      loginType
    }
    const res: any = await login(params)
    const data = res.data || res
    const roleType = data.roleType || loginType
    if (data?.token) {
      userStore.login(data.token, {
        employeeId: data.employeeId,
        patientId: data.patientId,
        realName: data.realName,
        realname: data.realname || data.realName,
        phone: data.phone,
        caseNumber: data.caseNumber,
        isNewPatient: data.isNewPatient,
        roleType,
        deptId: data.deptId
      })
      showToast('登录成功')
      router.push((route.query.redirect as string) || getHomePath(roleType))
    }
  } catch (error: any) {
    showToast(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}

const onCodeLogin = async () => {
  loading.value = true
  try {
    const res: any = await authRegister(codeForm)
    const data = res.data || res
    if (data?.token) {
      userStore.login(data.token, {
        patientId: data.patientId,
        realname: data.realName,
        caseNumber: data.caseNumber,
        isNewPatient: data.isNewPatient,
        roleType: 'PATIENT'
      })
      isNewPatient.value = data.isNewPatient || false
      showToast(data.isNewPatient ? '注册成功' : '登录成功')
      router.push((route.query.redirect as string) || '/patient')
    } else {
      showToast('登录失败：未获取到token')
    }
  } catch (error: any) {
    showToast(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.login-container {
  width: 100%;
  max-width: 400px;
}
.logo-area {
  text-align: center;
  margin-bottom: 32px;
  .logo { width: 80px; height: 80px; margin-bottom: 16px; }
  .title { color: white; font-size: 24px; font-weight: 700; margin-bottom: 8px; }
  .subtitle { color: rgba(255,255,255,0.8); font-size: 14px; }
}
.form-area {
  background: white;
  border-radius: 16px;
  padding: 32px 20px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
}
.submit-btn { margin-top: 24px; padding: 0 12px; }
.submit-btn :deep(.van-button) {
  background-color: #4CAF50;
  border-color: #4CAF50;
  height: 44px;
}
.test-accounts {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #E6EBF2;
  .test-title { font-size: 12px; color: #687789; margin-bottom: 8px; }
  .test-item {
    font-size: 12px;
    color: #687789;
    padding: 4px 0;
    cursor: pointer;
    &:hover { color: #4CAF50; }
  }
}
</style>
