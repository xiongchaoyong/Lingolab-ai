<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'
import ScoreBar from '@/components/common/ScoreBar.vue'
import { useGamificationStore } from '@/stores/gamification'

const store = useGamificationStore()

const tabActive = ref('daily')

// 配音选中状态
const selectedClip = ref(null)
const showRecorder = ref(false)

// ===== 动画状态 =====
const animatingScore = ref({})       // { [levelIndex]: displayedScore } 用于分数递增动画
const levelJustPassed = ref(-1)       // 刚通过关卡索引
const levelJustFailed = ref(-1)       // 刚失败关卡索引
const showPointsFly = ref(false)      // 积分飞入动画
const flyPointsText = ref('')         // 飞入积分文字
const flyPointsKey = ref(0)          // 触发重复动画的 key
const showBadgeModal = ref(false)     // 勋章弹窗
const badgeModalBadges = ref([])      // 弹窗中的勋章
const pointsCounting = ref(0)         // 积分栏递增数字
const showConfetti = ref(false)       // 撒花效果
const dubbingScoreAnimated = ref(false) // 配音评分动画

// 分值递增动画
function animateScore(levelIndex, targetScore) {
  const start = 0
  const duration = 600
  const startTime = performance.now()
  animatingScore.value[levelIndex] = 0

  function step(now) {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    // easeOutCubic
    const eased = 1 - Math.pow(1 - progress, 3)
    animatingScore.value[levelIndex] = Math.round(start + (targetScore - start) * eased)
    if (progress < 1) {
      requestAnimationFrame(step)
    }
  }
  requestAnimationFrame(step)
}

// 积分飞入动画
function triggerPointsFly(text) {
  flyPointsText.value = text
  flyPointsKey.value++
  showPointsFly.value = true
  setTimeout(() => { showPointsFly.value = false }, 1200)
}

// 积分栏数字递增
function animatePointsCount(target) {
  const start = pointsCounting.value
  const duration = 800
  const startTime = performance.now()

  function step(now) {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    pointsCounting.value = Math.round(start + (target - start) * eased)
    if (progress < 1) {
      requestAnimationFrame(step)
    }
  }
  requestAnimationFrame(step)
}

onMounted(() => {
  store.fetchDailyChallenge()
  pointsCounting.value = store.dailyPoints
})

// 监听每日积分变化
watch(() => store.dailyPoints, (newVal, oldVal) => {
  animatePointsCount(newVal)
})

// 监听积分获得
watch(() => store.lastPointsEarned, (pts) => {
  if (pts > 0) {
    nextTick(() => triggerPointsFly(`+${pts}`))
  }
})

// 监听勋章解锁
watch(() => store.newBadges, (badges) => {
  if (badges.length > 0) {
    badgeModalBadges.value = badges
    showBadgeModal.value = true
    showConfetti.value = true
    setTimeout(() => { showConfetti.value = false }, 3000)
  }
})

// ===== 每日闯关 =====

