<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'
import DimensionBars from '@/components/common/DimensionBars.vue'

// ========== Mock 数据 ==========

const SCENARIOS = [
  { id: 1, title: '自我介绍', icon: 'User', desc: '姓名/职业/兴趣/家庭介绍', level: 'A1-B1', color: '#4F46E5' },
  { id: 2, title: '问路指路', icon: 'MapLocation', desc: '地铁/公交/地址方向指引', level: 'A2-B2', color: '#059669' },
  { id: 3, title: '购物', icon: 'ShoppingCart', desc: '商品询价/尺码/颜色', level: 'A2-B2', color: '#D97706' },
  { id: 4, title: '餐厅', icon: 'DishDot', desc: '预定/点餐/忌口/结账', level: 'A1-B2', color: '#DC2626' },
]

const MOCK_CONVERSATIONS = {
  1: [
    { role: 'ai', text: "Hello! My name is Alex. What's your name?", grammar: null },
    { role: 'user', text: "Hi Alex, I'm David. Nice to meet you!" },
    { role: 'ai', text: 'Nice to meet you too, David! Where are you from?', grammar: null },
    { role: 'user', text: "I'm from China. I come from Beijing." },
    { role: 'ai', text: "Beijing is a beautiful city! What do you do for work?", grammar: null },
    { role: 'user', text: 'I am a software engineer. I work at a tech company.' },
    { role: 'ai', text: "That's interesting! Do you have any hobbies?", grammar: null },
    { role: 'user', text: 'Yes, I like playing basketball and reading books.' },
  ],
  2: [
    { role: 'ai', text: 'Excuse me, could you tell me how to get to the nearest subway station?', grammar: null },
    { role: 'user', text: 'Sure! Go straight ahead for about 200 meters, then turn left.' },
    { role: 'ai', text: 'So go straight and then turn left? Is it far from here?', grammar: null },
    { role: 'user', text: "No, it's not far. About 5 minutes walk." },
    { role: 'ai', text: 'Thank you very much! Is there a bus stop nearby as well?', grammar: null },
    { role: 'user', text: 'Yes, the bus stop is right next to the subway entrance.' },
  ],
  3: [
    { role: 'ai', text: 'Welcome! How can I help you today?', grammar: null },
    { role: 'user', text: 'I am looking for a jacket. Do you have any in blue?' },
    { role: 'ai', text: 'Yes, we have several styles in blue. What size are you looking for?', grammar: null },
    { role: 'user', text: 'Medium size. Also, how much is this one?' },
    { role: 'ai', text: 'That one is $89.99. We have a 20% discount today! Would you like to try it on?', grammar: null },
    { role: 'user', text: "Yes, please. Also, do you accept returns if it doesn't fit?" },
  ],
  4: [
    { role: 'ai', text: 'Good evening! Do you have a reservation?', grammar: null },
    { role: 'user', text: 'No, I do not have a reservation. Do you have a table for two?' },
    { role: 'ai', text: 'Let me check... Yes, we have a table by the window. Follow me please.', grammar: null },
    { role: 'user', text: "Thank you. Can I see the menu, please?" },
    { role: 'ai', text: 'Here is the menu. Our special today is grilled salmon. Would you like to order drinks first?', grammar: null },
    { role: 'user', text: 'I will have a glass of water and the grilled salmon, please.' },
  ],
}

// ========== 状态 ==========

const selectedScenario = ref(null)
const messages = ref([])
const currentRound = ref(0)
const recorderRef = ref(null)
const chatContainer = ref(null)
const showScoreDialog = ref(false)
const isRecording = ref(false)

const conversationProgress = computed(() => {
  if (!selectedScenario.value) return null
  const script = MOCK_CONVERSATIONS[selectedScenario.value.id]
  const userMsgs = messages.value.filter(m => m.role === 'user').length
  const total = script.filter(m => m.role === 'user').length
  return { current: userMsgs, total }
})

// ========== 方法 ==========

function selectScenario(scenario) {
  selectedScenario.value = scenario
  messages.value = []
  currentRound.value = 0
  // AI 开场白
  setTimeout(() => addAiMessage(), 300)
}

