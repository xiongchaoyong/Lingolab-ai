<script setup>
import { ref } from 'vue'

const activeTab = ref('challenge')

const voiceRanking = ref([
  { rank: 1, user: 'Alice', score: 98, topic: 'Tongue Twister Challenge', date: '6月3日' },
  { rank: 2, user: 'Bob', score: 95, topic: 'Shadow Reading - BBC News', date: '6月3日' },
  { rank: 3, user: 'Charlie', score: 92, topic: 'Poem Recitation', date: '6月2日' },
  { rank: 4, user: 'David', score: 89, topic: 'Impromptu Speech', date: '6月1日' },
  { rank: 5, user: 'Eve', score: 87, topic: 'Daily Phrase Challenge', date: '6月3日' },
])

const currentChallenge = ref({ title: 'Tongue Twister Challenge', deadline: '6月5日 23:59', participants: 28 })

const discussions = ref([
  {
    id: 1, user: 'Alice', avatar: 'A', topic: 'What is the best way to improve English speaking fluency?',
    content: "I think the key is consistent practice every day. Even 15 minutes of speaking out loud makes a huge difference.",
    grammarNotes: [{ word: 'consistent', tag: 'adj.', correct: true }, { word: 'practice', tag: 'n.', correct: true }],
    likes: 24, replies: 8, time: '2小时前',
  },
  {
    id: 2, user: 'Bob', avatar: 'B', topic: 'Tips for reducing accent in English?',
    content: 'Shadow reading has been the most effective method for me. I listen to BBC podcasts and repeat after the speaker.',
    grammarNotes: [{ word: 'Shadow reading', tag: 'n. phrase', correct: true }, { word: 'effective', tag: 'adj.', correct: true }],
    likes: 18, replies: 5, time: '5小时前',
  },
  {
    id: 3, user: 'Teacher_Wang', avatar: 'W', topic: 'How to prepare for IELTS speaking test?',
    content: 'Focus on coherence and fluency first. Many students worry too much about vocabulary but forget about natural flow.',
    grammarNotes: [{ word: 'coherence', tag: 'n.', correct: true }, { word: 'fluency', tag: 'n.', correct: true }],
    likes: 42, replies: 15, time: '1天前',
  },
])

const newPost = ref('')

function addPost() {
  if (!newPost.value.trim()) return
  discussions.value.unshift({
    id: Date.now(), user: '我', avatar: '我',
    topic: newPost.value.slice(0, 30) + (newPost.value.length > 30 ? '...' : ''),
    content: newPost.value,
    grammarNotes: [],
    likes: 0, replies: 0, time: '刚刚',
  })
  newPost.value = ''
}

const studyGroups = ref([
  { id: 1, name: 'Daily Speaking Club', members: 128, level: 'B1+', schedule: '每天晚上 20:00', tags: ['口语', '日常'], joined: true },
  { id: 2, name: 'IELTS Prep Squad', members: 86, level: 'B2+', schedule: '周二/周四 19:30', tags: ['雅思', '备考'], joined: false },
  { id: 3, name: 'Pronunciation Lab', members: 56, level: 'A2+', schedule: '周一/三/五 18:00', tags: ['发音', '纠音'], joined: false },
  { id: 4, name: 'Business English', members: 45, level: 'B2+', schedule: '周六 10:00', tags: ['商务', '职场'], joined: true },
])

function toggleGroup(group) {
  group.joined = !group.joined
}

const rankColors = { 1: '#FFD700', 2: '#C0C0C0', 3: '#CD7F32' }
</script>

