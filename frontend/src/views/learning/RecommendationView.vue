<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getRecommendationsApi,
  dislikeRecommendationApi,
  refreshRecommendationsApi,
  clickRecommendationApi,
} from '@/api/recommendation'

const recommendations = ref({ videos: [], articles: [], audios: [] })
const dislikedIds = ref(new Set())
const generatedAt = ref('')
const loading = ref(false)

async function fetchRecommendations() {
  loading.value = true
  try {
    const res = await getRecommendationsApi()
    recommendations.value = {
      videos: res.videos || [],
      articles: res.articles || [],
      audios: res.audios || [],
    }
    generatedAt.value = res.generated_at || ''
    dislikedIds.value = new Set()
  } catch {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  loading.value = true
  try {
    const res = await refreshRecommendationsApi()
    recommendations.value = {
      videos: res.videos || [],
      articles: res.articles || [],
      audios: res.audios || [],
    }
    generatedAt.value = res.generated_at || ''
    dislikedIds.value = new Set()
  } catch {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}

async function handleDislike(material) {
  try {
    await dislikeRecommendationApi(material.id)
    dislikedIds.value.add(material.id)
  } catch {
    // 错误已在拦截器处理
  }
}

function isDisliked(id) {
  return dislikedIds.value.has(id)
}

async function handleView(item) {
  // 记录查看行为
  try {
    await clickRecommendationApi(item.id, 'view')
  } catch {
    // 静默失败
  }

  // 打开资料链接
  if (item.url) {
    window.open(item.url, '_blank')
  } else {
    ElMessage.warning('该资料暂无链接')
  }
}

const typeMeta = {
  videos: { label: '视频推荐', icon: 'VideoCamera' },
  articles: { label: '文章推荐', icon: 'Document' },
  audios: { label: '音频推荐', icon: 'Headset' },
}

function getMaterialIcon(type) {
  if (type === 'video') return 'VideoCamera'
  if (type === 'article') return 'Document'
  return 'Headset'
}

function getLevelType(level) {
  if (!level) return 'info'
  if (level.startsWith('C')) return 'danger'
  if (level.startsWith('B')) return 'warning'
  return 'success'
}

onMounted(() => {
  fetchRecommendations()
})
</script>

<template>
  <div class="content-card" v-loading="loading">
    <div class="page-header">
      <div>
        <h2 class="page-title">为你推荐</h2>
        <p class="page-subtitle">基于你的学习短板和兴趣，每日精选 6 条学习资料</p>
      </div>
      <el-button @click="refreshAll" :icon="Refresh" type="primary" plain :loading="loading">换一批</el-button>
    </div>

    <!-- 三类资料 -->
    <div v-for="(items, typeKey) in recommendations" :key="typeKey" class="material-section">
      <div class="section-header">
        <el-icon :size="18" color="var(--color-primary)">
          <component :is="typeMeta[typeKey]?.icon" />
        </el-icon>
        <span class="section-label">{{ typeMeta[typeKey]?.label }}</span>
        <span class="section-count">{{ items.length }} 条</span>
      </div>

      <el-empty v-if="items.length === 0" description="暂无推荐" :image-size="40" />

      <el-row :gutter="16">
        <el-col :span="12" v-for="item in items" :key="item.id">
          <div class="material-card" :class="{ disliked: isDisliked(item.id) }">
            <div class="material-icon">
              <el-icon :size="24">
                <component :is="getMaterialIcon(item.type)" />
              </el-icon>
            </div>
            <div class="material-body">
              <h4 class="material-title">{{ item.title }}</h4>
              <div class="material-tags">
                <el-tag v-if="item.tag" size="small" effect="plain">{{ item.tag }}</el-tag>
                <el-tag size="small" effect="plain" :type="getLevelType(item.difficulty)">
                  {{ item.difficulty }}
                </el-tag>
                <span class="material-duration">{{ item.duration }}</span>
              </div>
              <div class="material-score" v-if="item.score">
                推荐分：{{ item.score }}
              </div>
              <div class="material-actions" v-if="!isDisliked(item.id)">
                <el-button size="small" text type="primary" @click="handleView(item)">查看</el-button>
                <el-button size="small" text @click="handleDislike(item)">不感兴趣</el-button>
              </div>
              <div v-else class="disliked-hint">
                <el-icon><RemoveFilled /></el-icon> 已隐藏
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);

  .page-subtitle {
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
    margin-top: var(--spacing-xs);
  }
}

.material-section {
  margin-bottom: var(--spacing-xxl);

  &:last-child { margin-bottom: 0; }
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);

  .section-label {
    font-size: var(--font-size-base);
    font-weight: 600;
    color: var(--color-text-primary);
  }
}

.material-card {
  display: flex;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-base);
  transition: all 0.2s;

  &:hover {
    box-shadow: var(--shadow-hover);
  }

  &.disliked {
    opacity: 0.4;
  }
}

.material-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: rgba(var(--color-primary-rgb), 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  flex-shrink: 0;
}

.material-body {
  flex: 1;
}

.material-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-primary);
}

.material-tags {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);

  .material-duration {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-left: auto;
  }
}

.material-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.disliked-hint {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-disabled);
}
</style>
