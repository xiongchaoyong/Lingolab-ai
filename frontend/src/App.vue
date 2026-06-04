<script setup>
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>

<template>
  <router-view v-if="!appStore.isLoading" />
  <div v-else class="flex-center" style="height: 100vh;">
    <el-icon class="is-loading" :size="40">
      <Loading />
    </el-icon>
  </div>
</template>
