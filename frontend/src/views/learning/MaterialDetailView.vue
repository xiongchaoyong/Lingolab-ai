<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, VideoCamera, Document, Headset, Link } from '@element-plus/icons-vue'
import { getMaterialDetailApi, clickRecommendationApi } from '@/api/recommendation'

const route = useRoute()
const router = useRouter()

const material = ref(null)
const loading = ref(false)
const error = ref('')

const materialId = computed(() => route.params.id)
const isRecommendation = computed(() => route.query.recId != null)
const recId = computed(() => Number(route.query.recId) || 0)

const typeLabel = computed(() => {
  const map = { video: '视频', article: '文章', audio: '音频' }
  return map[material.value?.material_type] || '资料'
})

const typeIcon = computed(() => {
  const map = { video: VideoCamera, article: Document, audio: Headset }
  return map[material.value?.material_type] || Document
})

const levelType = computed(() => {
  const lv = material.value?.cefr_level || ''
  if (lv.startsWith('C')) return 'danger'
  if (lv.startsWith('B')) return 'warning'
  return 'success'
})

const durationText = computed(() => {
  if (!material.value?.duration_seconds) return ''
  const mins = Math.round(material.value.duration_seconds / 60)
  return mins >= 1 ? `约 ${mins} 分钟` : `${material.value.duration_seconds} 秒`
})

async function fetchMaterial() {
  loading.value = true
  try {
    const res = await getMaterialDetailApi(materialId.value)
    material.value = res
  } catch {
    error.value = '资料不存在或加载失败'
  } finally {
    loading.value = false
  }
}

async function handleViewExternal() {
  if (isRecommendation.value && recId.value) {
    try { await clickRecommendationApi(recId.value, 'view') } catch { /* 静默 */ }
  }
  if (material.value?.url) {
    window.open(material.value.url, '_blank')
  } else {
    ElMessage.warning('暂无外部链接')
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/recommend')
  }
}

onMounted(() => {
  fetchMaterial()
})
</script>

<template>
  <div class="content-card material-detail">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-state" v-loading="true" element-loading-text="加载中..."></div>

    <!-- 错误 -->
    <div v-else-if="error" class="error-state">
      <el-empty :description="error">
        <el-button @click="goBack">返回</el-button>
      </el-empty>
    </div>

    <!-- 资料详情 -->
    <template v-else-if="material">
      <!-- 顶部导航 -->
      <div class="detail-header">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
      </div>

      <!-- 类型标识 -->
      <div class="detail-type-badge" :class="material.material_type">
        <el-icon :size="20"><component :is="typeIcon" /></el-icon>
        <span>{{ typeLabel }}</span>
      </div>

      <!-- 标题和描述 -->
      <h1 class="detail-title">{{ material.title }}</h1>
      <p class="detail-desc" v-if="material.description">{{ material.description }}</p>

      <!-- 元信息 -->
      <div class="detail-meta">
        <el-tag v-if="material.cefr_level" :type="levelType" effect="plain" size="large">
          {{ material.cefr_level }}
        </el-tag>
        <el-tag v-if="material.category" type="info" effect="plain" size="large">
          {{ material.category }}
        </el-tag>
        <span v-if="durationText" class="meta-duration">
          <el-icon><component :is="'Clock'" /></el-icon>
          {{ durationText }}
        </span>
      </div>

      <!-- 标签 -->
      <div class="detail-tags" v-if="material.tags && material.tags.length > 0">
        <el-tag v-for="tag in material.tags" :key="tag" size="small" effect="plain" round>{{ tag }}</el-tag>
      </div>

      <!-- 聚焦维度 -->
      <div class="detail-dimensions" v-if="material.focus_dimensions && material.focus_dimensions.length > 0">
        <span class="dim-label">训练维度：</span>
        <el-tag v-for="dim in material.focus_dimensions" :key="dim" size="small" type="warning" effect="light">
          {{ { listening: '听力', speaking: '口语', reading: '阅读', grammar: '语法', writing: '写作' }[dim] || dim }}
        </el-tag>
      </div>

      <!-- 预览区域 -->
      <div class="detail-preview">
        <!-- 视频 -->
        <div v-if="material.material_type === 'video'" class="preview-video">
          <div class="video-placeholder">
            <el-icon :size="64"><VideoCamera /></el-icon>
            <p>视频内容</p>
            <p class="video-hint">点击下方按钮在新标签页中打开</p>
          </div>
        </div>

        <!-- 文章 -->
        <div v-else-if="material.material_type === 'article'" class="preview-article">
          <div class="article-card">
            <el-icon :size="36"><Document /></el-icon>
            <h3>{{ material.title }}</h3>
            <p v-if="material.description">{{ material.description }}</p>
            <p v-else class="article-placeholder">文章内容将在新标签页中展示</p>
          </div>
        </div>

        <!-- 音频 -->
        <div v-else-if="material.material_type === 'audio'" class="preview-audio">
          <div class="audio-card">
            <div class="audio-visual">
              <el-icon :size="48"><Headset /></el-icon>
            </div>
            <p>{{ material.title }}</p>
            <p class="audio-hint" v-if="durationText">时长：{{ durationText }}</p>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="detail-actions">
        <el-button type="primary" size="large" @click="handleViewExternal">
          <el-icon><Link /></el-icon>
          打开原文链接
        </el-button>
        <el-button size="large" @click="goBack">返回</el-button>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.material-detail {
  min-height: 60vh;
}

