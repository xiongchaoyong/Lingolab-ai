<script setup>
import { ref, computed } from 'vue'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'
import ScoreBar from '@/components/common/ScoreBar.vue'

// 每日闯关
const DAILY_LEVELS = [
  { level: 1, stars: 1, text: "I'd like a cup of coffee.", difficulty: 'A1', passScore: 70 },
  { level: 2, stars: 2, text: 'Could you tell me how to get to the station?', difficulty: 'A2', passScore: 70 },
  { level: 3, stars: 2, text: 'The environment is a topic that concerns everyone.', difficulty: 'B1', passScore: 70 },
  { level: 4, stars: 3, text: 'The sophisticated technology revolutionized the industry.', difficulty: 'B2', passScore: 70 },
  { level: 5, stars: 3, text: 'Nevertheless, the implications of climate change are profound.', difficulty: 'B2', passScore: 70 },
]

const currentLevel = ref(0)
const levelScores = ref({})
const dailyCompleted = ref(false)

function completeLevel() {
  const score = randomScore(55, 95)
  levelScores.value[currentLevel.value] = score
  if (currentLevel.value < 4) currentLevel.value++
  else dailyCompleted.value = true
}

function resetDaily() { currentLevel.value = 0; levelScores.value = {}; dailyCompleted.value = false }

const dailyPoints = computed(() => {
  let pts = 0
  Object.values(levelScores.value).forEach(s => { if (s >= 70) pts += 20 })
  if (dailyCompleted.value) pts += 30
  return pts
})

// 配音挑战
const DUBBING_CLIPS = [
  { id: 1, title: 'Toy Story', line: 'To infinity and beyond!', difficulty: '简单', duration: '5s' },
  { id: 2, title: 'Apollo 13', line: 'Houston, we have a problem.', difficulty: '中等', duration: '8s' },
  { id: 3, title: 'The King\'s Speech', line: 'I have a voice!', difficulty: '中等', duration: '6s' },
  { id: 4, title: 'Braveheart', line: 'They may take our lives, but they will never take our freedom!', difficulty: '困难', duration: '12s' },
]
const selectedClip = ref(null)
const dubbingScore = ref(null)

function startDubbing(clip) {
  selectedClip.value = clip
  dubbingScore.value = null
}
function completeDubbing() {
  dubbingScore.value = {
    overall: randomScore(55, 92),
    dimensions: [
      { label: '发音相似度', score: randomScore(55, 90) },
      { label: '语调相似度', score: randomScore(50, 88) },
      { label: '情感匹配度', score: randomScore(50, 85) },
    ],
  }
}

// 勋章
const BADGES = [
  { name: '初出茅庐', desc: '完成首次跟读', earned: true, icon: 'Medal' },
  { name: '坚持不懈', desc: '连续打卡7天', earned: true, icon: 'Timer' },
  { name: '发音达人', desc: '发音分≥85累计10次', earned: false, icon: 'StarFilled' },
  { name: '社交达人', desc: '发布20条社区评论', earned: false, icon: 'Share' },
  { name: '闯关王', desc: '每日闯关全通10次', earned: false, icon: 'Trophy' },
  { name: '配音高手', desc: '完成20次配音', earned: false, icon: 'VideoCamera' },
]

const tabActive = ref('daily')

