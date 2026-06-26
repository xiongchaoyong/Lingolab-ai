-- ============================================================
-- Lingolab-ai 数据库初始化脚本
-- 版本: 1.0.0 | 日期: 2026-06-22
-- 数据库: MySQL 8.0+ | 字符集: utf8mb4 | 引擎: InnoDB
-- 基于《需求规格说明书》v1.0 数据字典 (3.9节)
-- ============================================================

CREATE DATABASE IF NOT EXISTS english_training_dev
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE english_training_dev;

-- ============================================================
-- 模块一：用户服务模块
-- ============================================================

-- 1. 用户表
CREATE TABLE user_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    age_group ENUM('儿童','青少年','大学生','职场','中老年') NOT NULL,
    learning_goal ENUM('日常交流','考试','商务','出国','兴趣爱好') NOT NULL,
    interests JSON DEFAULT NULL COMMENT '兴趣标签数组，如["音乐","旅行"]',
    level_self VARCHAR(10) DEFAULT NULL COMMENT '用户自评等级：初级/中级/高级',
    level_test VARCHAR(5) DEFAULT NULL COMMENT '测评CEFR等级：A1/A2/B1/B2/C1/C2',
    level_final VARCHAR(5) DEFAULT NULL COMMENT '综合等级，以level_test为准',
    role ENUM('learner','teacher','admin') NOT NULL DEFAULT 'learner',
    assessment_completed TINYINT(1) NOT NULL DEFAULT 0 COMMENT '0-未完成 1-已完成',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '0-禁用 1-正常',
    version INT NOT NULL DEFAULT 1 COMMENT '乐观锁版本号',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active),
    INDEX idx_level_final (level_final)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 2. 测评题库表
CREATE TABLE assessment_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_text TEXT NOT NULL,
    options JSON NOT NULL COMMENT '客观题选项数组，每题4个选项',
    correct_option TINYINT NOT NULL COMMENT '正确选项序号 1-4',
    dimension ENUM('listening','speaking','reading','grammar') NOT NULL,
    difficulty VARCHAR(5) NOT NULL COMMENT 'CEFR难度：A1/A2/B1/B2/C1/C2',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_dimension_difficulty (dimension, difficulty),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测评题库表';

-- 3. 测评记录表
CREATE TABLE assessment_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id VARCHAR(36) NOT NULL COMMENT '测评会话UUID，一次测评对应一个',
    question_id INT NOT NULL,
    question_type ENUM('multiple_choice','speaking') NOT NULL,
    user_answer TEXT DEFAULT NULL COMMENT '用户答案（选项ID 或 录音URL）',
    is_correct TINYINT(1) DEFAULT NULL COMMENT '客观题是否正确，口语题为NULL',
    score DECIMAL(5,2) DEFAULT NULL COMMENT '该题得分 0-100',
    audio_url VARCHAR(500) DEFAULT NULL COMMENT '口语题录音文件路径',
    transcript TEXT DEFAULT NULL COMMENT '口语题Whisper转写文本',
    question_order TINYINT NOT NULL COMMENT '题号 1-10',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作答时间',

    CONSTRAINT fk_assessment_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    CONSTRAINT fk_assessment_question FOREIGN KEY (question_id) REFERENCES assessment_questions(id),
    INDEX idx_user_session (user_id, session_id),
    INDEX idx_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测评记录表';

-- ============================================================
-- 模块二：学习服务模块
-- ============================================================