.loading-state {
  padding: 80px 0;
}

.error-state {
  padding: 40px 0;
}

.detail-header {
  margin-bottom: var(--spacing-xl);
}

.detail-type-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: 4px 14px;
  border-radius: 20px;
  font-size: var(--font-size-sm);
  font-weight: 500;
  margin-bottom: var(--spacing-lg);

  &.video {
    background: rgba(var(--color-primary-rgb), 0.1);
    color: var(--color-primary);
  }
  &.article {
    background: rgba(var(--color-success-rgb), 0.1);
    color: var(--color-success);
  }
  &.audio {
    background: rgba(var(--color-warning-rgb), 0.1);
    color: var(--color-warning);
  }
}

.detail-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: var(--spacing-md);
  color: var(--color-text-primary);
}

.detail-desc {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  line-height: 1.8;
  margin-bottom: var(--spacing-lg);
  max-width: 720px;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
  flex-wrap: wrap;

  .meta-duration {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
}

.detail-tags {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-lg);
}

.detail-dimensions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xl);

  .dim-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
}

.detail-preview {
  margin-bottom: var(--spacing-2xl);
}

.preview-video .video-placeholder {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-xl);
  padding: 60px;
  text-align: center;
  color: var(--color-text-secondary);

  .video-hint {
    font-size: var(--font-size-sm);
    margin-top: var(--spacing-sm);
  }
}

.preview-article .article-card {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-xl);
  padding: 40px;
  text-align: center;
  color: var(--color-text-secondary);

  h3 {
    font-size: var(--font-size-lg);
    color: var(--color-text-primary);
    margin: var(--spacing-md) 0;
  }

  .article-placeholder {
    font-size: var(--font-size-sm);
  }
}

.preview-audio .audio-card {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-xl);
  padding: 40px;
  text-align: center;
  color: var(--color-text-secondary);

  .audio-visual {
    width: 96px;
    height: 96px;
    border-radius: 50%;
    background: rgba(var(--color-warning-rgb), 0.1);
    color: var(--color-warning);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto var(--spacing-lg);
  }

  .audio-hint {
    font-size: var(--font-size-sm);
    margin-top: var(--spacing-xs);
  }
}

.detail-actions {
  display: flex;
  gap: var(--spacing-md);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}
</style>