<script setup>
import { ref, nextTick, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { Promotion } from '@element-plus/icons-vue'
import { chatText, chatVoice, chatStream } from '@/api/help'

const authStore = useAuthStore()

// 功能介绍弹窗
const featureDialogVisible = ref(false)

const faqCategories = [
  {
    title: '账号相关',
    icon: 'User',
    questions: [
      { q: '如何注册账号？', a: '点击右上角「注册」按钮，输入用户名和密码即可完成注册。注册后建议完成水平测试，系统会为你推荐合适的学习内容。' },
      { q: '忘记密码怎么办？', a: '在登录页点击「忘记密码」，输入注册邮箱即可收到重置链接。如未收到邮件，请检查垃圾邮件箱。' },
      { q: '如何修改个人信息？', a: '点击右上角头像 → 个人设置，可修改昵称、头像、学习目标等信息。' },
    ],
  },
  {
    title: '学习功能',
    icon: 'Reading',
    questions: [
      { q: '发音评测是如何工作的？', a: '系统使用 Whisper 语音识别 + 自研评分算法，从准确度、流利度、完整度、重音、语调五个维度给出评分和纠音建议。' },
      { q: 'AI 对话支持哪些场景？', a: '目前支持餐厅点餐、酒店入住、机场值机、购物等生活场景，以及工作面试、商务会议等职场场景。' },
      { q: '学习路径是如何生成的？', a: '系统根据你的 CEFR 等级和薄弱维度，每天自动生成包含跟读、对话、语法、词汇四类任务的个性化学习路径。' },
    ],
  },
  {
    title: '技术问题',
    icon: 'SetUp',
    questions: [
      { q: '录音没有反应怎么办？', a: '请检查浏览器是否已授权麦克风权限。Chrome/Edge 浏览器点击地址栏左侧的锁图标 → 允许麦克风。建议使用最新版 Chrome 浏览器。' },
      { q: '页面加载缓慢或白屏？', a: '建议使用 Chrome 85+ 或 Edge 85+ 浏览器。请清理浏览器缓存后刷新重试，或尝试使用无痕模式。' },
      { q: '语音识别不准确？', a: '请在安静环境中使用，确保麦克风距离适中。如果口音较重，建议先使用单词模式练习基础发音。' },
    ],
  },
  {
    title: '会员与支付',
    icon: 'Wallet',
    questions: [
      { q: '免费版和付费版有什么区别？', a: '免费版每天可完成 3 次发音评测和 1 次 AI 对话。付费版不限次数，并开放角色扮演、配音挑战等高级功能。' },
      { q: '如何取消订阅？', a: '在个人设置 → 会员中心 → 管理订阅，可取消自动续费。已支付的费用不支持退款。' },
    ],
  },
]

const messages = ref([
  { role: 'ai', text: '你好！我是 Lingolab 智能客服小语，有什么可以帮你的？', time: '刚刚' },
])

const inputText = ref('')
const chatRef = ref(null)
const showQuickQuestions = ref(true)
const loading = ref(false)
const isRecording = ref(false)

// 语音录制
let mediaRecorder = null
let audioChunks = []
let stream = null

const quickQuestions = [
  '如何练习发音？', '口语水平怎么提升？', '学习路径如何调整？',
  '怎么查看学习报告？', '如何加入学习小组？', '反馈建议在哪里提交？',
]

function getHistory() {
  return messages.value
    .filter(m => m.role === 'user' || m.role === 'ai')
    .slice(-12)
    .map(m => ({ role: m.role === 'ai' ? 'ai' : 'user', text: m.text }))
}

function selectFaq(faq) {
  messages.value.push({ role: 'user', text: faq.q, time: formatTime() })
  showQuickQuestions.value = false
  scrollToBottom()
  // FAQ 使用预置答案，不调 API
  setTimeout(() => {
    messages.value.push({ role: 'ai', text: faq.a, time: formatTime() })
    scrollToBottom()
  }, 400)
}

async function selectQuick(q) {
  messages.value.push({ role: 'user', text: q, time: formatTime() })
  showQuickQuestions.value = false
  scrollToBottom()
  await callChatAPI(q)
}

async function sendMessage() {
  if (!inputText.value.trim() || loading.value) return
  const text = inputText.value.trim()
  messages.value.push({ role: 'user', text, time: formatTime() })
  inputText.value = ''
  showQuickQuestions.value = false
  scrollToBottom()
  await callChatAPI(text)
}

async function callChatAPI(message) {
  loading.value = true
  scrollToBottom()

  try {
    const history = getHistory().slice(0, -1)
    const response = await chatStream(message, history)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let aiMsg = null

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue
          try {
            const parsed = JSON.parse(data)
            if (parsed.content) {
              // 第一个 token 到达时创建消息气泡，loading 变为 false 隐藏打字动画
              if (!aiMsg) {
                loading.value = false
                messages.value.push({ role: 'ai', text: '', time: formatTime() })
                aiMsg = messages.value[messages.value.length - 1]
              }
              aiMsg.text += parsed.content
              scrollToBottom()
            }
          } catch { /* ignore parse errors */ }
        }
      }
    }
  } catch (e) {
    console.error('客服流式 API 调用失败:', e)
    loading.value = false
    messages.value.push({
      role: 'ai',
      text: '抱歉，我暂时无法处理你的问题。请稍后重试。',
      time: formatTime(),
    })
  } finally {
    loading.value = false
  }
}

