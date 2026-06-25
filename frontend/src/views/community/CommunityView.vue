<script setup>
import { ref, onMounted } from 'vue'
import { Microphone, Star, ChatLineRound, Picture, UserFilled, Clock } from '@element-plus/icons-vue'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'
import { useCommunityStore } from '@/stores/community'

const store = useCommunityStore()

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

onMounted(() => {
  store.fetchChallenges()
  store.fetchPosts()
  store.fetchGroups()
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

// ===== 学习小组 =====

async function handleToggleGroup(group) {
  await store.toggleGroup(group.id)
}

// ===== 排行榜颜色 =====
const rankColors = { 1: '#FFD700', 2: '#C0C0C0', 3: '#CD7F32' }
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">学习社区</h2>

    <el-tabs v-model="activeTab">
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

      <!-- ======================================== 学习小组 -->
      <el-tab-pane label="学习小组" name="groups">
        <div v-if="store.groups.length === 0 && !store.groupsLoading" class="empty-hint">
          暂无学习小组
        </div>
        <el-row v-else :gutter="16">
          <el-col :span="12" v-for="group in store.groups" :key="group.id">
            <div class="group-card" :class="{ joined: group.is_joined }">
              <div class="group-header">
                <h4>{{ group.name }}</h4>
                <el-tag size="small" :type="group.is_joined ? 'success' : 'info'">
                  {{ group.is_joined ? '已加入' : '开放' }}
                </el-tag>
              </div>
              <div class="group-body">
                <div class="group-stat"><el-icon><UserFilled /></el-icon> {{ group.member_count }} 人</div>
                <div class="group-stat"><el-icon><Clock /></el-icon> {{ group.schedule }}</div>
                <div class="group-stat">
                  <el-tag size="small" type="warning">{{ group.level }}</el-tag>
                  <el-tag v-for="t in group.tags" :key="t" size="small" effect="plain" style="margin-left:4px">{{ t }}</el-tag>
                </div>
              </div>
              <el-button
                :type="group.is_joined ? 'default' : 'primary'"
                size="small"
                @click="handleToggleGroup(group)"
              >
                {{ group.is_joined ? '退出小组' : '加入小组' }}
              </el-button>
            </div>
          </el-col>
        </el-row>
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

.group-card {
  background: var(--color-bg-secondary); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: var(--spacing-xl);
  margin-bottom: var(--spacing-lg);
  &.joined { border-color: rgba(var(--color-success-rgb), 0.3); }
  .group-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-md);
    h4 { margin: 0; }
  }
  .group-body { display: flex; flex-direction: column; gap: var(--spacing-sm); margin-bottom: var(--spacing-md); }
  .group-stat { font-size: var(--font-size-sm); color: var(--color-text-secondary); display: flex; align-items: center; gap: var(--spacing-xs); }
}

.comment-list { max-height: 300px; overflow-y: auto; margin-bottom: var(--spacing-lg); }
.comment-item {
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border-light);
  .comment-user { font-weight: 600; font-size: var(--font-size-sm); }
  .comment-time { color: var(--color-text-disabled); font-size: 12px; margin-left: var(--spacing-sm); }
  .comment-content { margin: 4px 0 0; color: var(--color-text-secondary); font-size: var(--font-size-sm); }
}
.comment-input-box { margin-top: var(--spacing-md); }
</style>