function addAiMessage() {
  const script = MOCK_CONVERSATIONS[selectedScenario.value.id]
  const msg = script.find((m, i) => m.role === 'ai' && !messages.value.some(
    existing => existing._index === i
  ))
  if (msg) {
    const aiMsgs = script.filter((m, i) => m.role === 'ai' && i <= script.indexOf(msg))
    msg._index = script.indexOf(msg)
    messages.value.push({ ...msg })
    currentRound.value = messages.value.filter(m => m.role === 'user').length
    scrollToBottom()
  }
}

function handleRecordComplete() {
  isRecording.value = false
  const script = MOCK_CONVERSATIONS[selectedScenario.value.id]
  const userMsgs = messages.value.filter(m => m.role === 'user').length
  const scriptUserMsgs = script.filter(m => m.role === 'user')

  if (userMsgs < scriptUserMsgs.length) {
    // 添加用户消息
    const userMsg = scriptUserMsgs[userMsgs]
    userMsg._index = script.indexOf(userMsg)
    messages.value.push({ ...userMsg })

    // 添加语法标注
    if (userMsgs === 3) {
      messages.value[messages.value.length - 1].grammar = {
        original: 'I like play basketball',
        correction: 'I like playing basketball',
        tip: 'like 后接动名词 (playing) 或不定式 (to play)',
      }
    }

    scrollToBottom()

    // 延迟添加 AI 回复
    setTimeout(() => {
      const aiReply = script.find((m, i) => m.role === 'ai' && i > userMsg._index && !messages.value.some(e => e._index === i))
      if (aiReply) {
        aiReply._index = script.indexOf(aiReply)
        messages.value.push({ ...aiReply })
        currentRound.value = messages.value.filter(m => m.role === 'user').length
        scrollToBottom()
      }

      // 对话结束
      const remainingUser = scriptUserMsgs.length - (userMsgs + 1)
      if (remainingUser <= 0) {
        setTimeout(() => { showScoreDialog.value = true }, 500)
      }
    }, 600)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function handleEndConversation() {
  showScoreDialog.value = true
}

const mockScore = computed(() => ({
  overall: randomScore(60, 90),
  dimensions: [
    { label: '发音准确率', score: randomScore(60, 92) },
    { label: '语法正确率', score: randomScore(55, 90) },
    { label: '词汇丰富度', score: randomScore(50, 88) },
    { label: '对话参与度', score: randomScore(60, 95) },
  ],
}))

function closeScoreDialog() {
  showScoreDialog.value = false
}

function restartConversation() {
  showScoreDialog.value = false
  const scenario = selectedScenario.value
  selectedScenario.value = null
  setTimeout(() => selectScenario(scenario), 100)
}

function goBackToScenarios() {
  showScoreDialog.value = false
  selectedScenario.value = null
  messages.value = []
}

function getScoreColor(score) {
  if (score >= 80) return 'var(--color-success)'
  if (score >= 60) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

function randomScore(min, max) {
  return Math.round(min + Math.random() * (max - min))
}

function getDifficultyLabel() {
  return 'B1' // mock
}
</script>

<template>
  <div class="content-card conversation-page">
    <!-- 场景选择模式 -->
    <template v-if="!selectedScenario">
      <h2 class="page-title">AI 智能对话</h2>
      <p class="page-subtitle">选择一个场景，开始沉浸式英语对话练习</p>

      <el-row :gutter="16" class="scenario-grid">
        <el-col :span="12" v-for="scene in SCENARIOS" :key="scene.id">
          <div
            class="scenario-card"
            :style="{ borderTopColor: scene.color }"
            @click="selectScenario(scene)"
          >
            <div class="scenario-icon" :style="{ color: scene.color }">
              <el-icon :size="28"><component :is="scene.icon" /></el-icon>
            </div>
            <h4>{{ scene.title }}</h4>
            <p class="scenario-desc">{{ scene.desc }}</p>
            <el-tag size="small" effect="plain">{{ scene.level }}</el-tag>
          </div>
        </el-col>
      </el-row>
    </template>

    <!-- 对话模式 -->
    <template v-else>
      <!-- 顶栏 -->
      <div class="chat-header">
        <el-button text @click="goBackToScenarios">
          <el-icon><ArrowLeft /></el-icon> 切换场景
        </el-button>
        <div class="chat-header-info">
          <span class="chat-scene-title">{{ selectedScenario.title }}</span>
          <el-tag size="small" effect="plain">{{ selectedScenario.level }}</el-tag>
        </div>
        <el-button text type="danger" @click="handleEndConversation" :disabled="messages.length < 2">
          结束对话
        </el-button>
      </div>

      <!-- 对话区域 -->
      <div class="chat-messages" ref="chatContainer">
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="chat-bubble-row"
          :class="msg.role === 'ai' ? 'ai-row' : 'user-row'"
        >
          <!-- AI 气泡 -->
          <div v-if="msg.role === 'ai'" class="bubble ai-bubble">
            <div class="bubble-avatar">
              <el-icon :size="20"><Service /></el-icon>
            </div>
            <div class="bubble-content">
              <div class="bubble-text">{{ msg.text }}</div>
              <div class="bubble-actions">
                <el-button text size="small" type="primary">
                  <el-icon><VideoPlay /></el-icon> 播放语音
                </el-button>
              </div>
              <div v-if="msg.grammar" class="grammar-note">
                <el-icon><WarningFilled /></el-icon>
                语法建议：无错误
              </div>
            </div>
          </div>

          <!-- 用户气泡 -->
          <div v-else class="bubble user-bubble">
            <div class="bubble-content">
              <div class="bubble-text">{{ msg.text }}</div>
              <div class="bubble-actions user-actions">
                <el-icon><Microphone /></el-icon>
                <span class="record-icon-label">语音输入</span>
              </div>
              <div v-if="msg.grammar" class="grammar-note error">
                <el-icon><WarningFilled /></el-icon>
                <div>
                  <div>{{ msg.grammar.original }} → {{ msg.grammar.correction }}</div>
                  <div class="grammar-tip">{{ msg.grammar.tip }}</div>
                </div>
              </div>
            </div>
            <div class="bubble-avatar user-avatar">
              <el-icon :size="20"><UserFilled /></el-icon>
            </div>
          </div>
        </div>

        <!-- 录音中状态 -->
        <div v-if="isRecording" class="chat-bubble-row ai-row">
          <div class="bubble ai-bubble">
            <div class="bubble-avatar">
              <el-icon :size="20"><Service /></el-icon>
            </div>
            <div class="bubble-content">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部输入栏 -->
      <div class="chat-input-bar">
        <div class="input-hint" v-if="!isRecording">
          <el-icon><Microphone /></el-icon>
          <span>点击录音开始说话</span>
        </div>
        <div class="recorder-wrapper" v-if="!isRecording">
          <el-button
            type="primary"
            :icon="Microphone"
            circle
            size="large"
            @click="isRecording = true"
          />
        </div>
        <div class="recorder-wrapper recording-active" v-if="isRecording">
          <VoiceRecorder
            ref="recorderRef"
            :prep-time="1"
            :max-duration="30"
            @complete="handleRecordComplete"
          />
        </div>

        <!-- 状态栏 -->
        <div class="chat-status-bar">
          <span>CEFR: {{ getDifficultyLabel() }}</span>
          <el-divider direction="vertical" />
          <span>难度自动调整中</span>
          <el-divider direction="vertical" />
          <span v-if="conversationProgress">
            第 {{ conversationProgress.current }} / {{ conversationProgress.total }} 轮
          </span>
        </div>
      </div>
    </template>

    <!-- 评分弹窗 -->
    <el-dialog
      v-model="showScoreDialog"
      title="本次对话评分"
      width="420px"
      :close-on-click-modal="false"
    >
      <div class="score-dialog-content">
        <div class="overall-score" :style="{ color: getScoreColor(mockScore.overall) }">
          <span class="overall-number">{{ mockScore.overall }}</span>
          <span class="overall-unit">分</span>
          <el-tag
            :type="mockScore.overall >= 80 ? 'success' : mockScore.overall >= 60 ? 'warning' : 'danger'"
            size="small"
          >
            {{ mockScore.overall >= 80 ? '优秀' : mockScore.overall >= 60 ? '良好' : '需加强' }}
          </el-tag>
        </div>

        <DimensionBars :dimensions="mockScore.dimensions" />
      </div>

      <template #footer>
        <el-button @click="restartConversation" type="primary">再来一次</el-button>
        <el-button @click="goBackToScenarios">返回首页</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.conversation-page {
  padding: 0;
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - var(--spacing-xl) * 2);
}

.page-subtitle {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
}

// 场景卡片
.scenario-grid {
  .scenario-card {
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-top: 3px solid;
    border-radius: var(--radius-md);
    padding: var(--spacing-xl);
    margin-bottom: var(--spacing-base);
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      box-shadow: var(--shadow-hover);
      transform: translateY(-2px);
    }

    .scenario-icon {
      margin-bottom: var(--spacing-md);
    }

    h4 {
      font-size: var(--font-size-base);
      font-weight: 600;
      margin-bottom: var(--spacing-xs);
    }

    .scenario-desc {
      font-size: var(--font-size-sm);
      color: var(--color-text-secondary);
      margin-bottom: var(--spacing-md);
    }
  }
}

// 对话头部
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-xl);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
}

