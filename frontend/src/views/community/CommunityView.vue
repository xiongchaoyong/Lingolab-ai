<script setup>
import { ref, onMounted } from 'vue'
import { Microphone, Star, ChatLineRound, Picture, Loading, CircleCheckFilled, Medal } from '@element-plus/icons-vue'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'
import ScoreBar from '@/components/common/ScoreBar.vue'
import { useCommunityStore } from '@/stores/community'
import { useGamificationStore } from '@/stores/gamification'

const store = useCommunityStore()
const gameStore = useGamificationStore()

const activeTab = ref('challenge')
const newPost = ref('')
const newPostTopic = ref('')
const showCommentDialog = ref(false)
const commentDialogPost = ref(null)
const commentContent = ref('')
const comments = ref([])
const showRecorder = ref(false)
const submitting = ref(false)
const submitResult = ref(null)

// ========== 闯关挑战子 tab ==========
const challengeSubTab = ref('daily')
const selectedClip = ref(null)
const showDubbingRecorder = ref(false)

onMounted(() => {
  store.fetchChallenges()
  store.fetchPosts()
})

// ===== 语音挑战 =====

async function handleChallengeSubmit({ blob }) {
  if (!store.currentChallenge) return
  submitting.value = true
  submitResult.value = null
  try {
    const result = await store.submitChallenge(store.currentChallenge.id, blob)
    submitResult.value = result
    store.fetchLeaderboard(store.currentChallenge.id)
  } finally {
    submitting.value = false
  }
}

function selectChallenge(challenge) {
  store.currentChallenge = challenge
  showRecorder.value = false
  submitResult.value = null
  store.fetchLeaderboard(challenge.id)
}

// ===== 话题讨论 =====

async function handleCreatePost() {
  if (!newPostTopic.value.trim() || !newPost.value.trim()) return
  await store.createPost(newPostTopic.value.trim(), newPost.value.trim())
  newPostTopic.value = ''
  newPost.value = ''
}

async function handleLike(postId) {
  await store.toggleLike(postId)
}

async function openComments(post) {
  showCommentDialog.value = true
  commentDialogPost.value = post
  commentContent.value = ''
  comments.value = await store.fetchComments(post.id)
}

async function handleAddComment() {
  if (!commentContent.value.trim() || !commentDialogPost.value) return
  await store.addComment(commentDialogPost.value.id, commentContent.value.trim())
  commentContent.value = ''
  comments.value = await store.fetchComments(commentDialogPost.value.id)
}

// ===== 闯关挑战 =====

async function handleLevelComplete(levelIndex, { blob }) {
  const result = await gameStore.submitLevel(blob, levelIndex)
  if (result && levelIndex >= gameStore.dailyLevels.length - 1 && result.passed) {
    await gameStore.completeDailyChallenge()
    gameStore.fetchBadges()
    gameStore.fetchPoints()
  }
}

function startDubbing(clip) {
  selectedClip.value = clip
  showDubbingRecorder.value = false
  gameStore.clearDubbingResult()
}

async function handleDubbingRecord({ blob }) {
  const result = await gameStore.submitDubbing(blob, selectedClip.value.id)
  if (result) {
    gameStore.fetchBadges()
    gameStore.fetchPoints()
  }
}

function backToClipList() {
  selectedClip.value = null
  showDubbingRecorder.value = false
  gameStore.clearDubbingResult()
}

function onMainTabChange(tabName) {
  if (tabName === 'challenge-game' && gameStore.dailyLevels.length === 0) {
    gameStore.fetchDailyChallenge()
  }
}

function onChallengeSubTabChange(tabName) {
  if (tabName === 'daily') {
    gameStore.fetchDailyChallenge()
  }
  if (tabName === 'dubbing' && gameStore.dubbingContent.length === 0) {
    gameStore.fetchDubbingContent()
  }
  if (tabName === 'badges' && gameStore.badges.length === 0) {
    gameStore.fetchBadges()
  }
}

