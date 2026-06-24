<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)
const errorMsg = ref('')

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 20, message: '用户名长度为 4-20 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 32, message: '密码长度为 8-32 个字符', trigger: 'blur' },
  ],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  errorMsg.value = ''
  try {
    const res = await authStore.login(form.username, form.password)
    router.push(res.redirect || '/home')
  } catch (e) {
    const detail = e?.response?.data?.detail
    errorMsg.value = typeof detail === 'string' ? detail : '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="immersive-layout">
    <div class="immersive-card">
      <h2 class="login-title">登录 Lingolab</h2>
      <p class="login-subtitle">AI 驱动的英语口语训练平台</p>

      <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon :closable="false" style="margin-bottom: 16px;" />

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
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
            :loading="loading"
            @click="handleLogin"
            class="submit-btn"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="form-footer">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.login-title {
  font-family: var(--font-heading);
  font-size: var(--font-size-xxl);
  font-weight: 700;
  color: var(--color-text-primary);
  text-align: center;
  margin-bottom: var(--spacing-sm);
  letter-spacing: -0.5px;
}

.login-subtitle {
  text-align: center;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  margin-bottom: var(--spacing-xxxl);
}

.submit-btn {
  width: 100%;
}

.form-footer {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>