async function handleLevelComplete(levelIndex, { blob }) {
  const result = await store.submitLevel(blob, levelIndex)
  if (!result) return

  // 触发分数动画
  animateScore(levelIndex, result.score)

  if (result.passed) {
    levelJustPassed.value = levelIndex
    setTimeout(() => { levelJustPassed.value = -1 }, 800)
  } else {
    levelJustFailed.value = levelIndex
    setTimeout(() => { levelJustFailed.value = -1 }, 600)
  }

  if (levelIndex >= store.dailyLevels.length - 1 && result.passed) {
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
  dubbingScoreAnimated.value = false
}

async function handleDubbingRecord({ blob }) {
  const result = await store.submitDubbing(blob, selectedClip.value.id)
  if (result) {
    dubbingScoreAnimated.value = true
    store.fetchBadges()
    store.fetchPoints()
  }
}

function backToClipList() {
  selectedClip.value = null
  showRecorder.value = false
  store.clearDubbingResult()
  dubbingScoreAnimated.value = false
}

// ===== 勋章弹窗 =====

function closeBadgeModal() {
  showBadgeModal.value = false
  store.clearNewBadges()
}

// ===== 勋章墙 =====

function handleTabChange(tabName) {
  if (tabName === 'dubbing' && store.dubbingContent.length === 0) {
    store.fetchDubbingContent()
  }
  if (tabName === 'badges' && store.badges.length === 0) {
    store.fetchBadges()
  }
}

// 勋章描述映射
const badgeDescriptions = {
  newcomer: '完成第一次发音练习，迈出英语学习第一步',
  streak: '连续打卡 7 天，坚持就是胜利',
  pronunciation_break: '发音 ≥85 分累计 10 次，发音达人就是你',
  progress: 'CEFR 等级成功提升，学习效果显著',
  dubbing: '完成 20 次配音挑战，声优之路开启',
  perfect: '单次发音获得满分，完美无瑕',
  scholar: '全通闯关 10 次，学霸成就达成',
}
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">游戏化闯关</h2>

    <!-- ===== 积分飞入动画 ===== -->
    <div class="points-fly" v-if="showPointsFly" :key="'fly-' + flyPointsKey">
      <span class="fly-text">{{ flyPointsText }}</span>
    </div>

    <!-- ===== 勋章解锁弹窗 ===== -->
    <Teleport to="body">
      <div v-if="showBadgeModal" class="badge-modal-overlay" @click.self="closeBadgeModal">
        <div class="badge-modal cute-bounce">
          <div class="confetti-container" v-if="showConfetti">
            <span v-for="i in 20" :key="i" class="confetti-piece" :style="{
              '--x': Math.random() * 100 + '%',
              '--delay': Math.random() * 0.8 + 's',
              '--color': ['#FFD700','#FF6B6B','#4ECDC4','#A78BFA','#FBBF24','#EC4899'][i % 6],
              '--rotate': (Math.random() * 360) + 'deg',
            }"></span>
          </div>
          <div class="badge-modal-header">
            <span class="badge-modal-icon">🎉</span>
            <h2>恭喜获得新勋章！</h2>
          </div>
          <div class="badge-modal-list">
            <div v-for="badge in badgeModalBadges" :key="badge.badge_type" class="badge-modal-item">
              <div class="badge-modal-medal">
                <span class="medal-emoji">🏅</span>
              </div>
              <h3>{{ badge.badge_name }}</h3>
              <p>{{ badgeDescriptions[badge.badge_type] || badge.description }}</p>
            </div>
          </div>
          <el-button type="primary" size="large" @click="closeBadgeModal" class="badge-modal-btn">
            太棒了！
          </el-button>
        </div>
      </div>
    </Teleport>

    <el-tabs v-model="tabActive" @tab-change="handleTabChange">
      <!-- ===== 每日闯关 ===== -->
      <el-tab-pane label="每日闯关" name="daily">
        <div class="points-banner">
          <span>今日积分：<strong class="points-count">{{ pointsCounting }}</strong></span>
          <span v-if="store.dailyCompleted" style="color: var(--color-success);">今日已全部通关</span>
          <el-button v-if="store.dailyCompleted" size="small" @click="store.fetchDailyChallenge(); store.fetchPoints(); pointsCounting = store.dailyPoints;">刷新</el-button>
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
                'just-passed': levelJustPassed === idx,
                'just-failed': levelJustFailed === idx,
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
                <!-- 已通过（含动画分数） -->
                <el-tag v-if="store.levelScores[idx] >= lv.pass_score" type="success" class="score-tag">
                  {{ animatingScore[idx] ?? store.levelScores[idx] }}分 通过 +20
                </el-tag>
                <!-- 未通过 -->
                <template v-else-if="store.levelScores[idx] !== undefined">
                  <el-tag type="danger" class="score-tag">
                    {{ animatingScore[idx] ?? store.levelScores[idx] }}分 未通过
                  </el-tag>
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
                <!-- 未解锁 — 带入场动画 -->
                <el-tag v-else type="info" class="locked-tag">🔒 未解锁</el-tag>
              </div>
            </div>
          </div>

          <div v-if="store.dailyCompleted" class="complete-banner cute-bounce">
            <div class="complete-icon-wrap">
              <span class="complete-emoji">🎊</span>
            </div>
            <div class="complete-text">
              <strong>全部通关！</strong>
              <span>额外 +30 积分</span>
            </div>
            <div class="complete-stars">
              <span v-for="i in 5" :key="i" class="star" :style="{ animationDelay: i * 0.1 + 's' }">⭐</span>
            </div>
          </div>
        </template>
      </el-tab-pane>

      <!-- ===== 配音挑战 ===== -->
      <el-tab-pane label="配音挑战" name="dubbing">
        <div v-if="!selectedClip" class="dubbing-grid">
          <div v-for="clip in store.dubbingContent" :key="clip.id" class="dubbing-card" @click="startDubbing(clip)">
            <h4>{{ clip.title }}</h4>
            <p class="dubbing-line">"{{ clip.subtitle }}"</p>
            <div class="dubbing-meta">
              <el-tag size="small">{{ clip.difficulty === 'easy' ? '简单' : clip.difficulty === 'medium' ? '中等' : '困难' }}</el-tag>
              <span>{{ clip.duration }}s</span>
            </div>
          </div>
          <el-empty v-if="store.dubbingContent.length === 0 && !store.dubbingLoading" description="暂无配音内容" style="grid-column: 1 / -1;" />
        </div>

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

          <div v-if="store.dubbingResult" class="dubbing-result" :class="{ animated: dubbingScoreAnimated }">
            <div class="score-overall">
              <span class="score-label">综合：</span>
              <strong class="score-number">{{ dubbingScoreAnimated ? store.dubbingResult.total_score : 0 }}</strong>
              <span class="score-unit">分</span>
              <span class="score-points" v-if="store.dubbingResult.points_earned">
                +{{ store.dubbingResult.points_earned }}积分
              </span>
            </div>
            <ScoreBar label="发音相似度" :score="dubbingScoreAnimated ? store.dubbingResult.pronunciation_score : 0" />
            <ScoreBar label="语调相似度" :score="dubbingScoreAnimated ? store.dubbingResult.intonation_score : 0" />
            <ScoreBar label="情感匹配度" :score="dubbingScoreAnimated ? store.dubbingResult.emotion_score : 0" />
            <el-button type="primary" @click="backToClipList" style="width:100%;margin-top:16px;">返回列表</el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- ===== 勋章墙 ===== -->
      <el-tab-pane label="勋章墙" name="badges">
        <div v-if="store.badgesLoading" v-loading="store.badgesLoading" style="min-height: 200px;" />
        <div v-else class="badge-grid">
          <div v-for="badge in store.badges" :key="badge.badge_type" class="badge-card" :class="{ earned: badge.earned }">
            <div class="badge-icon-wrap" :class="{ 'cute-float': badge.earned }">
              <span class="badge-emoji">{{ badge.earned ? '🏅' : '🔒' }}</span>
            </div>
            <h4>{{ badge.badge_name }}</h4>
            <p>{{ badgeDescriptions[badge.badge_type] || badge.description }}</p>
            <el-tag v-if="badge.earned" type="warning" size="small">已获得</el-tag>
            <el-tag v-else type="info" size="small">未获得</el-tag>
          </div>
          <el-empty v-if="store.badges.length === 0" description="暂无勋章数据" style="grid-column: 1 / -1;" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style lang="scss" scoped>