// ===== 排行榜颜色 =====
const rankColors = { 1: '#FFD700', 2: '#C0C0C0', 3: '#CD7F32' }
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">学习社区</h2>

    <el-tabs v-model="activeTab" @tab-change="onMainTabChange">
      <!-- ======================================== 语音挑战 -->
      <el-tab-pane label="语音挑战" name="challenge">
        <!-- 挑战列表 -->
        <div v-if="store.challenges.length === 0 && !store.challengesLoading" class="empty-hint">
          暂无进行中的挑战，敬请期待
        </div>
        <div v-else class="challenge-selector">
          <el-radio-group
            v-model="store.currentChallenge"
            size="small"
            @change="selectChallenge"
          >
            <el-radio-button
              v-for="c in store.challenges"
              :key="c.id"
              :value="c"
            >
              {{ c.title }}
            </el-radio-button>
          </el-radio-group>
        </div>

        <div v-if="store.currentChallenge" class="challenge-hero">
          <div class="challenge-info">
            <h3>{{ store.currentChallenge.title }}</h3>
            <p class="challenge-desc">{{ store.currentChallenge.description }}</p>
            <p class="challenge-sample">示范文本：{{ store.currentChallenge.sample_text }}</p>
            <p>截止时间：{{ store.currentChallenge.deadline }} | {{ store.currentChallenge.participants_count }} 人参与</p>
          </div>
          <el-button
            v-if="!showRecorder"
            type="primary"
            :icon="Microphone"
            @click="showRecorder = true"
          >
            立即参与
          </el-button>
        </div>

        <!-- 录音 -->
        <div v-if="showRecorder" class="recorder-section">
          <VoiceRecorder
            :max-duration="30"
            @complete="handleChallengeSubmit"
          />
          <div v-if="submitting" class="scoring-hint">评分中...</div>
          <div v-if="submitResult" class="submit-result">
            <el-tag type="success" size="large">
              综合分 {{ submitResult.submission?.total_score }} 分 | 排名 #{{ submitResult.rank }}
            </el-tag>
          </div>
        </div>

        <!-- 排行榜 -->
        <h4 class="section-title">排行榜</h4>
        <div v-if="store.leaderboard.length === 0" class="empty-hint">暂无提交记录</div>
        <div v-else class="ranking-list">
          <div v-for="item in store.leaderboard" :key="item.rank" class="ranking-item">
            <div class="rank-badge" :style="item.rank <= 3 ? { background: rankColors[item.rank], color: '#fff' } : {}">
              {{ item.rank }}
            </div>
            <div class="rank-body">
              <span class="rank-user">{{ item.username }}</span>
            </div>
            <div class="rank-right">
              <span class="rank-score">{{ item.total_score ?? '--' }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- ======================================== 话题讨论 -->
      <el-tab-pane label="话题讨论" name="discussion">
        <div class="post-input-box">
          <el-input v-model="newPostTopic" placeholder="标题" style="margin-bottom: 8px" />
          <el-input v-model="newPost" type="textarea" :rows="3" placeholder="分享你的英语学习心得或提问..." />
          <div class="post-footer">
            <el-button text :icon="Picture" size="small">图片</el-button>
            <el-button type="primary" :disabled="!newPost.trim() || !newPostTopic.trim()" @click="handleCreatePost">发布</el-button>
          </div>
        </div>

        <div v-if="store.posts.length === 0 && !store.postsLoading" class="empty-hint">
          暂无讨论，快来发表第一个帖子吧
        </div>
        <div v-else class="discussion-list">
          <div v-for="d in store.posts" :key="d.id" class="discussion-card">
            <div class="disc-header">
              <div class="disc-avatar">{{ d.avatar }}</div>
              <div>
                <div class="disc-user">{{ d.username }}</div>
                <div class="disc-time">{{ d.created_at?.slice(0, 10) }}</div>
              </div>
            </div>
            <h4 class="disc-topic">{{ d.topic }}</h4>
            <p class="disc-content">{{ d.content }}</p>
            <div class="disc-actions">
              <el-button
                text
                :icon="Star"
                size="small"
                :type="d.is_liked ? 'primary' : 'default'"
                @click="handleLike(d.id)"
              >
                {{ d.likes_count }}
              </el-button>
              <el-button text :icon="ChatLineRound" size="small" @click="openComments(d)">
                {{ d.comments_count }}
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- ======================================== 闯关挑战 -->
      <el-tab-pane label="闯关挑战" name="challenge-game">
        <el-tabs v-model="challengeSubTab" @tab-change="onChallengeSubTabChange">
          <!-- 每日闯关 -->
          <el-tab-pane label="每日闯关" name="daily">
            <div class="points-banner">
              <span>今日积分：<strong>{{ gameStore.dailyPoints }}</strong></span>
              <span v-if="gameStore.dailyCompleted" style="color: var(--color-success);">今日已全部通关</span>
              <el-button v-if="gameStore.dailyCompleted" size="small" @click="gameStore.fetchDailyChallenge(); gameStore.fetchPoints();">刷新</el-button>
            </div>

            <div v-if="gameStore.dailyLoading" v-loading="gameStore.dailyLoading" style="min-height: 200px;" />

            <template v-else>
              <div class="level-list">
                <div
                  v-for="(lv, idx) in gameStore.dailyLevels" :key="lv.level"
                  class="level-card"
                  :class="{
                    active: gameStore.currentLevel === idx && !gameStore.dailyCompleted,
                    passed: gameStore.levelScores[idx] >= lv.pass_score,
                    failed: gameStore.levelScores[idx] !== undefined && gameStore.levelScores[idx] < lv.pass_score,
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
                    <el-tag v-if="gameStore.levelScores[idx] >= lv.pass_score" type="success">
                      {{ gameStore.levelScores[idx] }}分 通过 +20
                    </el-tag>
                    <template v-else-if="gameStore.levelScores[idx] !== undefined">
                      <el-tag type="danger">{{ gameStore.levelScores[idx] }}分 未通过</el-tag>
                    </template>
                    <template v-else-if="gameStore.currentLevel === idx && !gameStore.dailyCompleted">
                      <div v-if="gameStore.scoringLevel === idx" class="scoring-hint">
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
                    <el-tag v-else type="info">未解锁</el-tag>
                  </div>
                </div>
              </div>

              <div v-if="gameStore.dailyCompleted" class="complete-banner">
                <el-icon :size="28" color="var(--color-success)"><CircleCheckFilled /></el-icon>
                <span>全部通过！额外 +30 积分</span>
              </div>
            </template>
          </el-tab-pane>

          <!-- 配音挑战 -->
          <el-tab-pane label="配音挑战" name="dubbing">
            <div v-if="!selectedClip" class="dubbing-grid">
              <div v-for="clip in gameStore.dubbingContent" :key="clip.id" class="dubbing-card" @click="startDubbing(clip)">
                <h4>{{ clip.title }}</h4>
                <p class="dubbing-line">"{{ clip.subtitle }}"</p>
                <div class="dubbing-meta">
                  <el-tag size="small">{{ clip.difficulty === 'easy' ? '简单' : clip.difficulty === 'medium' ? '中等' : '困难' }}</el-tag>
                  <span>{{ clip.duration }}s</span>
                </div>
              </div>
              <el-empty v-if="gameStore.dubbingContent.length === 0 && !gameStore.dubbingLoading" description="暂无配音内容" style="grid-column: 1 / -1;" />
            </div>

            <div v-else class="dubbing-active">
              <div class="dubbing-content">
                <h3>{{ selectedClip.title }}</h3>
                <p class="dubbing-line-large">"{{ selectedClip.subtitle }}"</p>
                <el-tag size="small">
                  {{ selectedClip.difficulty === 'easy' ? '简单' : selectedClip.difficulty === 'medium' ? '中等' : '困难' }}
                </el-tag>
              </div>

              <div class="dubbing-record" v-if="!gameStore.dubbingResult && !gameStore.dubbingScoring">
                <VoiceRecorder
                  :prep-time="3"
                  :max-duration="20"
                  @complete="handleDubbingRecord"
                />
              </div>

              <div v-if="gameStore.dubbingScoring" class="scoring-hint" style="text-align:center; padding: var(--spacing-xxl);">
                <el-icon :size="32" class="is-loading"><Loading /></el-icon>
                <p style="margin-top: var(--spacing-md);">正在评分...</p>
              </div>

              <div v-if="gameStore.dubbingResult" class="dubbing-result">
                <div class="score-overall">
                  综合：<strong>{{ gameStore.dubbingResult.total_score }}</strong> 分
                  <span style="color: var(--color-success);">+{{ gameStore.dubbingResult.points_earned }}积分</span>
                </div>
                <ScoreBar label="发音相似度" :score="gameStore.dubbingResult.pronunciation_score" />
                <ScoreBar label="语调相似度" :score="gameStore.dubbingResult.intonation_score" />
                <ScoreBar label="情感匹配度" :score="gameStore.dubbingResult.emotion_score" />
                <el-button type="primary" @click="backToClipList" style="width:100%;margin-top:16px;">返回列表</el-button>
              </div>
            </div>
          </el-tab-pane>

          <!-- 勋章墙 -->
          <el-tab-pane label="勋章墙" name="badges">
            <div v-if="gameStore.badgesLoading" v-loading="gameStore.badgesLoading" style="min-height: 200px;" />
            <div v-else class="badge-grid">
              <div v-for="badge in gameStore.badges" :key="badge.badge_type" class="badge-card" :class="{ earned: badge.earned }">
                <el-icon :size="36" :color="badge.earned ? 'var(--color-warning)' : 'var(--color-text-disabled)'">
                  <Medal />
                </el-icon>
                <h4>{{ badge.badge_name }}</h4>
                <p>{{ badge.description }}</p>
                <el-tag v-if="badge.earned" type="warning" size="small">已获得</el-tag>
                <el-tag v-else type="info" size="small">未获得</el-tag>
              </div>
              <el-empty v-if="gameStore.badges.length === 0" description="暂无勋章数据" style="grid-column: 1 / -1;" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-tab-pane>
    </el-tabs>

    <!-- 评论弹窗 -->
    <el-dialog
      v-model="showCommentDialog"
      title="评论"
      width="500px"
      :close-on-click-modal="true"
      @close="commentDialogPost = null"
    >
      <template v-if="commentDialogPost">
        <h4 style="margin-bottom: 12px">{{ commentDialogPost.topic }}</h4>
        <div class="comment-list">
          <div v-if="comments.length === 0" class="empty-hint">暂无评论</div>
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <span class="comment-user">{{ c.username }}</span>
            <span class="comment-time">{{ c.created_at?.slice(0, 10) }}</span>
            <p class="comment-content">{{ c.content }}</p>
          </div>
        </div>
        <div class="comment-input-box">
          <el-input
            v-model="commentContent"
            placeholder="写评论..."
            @keyup.enter="handleAddComment"
          />
          <el-button type="primary" size="small" :disabled="!commentContent.trim()" @click="handleAddComment" style="margin-top: 8px">
            发表评论
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.empty-hint {
  text-align: center;
  color: var(--color-text-disabled);
  padding: var(--spacing-xl);
}

.challenge-selector {
  margin-bottom: var(--spacing-lg);
}

.challenge-hero {
  background: linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.08), rgba(var(--color-primary-rgb), 0.02));
  border: 1px solid rgba(var(--color-primary-rgb), 0.15);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: var(--spacing-xl);
  flex-wrap: wrap; gap: var(--spacing-md);
  h3 { margin: 0 0 var(--spacing-xs); }
  p { color: var(--color-text-secondary); font-size: var(--font-size-sm); margin: 0; }
  .challenge-desc { margin-bottom: 4px; }
  .challenge-sample { color: var(--color-primary); font-weight: 500; margin-bottom: 4px; }
}