async function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

async function startRecording() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { sampleRate: 16000, channelCount: 1 },
    })
  } catch (e) {
    console.error('麦克风访问失败:', e)
    return
  }

  isRecording.value = true
  audioChunks = []
  mediaRecorder = new MediaRecorder(stream)

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) audioChunks.push(e.data)
  }

  mediaRecorder.onstop = async () => {
    stream.getTracks().forEach(t => t.stop())
    const mimeType = mediaRecorder.mimeType || 'audio/webm'
    const blob = new Blob(audioChunks, { type: mimeType })
    await sendVoiceMessage(blob)
  }

  mediaRecorder.start()
}

function stopRecording() {
  isRecording.value = false
  if (mediaRecorder?.state === 'recording') {
    mediaRecorder.stop()
  }
}

async function sendVoiceMessage(blob) {
  loading.value = true
  showQuickQuestions.value = false
  try {
    const history = getHistory()
    const res = await chatVoice(blob, history)
    const data = res.data || res
    const transcript = data.transcript || ''
    const reply = data.reply || '未能识别你的语音，请用文字输入问题。'

    if (transcript) {
      messages.value.push({
        role: 'user',
        text: transcript,
        time: formatTime(),
      })
    }

    messages.value.push({
      role: 'ai',
      text: reply,
      time: formatTime(),
    })
  } catch (e) {
    console.error('语音客服失败:', e)
    messages.value.push({
      role: 'ai',
      text: '语音识别失败，请用文字输入问题或重试。',
      time: formatTime(),
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function handleEnter(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight
  })
}

function formatTime() {
  const now = new Date()
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
}

onUnmounted(() => {
  stream?.getTracks().forEach(t => t.stop())
})
</script>

<template>
  <div class="help-layout">
    <!-- 左侧FAQ面板 -->
    <div class="faq-panel">
      <h2 class="page-title">帮助中心</h2>
      <div v-for="cat in faqCategories" :key="cat.title" class="faq-category">
        <h4 class="faq-cat-title">
          <el-icon><component :is="cat.icon" /></el-icon>
          {{ cat.title }}
        </h4>
        <div
          v-for="faq in cat.questions"
          :key="faq.q"
          class="faq-item"
          @click="selectFaq(faq)"
        >
          {{ faq.q }}
        </div>
      </div>
    </div>

    <!-- 右侧聊天面板 -->
    <div class="chat-panel">
      <div class="chat-header">
        <div class="chat-agent-info">
          <div class="agent-avatar">
            <el-icon :size="24"><Service /></el-icon>
          </div>
          <div>
            <div class="agent-name">智能客服 · 小语</div>
            <div class="agent-status">在线 | AI 驱动</div>
          </div>
        </div>
        <div class="chat-header-right">
          <el-button circle :icon="QuestionFilled" @click="featureDialogVisible = true" />
          <el-tag size="small" type="success">AI 客服</el-tag>
        </div>
      </div>

      <div class="chat-messages" ref="chatRef">
        <div v-for="(msg, i) in messages" :key="i" :class="['msg-row', msg.role]">
          <div class="msg-avatar">
            <el-icon v-if="msg.role === 'ai'" :size="18"><Service /></el-icon>
            <el-avatar v-else :size="28" :src="authStore.userInfo?.avatar" icon="UserFilled" />
          </div>
          <div class="msg-bubble" :class="msg.role">
            <div class="msg-text">{{ msg.text }}</div>
            <div class="msg-meta">
              <span class="msg-time">{{ msg.time }}</span>
            </div>
          </div>
        </div>

        <!-- 加载动画 -->
        <div v-if="loading" class="msg-row ai">
          <div class="msg-avatar">
            <el-icon :size="18"><Service /></el-icon>
          </div>
          <div class="msg-bubble ai typing-bubble">
            <span class="typing-dot" />
            <span class="typing-dot" />
            <span class="typing-dot" />
          </div>
        </div>

        <div v-if="showQuickQuestions && !loading" class="quick-questions">
          <p class="quick-hint">你可能想问：</p>
          <el-tag
            v-for="q in quickQuestions" :key="q"
            class="quick-tag"
            size="small"
            @click="selectQuick(q)"
          >
            {{ q }}
          </el-tag>
        </div>
      </div>

      <div class="chat-input">
        <el-button
          :type="isRecording ? 'danger' : 'default'"
          :icon="isRecording ? 'VideoPause' : 'Microphone'"
          circle
          :class="{ 'is-recording': isRecording }"
          @click="toggleRecording"
        />
        <el-input
          v-model="inputText"
          placeholder="输入你的问题..."
          :disabled="loading"
          @keydown="handleEnter"
        />
        <el-button
          type="primary"
          :icon="Promotion"
          :disabled="!inputText.trim() || loading"
          :loading="loading"
          @click="sendMessage"
        />
      </div>
    </div>

    <!-- 功能介绍弹窗 -->
    <el-dialog v-model="featureDialogVisible" title="智能客服核心功能" width="600px" center>
      <div class="feature-section">
        <div class="feature-icon" style="background: rgba(64,158,255,0.1); color: #409EFF">
          <el-icon :size="28"><Search /></el-icon>
        </div>
        <div class="feature-body">
          <h4>RAG 检索增强生成</h4>
          <p>用户提问时，系统自动从知识库（FAQ + 产品文档）中检索最相关的 3 条内容，作为参考上下文注入 LLM，确保回复准确、基于真实文档而非凭空编造。</p>
          <div class="feature-flow">
            <span class="flow-step">用户提问</span>
            <span class="flow-arrow">→</span>
            <span class="flow-step">文本向量化</span>
            <span class="flow-arrow">→</span>
            <span class="flow-step">ChromaDB 语义检索</span>
            <span class="flow-arrow">→</span>
            <span class="flow-step">Top-3 文档注入</span>
            <span class="flow-arrow">→</span>
            <span class="flow-step">LLM 生成回复</span>
          </div>
        </div>
      </div>

      <div class="feature-section">
        <div class="feature-icon" style="background: rgba(103,194,58,0.1); color: #67C23A">
          <el-icon :size="28"><Connection /></el-icon>
        </div>
        <div class="feature-body">
          <h4>知识图谱学习推荐</h4>
          <p>LLM 自动从用户问题中提取薄弱知识点（如"过去时"），到知识图谱（129 节点、292 边）中查询关联资源：</p>
          <div class="kg-features">
            <el-tag type="warning" size="small">前置依赖技能</el-tag>
            <el-tag type="success" size="small">推荐学习资料</el-tag>
            <el-tag type="danger" size="small">易混淆技能</el-tag>
            <el-tag size="small">CEFR 等级定位</el-tag>
          </div>
          <p style="margin-top: 8px">将结果交给 LLM 生成个性化的分步学习建议。</p>
        </div>
      </div>

      <div class="feature-section">
        <div class="feature-icon" style="background: rgba(230,162,60,0.1); color: #E6A23C">
          <el-icon :size="28"><Microphone /></el-icon>
        </div>
        <div class="feature-body">
          <h4>语音输入 & 流式回复</h4>
          <p>支持语音提问（浏览器录音 → Whisper 转写 → 完整 RAG+KG 管线），SSE 流式逐 token 返回回复内容，模拟真实客服的打字效果。</p>
        </div>
      </div>

      <div class="feature-footer">
        <el-divider />
        <p class="feature-note">
          后台管理入口：<el-tag size="small" type="info">/admin/knowledge</el-tag>
          — 管理知识库文档、查看检索日志、重建向量索引
        </p>
      </div>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.help-layout {
  display: flex; gap: var(--spacing-xl); height: calc(100vh - var(--header-height) - 48px);
  .faq-panel { width: 320px; flex-shrink: 0; overflow-y: auto; }
  .chat-panel {
    flex: 1; background: var(--color-bg-secondary); border: 1px solid var(--color-border);
    border-radius: var(--radius-md); display: flex; flex-direction: column; overflow: hidden;
    min-width: 0;
  }
}

.faq-category { margin-bottom: var(--spacing-lg); }
.faq-cat-title {
  font-weight: 600; display: flex; align-items: center; gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
}
.faq-item {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm); color: var(--color-text-secondary);
  cursor: pointer; transition: all 0.15s;
  &:hover { background: rgba(var(--color-primary-rgb), 0.05); color: var(--color-primary); }
}

.chat-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--spacing-lg); border-bottom: 1px solid var(--color-border);
}
.chat-agent-info { display: flex; align-items: center; gap: var(--spacing-md); }
.agent-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: rgba(var(--color-primary-rgb), 0.1); color: var(--color-primary);
  display: flex; align-items: center; justify-content: center;
}
.agent-name { font-weight: 600; }
.agent-status { font-size: 12px; color: var(--color-text-disabled); }

