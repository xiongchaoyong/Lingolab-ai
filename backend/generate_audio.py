"""为发音练习内容批量生成 TTS 音频"""
import asyncio
import os
import sys

# 确保从 backend/ 目录运行，以便 pydantic 能找到 .env 文件
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

from app.core.database import SessionLocal
from app.models.pronunciation import PronunciationContent
from app.services.tts import synthesize_speech

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads", "pronunciation")


async def main():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    db = SessionLocal()

    items = db.query(PronunciationContent).filter(PronunciationContent.is_active == True).all()
    print(f"共 {len(items)} 条发音内容需要生成音频\n")

    generated = 0
    skipped = 0

    for item in items:
        # 文件名：pron_<id>.mp3
        filename = f"pron_{item.id}.mp3"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # 已存在则跳过
        if os.path.exists(filepath):
            print(f"  [{item.id}] ⏭ 跳过（已存在）: {item.title}")
            if not item.audio_url:
                item.audio_url = f"/static/pronunciation/{filename}"
                db.add(item)
            skipped += 1
            continue

        print(f"  [{item.id}] 🎤 生成中: {item.title} → \"{item.content_text[:50]}\"")
        try:
            audio_bytes = await synthesize_speech(item.content_text)
            with open(filepath, "wb") as f:
                f.write(audio_bytes)

            item.audio_url = f"/static/pronunciation/{filename}"
            db.add(item)
            generated += 1
            print(f"         ✅ 完成 ({len(audio_bytes)} bytes)")
        except Exception as e:
            print(f"         ❌ 失败: {e}")

    db.commit()
    db.close()

    print(f"\n===== 完成 =====")
    print(f"生成: {generated} | 跳过: {skipped} | 总计: {len(items)}")
    print(f"文件目录: {UPLOAD_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
