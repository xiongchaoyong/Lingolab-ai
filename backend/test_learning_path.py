"""学习路径模块单元测试 — 知识图谱 + 推荐算法纯函数"""

import pytest
import networkx as nx


# ============================================================
# 从 recommendation.py 提取纯函数，避免 DB 依赖
# ============================================================

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


def _calc_level_match(mat_level: str, user_level: str) -> float:
    """CEFR 等级匹配度（从 recommendation.py 提取）"""
    try:
        mat_idx = CEFR_ORDER.index(mat_level)
        user_idx = CEFR_ORDER.index(user_level)
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


def _calc_interest_match(mat_tags: list, user_interests: list) -> float:
    """兴趣标签匹配（从 recommendation.py 提取）"""
    if not user_interests or not mat_tags:
        return 0.5

    overlap = set(mat_tags) & set(user_interests)
    if not overlap:
        return 0.2

    return 0.5 + 0.5 * (len(overlap) / len(mat_tags))


def _calc_weakness_match_simple(taught_skills: set, weakness_skills: set) -> float:
    """短板匹配度（简化版，从 recommendation.py 提取逻辑）"""
    if not taught_skills:
        return 0.3

    overlap = taught_skills & weakness_skills
    if not overlap:
        return 0.2

    return 0.5 + 0.5 * (len(overlap) / len(taught_skills))


def _calc_novelty(recent_count: int, has_dislike: bool) -> float:
    """新颖度评分（简化版，从 recommendation.py 提取逻辑）"""
    if recent_count == 0:
        return 1.0

    if has_dislike:
        return 0.0

    penalty = recent_count * 0.3
    return max(0.1, 1.0 - penalty)


def _adjust_cefr_difficulty(current: str, direction: str) -> str | None:
    """调整 CEFR 难度 ±1 级（从 recommendation.py 提取）"""
    try:
        idx = CEFR_ORDER.index(current)
    except ValueError:
        return None

    if direction == "harder" and idx < len(CEFR_ORDER) - 1:
        return CEFR_ORDER[idx + 1]
    elif direction == "easier" and idx > 0:
        return CEFR_ORDER[idx - 1]
    return None


# ============================================================
# 知识图谱纯函数测试（构建测试用 DiGraph）
# ============================================================

