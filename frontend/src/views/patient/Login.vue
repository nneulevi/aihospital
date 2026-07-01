<!-- src/views/patient/Login.vue -->
<template>
  <div class="login-page">
    <!-- 顶部导航（无返回按钮） -->
    <van-nav-bar title=" " fixed placeholder />

    <div class="login-container">
      <div class="logo-area">
        <div class="logo-icon">
          <van-icon name="medal-o" size="48" color="#4CAF50" />
        </div>
        <h1 class="title">智慧云脑诊疗平台</h1>
        <p class="subtitle">AI赋能，智慧医疗</p>
      </div>

      <div class="form-area">
        <van-tabs v-model:active="activeTab" animated>
          <!-- 密码登录 -->
          <van-tab title="密码登录" name="password">
            <van-form @submit="onPasswordLogin">
              <van-cell-group inset>
                <van-field
                    v-model="loginForm.username"
                    name="username"
                    label="用户名"
                    placeholder="请输入用户名/手机号"
                    left-icon="user-o"
                    :rules="[{ required: true, message: '请填写用户名' }]"
                />
                <van-field
                    v-model="loginForm.password"
                    type="password"
                    name="password"
                    label="密码"
                    placeholder="请输入密码"
                    left-icon="lock-o"
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

          <!-- 验证码登录 -->
          <van-tab title="验证码登录" name="code">
            <van-form @submit="onCodeLogin">
              <van-cell-group inset>
                <van-field
                    v-model="codeForm.realName"
                    name="realName"
                    label="姓名"
                    placeholder="请输入真实姓名"
                    left-icon="user-o"
                    :rules="[{ required: true, message: '请填写姓名' }]"
                />
                <van-field
                    v-model="codeForm.cardNumber"
                    name="cardNumber"
                    label="身份证号"
                    placeholder="请输入18位身份证号"
                    left-icon="idcard"
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
                    left-icon="phone-o"
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
                    left-icon="shield-o"
                    :rules="[{ required: true, message: '请填写验证码' }]"
                >
                  <template #button>
                    <van-button
                        size="small"
                        type="primary"
                        :disabled="countdown > 0"
                        @click="onSendCode"
                    >
                      {{ countdown > 0 ? `${countdown}秒` : '获取验证码' }}
                    </van-button>
                  </template>
                </van-field>
                <!-- 可选字段 -->
                <van-field
                    v-model="codeForm.gender"
                    name="gender"
                    label="性别"
                    placeholder="选填"
                    left-icon="user-o"
                />
                <van-field
                    v-model="codeForm.birthdate"
                    name="birthdate"
                    label="出生日期"
                    placeholder="选填，如 1990-01-01"
                    left-icon="calendar-o"
                />
                <van-field
                    v-model="codeForm.homeAddress"
                    name="homeAddress"
                    label="家庭地址"
                    placeholder="选填"
                    left-icon="location-o"
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

        <!-- 测试账号 -->
        <div class="test-accounts" v-if="isDev">
          <div class="test-title">测试账号</div>
          <div class="test-item" @click="fillTestAccount('patient')">
            <van-icon name="user-o" /> 患者端：patient / 123456
          </div>
          <div class="test-item" @click="fillTestAccount('doctor')">
            <van-icon name="doctor-o" /> 医生端：doctor / 123456
          </div>
          <div class="test-item" @click="fillTestAccount('admin')">
            <van-icon name="setting-o" /> 管理员端：admin / 123456
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
    const token = res?.data?.token || res?.token
    if (token) {
      const userData = res?.data || res
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
    const token = res?.data?.token || res?.token
    if (token) {
      const userData = res?.data || res
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
  background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 50%, #A5D6A7 100%);
  display: flex;
  flex-direction: column;
  padding: 0 24px 40px;
}

.login-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 400px;
  width: 100%;
  margin: 0 auto;
}

.logo-area {
  text-align: center;
  margin-bottom: 32px;

  .logo-icon {
    width: 72px;
    height: 72px;
    background: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
    box-shadow: 0 4px 20px rgba(76, 175, 80, 0.25);
  }

  .title {
    font-size: 24px;
    font-weight: 700;
    color: #2E7D32;
    margin-bottom: 8px;
  }

  .subtitle {
    font-size: 14px;
    color: #6B6B7E;
  }
}

.form-area {
  background: white;
  border-radius: 16px;
  padding: 24px 16px 32px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);

  :deep(.van-tabs) {
    .van-tabs__wrap {
      margin-bottom: 8px;
    }
    .van-tabs__line {
      background-color: #4CAF50;
    }
    .van-tab--active {
      color: #4CAF50;
    }
  }

  :deep(.van-cell-group) {
    background: transparent;
    .van-cell {
      background: #F5F7FA;
      border-radius: 10px;
      margin-bottom: 10px;
      padding: 8px 14px;

      .van-field__left-icon {
        color: #4CAF50;
      }
      .van-field__label {
        color: #1A1A2E;
        font-weight: 500;
        width: 72px;
      }
      .van-field__body {
        input::placeholder {
          color: #B0B0C0;
        }
      }
    }
  }
}

.submit-btn {
  margin-top: 20px;
  padding: 0 4px;

  :deep(.van-button) {
    background-color: #4CAF50;
    border-color: #4CAF50;
    height: 48px;
    font-size: 16px;
    border-radius: 24px;
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);

    &:active {
      transform: scale(0.97);
    }
  }
}

.test-accounts {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #E8E8E8;

  .test-title {
    font-size: 12px;
    color: #6B6B7E;
    margin-bottom: 8px;
  }

  .test-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #6B6B7E;
    padding: 6px 0;
    cursor: pointer;
    transition: color 0.2s;

    .van-icon {
      font-size: 16px;
    }

    &:hover {
      color: #4CAF50;
    }
    &:active {
      opacity: 0.6;
    }
  }
}
</style>