.chat-header-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  .chat-scene-title {
    font-weight: 600;
    color: var(--color-text-primary);
  }
}

// 对话区域
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-xl);
  background: var(--color-bg-primary);
}

.chat-bubble-row {
  display: flex;
  margin-bottom: var(--spacing-lg);

  &.ai-row { justify-content: flex-start; }
  &.user-row { justify-content: flex-end; }
}

.bubble {
  display: flex;
  gap: var(--spacing-md);
  max-width: 70%;

  .bubble-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .bubble-content {
    .bubble-text {
      padding: var(--spacing-md) var(--spacing-lg);
      border-radius: var(--radius-md);
      line-height: 1.6;
      font-size: var(--font-size-base);
    }
  }
}

.ai-bubble {
  .bubble-avatar {
    background: rgba(var(--color-primary-rgb), 0.1);
    color: var(--color-primary);
  }
  .bubble-text {
    background: var(--color-bg-secondary);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
    border-top-left-radius: 4px;
  }
}

.user-bubble {
  .bubble-avatar {
    background: rgba(var(--color-success-rgb), 0.1);
    color: var(--color-success);
  }
  .bubble-text {
    background: var(--color-primary);
    color: #fff;
    border-top-right-radius: 4px;
  }
}

.bubble-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-xs);
  padding: 0 var(--spacing-xs);
}

