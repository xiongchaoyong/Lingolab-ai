"""知识图谱服务 — NetworkX 内存图 + MySQL 持久化

应用启动时从 MySQL 加载全量节点/边到 NetworkX 有向图，
写操作同时写 MySQL 和内存图，读操作直接查内存图。
"""

import networkx as nx
from typing import List, Optional, Dict, Set
from sqlalchemy.orm import Session

from app.models.knowledge_graph import KGNode, KGEdge


class KnowledgeGraphService:
    """知识图谱核心服务 — 单例模式"""

    _instance: Optional["KnowledgeGraphService"] = None

    def __init__(self):
        self.graph = nx.DiGraph()  # 有向图

    @classmethod
    def get_instance(cls) -> "KnowledgeGraphService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ============================================================
    # 加载
    # ============================================================

    def load_from_db(self, db: Session):
        """从 MySQL 全量加载到 NetworkX 内存图"""
        self.graph.clear()

        # 加载节点
        nodes = db.query(KGNode).filter(KGNode.is_active == 1).all()
        for node in nodes:
            self.graph.add_node(
                node.id,
                type=node.type,
                sub_type=node.sub_type,
                label=node.label,
                extra_data=node.extra_data or {},
            )

        # 加载边
        edges = db.query(KGEdge).filter(KGEdge.is_active == 1).all()
        for edge in edges:
            self.graph.add_edge(
                edge.source_id,
                edge.target_id,
                relation=edge.relation,
                weight=float(edge.weight) if edge.weight else 1.0,
                extra_data=edge.extra_data or {},
            )

        print(f"[KnowledgeGraph] 已加载 {self.graph.number_of_nodes()} 节点, "
              f"{self.graph.number_of_edges()} 边")

    # ============================================================
    # 节点查询
    # ============================================================

    def get_node(self, node_id: str) -> Optional[dict]:
        """获取单个节点属性"""
        if node_id in self.graph:
            return self.graph.nodes[node_id]
        return None

    def get_nodes_by_type(self, node_type: str, sub_type: Optional[str] = None) -> List[dict]:
        """按类型获取节点列表"""
        results = []
        for nid, attrs in self.graph.nodes(data=True):
            if attrs["type"] == node_type:
                if sub_type is None or attrs.get("sub_type") == sub_type:
                    results.append({"id": nid, **attrs})
        return results

    def get_skill_nodes(self, sub_type: Optional[str] = None) -> List[dict]:
        """获取所有技能节点"""
        return self.get_nodes_by_type("skill", sub_type)

    def get_material_nodes(self, sub_type: Optional[str] = None) -> List[dict]:
        """获取所有资料节点"""
        return self.get_nodes_by_type("material", sub_type)

    def get_topic_nodes(self) -> List[dict]:
        """获取所有场景节点"""
        return self.get_nodes_by_type("topic")

    def get_cefr_levels(self) -> List[str]:
        """获取所有 CEFR 等级，从低到高排序"""
        levels = []
        for nid, attrs in self.graph.nodes(data=True):
            if attrs["type"] == "cefr_level":
                levels.append(nid.replace("cefr:", ""))
        return sorted(levels)

    # ============================================================
    # 边/关系查询
    # ============================================================

    def get_neighbors(self, node_id: str, relation: Optional[str] = None,
                      direction: str = "out") -> List[dict]:
        """获取节点的邻居节点

        Args:
            node_id: 源节点 ID
            relation: 边类型过滤，None 表示所有类型
            direction: "out"(出边) / "in"(入边) / "both"
        """
        if node_id not in self.graph:
            return []

        results = []

        if direction in ("out", "both"):
            for _, target, edge_attrs in self.graph.out_edges(node_id, data=True):
                if relation and edge_attrs["relation"] != relation:
                    continue
                target_attrs = self.graph.nodes[target]
                results.append({"id": target, **target_attrs, "_edge": edge_attrs})

        if direction in ("in", "both"):
            for source, _, edge_attrs in self.graph.in_edges(node_id, data=True):
                if relation and edge_attrs["relation"] != relation:
                    continue
                source_attrs = self.graph.nodes[source]
                results.append({"id": source, **source_attrs, "_edge": edge_attrs})

        return results

    def get_prerequisites(self, skill_id: str) -> List[dict]:
        """获取技能的前置依赖技能"""
        return self.get_neighbors(skill_id, relation="HAS_PREREQ", direction="out")

    def get_similar_skills(self, skill_id: str) -> List[dict]:
        """获取易混淆的相似技能"""
        return self.get_neighbors(skill_id, relation="SIMILAR_TO", direction="out")

    def get_materials_teaching(self, skill_id: str) -> List[dict]:
        """获取教授某技能的资料（入边 TEACHES）"""
        return self.get_neighbors(skill_id, relation="TEACHES", direction="in")

    def get_skills_by_cefr(self, level: str, sub_type: Optional[str] = None) -> List[dict]:
        """获取某 CEFR 等级下的所有技能"""
        cefr_id = f"cefr:{level}"
        results = []
        for nid, attrs in self.graph.nodes(data=True):
            if attrs["type"] != "skill":
                continue
            if sub_type and attrs.get("sub_type") != sub_type:
                continue
            # 检查是否有 BELONGS_TO 边指向该 CEFR
            if self.graph.has_edge(nid, cefr_id):
                edge = self.graph.edges[nid, cefr_id]
                if edge["relation"] == "BELONGS_TO":
                    results.append({"id": nid, **attrs})
        return results

    def get_materials_by_cefr(self, level: str) -> List[dict]:
        """获取某 CEFR 等级的资料"""
        cefr_id = f"cefr:{level}"
        results = []
        for nid, attrs in self.graph.nodes(data=True):
            if attrs["type"] != "material":
                continue
            if self.graph.has_edge(nid, cefr_id):
                edge = self.graph.edges[nid, cefr_id]
                if edge["relation"] == "BELONGS_TO":
                    results.append({"id": nid, **attrs})
        return results

    def get_materials_covering_topic(self, topic_id: str) -> List[dict]:
        """获取覆盖某场景的资料（入边 COVERS）"""
        return self.get_neighbors(topic_id, relation="COVERS", direction="in")

    # ============================================================
    # 图遍历
    # ============================================================

    def get_prerequisite_chain(self, skill_id: str) -> List[str]:
        """获取技能的完整前置依赖链（拓扑排序）"""
        if skill_id not in self.graph:
            return []

        # BFS 收集所有前置节点
        visited = set()
        queue = [skill_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for _, prereq, attrs in self.graph.out_edges(current, data=True):
                if attrs["relation"] == "HAS_PREREQ" and prereq not in visited:
                    queue.append(prereq)

        # 子图拓扑排序
        subgraph = self.graph.subgraph(visited)
        try:
            return list(nx.topological_sort(subgraph))
        except nx.NetworkXError:
            return list(visited)

    def shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """两节点间最短路径"""
        if source_id not in self.graph or target_id not in self.graph:
            return None
        try:
            return nx.shortest_path(self.graph, source_id, target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_skills_by_dimension(self, dimension: str) -> List[str]:
        """获取属于某维度的技能节点 ID 列表

        dimension: listening / speaking / reading / grammar
        """
        results = []
        for nid, attrs in self.graph.nodes(data=True):
            if attrs["type"] != "skill":
                continue
            extra = attrs.get("extra_data", {})
            if extra.get("dimension") == dimension:
                results.append(nid)
        return results

    # 维度 → 技能子类型映射
    DIMENSION_SKILL_MAP = {
        "listening": None,       # 听力理解关联所有音素
        "speaking": "phoneme",   # 口语表达关联音素
        "reading": "vocabulary", # 阅读理解关联词汇
        "grammar": "grammar",    # 语法选择关联语法
    }

    def get_skills_for_dimension(self, dimension: str) -> List[str]:
        """根据测评维度获取关联的技能节点 ID"""
        sub_type = self.DIMENSION_SKILL_MAP.get(dimension)
        if sub_type:
            skills = self.get_nodes_by_type("skill", sub_type)
        else:
            # listening 维度关联所有音素
            skills = self.get_nodes_by_type("skill", "phoneme")
        return [s["id"] for s in skills]

    def get_topics_by_tags(self, tags: List[str]) -> List[dict]:
        """根据兴趣标签匹配场景"""
        results = []
        for nid, attrs in self.graph.nodes(data=True):
            if attrs["type"] != "topic":
                continue
            topic_tags = attrs.get("extra_data", {}).get("tags", [])
            if any(t in topic_tags for t in tags):
                results.append({"id": nid, **attrs})
        return results

    # ============================================================
    # 智能客服集成 — 薄弱点搜索 + 资源推荐
    # ============================================================

    def search_skills(self, keyword: str) -> List[dict]:
        """模糊搜索技能节点 — 按 label 关键词匹配

        返回: [{"id": "skill:past_tense", "label": "过去时", "type": "skill", "sub_type": "grammar"}, ...]
        """
        keyword_lower = keyword.lower()
        results = []
        for nid, attrs in self.graph.nodes(data=True):
            if attrs["type"] != "skill":
                continue
            label = attrs.get("label", "").lower()
            # 关键词匹配：label 包含 keyword，或 keyword 包含在 label 中
            if keyword_lower in label or any(
                kw in label for kw in keyword_lower.split()
            ):
                results.append({"id": nid, **attrs})
        # 按匹配度排序（完全匹配优先）
        results.sort(key=lambda r: len(r["label"]))
        return results

    def get_skill_context(self, skill_id: str) -> dict:
        """获取技能节点的完整教学上下文

        返回:
            {
                "skill": {"id": "...", "label": "...", ...},
                "cefr_level": "A2",
                "prerequisites": [{"id": "...", "label": "..."}, ...],
                "materials": [{"id": "...", "label": "...", "type": "video"}, ...],
                "similar_skills": [{"id": "...", "label": "..."}, ...],
            }
        """
        if skill_id not in self.graph:
            return {}

        skill_attrs = dict(self.graph.nodes[skill_id])
        result = {
            "skill": {"id": skill_id, **skill_attrs},
            "cefr_level": self._get_cefr_for_skill(skill_id),
            "prerequisites": self._get_prerequisite_labels(skill_id),
            "materials": self._get_material_labels(skill_id),
            "similar_skills": self._get_similar_labels(skill_id),
        }
        return result

    def _get_cefr_for_skill(self, skill_id: str) -> str:
        """获取技能所属的 CEFR 等级"""
        for _, target, attrs in self.graph.out_edges(skill_id, data=True):
            if attrs["relation"] == "BELONGS_TO":
                target_attrs = self.graph.nodes[target]
                if target_attrs["type"] == "cefr_level":
                    return target_attrs.get("label", target)
        return "未知"

    def _get_prerequisite_labels(self, skill_id: str) -> List[dict]:
        """获取技能的前置依赖（简化列表）"""
        prereqs = self.get_prerequisites(skill_id)
        return [{"id": p["id"], "label": p.get("label", p["id"])} for p in prereqs]

    def _get_material_labels(self, skill_id: str) -> List[dict]:
        """获取教授该技能的资料（简化列表）"""
        materials = self.get_materials_teaching(skill_id)
        return [{"id": m["id"], "label": m.get("label", m["id"]),
                 "type": m.get("sub_type", m.get("type", "material"))} for m in materials]

    def _get_similar_labels(self, skill_id: str) -> List[dict]:
        """获取易混淆技能（简化列表）"""
        similar = self.get_similar_skills(skill_id)
        return [{"id": s["id"], "label": s.get("label", s["id"])} for s in similar]

    def find_recommendations(self, keyword: str) -> dict:
        """根据关键词查找技能并返回完整推荐上下文

        这是智能客服调用的主入口：
        1. 搜索匹配的技能
        2. 对每个匹配技能获取完整上下文（前置/资料/相似技能/等级）
        """
        skills = self.search_skills(keyword)
        if not skills:
            return {"found": False, "keyword": keyword, "results": []}

        results = []
        for skill in skills[:3]:  # 最多取前3个匹配
            context = self.get_skill_context(skill["id"])
            results.append(context)

        return {"found": True, "keyword": keyword, "results": results}

    def add_node(self, db: Session, node_id: str, node_type: str, label: str,
                 sub_type: Optional[str] = None, extra_data: Optional[dict] = None):
        """添加节点"""
        db_node = KGNode(
            id=node_id, type=node_type, sub_type=sub_type,
            label=label, extra_data=extra_data or {},
        )
        db.add(db_node)
        db.commit()
        self.graph.add_node(node_id, type=node_type, sub_type=sub_type,
                            label=label, extra_data=extra_data or {})

    def add_edge(self, db: Session, source_id: str, target_id: str,
                 relation: str, weight: float = 1.0, extra_data: Optional[dict] = None):
        """添加边"""
        db_edge = KGEdge(
            source_id=source_id, target_id=target_id,
            relation=relation, weight=weight, extra_data=extra_data or {},
        )
        db.add(db_edge)
        db.commit()
        self.graph.add_edge(source_id, target_id, relation=relation,
                            weight=weight, extra_data=extra_data or {})


# 全局单例
kg_service = KnowledgeGraphService.get_instance()