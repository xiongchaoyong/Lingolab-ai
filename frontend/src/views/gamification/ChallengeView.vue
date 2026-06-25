<script setup>
import { ref, onMounted } from 'vue'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'
import ScoreBar from '@/components/common/ScoreBar.vue'
import { useGamificationStore } from '@/stores/gamification'

const store = useGamificationStore()

const tabActive = ref('daily')

// 配音选中状态
const selectedClip = ref(null)
const showRecorder = ref(false)

onMounted(() => {
  store.fetchDailyChallenge()
})

// ===== 每日闯关 =====

async function handleLevelComplete(levelIndex, { blob }) {
  const result = await store.submitLevel(blob, levelIndex)
  if (result && levelIndex >= store.dailyLevels.length - 1 && result.passed) {
    // 最后一关通过，自动完成
    await store.completeDailyChallenge()
    store.fetchBadges()
    store.fetchPoints()
  }
}

// ===== 配音挑战 =====

function startDubbing(clip) {
  selectedClip.value = clip
  showRecorder.value = false
  store.clearDubbingResult()
}

async function handleDubbingRecord({ blob }) {
  const result = await store.submitDubbing(blob, selectedClip.value.id)
  if (result) {
    store.fetchBadges()
    store.fetchPoints()
  }
}

function backToClipList() {
  selectedClip.value = null
  showRecorder.value = false
  store.clearDubbingResult()
}

// ===== 勋章墙 =====

function handleBadgeTab() {
  if (store.badges.length === 0) {
    store.fetchBadges()
  }
}
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">游戏化闯关</h2>

    <el-tabs v-model="tabActive">
      <!-- 每日闯关 -->
      <el-tab-pane label="每日闯关" name="daily">
        <div class="points-banner">
          <span>今日积分：<strong>{{ store.dailyPoints }}</strong></span>
          <span v-if="store.dailyCompleted" style="color: var(--color-success);">今日已全部通关</span>
          <el-button v-if="store.dailyCompleted" size="small" @click="store.fetchDailyChallenge(); store.fetchPoints();">刷新</el-button>
        </div>

        <div v-if="store.dailyLoading" v-loading="store.dailyLoading" style="min-height: 200px;" />

        <template v-else>
          <div class="level-list">
            <div
              v-for="(lv, idx) in store.dailyLevels" :key="lv.level"
              class="level-card"
              :class="{
                active: store.currentLevel === idx && !store.dailyCompleted,
                passed: store.levelScores[idx] >= lv.pass_score,
                failed: store.levelScores[idx] !== undefined && store.levelScores[idx] < lv.pass_score,
              }"
            >
              <div class="level-left">
                <span class="level-num">{{ lv.level }}</span>
                <span class="level-stars">{{ '★'.repeat(lv.level <= 2 ? 1 : lv.level <= 3 ? 2 : 3) }}{{ '☆'.repeat(lv.level <= 2 ? 2 : lv.level <= 3 ? 1 : 0) }}</span>
              </div>
              <div class="level-body">
                <p class="level-text">{{ lv.text }}</p>
                <el-tag size="small">{{ lv.difficulty }}</el-tag>
                <span class="level-requirement">需 ≥ {{ lv.pass_score }} 分</span>
              </div>
              <div class="level-action">
                <!-- 已通过 -->
                <el-tag v-if="store.levelScores[idx] >= lv.pass_score" type="success">
                  {{ store.levelScores[idx] }}分 通过 +20
                </el-tag>
                <!-- 未通过 -->
                <template v-else-if="store.levelScores[idx] !== undefined">
                  <el-tag type="danger">{{ store.levelScores[idx] }}分 未通过</el-tag>
                </template>
                <!-- 当前关卡 -->
                <template v-else-if="store.currentLevel === idx && !store.dailyCompleted">
                  <div v-if="store.scoringLevel === idx" class="scoring-hint">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>评分中...</span>
                  </div>
                  <VoiceRecorder
                    v-else
                    :prep-time="3"
                    :max-duration="15"
                    :key="'level-' + idx"
                    @complete="handleLevelComplete(idx, $event)"
                  />
                </template>
                <!-- 未解锁 -->
                <el-tag v-else type="info">未解锁</el-tag>
              </div>
            </div>
          </div>

          <div v-if="store.dailyCompleted" class="complete-banner">
            <el-icon :size="28" color="var(--color-success)"><CircleCheckFilled /></el-icon>
            <span>全部通过！额外 +30 积分</span>
          </div>
        </template>
      </el-tab-pane>

      <!-- 配音挑战 -->
      <el-tab-pane label="配音挑战" name="dubbing" @tab-change="handleBadgeTab">
        <!-- 内容列表 -->
        <el-row v-if="!selectedClip" :gutter="16">
          <el-col :span="12" v-for="clip in store.dubbingContent" :key="clip.id">
            <div class="dubbing-card" @click="startDubbing(clip)">
              <h4>{{ clip.title }}</h4>
              <p class="dubbing-line">"{{ clip.subtitle }}"</p>
              <div class="dubbing-meta">
                <el-tag size="small">{{ clip.difficulty === 'easy' ? '简单' : clip.difficulty === 'medium' ? '中等' : '困难' }}</el-tag>
                <span>{{ clip.duration }}s</span>
              </div>
            </div>
          </el-col>
          <el-col :span="24" v-if="store.dubbingContent.length === 0 && !store.dubbingLoading">
            <el-empty description="暂无配音内容" />
          </el-col>
        </el-row>

        <!-- 配音详情 -->
        <div v-else class="dubbing-active">
          <div class="dubbing-content">
            <h3>{{ selectedClip.title }}</h3>
            <p class="dubbing-line-large">"{{ selectedClip.subtitle }}"</p>
            <el-tag size="small">
              {{ selectedClip.difficulty === 'easy' ? '简单' : selectedClip.difficulty === 'medium' ? '中等' : '困难' }}
            </el-tag>
          </div>

          <div class="dubbing-record" v-if="!store.dubbingResult && !store.dubbingScoring">
            <VoiceRecorder
              :prep-time="3"
              :max-duration="20"
              @complete="handleDubbingRecord"
            />
          </div>

          <div v-if="store.dubbingScoring" class="scoring-hint" style="text-align:center; padding: var(--spacing-xxl);">
            <el-icon :size="32" class="is-loading"><Loading /></el-icon>
            <p style="margin-top: var(--spacing-md);">正在评分...</p>
          </div>

          <div v-if="store.dubbingResult" class="dubbing-result">
            <div class="score-overall">
              综合：<strong>{{ store.dubbingResult.total_score }}</strong> 分
              <span style="color: var(--color-success);">+{{ store.dubbingResult.points_earned }}积分</span>
            </div>
            <ScoreBar label="发音相似度" :score="store.dubbingResult.pronunciation_score" />
            <ScoreBar label="语调相似度" :score="store.dubbingResult.intonation_score" />
            <ScoreBar label="情感匹配度" :score="store.dubbingResult.emotion_score" />
            <el-button type="primary" @click="backToClipList" style="width:100%;margin-top:16px;">返回列表</el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- 勋章墙 -->
      <el-tab-pane label="勋章墙" name="badges" @tab-change="handleBadgeTab">
        <div v-if="store.badgesLoading" v-loading="store.badgesLoading" style="min-height: 200px;" />
        <el-row v-else :gutter="12">
          <el-col :span="8" v-for="badge in store.badges" :key="badge.badge_type">
            <div class="badge-card" :class="{ earned: badge.earned }">
              <el-icon :size="36" :color="badge.earned ? 'var(--color-warning)' : 'var(--color-text-disabled)'">
                <Medal />
              </el-icon>
              <h4>{{ badge.badge_name }}</h4>
              <p>{{ badge.description }}</p>
              <el-tag v-if="badge.earned" type="warning" size="small">已获得</el-tag>
              <el-tag v-else type="info" size="small">未获得</el-tag>
            </div>
          </el-col>
          <el-col :span="24" v-if="store.badges.length === 0">
            <el-empty description="暂无勋章数据" />
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style lang="scss" scoped>
.points-banner {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg); background: rgba(var(--color-warning-rgb), 0.08);
  border-radius: var(--radius-md); margin-bottom: var(--spacing-lg);
  strong { font-size: var(--font-size-xl); color: var(--color-warning); }
}

