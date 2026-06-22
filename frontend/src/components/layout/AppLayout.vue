<script setup>
import TopHeader from './TopHeader.vue'
import SidebarNav from './SidebarNav.vue'
</script>

<template>
  <el-container class="app-layout">
    <TopHeader />
    <el-container class="main-container">
      <SidebarNav />
      <el-main class="content-area">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style lang="scss" scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-container {
  flex: 1;
  overflow: hidden;
}

.content-area {
  background: var(--color-bg-primary);
  padding: var(--spacing-xl);
  overflow-y: auto;
  max-width: var(--content-max-width);
  margin: 0 auto;
  width: 100%;
  background-image:
    radial-gradient(ellipse at 20% 0%, rgba(var(--color-primary-rgb), 0.04) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(var(--color-secondary-rgb), 0.04) 0%, transparent 50%);
}
</style>