.chat-messages {
  flex: 1; overflow-y: auto; padding: var(--spacing-lg);
  display: flex; flex-direction: column; gap: var(--spacing-lg);
}
.msg-row {
  display: flex;
  gap: var(--spacing-sm);
  align-items: flex-end;
}
.msg-row.ai {
  justify-content: flex-start;
}
.msg-row.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.msg-row.ai .msg-avatar {
  background: rgba(var(--color-primary-rgb), 0.1);
  color: var(--color-primary);
}
.msg-row.user .msg-avatar {
  background: rgba(var(--color-success-rgb), 0.1);
  color: var(--color-success);
}

.msg-bubble {
  max-width: 70%;
}
.msg-bubble.ai {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  border-top-left-radius: 0;
}
.msg-bubble.user {
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md);
  border-top-right-radius: 0;
}
.msg-bubble .msg-text {
  padding: var(--spacing-md);
  font-size: var(--font-size-base);
  line-height: 1.6;
  white-space: pre-line;
}
.msg-bubble .msg-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 2px var(--spacing-md) var(--spacing-sm);
}
.msg-row.user .msg-bubble .msg-meta {
  justify-content: flex-end;
}

.msg-time {
  font-size: 11px;
  opacity: 0.6;
}
.msg-row.user .msg-time {
  opacity: 0.8;
}
.msg-category-tag {
  font-size: 10px;
}

