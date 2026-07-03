"""个性化推荐服务 — 短板分析 + 四因子评分 + 每日任务生成"""

import random
from datetime import date, timedelta
from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import UserProfile
from app.models.knowledge_graph import DailyTask, MaterialRecommendation
from app.services.knowledge_graph import kg_service


# 学习目标 → 场景偏好
GOAL_TOPIC_MAP = {
    "日常交流": ["topic:self_introduction", "topic:restaurant", "topic:shopping", "topic:entertainment"],
    "考试": ["topic:education", "topic:academic_presentation"],
    "商务": ["topic:job_interview", "topic:business_meeting"],
    "出国": ["topic:travel", "topic:airport", "topic:hotel"],
    "兴趣爱好": ["topic:entertainment", "topic:culture", "topic:technology"],
}

# 任务类型 → 标题模板
TASK_TEMPLATES = {
    "shadowing": {
        "title": "跟读练习：{skill_label}",
        "description": "模仿标准发音，重点练习 {skill_label}，提升口语准确度",
    },
    "conversation": {
        "title": "对话练习：{scene_label}",
        "description": "在 {scene_label} 场景中进行 AI 对话，练习实际应用",
    },
    "grammar": {
        "title": "语法纠错：{skill_label}",
        "description": "识别并修正 {skill_label} 相关的语法错误，提升写作和口语准确性",
    },
    "vocabulary": {
        "title": "词汇练习：{skill_label}",
        "description": "学习 {skill_label} 相关的核心词汇，扩充表达能力",
    },
}


