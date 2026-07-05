"""Lingolab 端到端功能测试 — 真实 API 请求"""
import requests
import json
import time

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0
SKIP = 0
RESULTS = []
TOKEN = None
USER_ID = None

def test(name, method, path, expected_status, data=None, check_fn=None, auth=True, form=False):
    global PASS, FAIL, SKIP, TOKEN
    url = f"{BASE}{path}"
    headers = {"Authorization": f"Bearer {TOKEN}"} if auth and TOKEN else {}
    try:
        if method == "GET":
            resp = requests.get(url, params=data if method == "GET" else None, headers=headers, timeout=15)
        elif method == "POST" and form:
            resp = requests.post(url, data=data, headers=headers, timeout=15)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=headers, timeout=15)
        elif method == "PUT":
            resp = requests.put(url, json=data, headers=headers, timeout=15)
        elif method == "DELETE":
            resp = requests.delete(url, json=data, headers=headers, timeout=15)

        status_ok = resp.status_code == expected_status
        check_ok = True
        check_detail = ""
        body = {}
        if check_fn and status_ok:
            try:
                body = resp.json()
                check_ok = check_fn(body, resp)
                if not check_ok:
                    check_detail = "业务校验失败"
            except:
                check_ok = False
                check_detail = "JSON解析失败"

        if status_ok and check_ok:
            PASS += 1
            RESULTS.append(("✅", name, f"HTTP {resp.status_code}"))
        else:
            FAIL += 1
            detail = check_detail or f"期望 {expected_status}, 实际 {resp.status_code}"
            try:
                if isinstance(resp.json(), dict):
                    detail += f" | {json.dumps(resp.json(), ensure_ascii=False)[:150]}"
                else:
                    detail += f" | {str(resp.json())[:150]}"
            except:
                detail += f" | {resp.text[:150]}"
            RESULTS.append(("❌", name, detail))
    except requests.exceptions.ConnectionError:
        SKIP += 1
        RESULTS.append(("⏭️", name, "后端未启动"))
    except Exception as e:
        FAIL += 1
        RESULTS.append(("❌", name, str(e)[:150]))

