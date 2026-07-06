<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePredictionStore } from '@/stores/prediction'
import {
  Odometer, School, Document, Edit, Collection,
  UserFilled, Files, ChatLineSquare, Setting,
  Bell, ArrowDown, DArrowLeft, DArrowRight,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const predStore = usePredictionStore()

const collapsed = ref(false)
let noticeTimer = null

onMounted(() => {
  if (authStore.isLoggedIn) {
    if (!authStore.userInfo?.avatar || !authStore.userInfo?.email) {
      authStore.fetchProfile()
    }
    predStore.fetchUnreadCount()
    noticeTimer = setInterval(() => predStore.fetchUnreadCount(), 60000)
  }
})

onUnmounted(() => {
  if (noticeTimer) clearInterval(noticeTimer)
})

const roleLabel = computed(() => {
  const role = authStore.userRole
  if (role === 'admin') return '运营管理'
  if (role === 'teacher') return '教师管理'
  return ''
})

const portalHome = computed(() => {
  const role = authStore.userRole
  if (role === 'admin') return '/admin/dashboard'
  if (role === 'teacher') return '/teacher/dashboard'
  return '/'
})

const teacherMenus = [
  { path: '/teacher/dashboard', title: '工作台', icon: Odometer },
  { path: '/teacher/classes', title: '班级管理', icon: School },
  { path: '/teacher/reports', title: '学生报告', icon: Document },
  { path: '/teacher/homework', title: '作业管理', icon: Edit },
  { path: '/teacher/courses', title: '课程管理', icon: Collection },
]

const adminMenus = [
  { path: '/admin/dashboard', title: '运营看板', icon: Odometer },
  { path: '/admin/users', title: '用户管理', icon: UserFilled },
  { path: '/admin/content', title: '内容管理', icon: Files },
  { path: '/admin/feedback', title: '反馈管理', icon: ChatLineSquare },
  { path: '/admin/knowledge', title: '知识库管理', icon: Collection },
  { path: '/admin/settings', title: '系统设置', icon: Setting },
]

const menuItems = computed(() => {
  return authStore.userRole === 'admin' ? adminMenus : teacherMenus
})

function toggleCollapse() {
  collapsed.value = !collapsed.value
}

function handleCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<template>
  <div class="admin-layout">
    <!-- 顶部导航栏 -->
    <header class="admin-header">
      <div class="admin-header-left">
        <h1 class="admin-logo" @click="router.push(portalHome)">Lingolab</h1>
        <el-tag size="small" effect="plain" type="warning" class="role-tag">
          {{ roleLabel }}
        </el-tag>
      </div>
      <div class="admin-header-right">
        <el-badge
          :value="predStore.unreadCount"
          :max="99"
          :hidden="!predStore.unreadCount"
          class="admin-notice"
          @click="router.push('/notices')"
        >
          <el-icon :size="18"><Bell /></el-icon>
        </el-badge>
        <el-dropdown trigger="click" @command="handleCommand">
          <span class="admin-user">
            <el-avatar :size="32" :src="authStore.userInfo?.avatar" icon="UserFilled" />
            <span class="admin-username">{{ authStore.userInfo?.username || '用户' }}</span>
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
    </header>

    <!-- 主体：侧边栏 + 内容 -->
    <div class="admin-body">
      <aside :class="['admin-sidebar', { collapsed }]">
        <el-menu
          :default-active="route.path"
          :collapse="collapsed"
          router
          background-color="transparent"
          class="admin-menu"
        >
          <el-menu-item v-for="menu in menuItems" :key="menu.path" :index="menu.path">
            <el-icon><component :is="menu.icon" /></el-icon>
            <template #title>{{ menu.title }}</template>
          </el-menu-item>
        </el-menu>
        <div class="sidebar-footer">
          <el-button text @click="toggleCollapse" class="collapse-btn">
            <el-icon :size="16">
              <DArrowLeft v-if="!collapsed" />
              <DArrowRight v-else />
            </el-icon>
          </el-button>
        </div>
      </aside>

      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.admin-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}

/* 顶部栏 */
.admin-header {
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-xl);
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  z-index: 10;
}

.admin-header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.admin-logo {
  font-family: var(--font-heading);
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  cursor: pointer;
  transition: opacity var(--transition-fast);

  &:hover { opacity: 0.85; }
}

.role-tag {
  font-weight: 500;
}

.admin-header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.admin-notice {
  cursor: pointer;
  color: var(--color-text-secondary);
  padding: 6px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);

  &:hover {
    color: var(--color-primary);
    background: rgba(var(--color-primary-rgb), 0.06);
  }
}

.admin-user {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  padding: 4px 12px 4px 4px;
  border-radius: 20px;
  transition: all var(--transition-fast);

  &:hover {
    background: var(--color-bg-secondary);
  }
}

.admin-username {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

/* 主体区域 */
.admin-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 侧边栏 */
.admin-sidebar {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #fafbfc;
  border-right: 1px solid var(--color-border);
  transition: width 0.25s ease;
  overflow: hidden;

  &.collapsed {
    width: 64px;
  }
}

.admin-menu {
  flex: 1;
  border-right: none;
  padding: var(--spacing-sm) 0;

  :deep(.el-menu-item) {
    height: 44px;
    line-height: 44px;
    margin: 2px 8px;
    border-radius: var(--radius-md);
    font-size: var(--font-size-base);
    color: var(--color-text-secondary);
    transition: all var(--transition-fast);

    &:hover {
      color: var(--color-primary);
      background: rgba(var(--color-primary-rgb), 0.06);
    }

    &.is-active {
      color: var(--color-primary);
      font-weight: 600;
      background: linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.1), rgba(var(--color-secondary-rgb), 0.06));
    }
  }
}

.sidebar-footer {
  padding: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: center;
}

.collapse-btn {
  width: 100%;
  color: var(--color-text-tertiary);
}

/* 内容区 */
.admin-content {
  flex: 1;
  padding: var(--spacing-xl);
  overflow-y: auto;
  background: var(--color-bg-primary);
}
</style>
