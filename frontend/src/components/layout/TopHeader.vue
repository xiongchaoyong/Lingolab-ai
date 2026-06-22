<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-header class="top-header">
    <div class="header-left">
      <h1 class="logo">Lingolab</h1>
    </div>
    <div class="header-right">
      <el-badge :value="3" :max="99" class="notice-badge">
        <el-icon :size="20"><Bell /></el-icon>
      </el-badge>
      <el-dropdown trigger="click" @command="handleLogout">
        <span class="user-info">
          <el-avatar :size="32" icon="UserFilled" />
          <span class="username">{{ authStore.userInfo?.username || '用户' }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人设置</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<style lang="scss" scoped>
.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1.5px solid var(--color-border);
  box-shadow: 0 2px 12px rgba(var(--color-primary-rgb), 0.06);
  padding: 0 var(--spacing-xl);
  z-index: 10;
}

.header-left {
  .logo {
    font-family: var(--font-heading);
    font-size: var(--font-size-lg);
    font-weight: 700;
    background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);

  .notice-badge {
    cursor: pointer;
    transition: all var(--transition-fast);

    &:hover {
      transform: translateY(-1px);
    }
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    cursor: pointer;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    transition: background var(--transition-fast);

    &:hover {
      background: rgba(var(--color-primary-rgb), 0.04);
    }

    .username {
      font-family: var(--font-body);
      font-size: var(--font-size-base);
      font-weight: 500;
      color: var(--color-text-primary);
    }
  }
}
</style>
