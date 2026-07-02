# 数据库导出包

> 导出时间：2026-07-01 | 数据库：MySQL 8.0+ | 数据库名：english_training_dev

## 文件说明

| 文件 | 说明 |
|------|------|
| `full-dump-data+structure.sql` | **完整导出（数据+结构）**，405KB，可直接导入空库 |
| `schema-only.sql` | **仅表结构**，51KB，不含数据 |
| `init.sql` | 原始建库脚本（32张表 + 系统配置初始数据） |
| `420bb62f1724_初始化全部35张业务表.py` | Alembic 迁移脚本（35张业务表） |
| `env.py` | Alembic 环境配置 |
| `alembic-README` | Alembic 说明 |
| `model-files/` | SQLAlchemy ORM 模型文件（14个 Python 文件） |

## 数据库概览（43张表，含数据）

| 表名 | 行数 | 说明 |
|------|------|------|
| user_profiles | 11 | 用户表 |
| assessment_questions | 11 | 测评题库 |
| assessment_records | 38 | 测评记录 |
| pronunciation_content | 21 | 发音跟读内容 |
| pronunciation_records | 27 | 发音评测记录 |
| conversation_sessions | 103 | 对话会话 |
| conversation_messages | 135 | 对话消息 |
| daily_tasks | 55 | 每日任务 |
| learning_materials | 12 | 学习资料 |
| material_records | 9 | 学习资料记录 |
| material_recommendations | 714 | 资料推荐记录 |
| user_scores | 264 | 积分记录 |
| user_badges | 7 | 用户徽章 |
| user_skill_scores | 409 | 用户技能分数 |
| dubbing_content | 10 | 配音内容 |
| dubbing_records | 4 | 配音记录 |
| learning_predictions | 1 | 学习预测 |
| notices | 12 | 通知 |
| challenge_topics | 0 | 语音挑战 |
| challenge_submissions | 32 | 挑战参与 |
| challenge_participations | 0 | 挑战参与（旧） |
| voice_challenges | 6 | 语音挑战（新） |
| discussion_topics | 0 | 讨论主题 |
| discussion_posts | 7 | 讨论帖子 |
| discussion_comments | 0 | 讨论评论 |
| post_comments | 13 | 帖子评论 |
| post_likes | 4 | 帖子点赞 |
| groups | 8 | 学习小组 |
| group_members | 2 | 小组成员 |
| classes | 6 | 班级 |
| class_students | 16 | 班级学生 |
| assignments | 12 | 作业 |
| assignment_submissions | 26 | 作业提交 |
| admin_logs | 5 | 管理员操作日志 |
| faq_entries | 10 | FAQ条目 |
| customer_service_sessions | 0 | 客服会话（旧） |
| support_sessions | 0 | 客服会话 |
| system_config | 10 | 系统配置 |
| security_logs | 0 | 安全日志 |
| user_feedbacks | 5 | 用户反馈 |
| kg_nodes | 129 | 知识图谱节点 |
| kg_edges | 292 | 知识图谱边 |
| alembic_version | 1 | Alembic 版本记录 |

## 导入方式

### 方式一：MySQL 命令行导入（推荐）

```bash
# 导入完整数据（数据+结构）
mysql -u root -p < full-dump-data+structure.sql

# 或仅导入结构
mysql -u root -p < schema-only.sql
```

### 方式二：Alembic 迁移（仅结构）

```bash
cd backend
alembic upgrade head
```

### 方式三：手动执行 init.sql

```bash
mysql -u root -p < init.sql
```

## 注意事项

- 数据库字符集为 utf8mb4，需要 MySQL 8.0+
- `full-dump-data+structure.sql` 包含 `DROP TABLE IF EXISTS` 和 `CREATE DATABASE IF NOT EXISTS`，会覆盖同名数据库
- 导入前请确保没有同名数据库或已备份
- 种子数据包含：测评题、发音内容、配音内容、学习资料、FAQ、系统配置、知识图谱节点/边