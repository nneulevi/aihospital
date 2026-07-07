<template>
  <div class="booking-page">
    <van-nav-bar :title="title" fixed placeholder left-arrow @click-left="router.back()" />
    <van-steps :active="step - 1" class="booking-steps">
      <van-step>选择项目</van-step>
      <van-step>确认信息</van-step>
      <van-step>预约成功</van-step>
    </van-steps>
    <section class="booking-card">
      <span class="booking-icon" :style="{ color: tone, background: `${tone}18` }">
        <van-icon :name="icon" />
      </span>
      <strong>{{ title }}</strong>
      <p>{{ description || '以下项目与医院系统同步，已开立的申请会显示办理状态。' }}</p>

      <template v-if="step === 1">
        <div class="item-grid">
          <button
            v-for="item in items"
            :key="item.id || item.name"
            :class="{ active: selectedIds.includes(item.id || 0) }"
            :style="selectedIds.includes(item.id || 0) ? { borderColor: tone, background: `${tone}18` } : undefined"
            type="button"
            @click="toggleItem(item)"
          >
            <strong>{{ item.name }}</strong>
            <span v-if="item.price !== undefined">¥{{ Number(item.price || 0).toFixed(2) }}</span>
          </button>
        </div>
        <van-button
          type="primary"
          round
          block
          :disabled="selectedIds.length === 0"
          @click="goConfirm"
        >
          {{ canSubmit ? '下一步' : '查看就诊记录' }}
        </van-button>
      </template>

      <template v-if="step === 2">
        <section class="confirm-panel">
          <h3>确认预约信息</h3>
          <article>
            <span>已选项目</span>
            <strong>{{ selectedItemsText }}</strong>
          </article>
          <article>
            <span>费用合计</span>
            <strong>¥{{ selectedTotalPrice.toFixed(2) }}</strong>
          </article>
          <article>
            <span>办理说明</span>
            <strong>提交后进入医院系统，按缴费和执行状态继续流转。</strong>
          </article>
        </section>
        <van-button
          type="primary"
          round
          block
          :loading="submitting"
          @click="submitBooking"
        >
          确认提交
        </van-button>
        <van-button plain round block @click="step = 1">返回修改</van-button>
      </template>

      <template v-if="step === 3">
        <section class="success-panel">
          <van-icon name="passed" />
          <h3>预约申请已提交</h3>
          <p>请在“我的申请”中查看缴费、执行和报告状态。</p>
        </section>
        <van-button type="primary" round block @click="resetFlow">继续预约</van-button>
        <van-button plain round block @click="router.push('/patient/orders')">查看待缴费</van-button>
      </template>

      <section v-if="requests.length && step !== 3" class="request-list">
        <h3>我的申请</h3>
        <article v-for="request in requests" :key="`${request.itemType}-${request.requestId}`">
          <strong>{{ request.itemName }}</strong>
          <span>{{ request.stateName || request.state || '处理中' }}</span>
          <small>{{ request.creationTime || '-' }}</small>
        </article>
      </section>
      <van-button v-if="step !== 3" plain round block @click="router.push('/patient/appointment')">没有就诊记录，先去挂号</van-button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'

const props = withDefaults(defineProps<{
  title: string
  icon: string
  tone: string
  description?: string
  items: Array<{ id?: number; name: string; price?: number }>
  requests?: Array<{ requestId?: number; itemType?: string; itemName?: string; state?: string; stateName?: string; creationTime?: string }>
  submitHandler?: (ids: number[]) => Promise<void> | void
}>(), {
  description: '',
  requests: () => [],
})

const router = useRouter()
const selectedIds = ref<number[]>([])
const submitting = ref(false)
const step = ref(1)

const canSubmit = computed(() => typeof props.submitHandler === 'function')
const selectedItems = computed(() => itemsFromIds(selectedIds.value))
const selectedItemsText = computed(() => selectedItems.value.map((item) => item.name).join('、') || '-')
const selectedTotalPrice = computed(() => selectedItems.value.reduce((sum, item) => sum + Number(item.price || 0), 0))

const itemsFromIds = (ids: number[]) => props.items.filter((item) => item.id && ids.includes(item.id))

const toggleItem = (item: { id?: number }) => {
  if (!item.id) {
    showToast('该项目缺少后端编码，暂不可预约')
    return
  }
  selectedIds.value = selectedIds.value.includes(item.id)
    ? selectedIds.value.filter((id) => id !== item.id)
    : [...selectedIds.value, item.id]
}

const goConfirm = () => {
  if (!selectedIds.value.length) {
    showToast('请选择预约项目')
    return
  }
  if (!canSubmit.value) {
    router.push('/patient/records')
    return
  }
  step.value = 2
}

const submitBooking = async () => {
  if (!selectedIds.value.length) {
    showToast('请选择预约项目')
    return
  }
  if (!props.submitHandler) {
    router.push('/patient/records')
    return
  }
  submitting.value = true
  try {
    await props.submitHandler([...selectedIds.value])
    selectedIds.value = []
    step.value = 3
  } finally {
    submitting.value = false
  }
}

const resetFlow = () => {
  selectedIds.value = []
  step.value = 1
}
</script>

<style lang="scss" scoped>
.booking-page { min-height: 100vh; background: #f5f7fa; padding: 16px 16px 80px; }
.booking-steps { margin: 0 -16px 12px; }
.booking-card { display: grid; justify-items: center; gap: 12px; padding: 22px 16px; border-radius: 8px; background: #fff; box-shadow: 0 1px 8px rgba(31,42,55,.06); text-align: center; }
.booking-icon { width: 54px; height: 54px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 30px; }
.booking-card strong { color: #1a1a2e; font-size: 18px; }
.booking-card p { margin: 0; color: #5b6b80; line-height: 1.65; }
.item-grid { width: 100%; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.item-grid button { min-height: 48px; border: 1px solid #e8eef4; border-radius: 8px; background: #f8fafc; color: #465568; }
.item-grid button.active { color: #1f2a37; }
.item-grid strong, .item-grid span { display: block; }
.item-grid span { margin-top: 4px; color: #687789; font-size: 12px; }
.request-list { width: 100%; display: grid; gap: 8px; text-align: left; }
.request-list h3 { margin: 0; color: #1f2a37; font-size: 15px; }
.request-list article { padding: 10px; border: 1px solid #e8eef4; border-radius: 8px; background: #f8fafc; }
.request-list article strong, .request-list article span, .request-list article small { display: block; }
.request-list article span { margin-top: 4px; color: #2375ff; font-size: 13px; }
.request-list article small { margin-top: 4px; color: #8b8b9e; }
.confirm-panel,
.success-panel { width: 100%; display: grid; gap: 10px; text-align: left; }
.confirm-panel h3,
.success-panel h3 { margin: 0; color: #1f2a37; font-size: 16px; text-align: center; }
.confirm-panel article { padding: 12px; border: 1px solid #e8eef4; border-radius: 8px; background: #f8fafc; }
.confirm-panel article span,
.confirm-panel article strong { display: block; }
.confirm-panel article span { color: #687789; font-size: 12px; margin-bottom: 5px; }
.confirm-panel article strong { color: #1f2a37; font-size: 14px; line-height: 1.6; }
.success-panel { justify-items: center; text-align: center; padding: 10px 0; }
.success-panel :deep(.van-icon) { font-size: 48px; color: #4caf50; }
.success-panel p { margin: 0; color: #5b6b80; }
.booking-card :deep(.van-button--primary) { background: #4caf50; border-color: #4caf50; }
.booking-card :deep(.van-button--plain) { border-color: #d7dee8; color: #5b6b80; }
</style>
