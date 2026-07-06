<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePredictionStore } from '@/stores/prediction'
import FeedbackButton from '@/components/common/FeedbackButton.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const predStore = usePredictionStore()
const mobileMenuOpen = ref(false)
const hoveredNav = ref(null)

let noticeTimer = null

onMounted(() => {
  if (authStore.isLoggedIn) {
    // 加载完整用户信息（头像、用户名等）
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

// ========== 导航定义（按需求文档七个模块） ==========

const FULLSCREEN_ROUTES = ['/voice-chat']

const isFullscreenRoute = computed(() => FULLSCREEN_ROUTES.includes(route.path))

const learnerNavs = [
  { path: '/', title: '首页' },
  {
    title: '学习中心',
    children: [
      { path: '/pronunciation', title: '发音评测' },
      { path: '/voice-chat', title: 'AI 语音对话' },
      { path: '/grammar', title: '语法纠错' },
    ],
  },
  {
    title: '学习路径',
    children: [
      { path: '/learning-path', title: '路径规划' },
      { path: '/recommend', title: '资料推荐' },
      { path: '/profile-summary', title: '个人情况说明' },
    ],
  },
  {
    title: '社区',
    children: [
      { path: '/community', title: '社区广场' },
      { path: '/my-classes', title: '我的班级' },
    ],
  },
  { path: '/help', title: '智能客服' },
]

const navItems = learnerNavs

function isActive(item) {
  if (item.path) {
    return route.path === item.path
  }
  if (item.children) {
    return item.children.some(c => route.path === c.path || route.path.startsWith(c.path + '/'))
  }
  return false
}

function isChildActive(child) {
  return route.path === child.path || route.path.startsWith(child.path + '/')
}

function navigate(path) {
  mobileMenuOpen.value = false
  router.push(path)
}

function onParentClick(item) {
  // 有子菜单的父级：点击进入第一个子项
  if (item.children && item.children.length > 0) {
    router.push(item.children[0].path)
  } else if (item.path) {
    router.push(item.path)
  }
}

function handleCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    authStore.logout()
    router.push('/')
  }
}
</script>

<template>
  <div class="top-nav-layout">
    <!-- 顶部浮动层：全宽容器 -->
    <div class="tn-top-bar">
      <!-- 居中导航栏 — 玻璃效果 -->
      <header class="tn-header">
        <div class="tn-left">
          <h1 class="tn-logo" @click="router.push('/')">Lingolab</h1>
        </div>

        <!-- 桌面端导航链接 -->
        <nav class="tn-nav-desktop">
          <div
            v-for="item in navItems"
            :key="item.title"
            class="tn-nav-item"
            @mouseenter="hoveredNav = item.title"
            @mouseleave="hoveredNav = null"
          >
            <button
              :class="['tn-nav-link', { active: isActive(item) }]"
              @click="onParentClick(item)"
            >
              {{ item.title }}
              <span v-if="item.children" class="tn-arrow">▾</span>
            </button>

            <!-- 下拉子菜单 -->
            <transition name="dropdown">
              <div
                v-if="item.children && hoveredNav === item.title"
                class="tn-dropdown"
              >
                <button
                  v-for="child in item.children"
                  :key="child.path"
                  :class="['tn-dropdown-item', { active: isChildActive(child) }]"
                  @click="navigate(child.path)"
                >
                  {{ child.title }}
                </button>
              </div>
            </transition>
          </div>
        </nav>
        <!-- 通知铃铛 -->
        <el-badge
          v-if="authStore.isLoggedIn"
          :value="predStore.unreadCount" :max="99" :hidden="!predStore.unreadCount"
          class="tn-notice"
          @click="router.push('/notices')"
        >
          <el-icon :size="18"><Bell /></el-icon>
        </el-badge>
      </header>

      <!-- 页面右端：头像 + 登录 -->
      <div class="tn-header-right">
        <template v-if="!authStore.isLoggedIn">
          <el-button text @click="router.push('/login')">登录</el-button>
          <el-button type="primary" @click="router.push('/register')">免费注册</el-button>
        </template>
        <template v-else>
          <!-- 用户下拉 -->
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="tn-user">
              <el-avatar :size="36" :src="authStore.userInfo?.avatar" icon="UserFilled" />
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
        </template>

        <!-- 移动端汉堡菜单 -->
        <button class="tn-hamburger" @click="mobileMenuOpen = !mobileMenuOpen">
          <el-icon :size="22">
            <component :is="mobileMenuOpen ? 'Close' : 'Menu'" />
          </el-icon>
        </button>
      </div>
    </div>

    <!-- 移动端下拉菜单 -->
    <transition name="slide">
      <nav v-if="mobileMenuOpen" class="tn-mobile-nav">
        <template v-for="item in navItems" :key="item.title">
          <button
            v-if="item.path"
            :class="['tn-mobile-link', { active: isActive(item) }]"
            @click="navigate(item.path)"
          >
            {{ item.title }}
          </button>
          <div v-else class="tn-mobile-group">
            <div class="tn-mobile-group-title">{{ item.title }}</div>
            <button
              v-for="child in item.children"
              :key="child.path"
              :class="['tn-mobile-link', 'tn-mobile-sub', { active: isChildActive(child) }]"
              @click="navigate(child.path)"
            >
              {{ child.title }}
            </button>
          </div>
        </template>
      </nav>
    </transition>

    <!-- 反馈按钮（登录后可见） -->
    <FeedbackButton v-if="authStore.isLoggedIn" />

    <!-- 内容区域 -->
    <main :class="['tn-content', { 'tn-content--fullscreen': isFullscreenRoute }]">
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

/* 全宽浮动容器 */
.tn-top-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px var(--spacing-xl) 0;
  /* 作为 .tn-header-right absolute 的定位参考 */
}

