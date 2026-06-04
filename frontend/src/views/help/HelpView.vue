<script setup>
import { ref, nextTick } from 'vue'

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
      { q: '学习路径是如何生成的？', a: '系统根据你的 CEFR 等级和薄弱维度，每天自动生成包含跟读、对话、听力三类任务的个性化学习路径。' },
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

const quickQuestions = [
  '如何练习发音？', '口语水平怎么提升？', '学习路径如何调整？',
  '怎么查看学习报告？', '如何加入学习小组？', '反馈建议在哪里提交？',
]

function selectFaq(faq) {
  messages.value.push({ role: 'user', text: faq.q, time: '刚刚' })
  showQuickQuestions.value = false
  scrollToBottom()
  setTimeout(() => {
    messages.value.push({ role: 'ai', text: faq.a, time: '刚刚' })
    scrollToBottom()
  }, 600)
}

function selectQuick(q) {
  messages.value.push({ role: 'user', text: q, time: '刚刚' })
  showQuickQuestions.value = false
  scrollToBottom()
  setTimeout(() => {
    messages.value.push({ role: 'ai', text: '这是一个好问题！让我来帮你解答：\n\n你可以先在学习页面的发音评测模块进行基础练习，系统会根据你的表现给出具体建议。同时建议每天完成学习路径中的跟读任务，这是最有效的提升方法。\n\n如果还有疑问，可以查看「学习功能」分类下的常见问题。', time: '刚刚' })
    scrollToBottom()
  }, 600)
}

function sendMessage() {
  if (!inputText.value.trim()) return
  messages.value.push({ role: 'user', text: inputText.value, time: '刚刚' })
  inputText.value = ''
  showQuickQuestions.value = false
  scrollToBottom()
  setTimeout(() => {
    messages.value.push({ role: 'ai', text: '收到你的消息了！小语正在努力学习更多知识，目前建议你查看左侧的常见问题分类，或者联系人工客服获取更详细的帮助。', time: '刚刚' })
    scrollToBottom()
  }, 800)
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
            <div class="agent-status">在线 | 响应时间 &lt; 1分钟</div>
          </div>
        </div>
        <el-tag size="small" type="success">AI 客服</el-tag>
      </div>

      <div class="chat-messages" ref="chatRef">
        <div v-for="(msg, i) in messages" :key="i" :class="['msg-row', msg.role]">
          <div class="msg-avatar">
            <el-icon v-if="msg.role === 'ai'" :size="18"><Service /></el-icon>
            <el-icon v-else :size="18"><UserFilled /></el-icon>
          </div>
          <div class="msg-bubble" :class="msg.role">
            <div class="msg-text">{{ msg.text }}</div>
            <div class="msg-time">{{ msg.time }}</div>
          </div>
        </div>

        <div v-if="showQuickQuestions" class="quick-questions">
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
        <el-input
          v-model="inputText"
          placeholder="输入你的问题..."
          @keydown="handleEnter"
        >
          <template #suffix>
            <el-button text :icon="Microphone" size="small" />
          </template>
        </el-input>
        <el-button type="primary" :icon="Promotion" :disabled="!inputText.trim()" @click="sendMessage" />
      </div>
    </div>
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
.msg-row { display: flex; gap: var(--spacing-sm);
  &.ai { justify-content: flex-start; }
  &.user { justify-content: flex-end; flex-direction: row-reverse; }
}
.msg-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.msg-row.ai .msg-avatar { background: rgba(var(--color-primary-rgb), 0.1); color: var(--color-primary); }
.msg-row.user .msg-avatar { background: rgba(var(--color-success-rgb), 0.1); color: var(--color-success); }
.msg-bubble {
  max-width: 70%;
  &.ai { background: var(--color-bg-primary); border: 1px solid var(--color-border); border-radius: var(--radius-md); border-top-left-radius: 0; }
  &.user { background: var(--color-primary); color: #fff; border-radius: var(--radius-md); border-top-right-radius: 0; }
  .msg-text { padding: var(--spacing-md); font-size: var(--font-size-base); line-height: 1.6; white-space: pre-line; }
  .msg-time { font-size: 11px; padding: 2px var(--spacing-md) var(--spacing-sm); opacity: 0.6; }
}
.msg-row.user .msg-time { text-align: right; }

.quick-questions {
  background: var(--color-bg-primary); border-radius: var(--radius-md);
  padding: var(--spacing-lg); text-align: center;
  .quick-hint { font-size: var(--font-size-sm); color: var(--color-text-disabled); margin-bottom: var(--spacing-md); }
  .quick-tag { margin: 4px; cursor: pointer; }
}

.chat-input {
  display: flex; gap: var(--spacing-sm); padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}
</style>
