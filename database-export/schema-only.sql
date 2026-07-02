mysqldump: [Warning] Using a password on the command line interface can be insecure.
-- MySQL dump 10.13  Distrib 8.0.45, for macos15.7 (arm64)
--
-- Host: localhost    Database: english_training_dev
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admin_logs`
--

DROP TABLE IF EXISTS `admin_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `admin_id` int NOT NULL,
  `action` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作类型：user_disable/content_edit/class_create等',
  `target_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作对象类型：user/content/class等',
  `target_id` int DEFAULT NULL COMMENT '操作对象ID',
  `detail` text COLLATE utf8mb4_unicode_ci COMMENT '操作详情JSON',
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  PRIMARY KEY (`id`),
  KEY `idx_admin_created` (`admin_id`,`created_at`),
  KEY `idx_action` (`action`),
  KEY `idx_target` (`target_type`,`target_id`),
  CONSTRAINT `fk_admin_log_user` FOREIGN KEY (`admin_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员操作日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `assessment_questions`
--

DROP TABLE IF EXISTS `assessment_questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assessment_questions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `question_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `options` json NOT NULL COMMENT '客观题选项数组，每题4个选项',
  `correct_option` tinyint NOT NULL COMMENT '正确选项序号 1-4',
  `dimension` enum('listening','speaking','reading','grammar') COLLATE utf8mb4_unicode_ci NOT NULL,
  `difficulty` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'CEFR难度：A1/A2/B1/B2/C1/C2',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_dimension_difficulty` (`dimension`,`difficulty`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测评题库表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `assessment_records`
--

DROP TABLE IF EXISTS `assessment_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assessment_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `session_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '测评会话UUID，一次测评对应一个',
  `question_id` int NOT NULL,
  `question_type` enum('multiple_choice','speaking') COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_answer` text COLLATE utf8mb4_unicode_ci COMMENT '用户答案（选项ID 或 录音URL）',
  `is_correct` tinyint(1) DEFAULT NULL COMMENT '客观题是否正确，口语题为NULL',
  `score` decimal(5,2) DEFAULT NULL COMMENT '该题得分 0-100',
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '口语题录音文件路径',
  `transcript` text COLLATE utf8mb4_unicode_ci COMMENT '口语题Whisper转写文本',
  `question_order` tinyint NOT NULL COMMENT '题号 1-10',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作答时间',
  PRIMARY KEY (`id`),
  KEY `fk_assessment_question` (`question_id`),
  KEY `idx_user_session` (`user_id`,`session_id`),
  KEY `idx_session` (`session_id`),
  CONSTRAINT `fk_assessment_question` FOREIGN KEY (`question_id`) REFERENCES `assessment_questions` (`id`),
  CONSTRAINT `fk_assessment_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测评记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `assignment_submissions`
--

DROP TABLE IF EXISTS `assignment_submissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assignment_submissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `assignment_id` int NOT NULL,
  `user_id` int NOT NULL,
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '录音文件路径',
  `score` decimal(5,2) DEFAULT NULL COMMENT 'AI评分 0-100',
  `teacher_feedback` text COLLATE utf8mb4_unicode_ci COMMENT '教师点评文字',
  `teacher_score` decimal(5,2) DEFAULT NULL COMMENT '教师评分 0-100',
  `status` enum('submitted','reviewed') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'submitted',
  `submitted_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_assignment_user` (`assignment_id`,`user_id`),
  KEY `fk_sub_user` (`user_id`),
  KEY `idx_status` (`status`),
  CONSTRAINT `fk_sub_assignment` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`),
  CONSTRAINT `fk_sub_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业提交表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `assignments`
--