// ===== 积分飞入动画 =====
.points-fly {
  position: fixed;
  top: 80px;
  right: 40px;
  z-index: 3000;
  pointer-events: none;

  .fly-text {
    display: inline-block;
    font-size: 28px;
    font-weight: 800;
    color: var(--color-warning);
    text-shadow: 0 2px 8px rgba(251, 191, 36, 0.4);
    animation: fly-up 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
  }
}

@keyframes fly-up {
  0% { opacity: 1; transform: translateY(0) scale(0.6); }
  30% { opacity: 1; transform: translateY(-20px) scale(1.2); }
  100% { opacity: 0; transform: translateY(-60px) scale(0.8); }
}

// ===== 勋章弹窗 =====
.badge-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 4000;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.badge-modal {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-xl);
  padding: 40px;
  max-width: 420px;
  width: 90%;
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);

  .badge-modal-header {
    margin-bottom: var(--spacing-xl);
    .badge-modal-icon { font-size: 48px; display: block; margin-bottom: var(--spacing-sm); }
    h2 { font-size: var(--font-size-xl); color: var(--color-warning); }
  }

  .badge-modal-list {
    margin-bottom: var(--spacing-xl);
  }

  .badge-modal-item {
    padding: var(--spacing-lg);
    .badge-modal-medal {
      .medal-emoji { font-size: 40px; }
    }
    h3 { font-size: var(--font-size-lg); margin: var(--spacing-sm) 0; }
    p { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
  }

  .badge-modal-btn {
    min-width: 160px;
  }
}

// 撒花粒子
.confetti-container {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.confetti-piece {
  position: absolute;
  top: -10px;
  left: var(--x);
  width: 8px;
  height: 8px;
  border-radius: 2px;
  background: var(--color);
  animation: confetti-fall 3s ease-in var(--delay) forwards;
  transform: rotate(var(--rotate));
}

@keyframes confetti-fall {
  0% { transform: translateY(0) rotate(0deg); opacity: 1; }
  100% { transform: translateY(500px) rotate(720deg); opacity: 0; }
}

// ===== 积分栏 =====
.points-banner {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg); background: rgba(var(--color-warning-rgb), 0.08);
  border-radius: var(--radius-md); margin-bottom: var(--spacing-lg);
  strong.points-count {
    font-size: var(--font-size-xxl);
    color: var(--color-warning);
    font-variant-numeric: tabular-nums;
    transition: transform 0.2s;
  }
}