-- 4. 发音跟读内容表
CREATE TABLE pronunciation_content (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text VARCHAR(500) NOT NULL COMMENT '跟读文本（单词或句子）',
    ipa_transcription VARCHAR(500) DEFAULT NULL COMMENT '国际音标注音',
    phoneme_annotation JSON DEFAULT NULL COMMENT '音素级标注JSON',
    difficulty VARCHAR(5) NOT NULL COMMENT '难度等级：A1/A2/B1/B2',
    mode ENUM('word','sentence') NOT NULL,
    audio_url VARCHAR(500) NOT NULL COMMENT '标准音音频文件路径',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_difficulty_mode (difficulty, mode),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发音跟读内容表';

-- 5. 发音评测记录表
CREATE TABLE pronunciation_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content_id INT NOT NULL,
    mode ENUM('word','sentence') NOT NULL,
    audio_url VARCHAR(500) NOT NULL COMMENT '用户录音文件路径',
    transcript TEXT DEFAULT NULL COMMENT 'Whisper转写文本',
    accuracy_score DECIMAL(5,2) DEFAULT NULL COMMENT '音素准确度 0-100',
    stress_score DECIMAL(5,2) DEFAULT NULL COMMENT '重音位置分 0-100',
    liaison_score DECIMAL(5,2) DEFAULT NULL COMMENT '连读表现分 0-100（仅句子）',
    intonation_score DECIMAL(5,2) DEFAULT NULL COMMENT '语调曲线分 0-100',
    rhythm_score DECIMAL(5,2) DEFAULT NULL COMMENT '节奏感分 0-100',
    total_score DECIMAL(5,2) DEFAULT NULL COMMENT '加权综合分 0-100',
    error_phonemes JSON DEFAULT NULL COMMENT '错误音素列表JSON',
    feedback TEXT DEFAULT NULL COMMENT '中文纠音建议文本',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评测时间',

    CONSTRAINT fk_pron_record_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    CONSTRAINT fk_pron_record_content FOREIGN KEY (content_id) REFERENCES pronunciation_content(id),
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_content (content_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发音评测记录表';

-- 6. 对话会话表
CREATE TABLE conversation_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    scene_id INT NOT NULL COMMENT '场景ID：1-自我介绍/2-问路/3-购物/4-餐厅',
    role_id INT DEFAULT NULL COMMENT '角色ID（角色扮演会话用），NULL为普通对话',
    status ENUM('active','completed','abandoned') NOT NULL DEFAULT 'active',
    total_score DECIMAL(5,2) DEFAULT NULL COMMENT '对话结束综合评分',
    score_breakdown JSON DEFAULT NULL COMMENT '评分维度明细JSON',
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '对话开始时间',
    ended_at DATETIME DEFAULT NULL COMMENT '对话结束时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_conv_session_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    INDEX idx_user_status (user_id, status),
    INDEX idx_scene (scene_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话会话表';

-- 7. 对话消息表
CREATE TABLE conversation_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    role ENUM('user','ai') NOT NULL,
    text TEXT NOT NULL,
    audio_url VARCHAR(500) DEFAULT NULL COMMENT '语音消息文件路径',
    confidence DECIMAL(3,2) DEFAULT NULL COMMENT 'Whisper转写置信度 0-1',
    fluency_scores JSON DEFAULT NULL COMMENT '流利度五维评分JSON',
    grammar_check JSON DEFAULT NULL COMMENT '语法检查结果JSON（含纠错+润色）',
    message_order SMALLINT NOT NULL COMMENT '消息序号 1-10',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '消息时间',

    CONSTRAINT fk_conv_msg_session FOREIGN KEY (session_id) REFERENCES conversation_sessions(id),
    INDEX idx_session_order (session_id, message_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话消息表';

-- ============================================================
-- 模块三：个性化推荐服务模块
-- ============================================================

-- 8. 每日任务表
CREATE TABLE daily_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    task_date DATE NOT NULL,
    tasks JSON NOT NULL COMMENT '任务列表JSON[{type,content_id,title,duration,difficulty,scene,status}]',
    status ENUM('pending','partial','completed') NOT NULL DEFAULT 'pending',
    completed_at DATETIME DEFAULT NULL COMMENT '全部完成时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_task_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    UNIQUE KEY uk_user_date (user_id, task_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日任务表';

-- 9. 学习资料表
CREATE TABLE learning_materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    url VARCHAR(500) NOT NULL,
    type ENUM('video','article','audio') NOT NULL,
    difficulty VARCHAR(5) NOT NULL COMMENT 'CEFR难度：A1/A2/B1/B2',
    related_dimension ENUM('pronunciation','listening','grammar','fluency') NOT NULL,
    tags JSON DEFAULT NULL COMMENT '内容标签数组JSON',
    duration SMALLINT DEFAULT NULL COMMENT '时长（分钟），视频/音频适用',
    word_count SMALLINT DEFAULT NULL COMMENT '词数，文章适用',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_type_difficulty (type, difficulty),
    INDEX idx_dimension (related_dimension),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习资料表';

-- 10. 学习资料记录表
CREATE TABLE material_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    material_id INT NOT NULL,
    action ENUM('view','complete','dislike') NOT NULL,
    duration SMALLINT DEFAULT NULL COMMENT '实际学习时长（秒）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mat_record_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    CONSTRAINT fk_mat_record_material FOREIGN KEY (material_id) REFERENCES learning_materials(id),
    INDEX idx_user_action (user_id, action),
    INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习资料记录表';

-- ============================================================
-- 模块四：激励服务模块
-- ============================================================

-- 11. 积分记录表
CREATE TABLE user_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action_type VARCHAR(50) NOT NULL COMMENT '积分行为：daily_task/challenge/dubbing/streak/pronunciation_high/share',
    score SMALLINT NOT NULL COMMENT '积分变化值（正为获得，负为扣除）',
    description VARCHAR(200) DEFAULT '' COMMENT '积分说明文字',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_score_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_action_type (action_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='积分记录表';

-- 12. 用户徽章表
CREATE TABLE user_badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    badge_type VARCHAR(50) NOT NULL COMMENT '徽章类型：newcomer/streak/pronunciation_break/progress/dubbing/perfect/scholar',
    badge_name VARCHAR(50) NOT NULL COMMENT '徽章名称：新手上路/坚持之星/发音突破/进步达人/配音达人/满分挑战/学霸成就',
    awarded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_badge_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    UNIQUE KEY uk_user_badge (user_id, badge_type),
    INDEX idx_badge_type (badge_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户徽章表';

-- 13. 配音内容表
CREATE TABLE dubbing_content (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    source VARCHAR(100) DEFAULT '' COMMENT '来源：电影/动画/演讲名称',
    difficulty ENUM('easy','medium','hard') NOT NULL,
    duration TINYINT NOT NULL COMMENT '片段时长（秒）5-20',
    subtitle VARCHAR(500) NOT NULL,
    audio_url VARCHAR(500) NOT NULL COMMENT '原声片段文件路径',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_difficulty (difficulty),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配音内容表';

-- 14. 配音记录表
CREATE TABLE dubbing_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content_id INT NOT NULL,
    audio_url VARCHAR(500) NOT NULL COMMENT '用户配音文件路径',
    pronunciation_score DECIMAL(5,2) DEFAULT NULL COMMENT '发音相似度 0-100',
    intonation_score DECIMAL(5,2) DEFAULT NULL COMMENT '语调相似度 0-100',
    emotion_score DECIMAL(5,2) DEFAULT NULL COMMENT '情感匹配度 0-100',
    total_score DECIMAL(5,2) DEFAULT NULL COMMENT '综合评分 0-100',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '配音时间',

    CONSTRAINT fk_dub_record_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    CONSTRAINT fk_dub_record_content FOREIGN KEY (content_id) REFERENCES dubbing_content(id),
    INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配音记录表';

-- 15. 学习预测表
CREATE TABLE learning_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    current_score DECIMAL(5,2) NOT NULL COMMENT '当前综合分数 0-100',
    trend_slope DECIMAL(6,3) DEFAULT NULL COMMENT '趋势斜率（分/天），正为上升',
    target_score DECIMAL(5,2) NOT NULL COMMENT '目标分数',
    predicted_days SMALLINT DEFAULT NULL COMMENT '预计达标天数',
    predicted_date DATE DEFAULT NULL COMMENT '预计达标日期',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '预测更新时间',

    CONSTRAINT fk_prediction_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    UNIQUE KEY uk_user (user_id),
    INDEX idx_predicted_date (predicted_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习预测表';

-- 16. 通知表
CREATE TABLE notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('prediction','alert','achievement') NOT NULL,
    title VARCHAR(100) NOT NULL,
    message VARCHAR(500) NOT NULL,
    level ENUM('info','warning') NOT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0 COMMENT '0-未读 1-已读',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_notice_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    INDEX idx_user_read (user_id, is_read),
    INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知表';

-- ============================================================
-- 模块五：社区服务模块
-- ============================================================

-- 17. 语音挑战表
CREATE TABLE challenge_topics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '发起人用户ID',
    content_text VARCHAR(500) NOT NULL COMMENT '挑战跟读文本',
    audio_url VARCHAR(500) NOT NULL COMMENT '发起人示范录音',
    status ENUM('active','ended') NOT NULL DEFAULT 'active',
    participant_count SMALLINT NOT NULL DEFAULT 0,
    expires_at DATETIME NOT NULL COMMENT '过期时间（创建后7天）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_challenge_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    INDEX idx_status_expires (status, expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='语音挑战表';

-- 18. 挑战参与表
CREATE TABLE challenge_participations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    challenge_id INT NOT NULL,
    user_id INT NOT NULL,
    audio_url VARCHAR(500) NOT NULL COMMENT '参与录音文件',
    pronunciation_score DECIMAL(5,2) DEFAULT NULL COMMENT '发音评分 0-100',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_chal_part_challenge FOREIGN KEY (challenge_id) REFERENCES challenge_topics(id),
    CONSTRAINT fk_chal_part_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    UNIQUE KEY uk_challenge_user (challenge_id, user_id),
    INDEX idx_challenge_score (challenge_id, pronunciation_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='挑战参与表';

-- 19. 讨论主题表
CREATE TABLE discussion_topics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL COMMENT '分类：learning/experience/question/sharing',
    view_count INT NOT NULL DEFAULT 0,
    comment_count SMALLINT NOT NULL DEFAULT 0,
    is_pinned TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_topic_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    INDEX idx_category (category),
    INDEX idx_is_pinned_created (is_pinned, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='讨论主题表';

-- 20. 讨论评论表
CREATE TABLE discussion_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    parent_id INT DEFAULT NULL COMMENT '父评论ID（回复嵌套），NULL为顶级',
    is_reported TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_comment_topic FOREIGN KEY (topic_id) REFERENCES discussion_topics(id),
    CONSTRAINT fk_comment_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    CONSTRAINT fk_comment_parent FOREIGN KEY (parent_id) REFERENCES discussion_comments(id),
    INDEX idx_topic_created (topic_id, created_at),
    INDEX idx_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='讨论评论表';

-- 21. 学习小组表
CREATE TABLE `groups` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500) DEFAULT '',
    creator_id INT NOT NULL,
    level_range VARCHAR(20) DEFAULT '' COMMENT '等级范围如 A1-B1',
    max_members SMALLINT NOT NULL DEFAULT 20,
    member_count SMALLINT NOT NULL DEFAULT 0,
    is_archived TINYINT(1) NOT NULL DEFAULT 0 COMMENT '0-正常 1-已归档',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_group_creator FOREIGN KEY (creator_id) REFERENCES user_profiles(id),
    INDEX idx_is_archived (is_archived),
    INDEX idx_level_range (level_range)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习小组表';

-- 22. 小组成员表
CREATE TABLE group_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    role ENUM('owner','member') NOT NULL DEFAULT 'member',
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_gm_group FOREIGN KEY (group_id) REFERENCES `groups`(id),
    CONSTRAINT fk_gm_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    UNIQUE KEY uk_group_user (group_id, user_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='小组成员表';

-- ============================================================
-- 模块六：后台管理服务模块
-- ============================================================

-- 23. 班级表
CREATE TABLE classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500) DEFAULT '',
    teacher_id INT NOT NULL,
    invite_code VARCHAR(20) NOT NULL COMMENT '邀请码（唯一）',
    invite_expires_at DATETIME DEFAULT NULL COMMENT '邀请码过期时间',
    level_range VARCHAR(20) DEFAULT '' COMMENT '等级范围',
    student_count SMALLINT NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_class_teacher FOREIGN KEY (teacher_id) REFERENCES user_profiles(id),
    UNIQUE KEY uk_invite_code (invite_code),
    INDEX idx_teacher (teacher_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级表';

-- 24. 班级学生表
CREATE TABLE class_students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    user_id INT NOT NULL,
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_cs_class FOREIGN KEY (class_id) REFERENCES classes(id),
    CONSTRAINT fk_cs_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    UNIQUE KEY uk_class_user (class_id, user_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级学生表';

-- 25. 作业表
CREATE TABLE assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    content_type ENUM('pronunciation','conversation','dubbing') NOT NULL,
    content_ids JSON NOT NULL COMMENT '指定内容ID数组',
    due_date DATETIME DEFAULT NULL COMMENT '截止时间',
    completion_rate DECIMAL(4,1) NOT NULL DEFAULT 0.0 COMMENT '完成率百分比',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_assignment_class FOREIGN KEY (class_id) REFERENCES classes(id),
    INDEX idx_class_due (class_id, due_date),
    INDEX idx_due_date (due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业表';

-- 26. 作业提交表
CREATE TABLE assignment_submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT NOT NULL,
    user_id INT NOT NULL,
    audio_url VARCHAR(500) DEFAULT NULL COMMENT '录音文件路径',
    score DECIMAL(5,2) DEFAULT NULL COMMENT 'AI评分 0-100',
    teacher_feedback TEXT DEFAULT NULL COMMENT '教师点评文字',
    teacher_score DECIMAL(5,2) DEFAULT NULL COMMENT '教师评分 0-100',
    status ENUM('submitted','reviewed') NOT NULL DEFAULT 'submitted',
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sub_assignment FOREIGN KEY (assignment_id) REFERENCES assignments(id),
    CONSTRAINT fk_sub_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    UNIQUE KEY uk_assignment_user (assignment_id, user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业提交表';

-- 27. 管理员操作日志表
CREATE TABLE admin_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    action VARCHAR(100) NOT NULL COMMENT '操作类型：user_disable/content_edit/class_create等',
    target_type VARCHAR(50) NOT NULL COMMENT '操作对象类型：user/content/class等',
    target_id INT DEFAULT NULL COMMENT '操作对象ID',
    detail TEXT COMMENT '操作详情JSON',
    ip_address VARCHAR(45) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',

    CONSTRAINT fk_admin_log_user FOREIGN KEY (admin_id) REFERENCES user_profiles(id),
    INDEX idx_admin_created (admin_id, created_at),
    INDEX idx_action (action),
    INDEX idx_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员操作日志表';

-- ============================================================
-- 模块七：智能客服服务模块
-- ============================================================

-- 28. FAQ条目表
CREATE TABLE faq_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question VARCHAR(500) NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(50) NOT NULL COMMENT '分类：product_use/study_advice/tech_issue/account',
    priority TINYINT NOT NULL DEFAULT 0 COMMENT '展示优先级，越大越靠前',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_category_priority (category, priority),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='FAQ条目表';

-- 29. 客服会话表
CREATE TABLE customer_service_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(50) DEFAULT NULL COMMENT '问题分类：product_use/study_advice/tech_issue/refund/off_topic',
    need_manual TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否需要转人工',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_cs_session_user FOREIGN KEY (user_id) REFERENCES user_profiles(id),
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_category (category),
    INDEX idx_need_manual (need_manual)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客服会话表';

-- ============================================================
-- 安全与系统配置
-- ============================================================

-- 30. 安全日志表
CREATE TABLE security_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT NULL COMMENT '关联用户（可为空，匿名违规记录）',
    event_type VARCHAR(50) NOT NULL COMMENT '事件类型：sensitive_word/abnormal_request/violation',
    detail TEXT NOT NULL COMMENT '事件详情（问题文本/行为描述）',
    ip_address VARCHAR(45) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_event_type (event_type),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='安全日志表';

-- 31. 用户反馈表
CREATE TABLE IF NOT EXISTS user_feedbacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    content TEXT NOT NULL COMMENT '反馈内容',
    feedback_type ENUM('bug','feature','scene','other') NOT NULL DEFAULT 'other' COMMENT '反馈类型',
    status ENUM('pending','resolved') NOT NULL DEFAULT 'pending' COMMENT '处理状态',
    admin_reply TEXT DEFAULT NULL COMMENT '管理员回复',
    replied_at DATETIME DEFAULT NULL COMMENT '回复时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at),
    FOREIGN KEY (user_id) REFERENCES user_profiles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户反馈表';

-- 32. 系统配置表（文档多处引用但数据字典未定义，根据需求补充）
CREATE TABLE system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL COMMENT '配置键名',
    config_value TEXT NOT NULL COMMENT '配置值',
    config_type ENUM('string','integer','boolean','json') NOT NULL DEFAULT 'string',
    description VARCHAR(200) DEFAULT '' COMMENT '配置说明',
    is_public TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否可公开（0-仅管理员 1-前端可读）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ============================================================
-- 初始化默认系统配置
-- ============================================================
INSERT INTO system_config (config_key, config_value, config_type, description, is_public) VALUES
('deepseek_api_key', '', 'string', 'Deepseek API Key', 0),
('deepseek_model', 'deepseek-v4-flash', 'string', 'Deepseek模型名称', 0),
('whisper_model', 'small', 'string', 'WhisperX模型大小', 0),
('tts_voice', 'en-US-JennyNeural', 'string', 'Edge TTS默认音色', 1),
('assessment_question_count', '10', 'integer', '测评题目数量', 1),
('daily_task_count', '3', 'integer', '每日任务数量', 1),
('conversation_max_rounds', '10', 'integer', '对话最大轮数', 1),
('max_audio_duration', '30', 'integer', '单次录音最大时长（秒）', 1),
('jwt_expire_hours', '24', 'integer', 'JWT过期时间（小时）', 0),
('challenge_expire_days', '7', 'integer', '语音挑战过期天数', 1);