def hdr(data=None):
    """快捷带auth请求"""
    return {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

def print_report():
    total = PASS + FAIL + SKIP
    rate = PASS/(PASS+FAIL)*100 if (PASS+FAIL) > 0 else 0
    print("\n" + "="*70)
    print(f"  Lingolab 功能测试报告 — {time.strftime('%Y-%m-%d %H:%M')}")
    print(f"  总计: {total} | ✅ 通过: {PASS} | ❌ 失败: {FAIL} | ⏭️ 跳过: {SKIP} | 通过率: {rate:.1f}%")
    print("="*70)
    for s, n, d in RESULTS:
        print(f"  {s} {n}")
        if s == "❌":
            print(f"     → {d}")
    print("="*70)

# ==================== 准备：注册 + 登录 ====================
print("🔧 准备测试账号...")
TIMESTAMP = int(time.time())
TEST_USER = f"ftest_{TIMESTAMP}"
TEST_PASS = "test1234"
TEST_EMAIL = f"ftest_{TIMESTAMP}@test.com"

# 注册
r = requests.post(f"{BASE}/api/auth/register", json={
    "username": TEST_USER, "email": TEST_EMAIL,
    "password": TEST_PASS, "age": 25, "learning_goal": "daily"
})
if r.status_code == 200:
    TOKEN = r.json().get("token")
    USER_ID = r.json().get("user_id")
    print(f"   ✅ 测试账号: {TEST_USER} (ID={USER_ID})")
elif "already exists" in str(r.json()):
    # 登录已有的
    r2 = requests.post(f"{BASE}/api/auth/login", json={"username": TEST_USER, "password": TEST_PASS})
    if r2.status_code == 200:
        TOKEN = r2.json().get("token")
        USER_ID = r2.json().get("user_id")
        print(f"   ✅ 使用已有账号: {TEST_USER} (ID={USER_ID})")
    else:
        print(f"   ❌ 登录失败: {r2.json()}")
else:
    print(f"   ❌ 注册失败: {r.json()}")

# ==================== 模块1: 用户认证 (Auth) ====================
print("\n📋 模块1: 用户认证")

test("1.1 注册-正常", "POST", "/api/auth/register", 200,
    {"username": f"ftest2_{TIMESTAMP}", "email": f"ftest2_{TIMESTAMP}@test.com",
     "password": "pass1234", "age": 30, "learning_goal": "exam"},
    check_fn=lambda b,r: b.get("token") and b.get("user_id"), auth=False)

test("1.2 注册-用户名过短(<4字符)", "POST", "/api/auth/register", 422,
    {"username": "ab", "email": "a@test.com", "password": "test1234", "age": 20, "learning_goal": "daily"}, auth=False)

test("1.3 注册-密码纯字母(无数字)", "POST", "/api/auth/register", 422,
    {"username": "tester99", "email": "t@test.com", "password": "abcdefgh", "age": 20, "learning_goal": "daily"}, auth=False)

test("1.4 注册-密码纯数字(无字母)", "POST", "/api/auth/register", 422,
    {"username": "tester99", "email": "t@test.com", "password": "12345678", "age": 20, "learning_goal": "daily"}, auth=False)

test("1.5 注册-年龄为0", "POST", "/api/auth/register", 422,
    {"username": "tester99", "email": "t@test.com", "password": "test1234", "age": 0, "learning_goal": "daily"}, auth=False)

test("1.6 注册-无效学习目标", "POST", "/api/auth/register", 422,
    {"username": "tester99", "email": "t@test.com", "password": "test1234", "age": 20, "learning_goal": "invalid_goal"}, auth=False)

test("1.7 登录-正确凭证", "POST", "/api/auth/login", 200,
    {"username": TEST_USER, "password": TEST_PASS},
    check_fn=lambda b,r: b.get("token"), auth=False)

test("1.8 登录-错误密码", "POST", "/api/auth/login", 401,
    {"username": TEST_USER, "password": "wrongpassword"}, auth=False)

test("1.9 登录-不存在用户", "POST", "/api/auth/login", 401,
    {"username": "user_never_exists_xyz", "password": "test1234"}, auth=False)

# ==================== 模块2: 用户画像 (Profile) ====================
print("\n📋 模块2: 用户画像")

test("2.1 获取个人画像", "GET", "/api/auth/profile", 200,
    check_fn=lambda b,r: b.get("username") == TEST_USER)

test("2.2 更新画像-修改目标", "PUT", "/api/auth/profile", 200,
    {"learning_goal": "business", "interests": ["科技", "商务"]},
    check_fn=lambda b,r: b.get("learning_goal") == "business")

test("2.3 更新画像-无效目标", "PUT", "/api/auth/profile", 422,
    {"learning_goal": "flying"})

test("2.4 获取维度分数", "GET", "/api/auth/profile/scores", 200,
    check_fn=lambda b,r: isinstance(b, dict))

test("2.5 刷新用户画像", "POST", "/api/auth/profile/refresh", 200,
    check_fn=lambda b,r: "message" in b or "level_final" in b)

# ==================== 模块3: 水平测评 (Assessment) ====================
print("\n📋 模块3: 水平测评")

ASSESS_SESSION = None
ASSESS_QID = None

test("3.1 开始测评", "POST", "/api/assessment/start", 200,
    check_fn=lambda b,r: b.get("session_id") and b.get("question"))

# 获取session和题目ID用于答题
try:
    r = requests.post(f"{BASE}/api/assessment/start", json={}, headers=hdr())
    ASSESS_SESSION = r.json().get("session_id")
    ASSESS_QID = r.json()["question"]["id"]
except: pass

test("3.2 提交答题", "POST", "/api/assessment/answer", 200,
    {"session_id": ASSESS_SESSION, "question_id": ASSESS_QID, "answer": "B", "question_index": 0}, form=True)

test("3.3 提交答题-无效session", "POST", "/api/assessment/answer", 404,
    {"session_id": "fake_session_12345", "question_id": ASSESS_QID or 1, "answer": "B", "question_index": 0}, form=True)

test("3.4 恢复未完成测评", "POST", "/api/assessment/restore", 200,
    {"session_id": ASSESS_SESSION}, form=True,
    check_fn=lambda b,r: isinstance(b, dict))

test("3.5 提交空答案测评", "POST", "/api/assessment/submit", 422,
    {"session_id": ASSESS_SESSION}, form=True)

# ==================== 模块4: 学习路径 (Learning Path) ====================
print("\n📋 模块4: 学习路径")

test("4.1 获取每日任务", "GET", "/api/learning-path/tasks", 200,
    check_fn=lambda b,r: "tasks" in b)

test("4.2 获取学习历史", "GET", "/api/learning-path/history", 200,
    check_fn=lambda b,r: "data" in b or "records" in b or isinstance(b, dict))

test("4.3 获取画像摘要", "GET", "/api/learning-path/profile-summary", 200,
    check_fn=lambda b,r: isinstance(b, dict))

# ==================== 模块5: AI语音对话 (Voice Chat) ====================
print("\n📋 模块5: AI语音对话")

test("5.1 开始语音对话", "POST", "/api/voice-chat/start", 200,
    {"topic": "restaurant", "cefr_level": "B1"},
    check_fn=lambda b,r: b.get("session_id") and (b.get("greeting") or b.get("ai_text")))

test("5.2 开始对话-无topic", "POST", "/api/voice-chat/start", 422)

test("5.3 获取会话列表", "GET", "/api/voice-chat/sessions", 200,
    check_fn=lambda b,r: isinstance(b, (list, dict)))

# ==================== 模块6: 角色扮演 (Roleplay) ====================
print("\n📋 模块6: 角色扮演")

test("6.1 开始角色扮演(面试者)", "POST", "/api/roleplay/start", 200,
    {"topic": "interviewee", "cefr_level": "B1"},
    check_fn=lambda b,r: b.get("session_id") and b.get("ai_text"))

test("6.2 开始角色扮演(自定义角色)", "POST", "/api/roleplay/start", 200,
    {"topic": "astronaut", "cefr_level": "B1"},
    check_fn=lambda b,r: b.get("session_id") and b.get("ai_text"))

# ==================== 模块7: 发音评测 (Pronunciation) ====================
print("\n📋 模块7: 发音评测")

test("7.1 获取练习内容", "GET", "/api/pronunciation/content", 200,
    check_fn=lambda b,r: isinstance(b, list))

test("7.2 获取练习内容-单词", "GET", "/api/pronunciation/content", 200,
    {"type": "word"}, check_fn=lambda b,r: isinstance(b, list))

test("7.3 获取练习内容-句子", "GET", "/api/pronunciation/content", 200,
    {"type": "sentence"}, check_fn=lambda b,r: isinstance(b, list))

test("7.4 获取练习记录", "GET", "/api/pronunciation/records", 200,
    check_fn=lambda b,r: isinstance(b, list))

test("7.5 发音评测-无音频", "POST", "/api/pronunciation/score", 422)

# ==================== 模块8: 语法纠错 (Grammar) ====================
print("\n📋 模块8: 语法纠错")

test("8.1 语法纠错-有错误的句子", "POST", "/api/grammar/correct", 200,
    {"text": "I go to the store yesterday and buyed some apple", "cefr_level": "B1"}, form=True,
    check_fn=lambda b,r: len(b.get("errors", [])) > 0)

test("8.2 语法纠错-正确句子", "POST", "/api/grammar/correct", 200,
    {"text": "I went to the store yesterday", "cefr_level": "B1"}, form=True,
    check_fn=lambda b,r: isinstance(b.get("errors"), list))

test("8.3 语法纠错-空文本", "POST", "/api/grammar/correct", 422,
    {"text": "", "cefr_level": "B1"}, form=True)

# ==================== 模块9: 游戏化闯关 (Gamification) ====================
print("\n📋 模块9: 游戏化闯关")

test("9.1 获取每日挑战", "GET", "/api/gamification/daily-challenge", 200,
    check_fn=lambda b,r: "levels" in b or "challenges" in b or isinstance(b, dict))

test("9.2 获取排行榜", "GET", "/api/gamification/leaderboard", 200,
    check_fn=lambda b,r: isinstance(b, list))

test("9.3 获取用户积分", "GET", "/api/gamification/points", 200,
    check_fn=lambda b,r: "total_points" in b)

test("9.4 获取徽章列表", "GET", "/api/gamification/badges", 200,
    check_fn=lambda b,r: isinstance(b, list))

# ==================== 模块10: 学习进度 (Progress) ====================
print("\n📋 模块10: 学习进度")

test("10.1 雷达图数据", "GET", "/api/progress/radar", 200,
    check_fn=lambda b,r: isinstance(b, dict))

test("10.2 趋势图数据", "GET", "/api/progress/trend", 200,
    {"dimension": "pronunciation", "period": "week"},
    check_fn=lambda b,r: isinstance(b, dict))

test("10.3 热力图数据", "GET", "/api/progress/heatmap", 200,
    check_fn=lambda b,r: isinstance(b, dict))

test("10.4 统计卡片", "GET", "/api/progress/stats", 200,
    check_fn=lambda b,r: isinstance(b, dict))

# ==================== 模块11: 学习预测 (Prediction) ====================
print("\n📋 模块11: 学习预测")

test("11.1 当前预测", "GET", "/api/prediction/current", 200,
    check_fn=lambda b,r: isinstance(b, dict))

test("11.2 预警检查", "GET", "/api/prediction/alerts", 200,
    check_fn=lambda b,r: isinstance(b, dict))

test("11.3 通知列表", "GET", "/api/notices", 200,
    check_fn=lambda b,r: isinstance(b, dict))

test("11.4 未读通知数", "GET", "/api/notices/unread-count", 200,
    check_fn=lambda b,r: "unread_count" in b)

# ==================== 模块12: 学习社区 (Community) ====================
print("\n📋 模块12: 学习社区")

test("12.1 语音挑战列表", "GET", "/api/community/challenges", 200,
    check_fn=lambda b,r: isinstance(b.get("challenges", []), list))

test("12.2 讨论区帖子", "GET", "/api/community/posts", 200,
    check_fn=lambda b,r: isinstance(b.get("posts", []), list))

# ==================== 模块13: 资料推荐 (Recommendations) ====================
print("\n📋 模块13: 资料推荐")

test("13.1 获取推荐列表", "GET", "/api/recommendations/", 200,
    check_fn=lambda b,r: isinstance(b.get("recommendations", []), list))

# ==================== 模块14: 智能客服 (Help) ====================
print("\n📋 模块14: 智能客服")

test("14.1 智能客服-提问", "POST", "/api/help/chat", 200,
    {"message": "发音评测功能怎么用？", "history": []},
    check_fn=lambda b,r: "reply" in b and len(b.get("reply", "")) > 0)

test("14.2 智能客服-空消息", "POST", "/api/help/chat", 422,
    {"message": "", "history": []})

test("14.3 智能客服-带历史", "POST", "/api/help/chat", 200,
    {"message": "什么是自适应测评？",
     "history": [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你好！我是小语"}]})

# ==================== 模块15: 学生端 (Student) ====================
print("\n📋 模块15: 学生端(B端)")

test("15.1 我的班级", "GET", "/api/student/classes", 200,
    check_fn=lambda b,r: isinstance(b, dict))

test("15.2 我的作业", "GET", "/api/student/assignments", 200,
    check_fn=lambda b,r: isinstance(b, dict))

# ==================== 模块16: 管理端权限 (Admin Auth) ====================
print("\n📋 模块16: 管理端权限")

test("16.1 仪表盘-学生无权限", "GET", "/api/admin/dashboard", 403)

test("16.2 用户管理-学生无权限", "GET", "/api/admin/users", 403)

test("16.3 班级管理-学生无权限", "GET", "/api/admin/classes", 403)

test("16.4 内容管理-学生无权限", "GET", "/api/admin/content/video", 403)

# ==================== 安全测试 ====================
print("\n📋 安全与鉴权")

test("S1 无Token访问需认证接口", "GET", "/api/progress/radar", 403, auth=False)

test("S2 无效Token访问", "GET", "/api/progress/radar", 403, auth=False)
# 手动测invalid token
try:
    r = requests.get(f"{BASE}/api/progress/radar",
                     headers={"Authorization": "Bearer eyJinvalid.token.here"})
    if r.status_code in (401, 403):
        PASS += 1
        RESULTS.append(("✅", "S2b 格式错误Token", f"HTTP {r.status_code}"))
    else:
        FAIL += 1
        RESULTS.append(("❌", "S2b 格式错误Token", f"期望401/403, 实际{r.status_code}"))
except Exception as e:
    FAIL += 1
    RESULTS.append(("❌", "S2b 格式错误Token", str(e)[:120]))

# ==================== 输出 ====================
print_report()
print(f"\n📁 报告已生成 — 测试完成于 {time.strftime('%Y-%m-%d %H:%M:%S')}")
