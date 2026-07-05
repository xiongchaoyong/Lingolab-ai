<script setup>
import { ref } from 'vue'
import { correctGrammar, correctGrammarVoice } from '@/api/grammar'
import VoiceRecorder from '@/components/common/VoiceRecorder.vue'

// ========== 状态 ==========
const inputMode = ref('text')
const inputText = ref('')
const cefrLevel = ref('B1')
const isLoading = ref(false)
const result = ref(null)
const errorMessage = ref('')
const recorderRef = ref(null)
const hasResult = ref(false)

// ========== 错误类型配置 ==========
const ERROR_TYPE_MAP = {
  tense: { label: '时态', color: '#E6A23C' },
  subject_verb_agreement: { label: '主谓一致', color: '#F56C6C' },
  article: { label: '冠词', color: '#409EFF' },
  preposition: { label: '介词', color: '#67C23A' },
  word_order: { label: '语序', color: '#E6A23C' },
  plural: { label: '单复数', color: '#F56C6C' },
  word_choice: { label: '用词', color: '#909399' },
  other: { label: '其他', color: '#909399' },
}

function errorLabel(type) { return ERROR_TYPE_MAP[type]?.label || type }
function errorColor(type) { return ERROR_TYPE_MAP[type]?.color || '#909399' }

// ========== 文本纠错 ==========
async function handleTextSubmit() {
  const text = inputText.value.trim()
  if (!text) return
  isLoading.value = true; errorMessage.value = ''; result.value = null; hasResult.value = false
  try {
    result.value = await correctGrammar(text, cefrLevel.value)
    hasResult.value = true
  } catch {
    errorMessage.value = '语法纠错失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}

// ========== 语音纠错 ==========
async function handleVoiceComplete({ blob }) {
  isLoading.value = true; errorMessage.value = ''; result.value = null; hasResult.value = false
  try {
    result.value = await correctGrammarVoice(blob, cefrLevel.value)
    hasResult.value = true
  } catch {
    errorMessage.value = '语音纠错失败，请重新录音'
  } finally {
    isLoading.value = false
  }
}

function resetResult() {
  result.value = null; hasResult.value = false; errorMessage.value = ''; inputText.value = ''
}

// ========== 修正文本高亮 ==========
// 位置对位对比：修正版中与原文不同的词高亮
function highlightWords(original, corrected) {
  if (!corrected) return []
  const origWords = (original || '').split(/\s+/).filter(Boolean)
  const corrWords = corrected.split(/\s+/).filter(Boolean)
  return corrWords.map((w, i) => ({
    text: w,
    isError: i < origWords.length && w !== origWords[i],
  }))
}
</script>

<template>
  <div class="grammar-page">
    <div class="grammar-header">
      <h2>AI 语法纠错</h2>
      <p>输入英文句子，AI 帮你找出语法错误并提供修正</p>
    </div>

    <!-- 输入区域 -->
    <div class="grammar-input-area">
      <div class="mode-switch">
        <el-radio-group v-model="inputMode" @change="resetResult">
          <el-radio-button value="text">文本输入</el-radio-button>
          <el-radio-button value="voice">语音输入</el-radio-button>
        </el-radio-group>
        <div class="level-selector">
          <span>CEFR 等级：</span>
          <el-select v-model="cefrLevel" size="small" style="width: 100px">
            <el-option label="A1" value="A1" /><el-option label="A2" value="A2" />
            <el-option label="B1" value="B1" /><el-option label="B2" value="B2" />
          </el-select>
        </div>
      </div>

      <template v-if="inputMode === 'text'">
        <div class="text-input-wrap">
          <el-input v-model="inputText" type="textarea" :rows="4" maxlength="1000"
            show-word-limit placeholder="请输入你想检查的英文句子..."
            :disabled="isLoading" />
          <el-button type="primary" size="large" :loading="isLoading"
            :disabled="!inputText.trim()" class="submit-btn" @click="handleTextSubmit">
            检查语法
          </el-button>
        </div>
      </template>
      <template v-else>
        <div class="voice-input-wrap">
          <VoiceRecorder ref="recorderRef" :prep-time="3" :max-duration="30"
            :disabled="isLoading" @complete="handleVoiceComplete" />
        </div>
      </template>
    </div>

    <!-- 加载中 -->
    <div v-if="isLoading" class="grammar-loading">
      <div class="loading-spinner"></div>
      <p>正在分析语法...</p>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="grammar-error">
      <el-alert :title="errorMessage" type="error" show-icon closable @close="errorMessage = ''" />
    </div>

    <!-- 结果展示 -->
    <template v-if="hasResult && result && !isLoading">
      <div class="grammar-result">
        <!-- 原文 vs 修正版 -->
        <div class="compare-cards">
          <div class="compare-card card-original">
            <div class="card-label">原文</div>
            <p class="text-plain">{{ result.original_text }}</p>
          </div>
          <div class="compare-arrow">→</div>
          <div class="compare-card card-corrected" :class="{ clean: !result.errors?.length }">
            <div class="card-label">
              修正版
              <span v-if="!result.errors?.length" class="clean-badge">无错误</span>
            </div>
            <p class="text-highlight">
              <span v-for="(w, i) in highlightWords(result.original_text, result.corrected_text)"
                :key="i" :class="{ 'word-error': w.isError }"
              >{{ w.text }}</span>
            </p>
          </div>
        </div>

        <!-- 错误列表 -->
        <div v-if="result.errors?.length" class="error-list-section">
          <h3>发现的语法错误（{{ result.errors.length }} 个）</h3>
          <div class="error-cards">
            <div v-for="(err, idx) in result.errors" :key="idx" class="error-card">
              <div class="error-card-top">
                <el-tag :color="errorColor(err.error_type)" effect="dark" size="small">
                  {{ errorLabel(err.error_type) }}
                </el-tag>
                <span class="err-orig">{{ err.original }}</span>
                <span class="err-arrow">→</span>
                <span class="err-corr">{{ err.correction }}</span>
              </div>
              <p class="err-explain">{{ err.explanation }}</p>
            </div>
          </div>
        </div>

        <!-- 润色版本 -->
        <div v-if="result.polished_version && result.polished_version !== result.corrected_text"
          class="polished-section">
          <h3>地道表达建议</h3>
          <div class="polished-card"><p>{{ result.polished_version }}</p></div>
        </div>

        <!-- 改进建议 -->
        <div v-if="result.suggestions?.length" class="suggestions-section">
          <h3>改进建议</h3>
          <div class="suggestions-list">
            <div v-for="(tip, idx) in result.suggestions" :key="idx" class="suggestion-item">
              <span class="tip-num">{{ idx + 1 }}</span>
              <span>{{ tip }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="grammar-actions">
        <el-button @click="resetResult" size="large">再来一次</el-button>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-if="!hasResult && !isLoading && !errorMessage" class="grammar-empty">
      <p>输入英文句子，AI 将帮你找出语法错误并提供修正建议</p>
      <div class="empty-examples">
        <span class="example-label">试试这些例子：</span>
        <el-tag v-for="ex in ['He go to school yesterday', 'She don\'t like coffee', 'I have many homeworks']"
          :key="ex" class="example-tag" @click="inputText = ex; inputMode = 'text'">
          {{ ex }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.grammar-page {
  min-height: calc(100vh - 56px);
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px 48px;
  color: #4A4A5A;
}

.grammar-header {
  text-align: center; margin-bottom: 28px;
  h2 { font-size: 24px; font-weight: 700; color: #3D3D5C; margin-bottom: 4px; }
  p { font-size: 14px; color: #999; margin: 0; }
}

// 输入区
.grammar-input-area {
  background: #fff; border-radius: 16px; padding: 20px 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,.04); margin-bottom: 20px;
}
.mode-switch {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; flex-wrap: wrap; gap: 12px;
}
.level-selector { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #999; }
.text-input-wrap { display: flex; flex-direction: column; gap: 12px; }
.submit-btn {
  align-self: flex-end; min-width: 120px;
  background: linear-gradient(135deg, #7C6FF7, #5B8FF9); border: none;
  &:hover { opacity: 0.9; }
}
.voice-input-wrap { display: flex; justify-content: center; padding: 12px 0; }

// 加载
.grammar-loading {
  text-align: center; padding: 48px 20px;
  .loading-spinner {
    width: 36px; height: 36px; border: 3px solid #F0E8FF;
    border-top-color: #7C6FF7; border-radius: 50%;
    animation: spin 0.8s linear infinite; margin: 0 auto 12px;
  }
  p { color: #999; font-size: 14px; }
}
@keyframes spin { to { transform: rotate(360deg); } }
.grammar-error { margin-bottom: 16px; }

// 对比卡片
.compare-cards {
  display: flex; align-items: stretch; gap: 16px; margin-bottom: 20px;
  @media (max-width: 640px) { flex-direction: column; .compare-arrow { transform: rotate(90deg); } }
}
.compare-card {
  flex: 1; background: #fff; border-radius: 14px; overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,.04);
  &.card-corrected { border: 2px solid #67C23A; &.clean { border-color: #E0E0E0; } }
}
.card-label {
  padding: 8px 16px; font-size: 13px; font-weight: 600; color: #666;
  display: flex; align-items: center; gap: 8px;
}
.card-original .card-label { background: #F5F5F5; }
.card-corrected .card-label { background: #F0F9EB; }
.clean-badge { font-size: 12px; color: #67C23A; }

// 核心修复：flex + gap 保证单词间距，不依赖 HTML whitespace
.text-plain, .text-highlight {
  padding: 14px 16px; margin: 0; font-size: 15px; line-height: 1.8;
  color: #4A4A5A;
}
.text-highlight {
  display: flex; flex-wrap: wrap; gap: 0.35em;
}
.text-plain {
  white-space: pre-wrap; word-break: break-word;
}
.word-error {
  color: #67C23A; font-weight: 600;
  background: rgba(103,194,58,.1); border-radius: 3px; padding: 0 2px;
}

.compare-arrow {
  display: flex; align-items: center; font-size: 24px; color: #ccc; flex-shrink: 0;
}

// 错误列表
.error-list-section {
  margin-bottom: 20px;
  h3 { font-size: 16px; font-weight: 600; color: #3D3D5C; margin: 0 0 12px; }
}
.error-cards { display: flex; flex-direction: column; gap: 8px; }
.error-card {
  background: #fff; border-radius: 10px; padding: 12px 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,.04); border-left: 3px solid #F56C6C;
}
.error-card-top {
  display: flex; align-items: center; gap: 10px; margin-bottom: 4px; flex-wrap: wrap;
}
.err-orig { color: #F56C6C; font-family: monospace; font-size: 14px; text-decoration: line-through; }
.err-arrow { color: #ccc; }
.err-corr { color: #67C23A; font-family: monospace; font-size: 14px; font-weight: 600; }
.err-explain { margin: 0; font-size: 12px; color: #999; }

// 润色
.polished-section {
  margin-bottom: 20px;
  h3 { font-size: 16px; font-weight: 600; color: #3D3D5C; margin: 0 0 12px; }
}
.polished-card {
  background: #F8F0FF; border: 1px solid #E8D8FF; border-radius: 12px;
  padding: 16px 20px; border-left: 4px solid #7C6FF7;
  p { margin: 0; font-size: 15px; line-height: 1.7; color: #4A3A6A; font-style: italic; }
}

// 建议
.suggestions-section {
  margin-bottom: 20px;
  h3 { font-size: 16px; font-weight: 600; color: #3D3D5C; margin: 0 0 12px; }
}
.suggestions-list { display: flex; flex-direction: column; gap: 8px; }
.suggestion-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 12px 16px; background: #F0F8FF; border-radius: 10px;
  font-size: 13px; color: #5B6A8A; line-height: 1.6;
}
.tip-num {
  width: 22px; height: 22px; border-radius: 50%; background: #5B8FF9; color: #fff;
  font-size: 12px; font-weight: 600; display: flex; align-items: center;
  justify-content: center; flex-shrink: 0;
}

// 操作
.grammar-actions { text-align: center; padding: 8px 0 24px; }

// 空状态
.grammar-empty { text-align: center; padding: 48px 20px; color: #999; font-size: 14px; }
.empty-examples {
  display: flex; flex-direction: column; align-items: center; gap: 8px; margin-top: 16px;
  .example-label { font-size: 12px; color: #bbb; }
  .example-tag { cursor: pointer; &:hover { transform: translateY(-1px); } }
}
</style>
