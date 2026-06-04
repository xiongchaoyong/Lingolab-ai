<script setup>
import { ref, computed, nextTick } from 'vue'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'
import DimensionBars from '@/components/common/DimensionBars.vue'

const ROLES = [
  { id: 1, title: '面试者', aiRole: '面试官', icon: 'User', desc: '英文工作面试模拟', color: '#4F46E5',
    topics: '自我介绍/项目经历/职业规划/优缺点' },
  { id: 2, title: '服务员', aiRole: '顾客', icon: 'DishDot', desc: '餐厅服务场景', color: '#059669',
    topics: '迎宾/推荐菜品/处理忌口/结账' },
  { id: 3, title: '导游', aiRole: '游客', icon: 'MapLocation', desc: '景点导览场景', color: '#D97706',
    topics: '景点介绍/交通指引/餐饮推荐' },
]

const selectedRole = ref(null)
const messages = ref([])
const showScoreDialog = ref(false)
const chatRef = ref(null)

// 模拟对话
const MOCK_DIALOGUES = {
  1: [
    { role: 'ai', text: "Good morning! Thank you for coming in today. Could you start by telling me a bit about yourself?" },
    { role: 'user', text: "Good morning! My name is David, and I'm a software engineer with 5 years of experience." },
    { role: 'ai', text: "That's impressive. Can you tell me about a challenging project you've worked on?" },
    { role: 'user', text: "Sure. I led a team that built a real-time data processing platform for our clients." },
    { role: 'ai', text: "Great. Where do you see yourself in five years?" },
    { role: 'user', text: "I hope to grow into a technical lead role and mentor junior engineers." },
  ],
  2: [
    { role: 'ai', text: "Hi, table for two please." },
    { role: 'user', text: "Welcome! Right this way. Here are your menus." },
    { role: 'ai', text: "What would you recommend from the menu?" },
    { role: 'user', text: "Our chef's special today is grilled salmon with seasonal vegetables." },
  ],
  3: [
    { role: 'ai', text: "Excuse me, can you tell us about the history of this temple?" },
    { role: 'user', text: "Of course! This temple was built over 500 years ago during the Ming Dynasty." },
    { role: 'ai', text: "That's fascinating! Are there any special customs we should know before entering?" },
    { role: 'user', text: "Yes, please remove your shoes before entering the main hall." },
  ],
}

function selectRole(role) {
  selectedRole.value = role
  messages.value = []
  setTimeout(() => {
    messages.value.push({ role: 'ai', text: MOCK_DIALOGUES[role.id][0].text, _idx: 0 })
    scrollToBottom()
  }, 300)
}

function handleUserSpeech() {
  const dialogue = MOCK_DIALOGUES[selectedRole.value.id]
  const userCount = messages.value.filter(m => m.role === 'user').length
  const nextUser = dialogue.filter(m => m.role === 'user')[userCount]
  if (nextUser) {
    messages.value.push({ role: 'user', text: nextUser.text })
    scrollToBottom()
    setTimeout(() => {
      const nextAi = dialogue.filter(m => m.role === 'ai')[userCount + 1]
      if (nextAi) messages.value.push({ role: 'ai', text: nextAi.text })
      const totalUserMsgs = dialogue.filter(m => m.role === 'user').length
      if (userCount + 1 >= totalUserMsgs) {
        setTimeout(() => { showScoreDialog.value = true }, 500)
      }
      scrollToBottom()
    }, 500)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight
  })
}

const mockScore = computed(() => ({
  overall: randomScore(60, 88),
  dimensions: [
    { label: '角色贴合度', score: randomScore(60, 92) },
    { label: '场景礼仪', score: randomScore(55, 88) },
    { label: '专业术语', score: randomScore(50, 90) },
    { label: '应对能力', score: randomScore(55, 85) },
  ],
}))

function randomScore(min, max) { return Math.round(min + Math.random() * (max - min)) }
</script>