// ===== 关卡列表 =====
.level-list {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--spacing-md);
}

.level-card {
  display: flex; flex-direction: column; align-items: center; gap: var(--spacing-md);
  padding: var(--spacing-lg); border: 2px solid var(--color-border); border-radius: var(--radius-md);
  text-align: center; transition: all 0.3s ease;

  &.active {
    border-color: var(--color-primary);
    box-shadow: 0 0 12px rgba(var(--color-primary-rgb), 0.15);
  }
  &.passed {
    border-color: var(--color-success);
    background: rgba(var(--color-success-rgb), 0.04);
  }
  &.failed {
    border-color: var(--color-danger);
    background: rgba(var(--color-danger-rgb), 0.03);
  }

  // 刚通过弹跳
  &.just-passed {
    animation: cute-bounce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    border-color: var(--color-success);
    box-shadow: 0 0 20px rgba(var(--color-success-rgb), 0.3);
  }

  // 刚失败抖动
  &.just-failed {
    animation: cute-wiggle 0.3s ease-in-out;
    border-color: var(--color-danger);
  }
}

.level-left { text-align: center;
  .level-num { font-size: var(--font-size-xxl); font-weight: 700; }
  .level-stars { font-size: 12px; color: var(--color-warning); display: block; }
}

.level-body { flex: 1;
  .level-text { font-weight: 500; margin-bottom: var(--spacing-xs); font-size: var(--font-size-sm); }
  .level-requirement { font-size: var(--font-size-xs); color: var(--color-text-secondary); display: block; margin-top: var(--spacing-xs); }
}

.level-action { min-width: auto; }

.score-tag {
  animation: cute-bounce 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.locked-tag {
  opacity: 0.6;
}

.scoring-hint {
  display: flex; align-items: center; gap: var(--spacing-xs); color: var(--color-text-secondary);
}

// ===== 全部通关横幅 =====
.complete-banner {
  display: flex; align-items: center; justify-content: center; gap: var(--spacing-lg);
  padding: var(--spacing-xl); margin-top: var(--spacing-lg);
  background: linear-gradient(135deg, rgba(var(--color-success-rgb), 0.08), rgba(var(--color-warning-rgb), 0.08));
  border: 2px solid rgba(var(--color-success-rgb), 0.2);
  border-radius: var(--radius-lg);
  position: relative;
  overflow: hidden;

  .complete-icon-wrap {
    .complete-emoji { font-size: 36px; }
  }

  .complete-text {
    display: flex; flex-direction: column;
    strong { font-size: var(--font-size-lg); color: var(--color-success); }
    span { font-size: var(--font-size-sm); color: var(--color-warning); }
  }

  .complete-stars {
    display: flex; gap: 4px;
    .star {
      font-size: 20px;
      animation: star-pop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    }
  }
}

@keyframes star-pop {
  0% { transform: scale(0) rotate(-30deg); opacity: 0; }
  100% { transform: scale(1) rotate(0deg); opacity: 1; }
}

// ===== 配音挑战 =====
.dubbing-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-base);
}

.dubbing-card {
  padding: var(--spacing-xl); background: var(--color-bg-primary); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); cursor: pointer; transition: all 0.3s ease;
  &:hover { box-shadow: var(--shadow-hover); transform: translateY(-2px); }
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
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.5s ease;

  &.animated {
    opacity: 1;
    transform: translateY(0);
  }

  .score-overall {
    text-align: center; font-size: var(--font-size-xl); font-weight: 700; margin-bottom: var(--spacing-lg);
    .score-number { font-size: 36px; color: var(--color-primary); }
    .score-unit { font-size: var(--font-size-base); color: var(--color-text-secondary); }
    .score-points { display: block; font-size: var(--font-size-sm); color: var(--color-success); margin-top: var(--spacing-xs); }
  }
}

// ===== 勋章墙 =====
.badge-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-base);
}

.badge-card {
  text-align: center; padding: var(--spacing-xl); background: var(--color-bg-primary);
  border: 1px solid var(--color-border); border-radius: var(--radius-md);
  transition: all 0.3s ease;

  &.earned {
    border-color: var(--color-warning);
    background: rgba(var(--color-warning-rgb), 0.04);
    &:hover { transform: translateY(-3px); box-shadow: 0 4px 16px rgba(var(--color-warning-rgb), 0.2); }
  }

  .badge-icon-wrap {
    margin-bottom: var(--spacing-sm);
    .badge-emoji { font-size: 36px; display: block; }
  }

  h4 { margin: var(--spacing-sm) 0 var(--spacing-xs); font-size: var(--font-size-sm); }
  p { font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-bottom: var(--spacing-md); min-height: 32px; }
}
</style>