"""文本嵌入服务 — 本地 HuggingFace 模型（免费，无需 API）"""

import os
import logging
from typing import List

# 必须在导入 transformers 前设置 HF 镜像（国内加速）
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import torch
import numpy as np

logger = logging.getLogger(__name__)

# BGE 中文小模型：512 维，约 100MB，首次加载自动下载
MODEL_NAME = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DIM = 512

_tokenizer = None
_model = None


def _load():
    """懒加载模型和分词器"""
    global _tokenizer, _model
    if _model is None:
        from transformers import AutoModel, AutoTokenizer
        logger.info(f"正在加载嵌入模型: {MODEL_NAME} ...")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModel.from_pretrained(MODEL_NAME)
        _model.eval()
        logger.info(f"嵌入模型加载完成，维度: {EMBEDDING_DIM}")


def _embed_texts(texts: List[str]) -> List[List[float]]:
    """内部：批量编码文本为向量（mean pooling + L2 normalize）"""
    _load()

    # BGE 模型使用说明：query 不需要前缀，直接编码即可
    encoded = _tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )

    with torch.no_grad():
        outputs = _model(**encoded)
        # 取最后一层 hidden states，做 mean pooling
        attention_mask = encoded["attention_mask"]
        token_embeddings = outputs.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        embeddings = torch.sum(token_embeddings * input_mask_expanded, dim=1) / torch.clamp(
            input_mask_expanded.sum(dim=1), min=1e-9
        )
        # L2 归一化
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

    return embeddings.cpu().numpy().tolist()


async def embed(text: str) -> List[float]:
    """将单条文本转为向量"""
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIM
    result = _embed_texts([text.strip()])
    return result[0]


def embed_sync(text: str) -> List[float]:
    """同步版本，供 ChromaDB 内部调用"""
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIM
    result = _embed_texts([text.strip()])
    return result[0]


async def embed_batch(texts: List[str]) -> List[List[float]]:
    """批量将文本转为向量（建索引时使用）"""
    if not texts:
        return []
    texts = [t.strip() for t in texts if t and t.strip()]
    if not texts:
        return []
    return _embed_texts(texts)
