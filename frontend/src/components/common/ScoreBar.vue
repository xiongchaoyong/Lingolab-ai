<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  score: { type: Number, required: true },
  maxScore: { type: Number, default: 100 },
})

const percentage = computed(() => Math.round((props.score / props.maxScore) * 100))

const colorClass = computed(() => {
  if (percentage.value >= 80) return 'score-green'
  if (percentage.value >= 60) return 'score-yellow'
  return 'score-red'
})

const barWidth = computed(() => Math.max(percentage.value, 4) + '%')
</script>

<template>
  <div class="score-bar">
    <div class="score-header">
      <span class="score-label">{{ label }}</span>
      <span class="score-value" :class="colorClass">{{ score }}/{{ maxScore }}</span>
    </div>
    <div class="bar-track">
      <div
        class="bar-fill"
        :class="colorClass"
        :style="{ width: barWidth }"
      />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.score-bar {
  width: 100%;
}

.score-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
}

.score-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.score-value {
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.bar-track {
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;

  &.score-green { background: var(--color-success); }
  &.score-yellow { background: var(--color-warning); }
  &.score-red { background: var(--color-danger); }
}

.score-green { color: var(--color-success); }
.score-yellow { color: var(--color-warning); }
.score-red { color: var(--color-danger); }
</style>