<template>
  <div class="content-card">
    <template v-if="!selectedRole">
      <h2 class="page-title">情景角色扮演</h2>
      <p class="page-subtitle">选择角色，AI 扮演对方与你进行场景对话</p>
      <el-row :gutter="16">
        <el-col :span="8" v-for="role in ROLES" :key="role.id">
          <div class="role-card" :style="{ borderTopColor: role.color }" @click="selectRole(role)">
            <el-icon :size="32" :color="role.color"><component :is="role.icon" /></el-icon>
            <h4>{{ role.title }}</h4>
            <p>AI: {{ role.aiRole }}</p>
            <p class="role-desc">{{ role.desc }}</p>
            <el-tag size="small">{{ role.topics }}</el-tag>
          </div>
        </el-col>
      </el-row>
    </template>

    <template v-else>
      <div class="chat-header">
        <el-button text @click="selectedRole = null"><el-icon><ArrowLeft /></el-icon> 切换角色</el-button>
        <span class="chat-title">{{ selectedRole.title }} ← → {{ selectedRole.aiRole }}</span>
        <el-button text type="danger" @click="showScoreDialog = true">结束</el-button>
      </div>

      <div class="chat-messages" ref="chatRef">
        <div v-for="(msg, i) in messages" :key="i" :class="['bubble-row', msg.role]">
          <div class="bubble" :class="msg.role">
            <div class="bubble-avatar">
              <el-icon><component :is="msg.role === 'ai' ? 'Service' : 'UserFilled'" /></el-icon>
            </div>
            <div class="bubble-text">{{ msg.text }}</div>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <el-button type="primary" :icon="Microphone" circle size="large" @click="handleUserSpeech" />
        <span class="input-hint">点击模拟用户发言</span>
      </div>
    </template>

    <el-dialog v-model="showScoreDialog" title="角色扮演评分" width="420px">
      <div class="score-overall" :style="{ color: mockScore.overall >= 80 ? 'var(--color-success)' : 'var(--color-warning)' }">
        <span class="score-num">{{ mockScore.overall }}</span><span>分</span>
      </div>
      <DimensionBars :dimensions="mockScore.dimensions" />
      <template #footer>
        <el-button @click="showScoreDialog = false; selectedRole = null">返回</el-button>
        <el-button type="primary" @click="showScoreDialog = false; selectRole(selectedRole)">再来一次</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.role-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-top: 3px solid;
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
  h4 { margin: var(--spacing-md) 0 var(--spacing-xs); }
  p { color: var(--color-text-secondary); font-size: var(--font-size-sm); }
  .role-desc { margin-bottom: var(--spacing-md); }
}

.chat-header {
  display: flex; align-items: center; justify-content: space-between;
  padding-bottom: var(--spacing-lg); border-bottom: 1px solid var(--color-border); margin-bottom: var(--spacing-lg);
  .chat-title { font-weight: 600; }
}
.chat-messages {
  height: 360px; overflow-y: auto; display: flex; flex-direction: column; gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}
.bubble-row { display: flex;
  &.ai { justify-content: flex-start; }
  &.user { justify-content: flex-end; }
}
.bubble { display: flex; gap: var(--spacing-sm); max-width: 65%;
  .bubble-avatar {
    width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  &.ai .bubble-avatar { background: rgba(var(--color-primary-rgb), 0.1); color: var(--color-primary); }
  &.user .bubble-avatar { background: rgba(var(--color-success-rgb), 0.1); color: var(--color-success); }
  .bubble-text {
    padding: var(--spacing-md); border-radius: var(--radius-md); font-size: var(--font-size-base); line-height: 1.5;
  }
  &.ai .bubble-text { background: var(--color-bg-primary); border: 1px solid var(--color-border); }
  &.user .bubble-text { background: var(--color-primary); color: #fff; }
}
.chat-input { display: flex; flex-direction: column; align-items: center; gap: var(--spacing-sm);
  .input-hint { color: var(--color-text-disabled); font-size: var(--font-size-sm); }
}
.score-overall { text-align: center; font-size: 40px; font-weight: 800; margin-bottom: var(--spacing-xl);
  .score-num { font-size: 56px; }
}
</style>