// 打字动画
.typing-bubble {
  padding: var(--spacing-md);
  display: flex; align-items: center; gap: 4px;
  .typing-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--color-text-disabled);
    animation: typing-bounce 1.4s infinite ease-in-out both;
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
    &:nth-child(3) { animation-delay: 0s; }
  }
}
@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.quick-questions {
  background: var(--color-bg-primary); border-radius: var(--radius-md);
  padding: var(--spacing-lg); text-align: center;
  .quick-hint { font-size: var(--font-size-sm); color: var(--color-text-disabled); margin-bottom: var(--spacing-md); }
  .quick-tag { margin: 4px; cursor: pointer; }
}

.chat-input {
  display: flex; gap: var(--spacing-sm); padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border); align-items: center;
  .el-input { flex: 1; }
}
.chat-header-right {
  display: flex; align-items: center; gap: var(--spacing-sm);
}

.is-recording {
  animation: pulse-rec 1.2s infinite;
}
@keyframes pulse-rec {
  0%, 100% { box-shadow: 0 0 0 0 rgba(var(--color-danger-rgb), 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(var(--color-danger-rgb), 0); }
}

/* 功能介绍弹窗 */
.feature-section {
  display: flex; gap: var(--spacing-lg); margin-bottom: var(--spacing-xl);
}
.feature-icon {
  width: 52px; height: 52px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.feature-body {
  flex: 1;
  h4 { margin: 0 0 6px 0; font-size: 16px; font-weight: 600; }
  p { margin: 0 0 8px 0; font-size: var(--font-size-sm); color: var(--color-text-secondary); line-height: 1.7; }
}
.feature-flow {
  display: flex; align-items: center; gap: 4px; flex-wrap: wrap;
  padding: 10px 12px; background: var(--color-bg-secondary); border-radius: var(--radius-sm);
}
.flow-step {
  background: var(--color-primary); color: #fff;
  padding: 2px 8px; border-radius: 4px; font-size: 12px; white-space: nowrap;
}
.flow-arrow {
  color: var(--color-text-disabled); font-size: 12px;
}
.kg-features {
  display: flex; gap: 8px; flex-wrap: wrap;
}
.feature-note {
  font-size: var(--font-size-sm); color: var(--color-text-tertiary);
  display: flex; align-items: center; gap: 8px;
}
</style>