function randomScore(min, max) { return Math.round(min + Math.random() * (max - min)) }
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">游戏化闯关</h2>

    <el-tabs v-model="tabActive">
      <!-- 每日闯关 -->
      <el-tab-pane label="每日闯关" name="daily">
        <div class="points-banner">
          <span>今日积分：<strong>{{ dailyPoints }}</strong></span>
          <el-button size="small" @click="resetDaily" v-if="dailyCompleted">刷新（模拟次日）</el-button>
        </div>

        <div class="level-list">
          <div v-for="lv in DAILY_LEVELS" :key="lv.level" class="level-card"
            :class="{ active: currentLevel === lv.level - 1 && !dailyCompleted,
                      passed: levelScores[lv.level - 1] >= lv.passScore,
                      failed: levelScores[lv.level - 1] !== undefined && levelScores[lv.level - 1] < lv.passScore }">
            <div class="level-left">
              <span class="level-num">{{ lv.level }}</span>
              <span class="level-stars">{{ '★'.repeat(lv.stars) }}{{ '☆'.repeat(3 - lv.stars) }}</span>
            </div>
            <div class="level-body">
              <p class="level-text">{{ lv.text }}</p>
              <el-tag size="small">{{ lv.difficulty }}</el-tag>
              <span class="level-requirement">需 ≥ {{ lv.passScore }} 分</span>
            </div>
            <div class="level-action">
              <template v-if="levelScores[lv.level - 1] >= lv.passScore">
                <el-tag type="success">通过 +20</el-tag>
              </template>
              <template v-else-if="levelScores[lv.level - 1] !== undefined">
                <el-tag type="danger">{{ levelScores[lv.level - 1] }}分 重试</el-tag>
              </template>
              <template v-else-if="currentLevel === lv.level - 1 && !dailyCompleted">
                <el-button type="primary" size="small" @click="completeLevel">跟读评分</el-button>
              </template>
              <template v-else>
                <el-tag type="info" v-if="currentLevel < lv.level - 1">未解锁</el-tag>
              </template>
            </div>
          </div>
        </div>

        <div v-if="dailyCompleted" class="complete-banner">
          <el-icon :size="28" color="var(--color-success)"><CircleCheckFilled /></el-icon>
          <span>全部通过！额外 +30 积分</span>
        </div>
      </el-tab-pane>

      <!-- 配音挑战 -->
      <el-tab-pane label="配音挑战" name="dubbing">
        <el-row :gutter="16" v-if="!selectedClip">
          <el-col :span="12" v-for="clip in DUBBING_CLIPS" :key="clip.id">
            <div class="dubbing-card" @click="startDubbing(clip)">
              <h4>{{ clip.title }}</h4>
              <p class="dubbing-line">"{{ clip.line }}"</p>
              <div class="dubbing-meta">
                <el-tag size="small">{{ clip.difficulty }}</el-tag>
                <span>{{ clip.duration }}</span>
              </div>
            </div>
          </el-col>
        </el-row>

        <div v-else class="dubbing-active">
          <div class="dubbing-content">
            <h3>{{ selectedClip.title }}</h3>
            <p class="dubbing-line-large">"{{ selectedClip.line }}"</p>
            <el-button text type="primary"><el-icon><VideoPlay /></el-icon> 播放原声</el-button>
          </div>
          <div class="dubbing-record" v-if="!dubbingScore">
            <VoiceRecorder :prep-time="3" :max-duration="20" @complete="completeDubbing" />
          </div>
          <div v-if="dubbingScore" class="dubbing-result">
            <div class="score-overall">综合：{{ dubbingScore.overall }} 分 +30积分</div>
            <ScoreBar v-for="d in dubbingScore.dimensions" :key="d.label" :label="d.label" :score="d.score" />
            <el-button type="primary" @click="selectedClip = null; dubbingScore = null" style="width:100%;margin-top:16px;">返回列表</el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- 勋章墙 -->
      <el-tab-pane label="勋章墙" name="badges">
        <el-row :gutter="12">
          <el-col :span="8" v-for="badge in BADGES" :key="badge.name">
            <div class="badge-card" :class="{ earned: badge.earned }">
              <el-icon :size="36" :color="badge.earned ? 'var(--color-warning)' : 'var(--color-text-disabled)'">
                <component :is="badge.icon" />
              </el-icon>
              <h4>{{ badge.name }}</h4>
              <p>{{ badge.desc }}</p>
              <el-tag v-if="badge.earned" type="warning" size="small">已获得</el-tag>
              <el-tag v-else type="info" size="small">未获得</el-tag>
            </div>
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
