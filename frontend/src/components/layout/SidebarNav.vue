<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const appStore = useAppStore()
const authStore = useAuthStore()

// 学习者菜单
const learnerMenus = [
  { path: '/', title: '首页', icon: 'HomeFilled' },
  { path: '/pronunciation', title: '发音评测', icon: 'Microphone' },
  { path: '/conversation', title: 'AI 对话', icon: 'ChatDotRound' },
  { path: '/learning-path', title: '学习路径', icon: 'Guide' },
  { path: '/recommend', title: '资料推荐', icon: 'Collection' },
  { path: '/progress', title: '学习进度', icon: 'DataLine' },
  { path: '/challenge', title: '游戏化闯关', icon: 'Trophy' },
  { path: '/role-play', title: '角色扮演', icon: 'User' },
  { path: '/community', title: '学习社区', icon: 'Share' },
  { path: '/help', title: '智能客服', icon: 'Service' },
]

// 教师菜单
const teacherMenus = [
  { path: '/teacher/classes', title: '班级管理', icon: 'School' },
  { path: '/teacher/reports', title: '学生报告', icon: 'Document' },
  { path: '/teacher/homework', title: '作业管理', icon: 'Edit' },
]

// 管理员菜单
const adminMenus = [
  { path: '/admin/dashboard', title: '运营看板', icon: 'Odometer' },
  { path: '/admin/users', title: '用户管理', icon: 'UserFilled' },
  { path: '/admin/content', title: '内容管理', icon: 'Files' },
  { path: '/admin/feedback', title: '反馈管理', icon: 'ChatLineSquare' },
]

const menuList = computed(() => {
  const role = authStore.userRole
  if (role === 'admin') return adminMenus
  if (role === 'teacher') return teacherMenus
  return learnerMenus
})

</script>

<template>
  <el-aside :width="appStore.sidebarCollapsed ? '64px' : '240px'" class="sidebar">
    <el-menu
      :default-active="route.path"
      :collapse="appStore.sidebarCollapsed"
      :collapse-transition="false"
      router
      background-color="transparent"
    >
      <template v-for="menu in menuList" :key="menu.path">
        <el-menu-item :index="menu.path">
          <el-icon><component :is="menu.icon" /></el-icon>
          <template #title>{{ menu.title }}</template>
        </el-menu-item>
      </template>
    </el-menu>

    <div class="sidebar-footer">
      <el-button
        text
        @click="appStore.toggleSidebar()"
        class="collapse-btn"
      >
        <el-icon>
          <DArrowLeft v-if="!appStore.sidebarCollapsed" />
          <DArrowRight v-else />
        </el-icon>
      </el-button>
    </div>
  </el-aside>
</template>

<style lang="scss" scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height));
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border-light);
  transition: width var(--transition-smooth);
  overflow: hidden;

  .el-menu {
    flex: 1;
    border-right: none;
    overflow-y: auto;
    padding: var(--spacing-sm) 0;

    .el-menu-item {
      margin: 2px 10px;
      border-radius: var(--radius-md);
      font-family: var(--font-body);
      font-size: var(--font-size-base);
      transition: all var(--transition-fast);

      &:hover {
        background: rgba(var(--color-primary-rgb), 0.04);
        color: var(--color-primary);
      }

      &.is-active {
        background: rgba(var(--color-primary-rgb), 0.12);
        color: var(--color-primary-dark);
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(var(--color-primary-rgb), 0.1);
      }
    }
  }

  .sidebar-footer {
    padding: var(--spacing-sm);
    border-top: 1px solid var(--color-border-light);

    .collapse-btn {
      width: 100%;
      transition: color var(--transition-fast);

      &:hover {
        color: var(--color-primary);
      }
    }
  }
}
</style>