DROP TABLE IF EXISTS `assignments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `class_id` int NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `content_type` enum('pronunciation','conversation','dubbing') COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_ids` json NOT NULL COMMENT '指定内容ID数组',
  `due_date` datetime DEFAULT NULL COMMENT '截止时间',
  `completion_rate` decimal(4,1) NOT NULL DEFAULT '0.0' COMMENT '完成率百分比',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_class_due` (`class_id`,`due_date`),
  KEY `idx_due_date` (`due_date`),
  CONSTRAINT `fk_assignment_class` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `challenge_participations`
--

DROP TABLE IF EXISTS `challenge_participations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `challenge_participations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `challenge_id` int NOT NULL,
  `user_id` int NOT NULL,
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '参与录音文件',
  `pronunciation_score` decimal(5,2) DEFAULT NULL COMMENT '发音评分 0-100',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_challenge_user` (`challenge_id`,`user_id`),
  KEY `fk_chal_part_user` (`user_id`),
  KEY `idx_challenge_score` (`challenge_id`,`pronunciation_score`),
  CONSTRAINT `fk_chal_part_challenge` FOREIGN KEY (`challenge_id`) REFERENCES `challenge_topics` (`id`),
  CONSTRAINT `fk_chal_part_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='挑战参与表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `challenge_submissions`
--

DROP TABLE IF EXISTS `challenge_submissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `challenge_submissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `challenge_id` int NOT NULL,
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户录音文件路径',
  `pronunciation_score` smallint DEFAULT NULL COMMENT '发音分 0-100',
  `fluency_score` smallint DEFAULT NULL COMMENT '流利度分 0-100',
  `total_score` smallint DEFAULT NULL COMMENT '综合分 0-100',
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `challenge_id` (`challenge_id`),
  CONSTRAINT `challenge_submissions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`),
  CONSTRAINT `challenge_submissions_ibfk_2` FOREIGN KEY (`challenge_id`) REFERENCES `voice_challenges` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `challenge_topics`
--

DROP TABLE IF EXISTS `challenge_topics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `challenge_topics` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT '发起人用户ID',
  `content_text` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '挑战跟读文本',
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发起人示范录音',
  `status` enum('active','ended') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
  `participant_count` smallint NOT NULL DEFAULT '0',
  `expires_at` datetime NOT NULL COMMENT '过期时间（创建后7天）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_challenge_user` (`user_id`),
  KEY `idx_status_expires` (`status`,`expires_at`),
  CONSTRAINT `fk_challenge_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='语音挑战表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `class_students`
--

DROP TABLE IF EXISTS `class_students`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `class_students` (
  `id` int NOT NULL AUTO_INCREMENT,
  `class_id` int NOT NULL,
  `user_id` int NOT NULL,
  `joined_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_class_user` (`class_id`,`user_id`),
  KEY `idx_user` (`user_id`),
  CONSTRAINT `fk_cs_class` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`),
  CONSTRAINT `fk_cs_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级学生表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `classes`
--

DROP TABLE IF EXISTS `classes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `classes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `teacher_id` int NOT NULL,
  `invite_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邀请码（唯一）',
  `invite_expires_at` datetime DEFAULT NULL COMMENT '邀请码过期时间',
  `level_range` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '等级范围',
  `student_count` smallint NOT NULL DEFAULT '0',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_invite_code` (`invite_code`),
  KEY `idx_teacher` (`teacher_id`),
  KEY `idx_is_active` (`is_active`),
  CONSTRAINT `fk_class_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `conversation_messages`
--

DROP TABLE IF EXISTS `conversation_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conversation_messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` int NOT NULL,
  `round_number` int NOT NULL DEFAULT '0',
  `content_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` enum('user','assistant') COLLATE utf8mb4_unicode_ci NOT NULL,
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '语音消息文件路径',
  `fluency_scores` json DEFAULT NULL COMMENT '流利度五维评分JSON',
  `score` decimal(5,2) DEFAULT NULL,
  `grammar_check` json DEFAULT NULL COMMENT '语法检查结果JSON（含纠错+润色）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '消息时间',
  PRIMARY KEY (`id`),
  KEY `idx_session_order` (`session_id`),
  CONSTRAINT `fk_conv_msg_session` FOREIGN KEY (`session_id`) REFERENCES `conversation_sessions` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=136 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话消息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `conversation_sessions`
--

DROP TABLE IF EXISTS `conversation_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conversation_sessions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `session_uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `scene` enum('self_intro','directions','shopping','restaurant','free','hotel','airport','hospital','school') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'free' COMMENT '对话场景',
  `role_id` int DEFAULT NULL COMMENT '角色ID（角色扮演会话用），NULL为普通对话',
  `cefr_level` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `round_count` int DEFAULT '0',
  `score_pronunciation` decimal(5,2) DEFAULT NULL,
  `score_grammar` decimal(5,2) DEFAULT NULL,
  `score_vocabulary` decimal(5,2) DEFAULT NULL,
  `score_engagement` decimal(5,2) DEFAULT NULL,
  `score_overall` decimal(5,2) DEFAULT NULL,
  `improvement_suggestions` text COLLATE utf8mb4_unicode_ci,
  `status` enum('active','completed','abandoned') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
  `started_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '对话开始时间',
  `ended_at` datetime DEFAULT NULL COMMENT '对话结束时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_session_uuid` (`session_uuid`),
  KEY `idx_user_status` (`user_id`,`status`),
  CONSTRAINT `fk_conv_session_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话会话表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer_service_sessions`
