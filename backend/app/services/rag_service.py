"""RAG 检索服务 — ChromaDB 向量存储 + 语义搜索"""

import os
import logging
from typing import List, Dict, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.services.embedding import embed_sync, EMBEDDING_DIM

logger = logging.getLogger(__name__)

# ChromaDB 数据存储路径
CHROMA_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_data")
COLLECTION_NAME = "knowledge_base"


class RAGService:
    """RAG 检索服务单例"""

    def __init__(self):
        os.makedirs(CHROMA_DATA_DIR, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=CHROMA_DATA_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            try:
                self._collection = self._client.get_collection(COLLECTION_NAME)
            except Exception:
                self._collection = self._client.create_collection(
                    name=COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                )
        return self._collection

    def _embed(self, text: str) -> List[float]:
        """同步嵌入（ChromaDB add/query 要求同步）"""
        return embed_sync(text)

    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict] = None) -> bool:
        """添加或更新单条文档到向量库

        Args:
            doc_id: 文档唯一 ID（对应 KnowledgeDocument.id 的字符串）
            text: 用于检索的文本（标题 + 正文拼接）
            metadata: 附加元数据（标题、分类等）
        """
        try:
            embedding = self._embed(text)
            self.collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}],
            )
            logger.info(f"RAG: 文档 {doc_id} 已索引")
            return True
        except Exception as e:
            logger.error(f"RAG: 索引文档 {doc_id} 失败: {e}")
            return False

    def add_documents_batch(self, items: List[dict]) -> int:
        """批量添加文档到向量库

        Args:
            items: [{"id": "1", "text": "...", "metadata": {...}}, ...]
        Returns:
            成功索引的数量
        """
        if not items:
            return 0

        ids = [item["id"] for item in items]
        texts = [item["text"] for item in items]
        metadatas = [item.get("metadata", {}) for item in items]

        # 批量嵌入
        embeddings = [self._embed(t) for t in texts]

        try:
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
            logger.info(f"RAG: 批量索引 {len(items)} 条文档完成")
            return len(items)
        except Exception as e:
            logger.error(f"RAG: 批量索引失败: {e}")
            return 0

    def search(self, query: str, top_k: int = 3) -> List[dict]:
        """语义搜索，返回最相关的 top_k 条文档

        Returns:
            [{"id": "1", "text": "...", "metadata": {...}, "score": 0.95}, ...]
        """
        try:
            embedding = self._embed(query)
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            items = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 0
                    # cosine distance → similarity: 1 - distance
                    score = round(1 - distance, 4) if distance else 0
                    items.append({
                        "id": doc_id,
                        "text": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "score": score,
                    })
            return items
        except Exception as e:
            logger.error(f"RAG: 搜索失败: {e}")
            return []

    def delete_document(self, doc_id: str) -> bool:
        """从向量库删除文档"""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"RAG: 删除文档 {doc_id} 失败: {e}")
            return False

    def count(self) -> int:
        """返回向量库文档数量"""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def clear(self) -> bool:
        """清空向量库（重建索引用）"""
        try:
            try:
                self._client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass  # 集合不存在时忽略
            self._collection = self._client.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("RAG: 向量库已清空并重建")
            return True
        except Exception as e:
            logger.error(f"RAG: 清空向量库失败: {e}")
            return False


# 全局单例
rag_service = RAGService()