.level-card {
  display: flex; align-items: center; gap: var(--spacing-lg);
  padding: var(--spacing-lg); border: 2px solid var(--color-border); border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md); transition: border-color 0.2s;
  &.active { border-color: var(--color-primary); }
  &.passed { border-color: var(--color-success); background: rgba(var(--color-success-rgb), 0.04); }
  &.failed { border-color: var(--color-danger); }
}

.level-left { text-align: center; min-width: 48px;
  .level-num { font-size: var(--font-size-xl); font-weight: 700; }
  .level-stars { font-size: 12px; color: var(--color-warning); }
}

.level-body { flex: 1;
  .level-text { font-weight: 500; margin-bottom: var(--spacing-xs); }
  .level-requirement { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-left: var(--spacing-sm); }
}

.level-action { min-width: 120px; text-align: right; }

.scoring-hint {
  display: flex; align-items: center; gap: var(--spacing-xs); color: var(--color-text-secondary);
}

.complete-banner {
  display: flex; align-items: center; justify-content: center; gap: var(--spacing-sm);
  padding: var(--spacing-lg); margin-top: var(--spacing-lg);
  background: rgba(var(--color-success-rgb), 0.08); border-radius: var(--radius-md);
  font-weight: 600; color: var(--color-success);
}

.dubbing-card {
  padding: var(--spacing-xl); background: var(--color-bg-primary); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); cursor: pointer; margin-bottom: var(--spacing-base);
  &:hover { box-shadow: var(--shadow-hover); }
  h4 { margin-bottom: var(--spacing-sm); }
  .dubbing-line { color: var(--color-text-secondary); font-style: italic; margin-bottom: var(--spacing-md); }
  .dubbing-meta { display: flex; align-items: center; gap: var(--spacing-sm); }
}

.dubbing-active { text-align: center; }
.dubbing-content {
  padding: var(--spacing-xxl); background: rgba(var(--color-primary-rgb), 0.04);
  border-radius: var(--radius-lg); margin-bottom: var(--spacing-xl);
  .dubbing-line-large { font-size: var(--font-size-xl); font-style: italic; margin: var(--spacing-lg) 0; }
}

.dubbing-record { display: flex; justify-content: center; margin: var(--spacing-xxl) 0; }

.dubbing-result {
  text-align: left;
  .score-overall { text-align: center; font-size: var(--font-size-xl); font-weight: 700; margin-bottom: var(--spacing-lg); }
}

.badge-card {
  text-align: center; padding: var(--spacing-xl); background: var(--color-bg-primary);
  border: 1px solid var(--color-border); border-radius: var(--radius-md); margin-bottom: var(--spacing-base);
  &.earned { border-color: var(--color-warning); }
  h4 { margin: var(--spacing-sm) 0 var(--spacing-xs); font-size: var(--font-size-sm); }
  p { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--spacing-md); }
}
</style>