--

DROP TABLE IF EXISTS `customer_service_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_service_sessions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `question` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `answer` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '问题分类：product_use/study_advice/tech_issue/refund/off_topic',
  `need_manual` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否需要转人工',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_created` (`user_id`,`created_at`),
  KEY `idx_category` (`category`),
  KEY `idx_need_manual` (`need_manual`),
  CONSTRAINT `fk_cs_session_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客服会话表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daily_tasks`
--

DROP TABLE IF EXISTS `daily_tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily_tasks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `task_date` date NOT NULL COMMENT '任务日期',
  `task_type` enum('shadowing','conversation','listening') COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务标题',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '任务描述',
  `difficulty` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'CEFR 难度',
  `focus_skill_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '聚焦技能节点',
  `material_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联资料节点',
  `scene` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '对话场景 self_intro/restaurant/...',
  `status` enum('pending','skipped','completed') COLLATE utf8mb4_unicode_ci NOT NULL,
  `score` decimal(5,2) DEFAULT NULL COMMENT '完成得分',
  `duration_seconds` int DEFAULT NULL COMMENT '完成耗时（秒）',
  `skip_reason` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '跳过原因',
  `completed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `focus_skill_id` (`focus_skill_id`),
  KEY `material_id` (`material_id`),
  CONSTRAINT `daily_tasks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`),
  CONSTRAINT `daily_tasks_ibfk_2` FOREIGN KEY (`focus_skill_id`) REFERENCES `kg_nodes` (`id`),
  CONSTRAINT `daily_tasks_ibfk_3` FOREIGN KEY (`material_id`) REFERENCES `kg_nodes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=179 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `discussion_comments`
--

DROP TABLE IF EXISTS `discussion_comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `discussion_comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `topic_id` int NOT NULL,
  `user_id` int NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `parent_id` int DEFAULT NULL COMMENT '父评论ID（回复嵌套），NULL为顶级',
  `is_reported` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_comment_user` (`user_id`),
  KEY `idx_topic_created` (`topic_id`,`created_at`),
  KEY `idx_parent` (`parent_id`),
  CONSTRAINT `fk_comment_parent` FOREIGN KEY (`parent_id`) REFERENCES `discussion_comments` (`id`),
  CONSTRAINT `fk_comment_topic` FOREIGN KEY (`topic_id`) REFERENCES `discussion_topics` (`id`),
  CONSTRAINT `fk_comment_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='讨论评论表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `discussion_posts`
--

DROP TABLE IF EXISTS `discussion_posts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `discussion_posts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `topic` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '帖子标题',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '帖子内容',
  `likes_count` int DEFAULT NULL COMMENT '点赞数',
  `comments_count` int DEFAULT NULL COMMENT '评论数',
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `discussion_posts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `discussion_topics`
--

DROP TABLE IF EXISTS `discussion_topics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `discussion_topics` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分类：learning/experience/question/sharing',
  `view_count` int NOT NULL DEFAULT '0',
  `comment_count` smallint NOT NULL DEFAULT '0',
  `is_pinned` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_topic_user` (`user_id`),
  KEY `idx_category` (`category`),
  KEY `idx_is_pinned_created` (`is_pinned`,`created_at`),
  CONSTRAINT `fk_topic_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='讨论主题表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dubbing_content`
--

