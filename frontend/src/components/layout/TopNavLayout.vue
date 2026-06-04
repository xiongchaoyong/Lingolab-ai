<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const mobileMenuOpen = ref(false)

const learnerNavs = [
  { path: '/home', title: '首页' },
  { path: '/pronunciation', title: '发音评测' },
  { path: '/conversation', title: 'AI 对话' },
  { path: '/learning-path', title: '学习路径' },
  { path: '/progress', title: '学习进度' },
  { path: '/challenge', title: '闯关' },
  { path: '/role-play', title: '角色扮演' },
]

const teacherNavs = [
  { path: '/teacher/classes', title: '班级管理' },
  { path: '/teacher/reports', title: '学生报告' },
  { path: '/teacher/homework', title: '作业管理' },
]

const adminNavs = [
  { path: '/admin/dashboard', title: '运营看板' },
  { path: '/admin/users', title: '用户管理' },
  { path: '/admin/content', title: '内容管理' },
  { path: '/admin/feedback', title: '反馈管理' },
]

const navItems = computed(() => {
  const role = authStore.userRole
  if (role === 'admin') return adminNavs
  if (role === 'teacher') return teacherNavs
  return learnerNavs
})

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function navigate(path) {
  mobileMenuOpen.value = false
  router.push(path)
}

function handleLogout() {
  authStore.logout()
  router.push('/')
}
</script>

<template>
  <div class="top-nav-layout">
    <!-- 顶部导航栏 -->
    <header class="tn-header">
      <div class="tn-left">
        <h1 class="tn-logo" @click="router.push('/home')">Lingolab</h1>
      </div>

      <!-- 桌面端导航链接 -->
      <nav class="tn-nav-desktop">
        <button
          v-for="item in navItems"
          :key="item.path"
          :class="['tn-nav-link', { active: isActive(item.path) }]"
          @click="navigate(item.path)"
        >
          {{ item.title }}
        </button>
      </nav>

      <div class="tn-right">
        <!-- 通知 -->
        <el-badge :value="3" :max="99" class="tn-notice">
          <el-icon :size="20"><Bell /></el-icon>
        </el-badge>

        <!-- 用户下拉 -->
        <el-dropdown trigger="click" @command="handleLogout">
          <span class="tn-user">
            <el-avatar :size="32" icon="UserFilled" />
            <span class="tn-username">{{ authStore.userInfo?.username || '用户' }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人设置</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 移动端汉堡菜单 -->
        <button class="tn-hamburger" @click="mobileMenuOpen = !mobileMenuOpen">
          <el-icon :size="22">
            <component :is="mobileMenuOpen ? 'Close' : 'Menu'" />
          </el-icon>
        </button>
      </div>
    </header>

    <!-- 移动端下拉菜单 -->
    <transition name="slide">
      <nav v-if="mobileMenuOpen" class="tn-mobile-nav">
        <button
          v-for="item in navItems"
          :key="item.path"
          :class="['tn-mobile-link', { active: isActive(item.path) }]"
          @click="navigate(item.path)"
        >
          {{ item.title }}
        </button>
      </nav>
    </transition>

    <!-- 内容区域 -->
    <main class="tn-content">
      <router-view />
    </main>
  </div>
</template>

<style lang="scss" scoped>
.top-nav-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}

/* 顶部导航栏 */
.tn-header {
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 var(--spacing-xl);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  box-shadow: 0 1px 4px rgba(var(--color-primary-rgb), 0.04);
  position: sticky;
  top: 0;
  z-index: 100;
  gap: var(--spacing-xl);
}

.tn-left {
  flex-shrink: 0;
}

.tn-logo {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: -0.5px;
  cursor: pointer;
  margin: 0;
}

/* 桌面端导航 */
.tn-nav-desktop {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex: 1;
  justify-content: center;
}

.tn-nav-link {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: transparent;
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  white-space: nowrap;

  &:hover {
    color: var(--color-primary);
    background: rgba(var(--color-primary-rgb), 0.04);
  }

  &.active {
    color: var(--color-primary);
    font-weight: 600;
    background: rgba(var(--color-primary-rgb), 0.06);
  }
}

.tn-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  flex-shrink: 0;
}

.tn-notice {
  cursor: pointer;
  transition: transform var(--transition-fast);
  &:hover { transform: translateY(-1px); }
}

.tn-user {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);

  &:hover { background: rgba(var(--color-primary-rgb), 0.04); }
}

.tn-username {
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-primary);
}

/* 移动端汉堡按钮 */
.tn-hamburger {
  display: none;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  align-items: center;
  justify-content: center;
  transition: background var(--transition-fast);

  &:hover { background: rgba(var(--color-primary-rgb), 0.04); }
}

/* 移动端下拉菜单 */
.tn-mobile-nav {
  display: none;
  flex-direction: column;
  padding: var(--spacing-sm);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-card);
}

.tn-mobile-link {
  width: 100%;
  padding: var(--spacing-md) var(--spacing-lg);
  border: none;
  background: transparent;
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  text-align: left;
  transition: all var(--transition-fast);

  &:hover {
    color: var(--color-primary);
    background: rgba(var(--color-primary-rgb), 0.04);
  }

  &.active {
    color: var(--color-primary);
    font-weight: 600;
    background: rgba(var(--color-primary-rgb), 0.06);
  }
}

/* 内容区 */
.tn-content {
  flex: 1;
  padding: var(--spacing-xl);
  max-width: var(--content-max-width);
  margin: 0 auto;
  width: 100%;
  background-image:
    radial-gradient(ellipse at 20% 0%, rgba(var(--color-primary-rgb), 0.03) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(var(--color-success-rgb), 0.03) 0%, transparent 50%);
}

/* 过渡动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 响应式 */
@media (max-width: 768px) {
  .tn-nav-desktop,
  .tn-username,
  .tn-notice { display: none; }

  .tn-hamburger { display: flex; }

  .tn-mobile-nav { display: flex; }

  .tn-content { padding: var(--spacing-base); }
}
</style>
