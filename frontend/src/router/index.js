import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  // ========== 公开路由 ==========
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/assessment',
    name: 'Assessment',
    component: () => import('@/views/assessment/AssessmentView.vue'),
    meta: { auth: true },
  },
  {
    path: '/assessment/result',
    name: 'AssessmentResult',
    component: () => import('@/views/assessment/AssessmentResult.vue'),
    meta: { auth: true },
  },

  // ========== 主布局路由（顶部导航） ==========
  {
    path: '/',
    component: () => import('@/components/layout/TopNavLayout.vue'),
    children: [
      {
        path: '',
        name: 'Introduction',
        component: () => import('@/views/introduction/IntroductionView.vue'),
      },
      {
        path: 'home',
        name: 'Home',
        redirect: '/',
      },
      // 模块二：学习服务
      {
        path: 'pronunciation',
        name: 'Pronunciation',
        component: () => import('@/views/pronunciation/PronunciationView.vue'),
        meta: { title: '发音评测', auth: true },
      },
      {
        path: 'role-play',
        name: 'RolePlay',
        component: () => import('@/views/roleplay/RolePlayView.vue'),
        meta: { title: '角色扮演', auth: true },
      },
      // 模块三：个性化推荐
      {
        path: 'learning-path',
        name: 'LearningPath',
        component: () => import('@/views/learning/LearningPathView.vue'),
        meta: { title: '学习路径', auth: true },
      },
      {
        path: 'recommend',
        name: 'Recommend',
        component: () => import('@/views/learning/RecommendationView.vue'),
        meta: { title: '资料推荐', auth: true },
      },
      // 模块四：激励服务
      {
        path: 'progress',
        name: 'Progress',
        component: () => import('@/views/progress/ProgressView.vue'),
        meta: { title: '学习进度', auth: true },
      },
      {
        path: 'challenge',
        name: 'Challenge',
        component: () => import('@/views/gamification/ChallengeView.vue'),
        meta: { title: '闯关挑战', auth: true },
      },
      // 模块五：社区服务
      {
        path: 'community',
        name: 'Community',
        component: () => import('@/views/community/CommunityView.vue'),
        meta: { title: '社区', auth: true },
      },
      // 模块七：智能客服
      {
        path: 'help',
        name: 'Help',
        component: () => import('@/views/help/HelpView.vue'),
        meta: { title: '智能客服', auth: true },
      },
      {
        path: 'conversation',
        name: 'Conversation',
        component: () => import('@/views/conversation/VoiceCallView.vue'),
        meta: { title: 'AI 智能对话', auth: true },
      },
    ],
  },

  // ========== 教师端 ==========
  {
    path: '/teacher',
    component: () => import('@/components/layout/TopNavLayout.vue'),
    meta: { auth: true, role: 'teacher' },
    children: [
      {
        path: 'classes',
        name: 'TeacherClasses',
        component: () => import('@/views/teacher/ClassManageView.vue'),
        meta: { title: '班级管理' },
      },
      {
        path: 'reports',
        name: 'TeacherReports',
        component: () => import('@/views/teacher/StudentReportView.vue'),
        meta: { title: '学生报告' },
      },
      {
        path: 'homework',
        name: 'TeacherHomework',
        component: () => import('@/views/teacher/HomeworkView.vue'),
        meta: { title: '作业管理' },
      },
    ],
  },

  // ========== 运营后台 ==========
  {
    path: '/admin',
    component: () => import('@/components/layout/TopNavLayout.vue'),
    meta: { auth: true, role: 'admin' },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
        meta: { title: '运营看板' },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UserManageView.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'content',
        name: 'AdminContent',
        component: () => import('@/views/admin/ContentManageView.vue'),
        meta: { title: '内容管理' },
      },
      {
        path: 'feedback',
        name: 'AdminFeedback',
        component: () => import('@/views/admin/FeedbackView.vue'),
        meta: { title: '反馈管理' },
      },
    ],
  },

  // ========== 404 ==========
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ========== 路由守卫 ==========
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 游客路由：已登录用户访问 / /login /register → 重定向到首页
  if (to.meta.guest && authStore.isLoggedIn) {
    return next('/')
  }

  // 需认证路由：未登录 → 重定向到首页（功能介绍页）
  if (to.meta.auth && !authStore.isLoggedIn) {
    return next('/')
  }

  // 角色检查：教师/管理员路由
  if (to.meta.role && authStore.userInfo?.role !== to.meta.role) {
    return next('/')
  }

  next()
})

export default router
