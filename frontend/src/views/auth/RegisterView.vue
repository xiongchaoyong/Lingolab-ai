<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  age: null,
  learning_goal: '',
  interests: [],
})

const learningGoalOptions = [
  { label: '日常交流', value: 'daily' },
  { label: '考试备考', value: 'exam' },
  { label: '商务英语', value: 'business' },
  { label: '出国留学', value: 'abroad' },
  { label: '兴趣爱好', value: 'hobby' },
]

const interestOptions = [
  { label: '音乐', value: 'music' },
  { label: '体育', value: 'sports' },
  { label: '科技', value: 'tech' },
  { label: '美食', value: 'food' },
  { label: '旅行', value: 'travel' },
  { label: '电影', value: 'movie' },
  { label: '文学', value: 'literature' },
  { label: '其他', value: 'other' },
]

const validatePassword = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 20, message: '4-20 个字符，字母数字下划线', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '只允许字母、数字、下划线', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 32, message: '8-32 个字符，需包含字母和数字', trigger: 'blur' },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '密码必须包含字母和数字', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePassword, trigger: 'blur' },
  ],
  age: [
    { required: true, message: '请输入年龄', trigger: 'blur' },
  ],
  learning_goal: [
    { required: true, message: '请选择学习目标', trigger: 'change' },
  ],
}

function getAgeGroupLabel(age) {
  if (!age) return ''
  if (age <= 12) return '儿童'
  if (age <= 17) return '青少年'
  if (age <= 22) return '大学生'
  if (age <= 50) return '职场人士'
  return '中老年'
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.register({
      ...form,
      age_group: getAgeGroupLabel(form.age),
    })
    router.push('/assessment')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="immersive-layout" style="padding: 40px 0;">
    <div class="immersive-card" style="max-width: 520px;">
      <h2 class="register-title">创建账号</h2>
      <p class="register-subtitle">填写信息，开启你的英语口语训练之旅</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @keyup.enter="handleRegister"
      >
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="4-20个字符" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年龄" prop="age">
              <el-input-number
                v-model="form.age"
                :min="6"
                :max="99"
                placeholder="实际年龄"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item v-if="form.age" class="age-hint">
          <el-tag type="info" size="small">年龄归类：{{ getAgeGroupLabel(form.age) }}</el-tag>
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="8-32个字符，含字母和数字"
                show-password
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="再次输入密码"
                show-password
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="学习目标" prop="learning_goal">
          <el-select v-model="form.learning_goal" placeholder="请选择你的学习目标" style="width: 100%">
            <el-option
              v-for="item in learningGoalOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="兴趣爱好（选填）">
          <el-checkbox-group v-model="form.interests">
            <el-checkbox
              v-for="item in interestOptions"
              :key="item.value"
              :label="item.value"
              :value="item.value"
            >
              {{ item.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleRegister"
            class="submit-btn"
          >
            注册并开始测评
          </el-button>
        </el-form-item>
      </el-form>

      <div class="form-footer">
        已有账号？
        <router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.register-title {
  font-family: var(--font-heading);
  font-size: var(--font-size-xxl);
  font-weight: 700;
  color: var(--color-text-primary);
  text-align: center;
  margin-bottom: var(--spacing-sm);
  letter-spacing: -0.5px;
}

.register-subtitle {
  text-align: center;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  margin-bottom: var(--spacing-xxl);
}

.age-hint {
  margin-top: -16px;
}

.submit-btn {
  width: 100%;
  margin-top: var(--spacing-sm);
}

.form-footer {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>