DROP TABLE IF EXISTS `dubbing_content`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dubbing_content` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '来源：电影/动画/演讲名称',
  `difficulty` enum('easy','medium','hard') COLLATE utf8mb4_unicode_ci NOT NULL,
  `duration` tinyint NOT NULL COMMENT '片段时长（秒）5-20',
  `subtitle` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_difficulty` (`difficulty`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配音内容表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dubbing_records`
--

DROP TABLE IF EXISTS `dubbing_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dubbing_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `content_id` int NOT NULL,
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户配音文件路径',
  `pronunciation_score` decimal(5,2) DEFAULT NULL COMMENT '发音相似度 0-100',
  `intonation_score` decimal(5,2) DEFAULT NULL COMMENT '语调相似度 0-100',
  `emotion_score` decimal(5,2) DEFAULT NULL COMMENT '情感匹配度 0-100',
  `total_score` decimal(5,2) DEFAULT NULL COMMENT '综合评分 0-100',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '配音时间',
  PRIMARY KEY (`id`),
  KEY `fk_dub_record_content` (`content_id`),
  KEY `idx_user_created` (`user_id`,`created_at`),
  CONSTRAINT `fk_dub_record_content` FOREIGN KEY (`content_id`) REFERENCES `dubbing_content` (`id`),
  CONSTRAINT `fk_dub_record_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配音记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `faq_entries`
--

DROP TABLE IF EXISTS `faq_entries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `faq_entries` (
  `id` int NOT NULL AUTO_INCREMENT,
  `question` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `answer` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` enum('product_use','study_advice','tech_issue','refund','general') COLLATE utf8mb4_unicode_ci NOT NULL,
  `sort_order` int DEFAULT '0',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_category_priority` (`category`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='FAQ条目表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `group_members`
--

DROP TABLE IF EXISTS `group_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `group_members` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `user_id` int NOT NULL,
  `role` enum('owner','member') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'member',
  `joined_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_group_user` (`group_id`,`user_id`),
  KEY `idx_user` (`user_id`),
  CONSTRAINT `fk_gm_group` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`),
  CONSTRAINT `fk_gm_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='小组成员表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `creator_id` int NOT NULL,
  `level_range` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '等级范围如 A1-B1',
  `schedule` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `tags` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `max_members` smallint NOT NULL DEFAULT '20',
  `member_count` smallint NOT NULL DEFAULT '0',
  `is_archived` tinyint(1) NOT NULL DEFAULT '0' COMMENT '0-正常 1-已归档',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_group_creator` (`creator_id`),
  KEY `idx_is_archived` (`is_archived`),
  KEY `idx_level_range` (`level_range`),
  CONSTRAINT `fk_group_creator` FOREIGN KEY (`creator_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习小组表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kg_edges`
--

DROP TABLE IF EXISTS `kg_edges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kg_edges` (
  `id` int NOT NULL AUTO_INCREMENT,
  `source_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `target_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `relation` enum('HAS_PREREQ','BELONGS_TO','TEACHES','COVERS','SIMILAR_TO','PRACTICES') COLLATE utf8mb4_unicode_ci NOT NULL,
  `weight` decimal(5,2) DEFAULT NULL COMMENT '权重 0.00-1.00',
  `extra_data` json DEFAULT NULL COMMENT '附加属性',
  `is_active` int NOT NULL,
  `created_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `source_id` (`source_id`),
  KEY `target_id` (`target_id`),
  CONSTRAINT `kg_edges_ibfk_1` FOREIGN KEY (`source_id`) REFERENCES `kg_nodes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `kg_edges_ibfk_2` FOREIGN KEY (`target_id`) REFERENCES `kg_nodes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=492 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kg_nodes`
--

DROP TABLE IF EXISTS `kg_nodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kg_nodes` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '节点 ID，如 skill:th_sound, material:video_1',
  `type` enum('skill','material','topic','cefr_level','task_type') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '节点类型',
  `sub_type` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '子类型：phoneme/grammar/vocabulary/video/article/audio/scene',
  `label` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '显示名称',
  `extra_data` json DEFAULT NULL COMMENT '附加属性',
  `is_active` int NOT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `learning_materials`
--

DROP TABLE IF EXISTS `learning_materials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `learning_materials` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `material_type` enum('video','article','audio') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'article',
  `cefr_level` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'A1',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `duration_seconds` int DEFAULT NULL,
  `focus_dimensions` json DEFAULT NULL,
  `url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tags` json DEFAULT NULL COMMENT '内容标签数组JSON',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习资料表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `learning_predictions`
--

DROP TABLE IF EXISTS `learning_predictions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `learning_predictions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `current_score` decimal(5,2) NOT NULL COMMENT '当前综合分数 0-100',
  `trend_slope` decimal(6,3) DEFAULT NULL COMMENT '趋势斜率（分/天），正为上升',
  `target_score` decimal(5,2) NOT NULL COMMENT '目标分数',
  `predicted_days` smallint DEFAULT NULL COMMENT '预计达标天数',
  `predicted_date` date DEFAULT NULL COMMENT '预计达标日期',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '预测更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user` (`user_id`),
  KEY `idx_predicted_date` (`predicted_date`),
  CONSTRAINT `fk_prediction_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习预测表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `material_recommendations`
--

DROP TABLE IF EXISTS `material_recommendations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `material_recommendations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `material_node_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `recommend_date` date NOT NULL,
  `recommend_score` decimal(5,2) NOT NULL COMMENT '推荐综合分 0-100',
  `reason_tags` json DEFAULT NULL COMMENT '推荐原因标签数组',
  `action` enum('pending','viewed','completed','disliked') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `viewed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `material_node_id` (`material_node_id`),
  CONSTRAINT `material_recommendations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`),
  CONSTRAINT `material_recommendations_ibfk_2` FOREIGN KEY (`material_node_id`) REFERENCES `kg_nodes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=715 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `material_records`
--

DROP TABLE IF EXISTS `material_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `material_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `material_id` int NOT NULL,
  `action` enum('viewed','completed','disliked') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'viewed',
  `duration_seconds` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_mat_record_material` (`material_id`),
  KEY `idx_user_action` (`user_id`,`action`),
  KEY `idx_user_created` (`user_id`,`created_at`),
  CONSTRAINT `fk_mat_record_material` FOREIGN KEY (`material_id`) REFERENCES `learning_materials` (`id`),
  CONSTRAINT `fk_mat_record_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习资料记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notices`
--

DROP TABLE IF EXISTS `notices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `type` enum('prediction','alert','achievement','inactive_3days','duration_drop','no_improvement','system') COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `level` enum('info','warning') COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT '0' COMMENT '0-未读 1-已读',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_read` (`user_id`,`is_read`),
  KEY `idx_user_created` (`user_id`,`created_at`),
  CONSTRAINT `fk_notice_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `post_comments`
--

DROP TABLE IF EXISTS `post_comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `post_comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `post_id` int NOT NULL,
  `user_id` int NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '评论内容',
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `post_id` (`post_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `post_comments_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `discussion_posts` (`id`),
  CONSTRAINT `post_comments_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `post_likes`
--

DROP TABLE IF EXISTS `post_likes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `post_likes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `post_id` int NOT NULL,
  `user_id` int NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `post_id` (`post_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `post_likes_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `discussion_posts` (`id`),
  CONSTRAINT `post_likes_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pronunciation_content`
--

DROP TABLE IF EXISTS `pronunciation_content`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pronunciation_content` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `content_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type` enum('word','sentence') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'word',
  `cefr_level` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'A1',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phonetic_ipa` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tags` json DEFAULT NULL,
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发音跟读内容表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pronunciation_records`
--

DROP TABLE IF EXISTS `pronunciation_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pronunciation_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `content_id` int NOT NULL,
  `mode` enum('word','sentence') COLLATE utf8mb4_unicode_ci NOT NULL,
  `overall_score` decimal(5,2) NOT NULL DEFAULT '0.00',
  `phoneme_score` decimal(5,2) DEFAULT NULL,
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户录音文件路径',
  `transcript` text COLLATE utf8mb4_unicode_ci COMMENT 'Whisper转写文本',
  `stress_score` decimal(5,2) DEFAULT NULL COMMENT '重音位置分 0-100',
  `linking_score` decimal(5,2) DEFAULT NULL,
  `intonation_score` decimal(5,2) DEFAULT NULL COMMENT '语调曲线分 0-100',
  `rhythm_score` decimal(5,2) DEFAULT NULL COMMENT '节奏感分 0-100',
  `error_phonemes` json DEFAULT NULL COMMENT '错误音素列表JSON',
  `correction_advice` text COLLATE utf8mb4_unicode_ci,
  `teacher_review` text COLLATE utf8mb4_unicode_ci,
  `teacher_score` decimal(5,2) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评测时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_created` (`user_id`,`created_at`),
  KEY `idx_content` (`content_id`),
  CONSTRAINT `fk_pron_record_content` FOREIGN KEY (`content_id`) REFERENCES `pronunciation_content` (`id`),
  CONSTRAINT `fk_pron_record_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发音评测记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `security_logs`
--

DROP TABLE IF EXISTS `security_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `security_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL COMMENT '关联用户（可为空，匿名违规记录）',
  `event_type` enum('sensitive_content','rate_limit','auth_failure','suspicious_input') COLLATE utf8mb4_unicode_ci NOT NULL,
  `detail` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '事件详情（问题文本/行为描述）',
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_user` (`user_id`),
  KEY `idx_created` (`created_at`),
  CONSTRAINT `security_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='安全日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `support_sessions`
--

DROP TABLE IF EXISTS `support_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `support_sessions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `question` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `answer` text COLLATE utf8mb4_unicode_ci,
  `category` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `need_manual` int NOT NULL DEFAULT '0',
  `input_mode` enum('text','voice') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'text',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `support_sessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `system_config`
--

DROP TABLE IF EXISTS `system_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_config` (
  `id` int NOT NULL AUTO_INCREMENT,
  `config_key` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置键名',
  `config_value` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置值',
  `config_type` enum('string','integer','boolean','json') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'string',
  `description` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '配置说明',
  `is_public` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否可公开（0-仅管理员 1-前端可读）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_badges`
--

DROP TABLE IF EXISTS `user_badges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_badges` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `badge_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '徽章类型：newcomer/streak/pronunciation_break/progress/dubbing/perfect/scholar',
  `badge_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '徽章名称：新手上路/坚持之星/发音突破/进步达人/配音达人/满分挑战/学霸成就',
  `awarded_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_badge` (`user_id`,`badge_type`),
  KEY `idx_badge_type` (`badge_type`),
  CONSTRAINT `fk_badge_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户徽章表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_feedbacks`
--

DROP TABLE IF EXISTS `user_feedbacks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_feedbacks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '反馈内容',
  `feedback_type` enum('bug','feature','scene','other') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '反馈类型',
  `status` enum('pending','resolved') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '处理状态',
  `admin_reply` text COLLATE utf8mb4_unicode_ci COMMENT '管理员回复',
  `replied_at` datetime DEFAULT NULL COMMENT '回复时间',
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `user_feedbacks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_profiles`
--

DROP TABLE IF EXISTS `user_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_profiles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `age` int NOT NULL,
  `age_group` enum('儿童','青少年','大学生','职场','中老年') COLLATE utf8mb4_unicode_ci NOT NULL,
  `learning_goal` enum('日常交流','考试','商务','出国','兴趣爱好') COLLATE utf8mb4_unicode_ci NOT NULL,
  `interests` json DEFAULT NULL COMMENT '兴趣标签数组，如["音乐","旅行"]',
  `level_self` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户自评等级：初级/中级/高级',
  `level_test` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '测评CEFR等级：A1/A2/B1/B2/C1/C2',
  `level_final` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '综合等级，以level_test为准',
  `role` enum('learner','teacher','admin') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'learner',
  `assessment_completed` tinyint(1) NOT NULL DEFAULT '0' COMMENT '0-未完成 1-已完成',
  `avatar_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像URL',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '0-禁用 1-正常',
  `version` int NOT NULL DEFAULT '1' COMMENT '乐观锁版本号',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`),
  KEY `idx_role` (`role`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_level_final` (`level_final`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_scores`
--

DROP TABLE IF EXISTS `user_scores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_scores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `action_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '积分行为：daily_task/challenge/dubbing/streak/pronunciation_high/share',
  `score` smallint NOT NULL COMMENT '积分变化值（正为获得，负为扣除）',
  `description` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '积分说明文字',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_created` (`user_id`,`created_at`),
  KEY `idx_action_type` (`action_type`),
  CONSTRAINT `fk_score_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=304 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='积分记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_skill_scores`
--

DROP TABLE IF EXISTS `user_skill_scores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_skill_scores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `dimension` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'listening/speaking/reading/grammar',
  `skill_name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'pronunciation:phoneme_accuracy',
  `score` decimal(5,2) NOT NULL COMMENT '0-100',
  `source` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'pronunciation/conversation/daily_task/assessment',
  `source_id` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_dimension` (`user_id`,`dimension`),
  KEY `idx_user_created` (`user_id`,`created_at`),
  CONSTRAINT `fk_skill_score_user` FOREIGN KEY (`user_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=522 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voice_challenges`
--

DROP TABLE IF EXISTS `voice_challenges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `voice_challenges` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '挑战标题',
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '挑战描述',
  `sample_text` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '示范文本',
  `deadline` datetime NOT NULL COMMENT '截止时间',
  `is_active` tinyint(1) DEFAULT NULL COMMENT '是否启用',
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-01 15:35:07
