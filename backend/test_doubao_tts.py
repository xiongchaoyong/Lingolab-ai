"""
豆包 TTS 语音合成 — 功能测试
火山引擎 豆包语音合成大模型 v3 HTTP 异步接口

使用前请设置环境变量:
  export DOUBAO_APP_ID="your_app_id"
  export DOUBAO_ACCESS_KEY="your_access_key"

获取凭证: https://console.volcengine.com/speech/app → 创建应用 → 获取 App ID 和 Access Token
"""

import os
import sys
import time
import json
import uuid
import urllib.request

# ============================================================
# 配置
# ============================================================
APP_ID = os.environ.get("DOUBAO_APP_ID", "")
ACCESS_KEY = os.environ.get("DOUBAO_ACCESS_KEY", "")

# 音色: 可以用默认或指定
# 常见音色: zh_female_vv_uranus_bigtts, zh_male_M392_conversation_wvae_bigtts
# 更多: https://www.volcengine.com/docs/6561/79823
VOICE_TYPE = os.environ.get("DOUBAO_VOICE", "zh_female_vv_uranus_bigtts")

# API 配置
API_HOST = "https://openspeech.bytedance.com"
SUBMIT_URL = f"{API_HOST}/api/v3/tts/submit"
QUERY_URL = f"{API_HOST}/api/v3/tts/query"
RESOURCE_ID = "seed-tts-2.0"  # 2.0 模型，也可用 seed-tts-1.0

# ============================================================
# 1. 检查凭证
# ============================================================
print("=" * 50)
print("豆包 TTS 语音合成测试")
print("=" * 50)

if not APP_ID or not ACCESS_KEY:
    print("""
未设置 API 凭证！请先获取凭证:

1. 访问 https://console.volcengine.com/speech/app
2. 创建应用 → 勾选「语音合成」服务
3. 获取 App ID 和 Access Token
4. 设置环境变量:

   export DOUBAO_APP_ID="your_app_id"
   export DOUBAO_ACCESS_KEY="your_access_key"

然后重新运行: python3 test_doubao_tts.py

新用户有 2万字符免费额度: https://www.volcengine.com/docs/6561/
""")
    sys.exit(0)

print(f"App ID:    {APP_ID[:8]}...{APP_ID[-4:]}")
print(f"模型:      seed-tts-2.0")
print(f"音色:      {VOICE_TYPE}")
print(f"接口:      HTTP v3 异步长文本")

# ============================================================
# 2. 合成请求
# ============================================================
TEST_TEXTS = [
    ("短文本", "Hello, nice to meet you! Welcome to English speaking practice."),
    ("中文测试", "你好，欢迎使用豆包语音合成服务。"),
    ("长文本", (
        "The quick brown fox jumps over the lazy dog. "
        "Practice makes perfect. Keep practicing your English pronunciation every day, "
        "and you will see great improvement in your speaking skills. "
        "Remember that consistency is the key to success in language learning."
    )),
]

for label, text in TEST_TEXTS:
    print(f"\n{'─' * 40}")
    print(f"测试: {label}")
    print(f"文本: {text[:50]}{'...' if len(text) > 50 else ''}")
    print(f"{'─' * 40}")

    # 构建请求
    request_id = str(uuid.uuid4())
    payload = {
        "user": {"uid": "test_user_001"},
        "unique_id": request_id,
        "req_params": {
            "text": text,
            "speaker": VOICE_TYPE,
            "audio_params": {
                "format": "mp3",
                "sample_rate": 24000,
                "speech_rate": 0,
                "loudness_rate": 0,
            },
            "additions": {
                "disable_markdown_filter": True,
                # "enable_timestamp": True,  # 需要时间戳时打开
            },
        },
    }

    # 提交任务
    headers = {
        "Content-Type": "application/json",
        "X-Api-App-Id": APP_ID,
        "X-Api-Access-Key": ACCESS_KEY,
        "X-Api-Resource-Id": RESOURCE_ID,
    }

    req = urllib.request.Request(
        SUBMIT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        submit_time = time.time() - t0

        print(f"提交耗时: {submit_time:.2f}s")
        print(f"响应:     {json.dumps(result, ensure_ascii=False)}")

        if result.get("code") != 0 and result.get("status_code") != 200:
            error_msg = result.get("message", result.get("status_message", "未知错误"))
            print(f"提交失败: {error_msg}")
            continue

        task_id = result.get("task_id")
        if not task_id:
            print(f"未获取到 task_id，响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            continue

        print(f"任务ID:   {task_id}")

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"HTTP 错误: {e.code}")
        print(f"响应: {body}")
        continue
    except Exception as e:
        print(f"请求失败: {e}")
        continue

    # ============================================================
    # 3. 轮询结果
    # ============================================================
    print("\n轮询合成结果...")
    max_retries = 30  # 最多等 30 次
    audio_url = None

    for i in range(max_retries):
        time.sleep(2)

        query_payload = {"task_id": task_id}
        req = urllib.request.Request(
            QUERY_URL,
            data=json.dumps(query_payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                query_result = json.loads(resp.read().decode("utf-8"))

            status = query_result.get("task_status", query_result.get("status", -1))
            # task_status: 1=处理中, 2=成功, 3=失败
            if status == 2:
                # 成功 — 获取音频
                audio_url = query_result.get("audio_url")
                if not audio_url:
                    print(f"成功但无 audio_url: {json.dumps(query_result, ensure_ascii=False)}")
                break
            elif status == 3:
                print(f"合成失败: {query_result.get('message', '')}")
                break
            else:
                dots = "." * ((i % 3) + 1)
                print(f"\r  处理中{dots}   ", end="", flush=True)
        except Exception as e:
            print(f"\n查询失败: {e}")
            continue

    if not audio_url:
        print("\n未获取到音频")
        continue

    # ============================================================
    # 4. 下载音频
    # ============================================================
    audio_file = f"doubao_tts_{label}.mp3"
    print(f"\n下载音频: {audio_url[:60]}...")
    urllib.request.urlretrieve(audio_url, audio_file)

    file_size = os.path.getsize(audio_file)
    total_time = time.time() - t0
    print(f"文件保存: {audio_file}")
    print(f"文件大小: {file_size / 1024:.1f} KB")
    print(f"总耗时:   {total_time:.1f}s")

    # ============================================================
    # 5. 播放（macOS）
    # ============================================================
    if label == "短文本":
        print("\n播放音频...")
        import subprocess
        subprocess.run(["afplay", audio_file], check=False)

# ============================================================
# 总结
# ============================================================
print(f"\n{'=' * 50}")
print("测试完成!")
print(f"{'=' * 50}")
print(f"  接口:   {SUBMIT_URL}")
print(f"  模型:   seed-tts-2.0")
print(f"  音色:   {VOICE_TYPE}")
print(f"  格式:   MP3 / 24000Hz")
print()
print("生成文件:")
for _, label, _ in [(0, l, 0) for l, _ in TEST_TEXTS]:
    f = f"doubao_tts_{label}.mp3"
    if os.path.exists(f):
        print(f"  {f}  ({os.path.getsize(f)/1024:.1f} KB)")