/* 居中导航栏 — iOS 玻璃效果 */
.tn-header {
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 var(--spacing-lg);
  width: 65%;
  max-width: 880px;
  min-width: 520px;
  background: rgba(255, 255, 255, 0.38);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 24px;
  box-shadow:
    0 1px 8px rgba(0, 0, 0, 0.04),
    0 4px 24px rgba(0, 0, 0, 0.03),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  gap: var(--spacing-md);
}

.tn-left {
  flex-shrink: 0;
}

.tn-logo {
  font-family: var(--font-heading);
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
  cursor: pointer;
  margin: 0;
  transition: opacity var(--transition-fast);

  &:hover { opacity: 0.85; }
}

/* 桌面端导航 */
.tn-nav-desktop {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex: 1;
  justify-content: center;
}

.tn-nav-item {
  position: relative;
}

.tn-nav-link {
  display: flex;
  align-items: center;
  gap: 4px;
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
    background: rgba(var(--color-primary-rgb), 0.06);
  }

  &.active {
    color: var(--color-primary-dark);
    font-weight: 600;
    background: rgba(var(--color-primary-rgb), 0.1);
  }
}

.tn-arrow {
  font-size: 10px;
  transition: transform 0.2s;
}

/* 下拉子菜单 — 高亮不透黑 */
.tn-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  min-width: 150px;
  padding: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.08),
    0 12px 36px rgba(0, 0, 0, 0.06);
  z-index: 200;
  display: flex;
  flex-direction: column;
}

.tn-dropdown-item {
  display: block;
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: transparent;
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  text-align: left;
  white-space: nowrap;
  transition: all var(--transition-fast);

  &:hover {
    color: var(--color-primary);
    background: rgba(var(--color-primary-rgb), 0.06);
    transform: translateX(3px);
  }

  &.active {
    color: var(--color-primary);
    font-weight: 600;
    background: linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.08), rgba(var(--color-secondary-rgb), 0.08));
  }
}

/* 下拉动画 */
.dropdown-enter-active {
  transition: all 0.15s ease-out;
}
.dropdown-leave-active {
  transition: all 0.1s ease-in;
}
.dropdown-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-4px);
}
.dropdown-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-4px);
}

/* 页面右端：头像 + 按钮 */
.tn-header-right {
  position: absolute;
  right: var(--spacing-xl);
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  z-index: 101;

  .el-button {
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
  }
}

.tn-notice {
  cursor: pointer;
  color: var(--color-text-secondary);
  padding: 6px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  flex-shrink: 0;

  &:hover {
    color: var(--color-primary);
    background: rgba(var(--color-primary-rgb), 0.06);
  }
}

.tn-user {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  padding: 5px 16px 5px 5px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(12px) saturate(160%);
  -webkit-backdrop-filter: blur(12px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.45);
  transition: all var(--transition-fast);

  &:hover {
    background: rgba(255, 255, 255, 0.72);
    border-color: rgba(255, 255, 255, 0.65);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  }
}

.tn-username {
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
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

.tn-mobile-group {
  padding: var(--spacing-xs) 0;
}

.tn-mobile-group-title {
  padding: var(--spacing-sm) var(--spacing-lg);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
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

.tn-mobile-sub {
  padding-left: var(--spacing-xl);
  font-size: var(--font-size-sm);
}

/* 内容区 */
.tn-content {
  flex: 1;
  padding: var(--spacing-xl);
  max-width: var(--content-max-width);
  margin: 0 auto;
  width: 100%;
}

/* 全屏内容区 — 用于 AI 智能对话等需要铺满的页面 */
.tn-content--fullscreen {
  padding: 0;
  max-width: none;
  background: none;
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
  .tn-top-bar {
    padding: 4px 8px 0;
  }

  .tn-header {
    width: 100%;
    min-width: 0;
    max-width: none;
    border-radius: 20px;
    height: 44px;
    padding: 0 var(--spacing-md);
  }

  .tn-header-right {
    right: 12px;
  }

  .tn-nav-desktop,
  .tn-username,
  .tn-notice { display: none; }

  .tn-hamburger { display: flex; }

  .tn-mobile-nav { display: flex; }

  .tn-content { padding: var(--spacing-base); }
}
</style>