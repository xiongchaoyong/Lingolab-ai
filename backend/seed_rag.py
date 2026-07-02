"""RAG 知识库初始化脚本 — 从数据库 FAQ + Markdown 文档建立向量索引"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, Base, engine
from app.models.knowledge_base import KnowledgeDocument, SearchLog
from app.models.support import FAQEntry
from app.services.rag_service import rag_service

# 确保表存在
Base.metadata.create_all(bind=engine)


def import_faq_entries():
    """从 faq_entries 表导入到知识库"""
    db = SessionLocal()
    try:
        entries = db.query(FAQEntry).filter(FAQEntry.is_active == 1).all()
        if not entries:
            logger.info("faq_entries 表无数据，跳过")
            return []

        items = []
        for entry in entries:
            # 检查是否已存在
            existing = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.source_type == "faq",
                KnowledgeDocument.title == entry.question,
            ).first()
            if existing:
                continue

            category = entry.category if entry.category else "general"
            doc = KnowledgeDocument(
                title=entry.question,
                content=entry.answer,
                category=category,
                source_type="faq",
                is_active=1,
            )
            db.add(doc)
            db.flush()

            items.append({
                "id": str(doc.id),
                "text": f"问题：{entry.question}\n回答：{entry.answer}",
                "metadata": {
                    "title": entry.question,
                    "category": category,
                    "source_type": "faq",
                },
            })

        db.commit()
        logger.info(f"从 FAQ 导入 {len(items)} 条记录")
        return items
    finally:
        db.close()


def import_markdown_docs():
    """从 docs/ 目录导入 Markdown 文档"""
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    items = []

    if not os.path.isdir(docs_dir):
        logger.info("docs/ 目录不存在，跳过")
        return items

    # 需要索引的文档
    target_files = [
        "业务流程介绍文档.md",
        "introduction.md",
    ]

    for filename in target_files:
        filepath = os.path.join(docs_dir, filename)
        if not os.path.exists(filepath):
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 按 ## 标题分块
        chunks = _split_by_headers(content, filename)

        db = SessionLocal()
        try:
            for chunk_title, chunk_text in chunks:
                if len(chunk_text.strip()) < 50:
                    continue

                existing = db.query(KnowledgeDocument).filter(
                    KnowledgeDocument.source_type == "manual",
                    KnowledgeDocument.title == chunk_title,
                ).first()
                if existing:
                    continue

                doc = KnowledgeDocument(
                    title=chunk_title,
                    content=chunk_text,
                    category="general",
                    source_type="manual",
                    is_active=1,
                )
                db.add(doc)
                db.flush()

                items.append({
                    "id": str(doc.id),
                    "text": f"{chunk_title}\n{chunk_text}",
                    "metadata": {
                        "title": chunk_title,
                        "category": "general",
                        "source_type": "manual",
                    },
                })
            db.commit()
            logger.info(f"从 {filename} 导入 {len(items)} 条记录")
        finally:
            db.close()

    return items


def _split_by_headers(content: str, source: str) -> list:
    """按 ## 标题将文档拆分为多个段落"""
    lines = content.split("\n")
    chunks = []
    current_title = source.replace(".md", "")
    current_text = []

    for line in lines:
        if line.startswith("## "):
            if current_text and len("".join(current_text).strip()) >= 50:
                chunks.append((current_title, "".join(current_text)))
            current_title = line[3:].strip()
            current_text = []
        else:
            current_text.append(line)

    # 最后一个段落
    if current_text and len("".join(current_text).strip()) >= 50:
        chunks.append((current_title, "".join(current_text)))

    return chunks


def main():
    logger.info("=== RAG 知识库初始化 ===")

    # 1. 清空现有索引
    rag_service.clear()
    logger.info("向量库已清空")

    # 2. 导入 FAQ
    faq_items = import_faq_entries()

    # 3. 导入文档
    doc_items = import_markdown_docs()

    all_items = faq_items + doc_items

    if not all_items:
        logger.warning("没有可索引的文档！请先运行 seed_content.py 填充 FAQ 数据")
        return

    # 4. 批量向量化
    count = rag_service.add_documents_batch(all_items)
    logger.info(f"向量库索引完成: {count}/{len(all_items)} 条")


if __name__ == "__main__":
    main()