<template>
  <div class="content-card">
    <h2 class="page-title">学习社区</h2>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="语音挑战" name="challenge">
        <div class="challenge-hero">
          <div class="challenge-info">
            <h3>{{ currentChallenge.title }}</h3>
            <p>截止时间：{{ currentChallenge.deadline }} | {{ currentChallenge.participants }} 人参与</p>
          </div>
          <el-button type="primary" :icon="Microphone">立即参与</el-button>
        </div>

        <h4 class="section-title">排行榜</h4>
        <div class="ranking-list">
          <div v-for="item in voiceRanking" :key="item.rank" class="ranking-item">
            <div class="rank-badge" :style="item.rank <= 3 ? { background: rankColors[item.rank], color: '#fff' } : {}">
              {{ item.rank }}
            </div>
            <div class="rank-body">
              <span class="rank-user">{{ item.user }}</span>
              <span class="rank-topic">{{ item.topic }}</span>
            </div>
            <div class="rank-right">
              <span class="rank-score">{{ item.score }}</span>
              <span class="rank-date">{{ item.date }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="话题讨论" name="discussion">
        <div class="post-input-box">
          <el-input v-model="newPost" type="textarea" :rows="3" placeholder="分享你的英语学习心得或提问..." />
          <div class="post-footer">
            <el-button text :icon="Picture" size="small">图片</el-button>
            <el-button type="primary" :disabled="!newPost.trim()" @click="addPost">发布</el-button>
          </div>
        </div>

        <div class="discussion-list">
          <div v-for="d in discussions" :key="d.id" class="discussion-card">
            <div class="disc-header">
              <div class="disc-avatar">{{ d.avatar }}</div>
              <div>
                <div class="disc-user">{{ d.user }}</div>
                <div class="disc-time">{{ d.time }}</div>
              </div>
            </div>
            <h4 class="disc-topic">{{ d.topic }}</h4>
            <p class="disc-content">{{ d.content }}</p>
            <div v-if="d.grammarNotes.length" class="grammar-tags">
              <el-tag v-for="gn in d.grammarNotes" :key="gn.word" size="small" effect="plain">
                {{ gn.word }} <span :style="{ color: gn.correct ? 'var(--color-success)' : 'var(--color-danger)' }">{{ gn.tag }}</span>
              </el-tag>
            </div>
            <div class="disc-actions">
              <el-button text :icon="Star" size="small">{{ d.likes }}</el-button>
              <el-button text :icon="ChatLineRound" size="small">{{ d.replies }}</el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="学习小组" name="groups">
        <el-row :gutter="16">
          <el-col :span="12" v-for="group in studyGroups" :key="group.id">
            <div class="group-card" :class="{ joined: group.joined }">
              <div class="group-header">
                <h4>{{ group.name }}</h4>
                <el-tag size="small" :type="group.joined ? 'success' : 'info'">{{ group.joined ? '已加入' : '开放' }}</el-tag>
              </div>
              <div class="group-body">
                <div class="group-stat"><el-icon><UserFilled /></el-icon> {{ group.members }} 人</div>
                <div class="group-stat"><el-icon><Clock /></el-icon> {{ group.schedule }}</div>
                <div class="group-stat">
                  <el-tag size="small" type="warning">{{ group.level }}</el-tag>
                  <el-tag v-for="t in group.tags" :key="t" size="small" effect="plain" style="margin-left:4px">{{ t }}</el-tag>
                </div>
              </div>
              <el-button :type="group.joined ? 'default' : 'primary'" size="small" @click="toggleGroup(group)">
                {{ group.joined ? '退出小组' : '加入小组' }}
              </el-button>
            </div>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style lang="scss" scoped>
.challenge-hero {
  background: linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.08), rgba(var(--color-primary-rgb), 0.02));
  border: 1px solid rgba(var(--color-primary-rgb), 0.15);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: var(--spacing-xl);
  h3 { margin: 0 0 var(--spacing-xs); }
  p { color: var(--color-text-secondary); font-size: var(--font-size-sm); margin: 0; }
}

.section-title { margin-bottom: var(--spacing-lg); font-weight: 600; }

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
.rank-user { font-weight: 600; margin-right: var(--spacing-md); }
.rank-topic { color: var(--color-text-secondary); font-size: var(--font-size-sm); }
.rank-right { text-align: right; }
.rank-score { font-size: 20px; font-weight: 800; color: var(--color-primary); display: block; }
.rank-date { color: var(--color-text-disabled); font-size: 12px; }

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
.grammar-tags { display: flex; gap: var(--spacing-xs); flex-wrap: wrap; margin-bottom: var(--spacing-md); }
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
</style>