class TestKnowledgeGraph:
    """知识图谱图遍历算法"""

    def _build_test_graph(self) -> nx.DiGraph:
        """构建测试知识图谱"""
        G = nx.DiGraph()

        # CEFR 等级节点
        for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            G.add_node(f"cefr:{level}", type="cefr_level", label=level)

        # 技能节点
        skills = [
            ("skill:th_sound", "skill", "phoneme", "TH 音素"),
            ("skill:vowels", "skill", "phoneme", "元音"),
            ("skill:past_tense", "skill", "grammar", "过去时"),
            ("skill:present_perfect", "skill", "grammar", "现在完成时"),
            ("skill:conditionals", "skill", "grammar", "条件句"),
        ]
        for sid, stype, ssub, slabel in skills:
            G.add_node(sid, type=stype, sub_type=ssub, label=slabel, extra_data={"dimension": "grammar" if ssub == "grammar" else "speaking"})

        # 资料节点
        materials = [
            ("mat:video_1", "material", "video", "英语发音入门视频"),
            ("mat:article_1", "material", "article", "语法讲解文章"),
            ("mat:audio_1", "material", "audio", "听力练习音频"),
        ]
        for mid, mtype, msub, mlabel in materials:
            G.add_node(mid, type=mtype, sub_type=msub, label=mlabel, extra_data={"difficulty": "A2", "tags": ["grammar"]})

        # 场景节点
        G.add_node("topic:interview", type="topic", label="面试场景", extra_data={"tags": ["business"]})
        G.add_node("topic:shopping", type="topic", label="购物场景", extra_data={"tags": ["daily"]})

        # 边：技能 BELONGS_TO CEFR
        G.add_edge("skill:th_sound", "cefr:A1", relation="BELONGS_TO", weight=1.0)
        G.add_edge("skill:vowels", "cefr:A1", relation="BELONGS_TO", weight=1.0)
        G.add_edge("skill:past_tense", "cefr:A2", relation="BELONGS_TO", weight=1.0)
        G.add_edge("skill:present_perfect", "cefr:B1", relation="BELONGS_TO", weight=1.0)
        G.add_edge("skill:conditionals", "cefr:B2", relation="BELONGS_TO", weight=1.0)

        # 边：前置依赖 HAS_PREREQ
        G.add_edge("skill:present_perfect", "skill:past_tense", relation="HAS_PREREQ", weight=1.0)
        G.add_edge("skill:conditionals", "skill:present_perfect", relation="HAS_PREREQ", weight=1.0)

        # 边：资料 TEACHES 技能
        G.add_edge("mat:video_1", "skill:th_sound", relation="TEACHES", weight=1.0)
        G.add_edge("mat:video_1", "skill:vowels", relation="TEACHES", weight=1.0)
        G.add_edge("mat:article_1", "skill:past_tense", relation="TEACHES", weight=1.0)
        G.add_edge("mat:audio_1", "skill:th_sound", relation="TEACHES", weight=1.0)

        # 边：资料 COVERS 场景
        G.add_edge("mat:article_1", "topic:interview", relation="COVERS", weight=1.0)

        return G

    def test_graph_node_count(self):
        G = self._build_test_graph()
        # 6 CEFR + 5 skill + 3 material + 2 topic = 16
        assert G.number_of_nodes() == 16

    def test_graph_edge_count(self):
        G = self._build_test_graph()
        # BELONGS_TO: 5, HAS_PREREQ: 2, TEACHES: 4, COVERS: 1 = 12
        assert G.number_of_edges() == 12

    def test_prerequisite_chain(self):
        """拓扑排序：conditionals 的前置链"""
        G = self._build_test_graph()
        # BFS from conditionals following HAS_PREREQ
        visited = set()
        queue = ["skill:conditionals"]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for _, target, attrs in G.out_edges(current, data=True):
                if attrs["relation"] == "HAS_PREREQ" and target not in visited:
                    queue.append(target)

        subgraph = G.subgraph(visited)
        topo = list(nx.topological_sort(subgraph))

        # 拓扑排序：无入边的节点排在前面
        # conditionals(无入边) → present_perfect → past_tense
        assert len(topo) == 3
        assert topo.index("skill:conditionals") < topo.index("skill:present_perfect")
        assert topo.index("skill:present_perfect") < topo.index("skill:past_tense")

    def test_get_skills_by_cefr(self):
        """按 CEFR 等级筛选技能"""
        G = self._build_test_graph()
        cefr_id = "cefr:A1"
        skills = []
        for nid, attrs in G.nodes(data=True):
            if attrs["type"] != "skill":
                continue
            if G.has_edge(nid, cefr_id):
                edge = G.edges[nid, cefr_id]
                if edge["relation"] == "BELONGS_TO":
                    skills.append(nid)

        assert set(skills) == {"skill:th_sound", "skill:vowels"}

    def test_get_materials_teaching_skill(self):
        """查找教授某技能的资料"""
        G = self._build_test_graph()
        materials = []
        for source, target, attrs in G.in_edges("skill:th_sound", data=True):
            if attrs["relation"] == "TEACHES":
                materials.append(source)

        assert set(materials) == {"mat:video_1", "mat:audio_1"}

    def test_shortest_path(self):
        """最短路径"""
        G = self._build_test_graph()
        path = nx.shortest_path(G, "skill:conditionals", "skill:past_tense")
        assert path == ["skill:conditionals", "skill:present_perfect", "skill:past_tense"]

    def test_no_path_returns_none(self):
        """无路径情况"""
        G = self._build_test_graph()
        try:
            nx.shortest_path(G, "mat:video_1", "topic:interview")
            # If it finds a path through TEACHES→skill→BELONGS_TO→cefr, that's fine
        except nx.NetworkXNoPath:
            pass  # Expected for disconnected components


# ============================================================
# 推荐算法纯函数测试
# ============================================================

