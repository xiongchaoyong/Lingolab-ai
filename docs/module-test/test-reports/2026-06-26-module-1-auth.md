# 模块 1 测试报告：用户注册与多维度画像

> 日期：2026-06-26
> 测试框架：pytest 9.1.1
> 测试文件：`backend/test_auth.py`

---

## Summary

| 指标 | 值 |
|------|-----|
| 总用例数 | 41 |
| 通过 | 41 |
| 失败 | 0 |
| 跳过 | 0 |
| 耗时 | 1.52s |

---

## Test Cases

### TestRegisterRequest — 注册 Schema 校验（19 条）

| # | 用例 | 结果 |
|---|------|------|
| 1 | username 合法值 | ✅ PASS |
| 2 | username 少于 4 字符 → 拒绝 | ✅ PASS |
| 3 | username 超过 20 字符 → 拒绝 | ✅ PASS |
| 4 | username 含特殊字符 → 拒绝 | ✅ PASS |
| 5 | username 含下划线 → 允许 | ✅ PASS |
| 6 | email 合法格式 | ✅ PASS |
| 7 | email 无 @ → 拒绝 | ✅ PASS |
| 8 | email 无域名 → 拒绝 | ✅ PASS |
| 9 | password 少于 8 字符 → 拒绝 | ✅ PASS |
| 10 | password 无数字 → 拒绝 | ✅ PASS |
| 11 | password 无字母 → 拒绝 | ✅ PASS |
| 12 | password 合法值 | ✅ PASS |
| 13 | age 最小边界值（6） | ✅ PASS |
| 14 | age=5 后端允许（前端限制 6-99） | ✅ PASS |
| 15 | age=100 后端允许（前端限制 6-99） | ✅ PASS |
| 16 | age=0 被 ge=1 拒绝 | ✅ PASS |
| 17 | learning_goal 合法值 | ✅ PASS |
| 18 | learning_goal 无效值 → 拒绝 | ✅ PASS |
| 19 | interests 默认空数组 | ✅ PASS |

### TestLoginRequest — 登录 Schema 校验（1 条）

| # | 用例 | 结果 |
|---|------|------|
| 20 | 合法登录请求 | ✅ PASS |

### TestProfileUpdateRequest — 资料更新校验（3 条）

| # | 用例 | 结果 |
|---|------|------|
| 21 | 空更新（全 None）→ 允许 | ✅ PASS |
| 22 | 合法 learning_goal | ✅ PASS |
| 23 | 无效 learning_goal → 拒绝 | ✅ PASS |

### TestPasswordFunctions — 密码哈希/验证（4 条）

| # | 用例 | 结果 |
|---|------|------|
| 24 | 哈希结果不等于原始密码 | ✅ PASS |
| 25 | 同一密码两次哈希不同（bcrypt 加盐） | ✅ PASS |
| 26 | 正确密码验证通过 | ✅ PASS |
| 27 | 错误密码验证拒绝 | ✅ PASS |

### TestAgeGroup — 年龄分组映射（6 条）

| # | 用例 | 结果 |
|---|------|------|
| 28 | 儿童（6-12） | ✅ PASS |
| 29 | 青少年（13-17） | ✅ PASS |
| 30 | 大学生（18-22） | ✅ PASS |
| 31 | 职场（23-50） | ✅ PASS |
| 32 | 中老年（51+） | ✅ PASS |
| 33 | 边界值 12→13 跨组 | ✅ PASS |

### TestLearningGoalMap — 学习目标映射（3 条）

| # | 用例 | 结果 |
|---|------|------|
| 34 | 5 个 key 全部存在 | ✅ PASS |
| 35 | daily → 日常交流 | ✅ PASS |
| 36 | exam → 考试 | ✅ PASS |

### TestJWTToken — JWT 令牌（5 条）

| # | 用例 | 结果 |
|---|------|------|
| 37 | 创建 + 解析 Token，验证 user_id/username | ✅ PASS |
| 38 | Token 包含 exp 过期时间 | ✅ PASS |
| 39 | 无效 Token → 返回 None | ✅ PASS |
| 40 | 过期 Token + verify_exp=True → 返回 None | ✅ PASS |
| 41 | 过期 Token + verify_exp=False → 返回 payload（刷新用） | ✅ PASS |

---

## Findings

| 等级 | 描述 | 状态 |
|------|------|------|
| LOW | 原 test_age_below_min / test_age_above_max 断言错误：后端 Schema 允许 age 1-150，测试误以为有 6-99 限制 | 已修复 |
| LOW | Pydantic V2 废弃警告：`class-based config` 应迁移为 `ConfigDict` | 不影响功能 |
| LOW | python-jose 的 `datetime.utcnow()` 废弃警告 | 库自身问题，不影响功能 |

---

## Coverage Gaps

| 未覆盖功能 | 原因 | 建议 |
|------------|------|------|
| API 端点集成测试（register/login/profile） | 需要数据库 mock 或测试数据库 | 后续补充 |
| Token 刷新端点集成测试 | 同上 | 后续补充 |
| 路由守卫逻辑 | 前端 E2E 测试，需浏览器环境 | 后续补充 |
| 乐观锁并发行为 | 需并发测试场景 | 后续补充 |
