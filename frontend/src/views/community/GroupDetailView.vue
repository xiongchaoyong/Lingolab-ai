<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, UserFilled, Clock, Plus, ChatLineRound, Medal } from '@element-plus/icons-vue'
import { useCommunityStore } from '@/stores/community'

const route = useRoute()
const router = useRouter()
const store = useCommunityStore()

const groupId = ref(Number(route.params.id))
const newPostTopic = ref('')
const newPostContent = ref('')
const posting = ref(false)

onMounted(() => {
  store.fetchGroupDetail(groupId.value)
})

async function handleToggleJoin() {
  if (!store.groupDetail) return
  await store.toggleGroup(groupId.value)
  store.groupDetail.is_joined = !store.groupDetail.is_joined
  store.groupDetail.member_count += store.groupDetail.is_joined ? 1 : -1
}

async function handleCreatePost() {
  if (!newPostTopic.value.trim() || !newPostContent.value.trim()) return
  posting.value = true
  try {
    await store.createGroupPost(groupId.value, newPostTopic.value.trim(), newPostContent.value.trim())
    newPostTopic.value = ''
    newPostContent.value = ''
    ElMessage.success('发帖成功')
  } finally {
    posting.value = false
  }
}

function goBack() {
  router.push('/community')
}
</script>

<template>
  <div class="content-card group-detail" v-loading="store.groupDetailLoading">
    <!-- 返回 -->
    <div class="detail-header">
      <el-button text @click="goBack">
        <el-icon><ArrowLeft /></el-icon> 返回社区
      </el-button>
    </div>

    <template v-if="store.groupDetail">
      <!-- 小组信息 -->
      <div class="group-info">
        <div class="info-main">
          <h1 class="group-name">{{ store.groupDetail.name }}</h1>
          <p class="group-desc" v-if="store.groupDetail.description">{{ store.groupDetail.description }}</p>
          <div class="info-meta">
            <el-tag type="warning" size="large">{{ store.groupDetail.level }}</el-tag>
            <span class="meta-item"><el-icon><UserFilled /></el-icon> {{ store.groupDetail.member_count }} / {{ store.groupDetail.max_members }} 人</span>
            <span class="meta-item" v-if="store.groupDetail.schedule"><el-icon><Clock /></el-icon> {{ store.groupDetail.schedule }}</span>
          </div>
          <div class="info-tags" v-if="store.groupDetail.tags?.length">
            <el-tag v-for="t in store.groupDetail.tags" :key="t" size="small" effect="plain" round>{{ t }}</el-tag>
          </div>
        </div>
        <div class="info-action">
          <el-button
            :type="store.groupDetail.is_joined ? 'default' : 'primary'"
            size="large"
            @click="handleToggleJoin"
          >
            {{ store.groupDetail.is_joined ? '退出小组' : '加入小组' }}
          </el-button>
        </div>
      </div>

      <el-row :gutter="24">
        <!-- 成员列表 -->
        <el-col :span="8">
          <div class="section-card">
            <h3 class="section-title">
              <el-icon><UserFilled /></el-icon> 小组成员 ({{ store.groupMembers.length }})
            </h3>
            <div class="member-list">
              <div v-for="m in store.groupMembers" :key="m.user_id" class="member-item">
                <span class="member-avatar">{{ m.username?.charAt(0)?.toUpperCase() || '?' }}</span>
                <div class="member-info">
                  <span class="member-name">{{ m.username }}</span>
                  <el-tag v-if="m.role === 'owner'" size="small" type="warning" effect="dark">组长</el-tag>
                </div>
              </div>
              <div v-if="store.groupMembers.length === 0" class="empty-hint">暂无成员</div>
            </div>
          </div>
        </el-col>

        <!-- 小组帖子 -->
        <el-col :span="16">
          <div class="section-card">
            <h3 class="section-title">
              <el-icon><ChatLineRound /></el-icon> 小组讨论
            </h3>

            <!-- 发帖 -->
            <div class="post-form" v-if="store.groupDetail.is_joined">
              <el-input v-model="newPostTopic" placeholder="帖子标题" maxlength="200" style="margin-bottom: 8px" />
              <el-input v-model="newPostContent" type="textarea" :rows="3" placeholder="分享你的想法..." maxlength="2000" />
              <el-button type="primary" size="small" @click="handleCreatePost" :loading="posting" :disabled="!newPostTopic.trim() || !newPostContent.trim()" style="margin-top: 8px">
                <el-icon><Plus /></el-icon> 发帖
              </el-button>
            </div>
            <div v-else class="join-hint">
              加入小组后即可参与讨论
            </div>

            <!-- 帖子列表 -->
            <div class="post-list">
              <div v-for="post in store.groupPosts" :key="post.id" class="post-item">
                <h4>{{ post.topic }}</h4>
                <p class="post-content">{{ post.content }}</p>
                <div class="post-meta">
                  <span>{{ post.username || '用户' + post.user_id }}</span>
                  <span>{{ post.created_at?.slice(0, 10) }}</span>
                  <span>{{ post.comments_count }} 评论</span>
                </div>
              </div>
              <div v-if="store.groupPosts.length === 0" class="empty-hint">暂无讨论，快来发帖吧</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.group-detail {
  min-height: 60vh;
}

.detail-header {
  margin-bottom: var(--spacing-xl);
}

.group-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-xl);
  background: rgba(var(--color-primary-rgb), 0.04);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-xl);
}

.group-name {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: var(--spacing-sm);
}

.group-desc {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
  max-width: 600px;
}

.info-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;

  .meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
}

.info-tags {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.section-card {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-base);
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.member-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) 0;
}

.member-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.member-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  .member-name { font-size: var(--font-size-sm); font-weight: 500; }
}

.post-form {
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.join-hint {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.post-item {
  padding: var(--spacing-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  h4 { font-size: var(--font-size-base); margin-bottom: var(--spacing-xs); }
  .post-content { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--spacing-sm); }
  .post-meta { display: flex; gap: var(--spacing-lg); font-size: var(--font-size-xs); color: var(--color-text-disabled); }
}

.empty-hint {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>