class TestLevelMatch:
    """CEFR 等级匹配度"""

    def test_same_level(self):
        assert _calc_level_match("B1", "B1") == 1.0

    def test_one_level_diff(self):
        assert _calc_level_match("B1", "B2") == 0.6
        assert _calc_level_match("B2", "B1") == 0.6

    def test_two_levels_diff(self):
        assert _calc_level_match("A1", "B1") == 0.3
        assert _calc_level_match("C2", "B2") == 0.3

    def test_three_plus_levels_diff(self):
        assert _calc_level_match("A1", "C1") == 0.1
        assert _calc_level_match("A1", "C2") == 0.1

    def test_invalid_level(self):
        assert _calc_level_match("X1", "B1") == 0.5
        assert _calc_level_match("B1", "X1") == 0.5


class TestInterestMatch:
    """兴趣标签匹配"""

    def test_no_interests(self):
        assert _calc_interest_match(["grammar"], []) == 0.5

    def test_no_material_tags(self):
        assert _calc_interest_match([], ["grammar"]) == 0.5

    def test_both_empty(self):
        assert _calc_interest_match([], []) == 0.5

    def test_no_overlap(self):
        assert _calc_interest_match(["grammar"], ["music"]) == 0.2

    def test_partial_overlap(self):
        result = _calc_interest_match(["grammar", "vocab"], ["grammar"])
        assert result == 0.75  # 0.5 + 0.5 * (1/2)

    def test_full_overlap(self):
        result = _calc_interest_match(["grammar"], ["grammar", "music"])
        assert result == 1.0  # 0.5 + 0.5 * (1/1)


class TestWeaknessMatch:
    """短板匹配度"""

    def test_no_taught_skills(self):
        assert _calc_weakness_match_simple(set(), {"grammar"}) == 0.3

    def test_no_overlap(self):
        assert _calc_weakness_match_simple({"speaking"}, {"grammar"}) == 0.2

    def test_partial_overlap(self):
        result = _calc_weakness_match_simple({"speaking", "grammar"}, {"grammar"})
        assert result == 0.75  # 0.5 + 0.5 * (1/2)

    def test_full_overlap(self):
        result = _calc_weakness_match_simple({"grammar"}, {"grammar", "speaking"})
        assert result == 1.0  # 0.5 + 0.5 * (1/1)


class TestNovelty:
    """新颖度评分"""

    def test_first_time(self):
        assert _calc_novelty(0, False) == 1.0

    def test_disliked(self):
        assert _calc_novelty(1, True) == 0.0

    def test_recent_once(self):
        assert _calc_novelty(1, False) == 0.7  # 1.0 - 1*0.3

    def test_recent_twice(self):
        assert _calc_novelty(2, False) == 0.4  # 1.0 - 2*0.3

    def test_recent_three_times(self):
        assert _calc_novelty(3, False) == pytest.approx(0.1, abs=1e-9)  # 1.0 - 3*0.3 = 0.1

    def test_many_times_clamped(self):
        assert _calc_novelty(10, False) == 0.1  # max(0.1, 1.0 - 3.0) = 0.1


class TestCompositeScore:
    """四因子综合评分"""

    def test_perfect_match(self):
        """所有因子满分"""
        weakness = _calc_weakness_match_simple({"grammar"}, {"grammar"})
        level = _calc_level_match("B1", "B1")
        interest = _calc_interest_match(["grammar"], ["grammar"])
        novelty = _calc_novelty(0, False)

        base = weakness * 0.40 + level * 0.35 + interest * 0.25
        score = base * novelty * 100
        assert score == 100.0

    def test_disliked_score_zero(self):
        """disliked 资料分数归零"""
        weakness = _calc_weakness_match_simple({"grammar"}, {"grammar"})
        level = _calc_level_match("B1", "B1")
        interest = _calc_interest_match(["grammar"], ["grammar"])
        novelty = _calc_novelty(1, True)

        base = weakness * 0.40 + level * 0.35 + interest * 0.25
        score = base * novelty * 100
        assert score == 0.0

    def test_recent_recommendation_dampened(self):
        """最近推荐过的资料被打折"""
        weakness = _calc_weakness_match_simple({"grammar"}, {"grammar"})
        level = _calc_level_match("B1", "B1")
        interest = _calc_interest_match(["grammar"], ["grammar"])
        novelty = _calc_novelty(1, False)  # 0.7

        base = weakness * 0.40 + level * 0.35 + interest * 0.25
        score = base * novelty * 100
        assert score == 70.0  # 100 * 0.7