.user-actions {
  justify-content: flex-end;
  color: rgba(255,255,255,0.7);
  font-size: var(--font-size-sm);

  .record-icon-label {
    font-size: var(--font-size-sm);
  }
}

// 语法标注
.grammar-note {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  background: rgba(var(--color-success-rgb), 0.08);
  color: var(--color-success);

  &.error {
    background: rgba(var(--color-warning-rgb), 0.08);
    color: var(--color-warning);
  }

  .grammar-tip {
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
    margin-top: 2px;
  }
}

// 打字动画
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: var(--spacing-md) var(--spacing-lg);

  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-text-disabled);
    animation: typing 1.4s infinite;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}

// 输入区域
.chat-input-bar {
  padding: var(--spacing-lg) var(--spacing-xl);
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
}

.input-hint {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--color-text-disabled);
  font-size: var(--font-size-sm);
}

.recorder-wrapper {
  display: flex;
  justify-content: center;
}

.chat-status-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-disabled);
  width: 100%;
}

// 评分弹窗
.score-dialog-content {
  .overall-score {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-xl);

    .overall-number {
      font-size: 48px;
      font-weight: 800;
      line-height: 1;
    }

    .overall-unit {
      font-size: var(--font-size-lg);
      margin-right: var(--spacing-sm);
    }
  }
}
</style>