.recorder-section {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}
.scoring-hint {
  text-align: center; margin-top: var(--spacing-md);
  color: var(--color-primary); font-weight: 500;
}
.submit-result {
  text-align: center; margin-top: var(--spacing-md);
}

.section-title { margin: var(--spacing-xl) 0 var(--spacing-lg); font-weight: 600; }

.ranking-list { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.ranking-item {
  display: flex; align-items: center; gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-primary);
  border-radius: var(--radius-sm);
}
.rank-badge {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  display: flex; align-items: center; justify-content: center;
  font-size: var(--font-size-sm); font-weight: 700; flex-shrink: 0;
}
.rank-body { flex: 1; }
.rank-user { font-weight: 600; }
.rank-right { text-align: right; }
.rank-score { font-size: 20px; font-weight: 800; color: var(--color-primary); display: block; }

.post-input-box {
  background: var(--color-bg-primary); border-radius: var(--radius-md);
  padding: var(--spacing-lg); margin-bottom: var(--spacing-lg);
  .post-footer { display: flex; justify-content: space-between; align-items: center; margin-top: var(--spacing-md); }
}
.discussion-list { display: flex; flex-direction: column; gap: var(--spacing-lg); }
.discussion-card {
  background: var(--color-bg-secondary); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: var(--spacing-lg);
}
.disc-header { display: flex; align-items: center; gap: var(--spacing-md); margin-bottom: var(--spacing-md); }
.disc-avatar {
  width: 40px; height: 40px; border-radius: 50%; background: var(--color-primary);
  color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700;
}
.disc-user { font-weight: 600; }
.disc-time { color: var(--color-text-disabled); font-size: 12px; }
.disc-topic { margin: 0 0 var(--spacing-sm); font-weight: 600; }
.disc-content { color: var(--color-text-secondary); line-height: 1.6; margin-bottom: var(--spacing-md); }
.disc-actions { display: flex; gap: var(--spacing-sm); border-top: 1px solid var(--color-border); padding-top: var(--spacing-md); }

