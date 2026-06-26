<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const avatarPreview = ref('')
const avatarInput = ref(null)

const form = ref({
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

onMounted(async () => {
  loading.value = true
  try {
    const profile = await authStore.fetchProfile()
    form.value.learning_goal = profile.learning_goal
    form.value.interests = profile.interests || []
    avatarPreview.value = authStore.userInfo?.avatar || ''
  } catch {
    ElMessage.error('加载画像失败')
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  saving.value = true
  try {
    await authStore.updateProfile({
      learning_goal: form.value.learning_goal,
      interests: form.value.interests,
    })
    ElMessage.success('画像已更新')
    // 返回上一页，无历史记录则回首页
    if (window.history.length > 1) {
      router.back()
    } else {
      router.push('/')
    }
  } catch (e) {
    const detail = e?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : '更新失败')
  } finally {
    saving.value = false
  }
}

function triggerAvatarInput() {
  avatarInput.value?.click()
}

function handleAvatarSelect(e) {
  const file = e.target.files?.[0]
  if (!file) return

  const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowed.includes(file.type)) {
    ElMessage.error('仅支持 JPG、PNG、GIF、WebP 格式')
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('头像文件不能超过 2MB')
    return
  }

  // 本地预览
  avatarPreview.value = URL.createObjectURL(file)
  uploadAvatar(file)
}

async function uploadAvatar(file) {
  uploading.value = true
  try {
    await authStore.uploadAvatar(file)
    ElMessage.success('头像已更新')
  } catch (e) {
    const detail = e?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : '头像上传失败')
    avatarPreview.value = authStore.userInfo?.avatar || ''
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="immersive-layout" style="padding: 40px 0;">
    <div class="immersive-card" style="max-width: 520px;">
      <h2 class="profile-title">用户画像</h2>
      <p class="profile-subtitle">修改学习目标和兴趣偏好，获取更精准的学习推荐</p>

      <el-skeleton v-if="loading" :rows="6" animated />

      <template v-else>
        <!-- 头像上传 -->
        <div class="avatar-section">
          <div class="avatar-wrapper" @click="triggerAvatarInput" :class="{ 'is-uploading': uploading }">
            <el-avatar :size="80" :src="avatarPreview" icon="UserFilled" />
            <div class="avatar-overlay" v-loading="uploading">
              <el-icon :size="20"><Plus /></el-icon>
            </div>
          </div>
          <input
            ref="avatarInput"
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            style="display: none"
            @change="handleAvatarSelect"
          />
          <p class="avatar-hint">点击更换头像（支持 JPG/PNG/GIF/WebP，≤2MB）</p>
        </div>

        <!-- 只读信息 -->
        <el-descriptions :column="1" border size="small" style="margin-bottom: 24px;">
          <el-descriptions-item label="用户名">{{ authStore.userInfo?.username }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ authStore.userInfo?.email }}</el-descriptions-item>
          <el-descriptions-item label="年龄归类">{{ authStore.userInfo?.age_group }}</el-descriptions-item>
          <el-descriptions-item label="CEFR 等级">
            {{ authStore.userInfo?.level_final || '未测评' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 可编辑字段 -->
        <el-form label-position="top" @submit.prevent>
          <el-form-item label="学习目标">
            <el-select v-model="form.learning_goal" placeholder="请选择学习目标" style="width: 100%">
              <el-option
                v-for="item in learningGoalOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="兴趣爱好">
            <el-checkbox-group v-model="form.interests">
              <el-checkbox
                v-for="item in interestOptions"
                :key="item.value"
                :label="item.value"
              >
                {{ item.label }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="saving" @click="handleSave" style="width: 100%">
              保存修改
            </el-button>
          </el-form-item>
        </el-form>
      </template>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.profile-title {
  font-family: var(--font-heading);
  font-size: var(--font-size-xxl);
  font-weight: 700;
  color: var(--color-text-primary);
  text-align: center;
  margin-bottom: var(--spacing-sm);
}

.profile-subtitle {
  text-align: center;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  margin-bottom: var(--spacing-xxl);
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.avatar-wrapper {
  position: relative;
  cursor: pointer;
  border-radius: 50%;

  &.is-uploading { pointer-events: none; }
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s;

  .avatar-wrapper:hover & { opacity: 1; }
}

.avatar-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-disabled);
  margin-top: var(--spacing-sm);
}
</style>