<script setup>
import ScoreBar from './ScoreBar.vue'

defineProps({
  dimensions: {
    type: Array,
    required: true,
    // [{ label, score, maxScore }]
  },
})
</script>

<template>
  <div class="dimension-bars">
    <ScoreBar
      v-for="dim in dimensions"
      :key="dim.label"
      :label="dim.label"
      :score="dim.score"
      :max-score="dim.maxScore || 100"
    />
  </div>
</template>

<style lang="scss" scoped>
.dimension-bars {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}
</style>