.comment-list { max-height: 300px; overflow-y: auto; margin-bottom: var(--spacing-lg); }
.comment-item {
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border-light);
  .comment-user { font-weight: 600; font-size: var(--font-size-sm); }
  .comment-time { color: var(--color-text-disabled); font-size: 12px; margin-left: var(--spacing-sm); }
  .comment-content { margin: 4px 0 0; color: var(--color-text-secondary); font-size: var(--font-size-sm); }
}
.comment-input-box { margin-top: var(--spacing-md); }

/* ===== 闯关挑战样式 ===== */
.points-banner {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg); background: rgba(var(--color-warning-rgb), 0.08);
  border-radius: var(--radius-md); margin-bottom: var(--spacing-lg);
  strong { font-size: var(--font-size-xl); color: var(--color-warning); }
}

.level-list {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--spacing-md);
}

.level-card {
  display: flex; flex-direction: column; align-items: center; gap: var(--spacing-md);
  padding: var(--spacing-lg); border: 2px solid var(--color-border); border-radius: var(--radius-md);
  text-align: center; transition: border-color 0.2s;
  &.active { border-color: var(--color-primary); }
  &.passed { border-color: var(--color-success); background: rgba(var(--color-success-rgb), 0.04); }
  &.failed { border-color: var(--color-danger); }
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

.scoring-hint {
  display: flex; align-items: center; gap: var(--spacing-xs); color: var(--color-text-secondary);
}

.complete-banner {
  display: flex; align-items: center; justify-content: center; gap: var(--spacing-sm);
  padding: var(--spacing-lg); margin-top: var(--spacing-lg);
  background: rgba(var(--color-success-rgb), 0.08); border-radius: var(--radius-md);
  font-weight: 600; color: var(--color-success);
}

.dubbing-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-base);
}

.dubbing-card {
  padding: var(--spacing-xl); background: var(--color-bg-primary); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); cursor: pointer;
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

.badge-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-base);
}

.badge-card {
  text-align: center; padding: var(--spacing-xl); background: var(--color-bg-primary);
  border: 1px solid var(--color-border); border-radius: var(--radius-md);
  &.earned { border-color: var(--color-warning); }
  h4 { margin: var(--spacing-sm) 0 var(--spacing-xs); font-size: var(--font-size-sm); }
  p { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--spacing-md); }
}
</style>