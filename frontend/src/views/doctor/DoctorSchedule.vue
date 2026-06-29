<!-- src/views/doctor/DoctorSchedule.vue -->
<template>
  <div class="doctor-schedule">
    <div class="header-bar">
      <van-icon name="arrow-left" @click="goBack" />
      <span class="title">排班管理</span>
      <span class="hint">未来7天</span>
    </div>

    <div class="week-range">
      <span>{{ weekStart }} ~ {{ weekEnd }}</span>
      <van-button size="small" round type="primary" @click="resetSchedule">重置全部</van-button>
    </div>

    <div class="schedule-list">
      <div v-for="(day, index) in weekDays" :key="index" class="day-card">
        <div class="day-header">
          <div class="day-name">{{ day.weekday }}</div>
          <div class="day-date">{{ day.date }}</div>
          <span class="day-tag" v-if="day.isToday">今天</span>
        </div>

        <div class="shift-grid">
          <div
              v-for="shift in shifts"
              :key="shift.key"
              class="shift-item"
              :class="{
              active: day[shift.key],
              disabled: !day[shift.key] && day.available
            }"
              @click="toggleShift(index, shift.key)"
          >
            <div class="shift-time">{{ shift.time }}</div>
            <div class="shift-name">{{ shift.label }}</div>
            <van-icon
                :name="day[shift.key] ? 'success' : 'close'"
                class="shift-icon"
                :class="day[shift.key] ? 'active-icon' : 'inactive-icon'"
            />
          </div>
        </div>

        <div class="day-footer" v-if="getSelectedCount(day) === 0">
          <span class="empty-hint">⚠️ 当天未排班</span>
        </div>
        <div class="day-footer" v-else>
          <span class="selected-hint">已排 {{ getSelectedCount(day) }} 个班次</span>
        </div>
      </div>
    </div>

    <div class="action-bar">
      <van-button type="default" round block @click="goBack">取消</van-button>
      <van-button type="primary" round block :loading="saving" @click="saveSchedule">保存排班</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import dayjs from 'dayjs'

const router = useRouter()

const saving = ref(false)

// 班次定义
const shifts = [
  { key: 'morning', label: '早班', time: '08:00-12:00' },
  { key: 'afternoon', label: '中班', time: '12:00-17:00' },
  { key: 'evening', label: '晚班', time: '17:00-21:00' }
]

// 生成未来7天（从明天开始）
const weekDays = ref<any[]>([])

const generateWeek = () => {
  const days = []
  const today = dayjs()

  for (let i = 1; i <= 7; i++) {
    const d = today.add(i, 'day')
    const dateStr = d.format('MM-DD')
    const weekday = d.format('ddd')

    days.push({
      date: dateStr,
      weekday: weekday,
      fullDate: d.format('YYYY-MM-DD'),
      isToday: false,
      morning: i <= 5, // 默认工作日排早班
      afternoon: i <= 5 && i % 2 === 0, // 部分排中班
      evening: i <= 3, // 部分排晚班
      available: true
    })
  }
  return days
}

const weekStart = computed(() => {
  if (weekDays.value.length === 0) return ''
  return dayjs(weekDays.value[0].fullDate).format('MM月DD日')
})

const weekEnd = computed(() => {
  if (weekDays.value.length === 0) return ''
  return dayjs(weekDays.value[weekDays.value.length - 1].fullDate).format('MM月DD日')
})

const toggleShift = (dayIndex: number, shiftKey: string) => {
  const day = weekDays.value[dayIndex]
  if (!day.available) return
  day[shiftKey] = !day[shiftKey]
}

const getSelectedCount = (day: any) => {
  let count = 0
  shifts.forEach(s => {
    if (day[s.key]) count++
  })
  return count
}

const resetSchedule = () => {
  weekDays.value = generateWeek()
  showToast('已重置')
}

const saveSchedule = async () => {
  saving.value = true
  try {
    // 构建提交数据
    const scheduleData = weekDays.value.map(day => ({
      date: day.fullDate,
      morning: day.morning,
      afternoon: day.afternoon,
      evening: day.evening
    }))

    console.log('提交排班数据:', scheduleData)

    // 模拟API请求
    await new Promise(resolve => setTimeout(resolve, 800))
    showToast('排班保存成功')
  } catch {
    showToast('保存失败')
  } finally {
    saving.value = false
  }
}

const goBack = () => {
  router.push('/doctor/profile')
}

onMounted(() => {
  weekDays.value = generateWeek()
})
</script>

<style lang="scss" scoped>
.doctor-schedule {
  min-height: 100vh;
  background: #F5F7FA;
  padding: 12px;
  padding-bottom: 80px;
}

.header-bar {
  display: flex;
  align-items: center;
  background: white;
  padding: 12px 16px;
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
    font-size: 17px;
    font-weight: 600;
    margin-left: 12px;
    color: #2C3E50;
  }

  .hint {
    font-size: 12px;
    color: #7F8C8D;
    background: #F5F7FA;
    padding: 4px 10px;
    border-radius: 12px;
  }
}

.week-range {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 4px;
  margin-bottom: 12px;

  span {
    font-size: 14px;
    color: #2C3E50;
    font-weight: 500;
  }
}

.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.day-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.day-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;

  .day-name {
    font-size: 15px;
    font-weight: 600;
    color: #2C3E50;
  }

  .day-date {
    font-size: 14px;
    color: #7F8C8D;
  }

  .day-tag {
    margin-left: auto;
    font-size: 12px;
    color: #005B96;
    background: #E8F4FD;
    padding: 2px 10px;
    border-radius: 12px;
  }
}

.shift-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.shift-item {
  background: #F5F7FA;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;

  &.active {
    background: #E8F4FD;
    border-color: #005B96;

    .shift-name {
      color: #005B96;
    }
  }

  &.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .shift-time {
    font-size: 11px;
    color: #7F8C8D;
  }

  .shift-name {
    font-size: 14px;
    font-weight: 500;
    color: #2C3E50;
    margin: 4px 0;
  }

  .shift-icon {
    font-size: 16px;

    &.active-icon {
      color: #27AE60;
    }

    &.inactive-icon {
      color: #BDC3C7;
    }
  }
}

.day-footer {
  margin-top: 10px;
  text-align: center;

  .empty-hint {
    font-size: 12px;
    color: #E74C3C;
  }

  .selected-hint {
    font-size: 12px;
    color: #27AE60;
  }
}

.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 16px;
  padding-bottom: env(safe-area-inset-bottom);
  display: flex;
  gap: 12px;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.08);

  .van-button {
    flex: 1;
    height: 44px;
  }
}
</style>