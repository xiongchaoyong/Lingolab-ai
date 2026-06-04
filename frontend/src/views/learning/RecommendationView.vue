<script setup>
import { ref, computed } from 'vue'

// Mock 推荐数据池
const MATERIAL_POOL = [
  // 视频
  { id: 1, type: 'video', title: 'Master English TH Sound', category: '发音', level: 'B1', duration: '4min', icon: 'VideoCamera' },
  { id: 2, type: 'video', title: 'Speak Naturally in 30 Days', category: '流利度', level: 'B2', duration: '8min', icon: 'VideoCamera' },
  { id: 3, type: 'video', title: 'English Pronunciation Secrets', category: '发音', level: 'A2', duration: '6min', icon: 'VideoCamera' },
  { id: 4, type: 'video', title: 'Business English Conversations', category: '商务', level: 'B2', duration: '10min', icon: 'VideoCamera' },
  // 文章
  { id: 10, type: 'article', title: 'The History of English Language', category: '阅读', level: 'B1', duration: '350词', icon: 'Document' },
  { id: 11, type: 'article', title: 'Tips for Job Interviews in English', category: '语法', level: 'B2', duration: '280词', icon: 'Document' },
  { id: 12, type: 'article', title: 'How to Improve Your Accent', category: '发音', level: 'A2', duration: '420词', icon: 'Document' },
  { id: 13, type: 'article', title: 'Common English Grammar Mistakes', category: '语法', level: 'B1', duration: '310词', icon: 'Document' },
  // 音频
  { id: 20, type: 'audio', title: 'Ordering at a Restaurant', category: '听力', level: 'A2', duration: '5min', icon: 'Headset' },
  { id: 21, type: 'audio', title: 'Daily English Conversations', category: '对话', level: 'B1', duration: '6min', icon: 'Headset' },
  { id: 22, type: 'audio', title: 'Weather Forecast Listening', category: '听力', level: 'A1', duration: '3min', icon: 'Headset' },
  { id: 23, type: 'audio', title: 'Academic Lecture: Climate Change', category: '学术', level: 'C1', duration: '8min', icon: 'Headset' },
]

const recommendations = ref(getRandomBatch())
const dislikedIds = ref(new Set())

function getRandomBatch() {
  const videos = MATERIAL_POOL.filter(m => m.type === 'video').sort(() => Math.random() - 0.5).slice(0, 2)
  const articles = MATERIAL_POOL.filter(m => m.type === 'article').sort(() => Math.random() - 0.5).slice(0, 2)
  const audios = MATERIAL_POOL.filter(m => m.type === 'audio').sort(() => Math.random() - 0.5).slice(0, 2)
  return { videos, articles, audios }
}

function refreshAll() {
  recommendations.value = getRandomBatch()
  dislikedIds.value = new Set()
}

function handleDislike(material) {
  dislikedIds.value.add(material.id)
}

function isDisliked(id) {
  return dislikedIds.value.has(id)
}

const typeMeta = {
  video: { label: '视频推荐', icon: 'VideoCamera' },
  article: { label: '文章推荐', icon: 'Document' },
  audio: { label: '音频推荐', icon: 'Headset' },
}
</script>

<template>
  <div class="content-card">
    <div class="page-header">
      <div>
        <h2 class="page-title">为你推荐</h2>
        <p class="page-subtitle">基于你的学习短板和兴趣，每日精选 6 条学习资料</p>
      </div>
      <el-button @click="refreshAll" :icon="Refresh" type="primary" plain>换一批</el-button>
    </div>

    <!-- 三类资料 -->
    <div v-for="(items, typeKey) in recommendations" :key="typeKey" class="material-section">
      <div class="section-header">
        <el-icon :size="18" color="var(--color-primary)">
          <component :is="typeMeta[typeKey]?.icon" />
        </el-icon>
        <span class="section-label">{{ typeMeta[typeKey]?.label }}</span>
      </div>

      <el-row :gutter="16">
        <el-col :span="12" v-for="item in items" :key="item.id">
          <div class="material-card" :class="{ disliked: isDisliked(item.id) }">
            <div class="material-icon">
              <el-icon :size="24">
                <component :is="item.icon" />
              </el-icon>
            </div>
            <div class="material-body">
              <h4 class="material-title">{{ item.title }}</h4>
              <div class="material-tags">
                <el-tag size="small" effect="plain">{{ item.category }}</el-tag>
                <el-tag size="small" effect="plain" :type="item.level.startsWith('C') ? 'danger' : item.level.startsWith('B') ? 'warning' : 'success'">
                  {{ item.level }}
                </el-tag>
                <span class="material-duration">{{ item.duration }}</span>
              </div>
              <div class="material-actions" v-if="!isDisliked(item.id)">
                <el-button size="small" text type="primary">查看</el-button>
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