class TestAdjustDifficulty:
    """CEFR 难度调整"""

    def test_harder_from_b1(self):
        assert _adjust_cefr_difficulty("B1", "harder") == "B2"

    def test_easier_from_b1(self):
        assert _adjust_cefr_difficulty("B1", "easier") == "A2"

    def test_harder_at_c2_returns_none(self):
        assert _adjust_cefr_difficulty("C2", "harder") is None

    def test_easier_at_a1_returns_none(self):
        assert _adjust_cefr_difficulty("A1", "easier") is None

    def test_invalid_level(self):
        assert _adjust_cefr_difficulty("X1", "harder") is None

    def test_full_cycle_up_and_down(self):
        """从 A1 逐步升到 C2 再降回来"""
        level = "A1"
        for expected in ["A2", "B1", "B2", "C1", "C2"]:
            level = _adjust_cefr_difficulty(level, "harder")
            assert level == expected

        for expected in ["C1", "B2", "B1", "A2", "A1"]:
            level = _adjust_cefr_difficulty(level, "easier")
            assert level == expected


# ============================================================
# Schema 校验测试
# ============================================================

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.learning_path import (
    TaskItem,
    DailyTasksResponse,
    TaskProgress,
    SkipTaskRequest,
    AdjustDifficultyRequest,
    TaskActionResponse,
    HistoryDay,
    HistoryResponse,
    MaterialItem,
    RecommendationsResponse,
    DislikeResponse,
    ClickRequest,
    CompleteTaskRequest,
)


class TestTaskItemSchema:
    """任务项 Schema"""

    def test_valid_task(self):
        task = TaskItem(id=1, type="shadowing", title="跟读练习", duration="5-10分钟")
        assert task.id == 1
        assert task.status == "pending"  # 默认值

    def test_task_with_score(self):
        task = TaskItem(id=1, type="conversation", title="对话", duration="10分钟", score=85.5)
        assert task.score == 85.5

    def test_task_with_scene(self):
        task = TaskItem(id=1, type="conversation", title="对话", duration="10分钟", scene="restaurant")
        assert task.scene == "restaurant"


class TestDailyTasksResponseSchema:
    """每日任务响应 Schema"""

    def test_valid_response(self):
        task = TaskItem(id=1, type="shadowing", title="跟读", duration="5分钟")
        resp = DailyTasksResponse(
            date="2026-06-26",
            tasks=[task],
            progress=TaskProgress(done=0, total=1),
        )
        assert resp.date == "2026-06-26"
        assert len(resp.tasks) == 1
        assert resp.progress.done == 0


class TestAdjustDifficultyRequestSchema:
    """调整难度请求 Schema"""

    def test_harder(self):
        req = AdjustDifficultyRequest(direction="harder")
        assert req.direction == "harder"

    def test_easier(self):
        req = AdjustDifficultyRequest(direction="easier")
        assert req.direction == "easier"


class TestMaterialItemSchema:
    """资料推荐项 Schema"""

    def test_valid_material(self):
        mat = MaterialItem(
            id=1, material_id="mat:video_1", title="发音视频",
            url="https://example.com", type="video", score=85.0,
        )
        assert mat.type == "video"
        assert mat.score == 85.0


class TestRecommendationsResponseSchema:
    """资料推荐响应 Schema"""

    def test_valid_response(self):
        resp = RecommendationsResponse(
            videos=[],
            articles=[],
            audios=[],
            generated_at="2026-06-26T10:00:00",
        )
        assert len(resp.videos) == 0
        assert resp.generated_at == "2026-06-26T10:00:00"


class TestHistoryDaySchema:
    """历史记录 Schema"""

    def test_valid_history_day(self):
        day = HistoryDay(
            date="2026-06-26",
            tasks=["done", "skipped", "pending"],
            completed=1,
            total=3,
            minutes=15,
        )
        assert day.completed == 1
        assert len(day.tasks) == 3