class RecommendationService:
    """推荐服务 — 使用知识图谱服务进行图遍历"""

    # ============================================================
    # 短板分析
    # ============================================================

    def get_weakness_dimension(self, user: UserProfile, db: Session) -> str:
        """从动态画像获取用户短板维度（优先使用 EMA 分数）"""
        # 优先使用 UserSkillScore 动态分数
        from app.services.profile_updater import profile_updater
        dim_avgs = profile_updater.get_dimension_averages(user.id, db)

        valid_dims = {k: v for k, v in dim_avgs.items() if v is not None}
        if valid_dims:
            return min(valid_dims, key=valid_dims.get)

        # 回退：从测评记录获取
        from app.models.assessment import AssessmentRecord, AssessmentQuestion

        latest_record = (
            db.query(AssessmentRecord)
            .filter(AssessmentRecord.user_id == user.id)
            .order_by(AssessmentRecord.created_at.desc())
            .first()
        )

        if not latest_record:
            return "pronunciation"

        session_id = latest_record.session_id
        records = (
            db.query(AssessmentRecord)
            .filter(
                AssessmentRecord.user_id == user.id,
                AssessmentRecord.session_id == session_id,
            )
            .all()
        )

        dimension_scores = {}
        for r in records:
            if r.score is not None:
                q = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == r.question_id).first()
                if q:
                    dim = q.dimension
                    if dim not in dimension_scores:
                        dimension_scores[dim] = []
                    dimension_scores[dim].append(float(r.score))

        if not dimension_scores:
            return "pronunciation"

        # 映射测评维度到画像维度
        from app.services.profile_updater import ASSESSMENT_DIM_MAP
        profile_scores = {}
        for dim, scores in dimension_scores.items():
            mapped = ASSESSMENT_DIM_MAP.get(dim, dim)
            if mapped not in profile_scores:
                profile_scores[mapped] = []
            profile_scores[mapped].extend(scores)

        avg_scores = {}
        for dim, scores in profile_scores.items():
            avg_scores[dim] = sum(scores) / len(scores) if scores else 0

        return min(avg_scores, key=avg_scores.get)

    # ============================================================
    # 资料推荐 — 四因子评分
    # ============================================================

    def recommend_materials(
        self, user: UserProfile, db: Session,
        videos_count: int = 4, articles_count: int = 4, audios_count: int = 2,
    ) -> Dict[str, List[dict]]:
        """为用户推荐资料，按 sub_type 分组返回

        评分公式：短板匹配(40%) + 难度匹配(35%) + 兴趣匹配(25%)
        """
        weakness_dim = self.get_weakness_dimension(user, db)
        user_level = user.level_final or "A1"
        user_interests = user.interests or []

        # 获取所有资料
        all_materials = kg_service.get_material_nodes()

        # 计算每个资料的得分
        scored = []
        for mat in all_materials:
            total, factors = self._score_material(
                mat, weakness_dim, user_level, user_interests, user.id, db
            )
            scored.append((mat, total, factors))

        # 按分数降序排序
        scored.sort(key=lambda x: x[1], reverse=True)

        # 按 sub_type 分组
        result = {"videos": [], "articles": [], "audios": []}
        type_map = {"video": "videos", "article": "articles", "audio": "audios"}
        type_counts = {"videos": videos_count, "articles": articles_count, "audios": audios_count}

        for mat, score, factors in scored:
            sub_type = mat.get("sub_type", "video")
            group = type_map.get(sub_type)
            if group and len(result[group]) < type_counts[group]:
                extra = mat.get("extra_data", {})
                result[group].append({
                    "material_id": mat["id"],
                    "title": mat["label"],
                    "url": extra.get("url", ""),
                    "type": sub_type,
                    "difficulty": extra.get("difficulty", ""),
                    "duration": extra.get("duration", ""),
                    "tag": (extra.get("tags", []) or [""])[0] if extra.get("tags") else "",
                    "cefr": extra.get("difficulty", ""),
                    "score": factors["total"],
                    "score_factors": factors,
                })

        return result

    def _score_material(
        self, mat: dict, weakness_dim: str, user_level: str,
        user_interests: List[str], user_id: int, db: Session,
    ) -> tuple:
        """四因子评分：短板40% + 难度35% + 兴趣25% + 新颖度(去重)

        Returns: (total_score, factors_dict)
        """
        extra = mat.get("extra_data", {})

        # 1. 短板匹配 (40%)
        weakness_score = self._calc_weakness_match(mat, weakness_dim)

        # 2. 难度匹配 (35%)
        mat_level = extra.get("difficulty", "A1")
        level_score = self._calc_level_match(mat_level, user_level)

        # 3. 兴趣匹配 (25%)
        mat_tags = extra.get("tags", [])
        interest_score = self._calc_interest_match(mat_tags, user_interests)

        # 4. 新颖度 — 7天内推荐过扣分，disliked 直接归零
        novelty_score = self._calc_novelty(mat["id"], user_id, db)

        base = (
            weakness_score * 0.40
            + level_score * 0.35
            + interest_score * 0.25
        )
        total = base * novelty_score * 100

        factors = {
            "weakness": round(weakness_score * 100, 1),
            "level": round(level_score * 100, 1),
            "interest": round(interest_score * 100, 1),
            "novelty": round(novelty_score * 100, 1),
            "total": round(total, 1),
        }
        return total, factors

    def _calc_weakness_match(self, mat: dict, weakness_dim: str) -> float:
        """计算资料与短板维度的匹配度

        图遍历：资料 → TEACHES 技能 → 判断技能是否属于短板维度
        """
        weakness_skills = set(kg_service.get_skills_for_dimension(weakness_dim))

        # 资料教授的每个技能
        taught_skills = set()
        for _, target, attrs in kg_service.graph.out_edges(mat["id"], data=True):
            if attrs["relation"] == "TEACHES":
                taught_skills.add(target)

        if not taught_skills:
            return 0.3  # 无明确技能关联，给基础分

        overlap = taught_skills & weakness_skills
        if not overlap:
            return 0.2

        return 0.5 + 0.5 * (len(overlap) / len(taught_skills))

    def _calc_level_match(self, mat_level: str, user_level: str) -> float:
        """CEFR 等级匹配度"""
        cefr_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        try:
            mat_idx = cefr_order.index(mat_level)
            user_idx = cefr_order.index(user_level)
        except ValueError:
            return 0.5

        diff = abs(mat_idx - user_idx)
        if diff == 0:
            return 1.0
        if diff == 1:
            return 0.6
        if diff == 2:
            return 0.3
        return 0.1

    def _calc_interest_match(self, mat_tags: List[str], user_interests: List[str]) -> float:
        """兴趣标签匹配"""
        if not user_interests or not mat_tags:
            return 0.5  # 无数据时给中性分

        overlap = set(mat_tags) & set(user_interests)
        if not overlap:
            return 0.2

        return 0.5 + 0.5 * (len(overlap) / len(mat_tags))

    def _calc_novelty(self, material_id: str, user_id: int, db: Session) -> float:
        """新颖度评分 — 最近推荐过扣分，dislike 严重扣分"""
        seven_days_ago = date.today() - timedelta(days=7)

        recent = (
            db.query(MaterialRecommendation)
            .filter(
                MaterialRecommendation.user_id == user_id,
                MaterialRecommendation.material_node_id == material_id,
                MaterialRecommendation.recommend_date >= seven_days_ago,
            )
            .all()
        )

        if not recent:
            return 1.0

        # 检查是否有 disliked
        has_dislike = any(r.action == "disliked" for r in recent)
        if has_dislike:
            return 0.0

        # 推荐次数越多扣分越多
        penalty = len(recent) * 0.3
        return max(0.1, 1.0 - penalty)

    # ============================================================
    # 每日任务生成 — 六步图遍历
    # ============================================================

    def generate_daily_tasks(self, user: UserProfile, db: Session) -> List[dict]:
        """为用户生成当天的 3 个任务（跟读/对话/语法/词汇）

        步骤：
        1. 短板优先 → 取最低分维度
        2. 目标加权 → learning_goal 映射场景偏好
        3. CEFR 匹配 → 图查找 BELONGS_TO 同等级内容
        4. 前置依赖 → 检查技能是否已掌握
        5. 兴趣优选 → 资料标签 ∩ 用户兴趣
        6. 写入 daily_tasks
        """
        today = date.today()

        # 先检查今天是否已有任务
        existing = (
            db.query(DailyTask)
            .filter(
                DailyTask.user_id == user.id,
                DailyTask.task_date == today,
            )
            .count()
        )
        if existing > 0:
            # 返回已有任务
            return self._get_today_tasks(user.id, today, db)

        weakness_dim = self.get_weakness_dimension(user, db)
        user_level = user.level_final or "A1"
        user_interests = user.interests or []
        user_goal = user.learning_goal or "日常交流"

        # Step 1: 短板优先 — 找到短板关联的技能
        weakness_skills = kg_service.get_skills_for_dimension(weakness_dim)

        # Step 2: 目标加权 — 学习目标映射场景
        preferred_topics = GOAL_TOPIC_MAP.get(user_goal, [])
        preferred_topics_set = set(preferred_topics)

        # Step 3: CEFR 匹配 — 同等级内容
        cefr_skills = kg_service.get_skills_by_cefr(user_level, sub_type="phoneme")
        cefr_grammar = kg_service.get_skills_by_cefr(user_level, sub_type="grammar")
        cefr_vocab = kg_service.get_skills_by_cefr(user_level, sub_type="vocabulary")

        tasks = []

        # --- 跟读任务 (shadowing) — 基于音素技能 ---
        shadowing_skill = self._pick_best_skill(
            weakness_skills, cefr_skills, user_interests, "phoneme"
        )
        shadowing_material = self._pick_material_for_skill(shadowing_skill, user_interests)
        shadowing_label = kg_service.get_node(shadowing_skill)["label"] if shadowing_skill else "发音基础"

        tasks.append({
            "task_type": "shadowing",
            "title": f"跟读练习：{shadowing_label}",
            "description": f"模仿标准发音，重点练习 {shadowing_label}，提升口语准确度",
            "difficulty": user_level,
            "focus_skill_id": shadowing_skill,
            "material_id": shadowing_material,
            "scene": None,
        })

        # --- 对话任务 (conversation) — 基于场景 ---
        conversation_scene = self._pick_best_scene(
            preferred_topics, weakness_skills, user_level, user_interests
        )
        scene_node = kg_service.get_node(conversation_scene) if conversation_scene else None
        scene_label = scene_node["label"] if scene_node else "日常对话"
        scene_name = (scene_node.get("extra_data", {}) or {}).get("scene", "") if scene_node else ""

        tasks.append({
            "task_type": "conversation",
            "title": f"对话练习：{scene_label}",
            "description": f"在 {scene_label} 场景中进行 AI 对话，练习实际应用",
            "difficulty": user_level,
            "focus_skill_id": None,
            "material_id": None,
            "scene": scene_name,
        })

        # --- 语法任务 (grammar) — 基于语法技能 ---
        grammar_skill = self._pick_best_skill(
            weakness_skills, cefr_grammar, user_interests, "grammar"
        )
        grammar_label = kg_service.get_node(grammar_skill)["label"] if grammar_skill else "基础语法"
        grammar_material = self._pick_material_for_skill(grammar_skill, user_interests)

        tasks.append({
            "task_type": "grammar",
            "title": f"语法纠错：{grammar_label}",
            "description": f"识别并修正 {grammar_label} 相关的语法错误，提升写作和口语准确性",
            "difficulty": user_level,
            "focus_skill_id": grammar_skill,
            "material_id": grammar_material,
            "scene": None,
        })

        # --- 词汇任务 (vocabulary) — 基于词汇技能 ---
        vocab_skill = self._pick_best_skill(
            weakness_skills, cefr_vocab, user_interests, "vocabulary"
        )
        vocab_label = kg_service.get_node(vocab_skill)["label"] if vocab_skill else "核心词汇"

        tasks.append({
            "task_type": "vocabulary",
            "title": f"词汇练习：{vocab_label}",
            "description": f"学习 {vocab_label} 相关的核心词汇，扩充表达能力",
            "difficulty": user_level,
            "focus_skill_id": vocab_skill,
            "material_id": None,
            "scene": None,
        })

        # Step 6: 写入 daily_tasks
        for t in tasks:
            db_task = DailyTask(
                user_id=user.id,
                task_date=today,
                task_type=t["task_type"],
                title=t["title"],
                description=t["description"],
                difficulty=t["difficulty"],
                focus_skill_id=t["focus_skill_id"],
                material_id=t["material_id"],
                scene=t["scene"],
                status="pending",
            )
            db.add(db_task)

        db.commit()

        return self._get_today_tasks(user.id, today, db)

    def _pick_best_skill(
        self, weakness_skills: List[str], cefr_skills: List[dict],
        user_interests: List[str], sub_type: str,
    ) -> Optional[str]:
        """从候选技能中选出最佳技能"""
        # 候选：短板技能 ∩ CEFR等级技能
        cefr_skill_ids = {s["id"] for s in cefr_skills}
        candidates = [s for s in weakness_skills if s in cefr_skill_ids]

        if not candidates:
            # 放宽：只看 CEFR 等级
            candidates = list(cefr_skill_ids)

        if not candidates:
            # 再放宽：所有同子类型的技能
            all_skills = kg_service.get_nodes_by_type("skill", sub_type)
            candidates = [s["id"] for s in all_skills]

        if not candidates:
            return None

        # 随机选（后续可加入更多优化如用户历史完成记录）
        return random.choice(candidates)

    def _pick_material_for_skill(
        self, skill_id: Optional[str], user_interests: List[str],
    ) -> Optional[str]:
        """为技能选择最佳资料"""
        if not skill_id:
            return None

        materials = kg_service.get_materials_teaching(skill_id)
        if not materials:
            return None

        # 按兴趣标签匹配度排序
        scored = []
        for m in materials:
            tags = (m.get("extra_data", {}) or {}).get("tags", [])
            interest_overlap = len(set(tags) & set(user_interests)) if user_interests else 0
            scored.append((m, interest_overlap))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]["id"] if scored else None

    def _pick_best_scene(
        self, preferred_topics: List[str], weakness_skills: List[str],
        user_level: str, user_interests: List[str],
    ) -> Optional[str]:
        """选择最佳对话场景"""
        # 优先从偏好场景中选
        if preferred_topics:
            return random.choice(preferred_topics)

        # 回退：选同等级任意场景
        all_topics = kg_service.get_topic_nodes()
        if all_topics:
            return random.choice(all_topics)["id"]

        return "topic:self_introduction"

    # ============================================================
    # 任务读取 & 操作
    # ============================================================

    def _get_today_tasks(self, user_id: int, today: date, db: Session) -> List[dict]:
        """读取今日任务"""
        tasks = (
            db.query(DailyTask)
            .filter(
                DailyTask.user_id == user_id,
                DailyTask.task_date == today,
            )
            .order_by(DailyTask.id)
            .all()
        )

        result = []
        for t in tasks:
            if t.task_type == "listening":
                continue
            task_dict = {
                "id": t.id,
                "type": t.task_type,
                "title": t.title,
                "description": t.description or "",
                "difficulty": t.difficulty,
                "duration": "5-10分钟",
                "tag": t.difficulty,
                "scene": t.scene,
                "status": t.status,
                "score": float(t.score) if t.score else None,
            }
            result.append(task_dict)

        return result

    def get_task_progress(self, user_id: int, db: Session) -> Tuple[int, int]:
        """获取今日任务进度 (done, total)"""
        today = date.today()
        tasks = (
            db.query(DailyTask)
            .filter(
                DailyTask.user_id == user_id,
                DailyTask.task_date == today,
            )
            .all()
        )
        valid = [t for t in tasks if t.task_type != "listening"]
        done = sum(1 for t in valid if t.status == "completed")
        return done, len(valid)

    def skip_task(self, task_id: int, user_id: int, reason: Optional[str], db: Session) -> Optional[dict]:
        """跳过任务"""
        task = (
            db.query(DailyTask)
            .filter(DailyTask.id == task_id, DailyTask.user_id == user_id)
            .first()
        )
        if not task:
            return None

        task.status = "skipped"
        task.skip_reason = reason
        db.commit()

        return {
            "id": task.id,
            "type": task.task_type,
            "title": task.title,
            "status": task.status,
        }

    def replace_task(self, task_id: int, user_id: int, user: UserProfile, db: Session) -> Optional[dict]:
        """替换一个任务（同类型换一个）"""
        task = (
            db.query(DailyTask)
            .filter(DailyTask.id == task_id, DailyTask.user_id == user_id)
            .first()
        )
        if not task:
            return None

        # 删除旧任务
        db.delete(task)
        db.commit()

        # 生成一个同类型新任务
        today = date.today()
        user_level = user.level_final or "A1"
        user_interests = user.interests or []

        if task.task_type == "shadowing":
            skills = kg_service.get_skills_by_cefr(user_level, sub_type="phoneme")
            candidates = [s["id"] for s in skills]
            chosen = random.choice(candidates) if candidates else None
            label = kg_service.get_node(chosen)["label"] if chosen else "发音练习"

            new_task = DailyTask(
                user_id=user_id, task_date=today, task_type="shadowing",
                title=f"跟读练习：{label}",
                description=f"模仿标准发音，重点练习 {label}",
                difficulty=user_level, focus_skill_id=chosen, status="pending",
            )
        elif task.task_type == "conversation":
            preferred = GOAL_TOPIC_MAP.get(user.learning_goal or "日常交流", [])
            chosen = random.choice(preferred) if preferred else "topic:self_introduction"
            label = kg_service.get_node(chosen)["label"] if kg_service.get_node(chosen) else "日常对话"

            new_task = DailyTask(
                user_id=user_id, task_date=today, task_type="conversation",
                title=f"对话练习：{label}",
                description=f"在 {label} 场景中进行 AI 对话",
                difficulty=user_level, scene=chosen.replace("topic:", ""), status="pending",
            )
        elif task.task_type == "grammar":
            skills = kg_service.get_skills_by_cefr(user_level, sub_type="grammar")
            candidates = [s["id"] for s in skills]
            chosen = random.choice(candidates) if candidates else None
            label = kg_service.get_node(chosen)["label"] if chosen else "基础语法"

            new_task = DailyTask(
                user_id=user_id, task_date=today, task_type="grammar",
                title=f"语法纠错：{label}",
                description=f"识别并修正 {label} 相关的语法错误",
                difficulty=user_level, focus_skill_id=chosen, status="pending",
            )
        elif task.task_type == "vocabulary":
            skills = kg_service.get_skills_by_cefr(user_level, sub_type="vocabulary")
            candidates = [s["id"] for s in skills]
            chosen = random.choice(candidates) if candidates else None
            label = kg_service.get_node(chosen)["label"] if chosen else "核心词汇"

            new_task = DailyTask(
                user_id=user_id, task_date=today, task_type="vocabulary",
                title=f"词汇练习：{label}",
                description=f"学习 {label} 相关的核心词汇",
                difficulty=user_level, focus_skill_id=chosen, status="pending",
            )
        db.add(new_task)
        db.commit()

        return {
            "id": new_task.id,
            "type": new_task.task_type,
            "title": new_task.title,
            "description": new_task.description or "",
            "difficulty": new_task.difficulty,
            "duration": "5-10分钟",
            "tag": new_task.difficulty,
            "scene": new_task.scene,
            "status": "pending",
            "score": None,
        }

    def adjust_difficulty(self, task_id: int, user_id: int, direction: str, db: Session) -> Optional[dict]:
        """调整任务难度 ±1 级"""
        task = (
            db.query(DailyTask)
            .filter(DailyTask.id == task_id, DailyTask.user_id == user_id)
            .first()
        )
        if not task or not task.difficulty:
            return None

        cefr_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        try:
            idx = cefr_order.index(task.difficulty)
        except ValueError:
            return None

        if direction == "harder" and idx < len(cefr_order) - 1:
            new_level = cefr_order[idx + 1]
        elif direction == "easier" and idx > 0:
            new_level = cefr_order[idx - 1]
        else:
            return None

        task.difficulty = new_level
        db.commit()

        return {
            "id": task.id,
            "type": task.task_type,
            "title": task.title,
            "difficulty": new_level,
            "status": task.status,
        }

    def get_history(self, user_id: int, days: int, db: Session) -> List[dict]:
        """获取历史学习记录"""
        start_date = date.today() - timedelta(days=days - 1)
        tasks = (
            db.query(DailyTask)
            .filter(
                DailyTask.user_id == user_id,
                DailyTask.task_date >= start_date,
            )
            .order_by(DailyTask.task_date.desc(), DailyTask.id)
            .all()
        )

        # 按日期分组
        day_map = {}
        for t in tasks:
            d = t.task_date.isoformat()
            if d not in day_map:
                day_map[d] = {"tasks": [], "completed": 0, "total": 0, "minutes": 0}
            day_map[d]["tasks"].append(t.status)
            day_map[d]["total"] += 1
            if t.status == "completed":
                day_map[d]["completed"] += 1
            if t.duration_seconds:
                day_map[d]["minutes"] += t.duration_seconds // 60

        result = []
        for d in sorted(day_map.keys(), reverse=True):
            info = day_map[d]
            result.append({
                "date": d,
                "tasks": info["tasks"],
                "completed": info["completed"],
                "total": info["total"],
                "minutes": info["minutes"],
            })

        return result

    def save_recommendations(self, user_id: int, materials: Dict[str, List[dict]], db: Session):
        """将推荐结果写入 material_recommendations 表"""
        today = date.today()
        for group in ["videos", "articles", "audios"]:
            for mat in materials.get(group, []):
                rec = MaterialRecommendation(
                    user_id=user_id,
                    material_node_id=mat["material_id"],
                    recommend_date=today,
                    recommend_score=mat["score"],
                    reason_tags=[],
                    action="pending",
                )
                db.add(rec)
        db.commit()

    def get_today_refresh_count(self, user_id: int, db: Session) -> int:
        """获取今日手动刷新次数

        每次 GET / 或 POST /refresh 都会写入 6 条记录。
        首次加载（GET /）不算手动刷新，所以总批次 - 1 = 手动刷新次数。
        """
        today = date.today()
        count = (
            db.query(MaterialRecommendation)
            .filter(
                MaterialRecommendation.user_id == user_id,
                MaterialRecommendation.recommend_date == today,
            )
            .count()
        )
        batches = count // 6  # 总批次数
        return max(0, batches - 1)  # 减去首次加载


# 全局单例
recommendation_service = RecommendationService()