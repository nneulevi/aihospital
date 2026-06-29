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
            👤 患者端：patient / 123456
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
import { useRouter } from 'vue-router'
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

// ============ 发送验证码 ============
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

// ============ 填充测试账号 ============
const fillTestAccount = (role: string) => {
  loginForm.username = role
  loginForm.password = '123456'
  activeTab.value = 'password'
}

// ============ 密码登录 ============
const onPasswordLogin = async () => {
  loading.value = true
  try {
    const params: LoginRequestDTO = {
      username: loginForm.username,
      password: loginForm.password,
      loginType: 'PATIENT'
    }
    const res = await login(params) as LoginResponseVO
    // 判断响应数据结构：支持 res.data.token 和 res.token 两种格式
    const token = res?.data?.token || res?.token
    if (token) {
      const userData = res?.data || res
      // ✅ 修复：兼容 realName 和 realname 两种字段名
      userStore.login(token, {
        employeeId: userData.employeeId,
        realname: userData.realName || userData.realname || userData.username || '用户',
        roleType: userData.roleType,
        deptId: userData.deptId
      })
      showToast('登录成功')
      router.push('/patient')
    } else {
      showToast('登录失败：未获取到token')
    }
  } catch (error: any) {
    showToast(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}

// ============ 验证码登录/注册 ============
const onCodeLogin = async () => {
  loading.value = true
  try {
    const res = await authRegister(codeForm) as PatientLoginResponseVO
    // 判断响应数据结构：支持 res.data.token 和 res.token 两种格式
    const token = res?.data?.token || res?.token
    if (token) {
      const userData = res?.data || res
      // ✅ 修复：使用正确的字段名 realName
      userStore.login(token, {
        patientId: userData.patientId,
        realname: userData.realName || userData.realname || userData.realName || '用户',
        caseNumber: userData.caseNumber,
        isNewPatient: userData.isNewPatient,
        roleType: 'PATIENT'
      })
      isNewPatient.value = userData.isNewPatient || false
      showToast(userData.isNewPatient ? '注册成功' : '登录成功')
      router.push('/patient')
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
  background: linear-gradient(135deg, #F4A261 0%, #E76F51 100%);
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
  background-color: #F4A261;
  border-color: #F4A261;
  height: 44px;
}
.test-accounts {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #E8DCC8;
  .test-title { font-size: 12px; color: #8B7A6B; margin-bottom: 8px; }
  .test-item {
    font-size: 12px;
    color: #8B7A6B;
    padding: 4px 0;
    cursor: pointer;
    &:hover { color: #F4A261; }
  }
}
</style>