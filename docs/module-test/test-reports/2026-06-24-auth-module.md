# Test Report: 认证模块 — Schema 校验 + 安全工具函数

**Date**: 2026-06-24
**Tester**: Claude Code (test-master)
**Branch**: feat/pronunciation-assessment

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 35 |
| Passed | 35 |
| Failed | 0 |
| Skipped | 0 |
| Duration | 1.53s |
| Coverage | N/A (未配置) |

## Test Scope

- [x] Pydantic Schema 字段校验（RegisterRequest / LoginRequest / ProfileUpdateRequest）
- [x] 密码哈希与验证（bcrypt）
- [x] 年龄分组逻辑
- [x] 学习目标映射
- [ ] 数据库集成测试（需 mock DB）
- [ ] API 端点测试（需 TestClient）

## Test Cases

### RegisterRequest — username 校验
| # | Test | Result |
|---|------|--------|
| 1 | 合法用户名 `test_user` | PASSED |
| 2 | 过短 `abc` → ValueError | PASSED |
| 3 | 过长 `21 字符` → ValueError | PASSED |
| 4 | 特殊字符 `test user!` → ValueError | PASSED |
| 5 | 下划线+数字 `test_user_123` 合法 | PASSED |

### RegisterRequest — email 校验
| # | Test | Result |
|---|------|--------|
| 6 | 合法邮箱 `test@example.com` | PASSED |
| 7 | 无 @ 符号 → ValueError | PASSED |
| 8 | 无域名 `test@` → ValueError | PASSED |

### RegisterRequest — password 校验
| # | Test | Result |
|---|------|--------|
| 9 | 过短 `Ab1` → ValueError | PASSED |
| 10 | 无数字 → ValueError | PASSED |
| 11 | 无字母 → ValueError | PASSED |
| 12 | 合法密码 `abcd1234` | PASSED |

### RegisterRequest — age / learning_goal / interests
| # | Test | Result |
|---|------|--------|
| 13 | 最小年龄 6 岁 | PASSED |
| 14 | 低于最小 5 岁 → ValueError | PASSED |
| 15 | 超过最大 100 岁 → ValueError | PASSED |
| 16 | 合法学习目标 `business` | PASSED |
| 17 | 非法学习目标 → ValueError | PASSED |
| 18 | interests 默认空列表 | PASSED |

### 密码工具函数
| # | Test | Result |
|---|------|--------|
| 19-22 | 哈希不可逆、盐值不同、验证正确/错误密码 | PASSED |

### 年龄分组
| # | Test | Result |
|---|------|--------|
| 23-28 | 儿童/青少年/大学生/职场/中老年 + 边界值 12→13 | PASSED |

### 学习目标映射
| # | Test | Result |
|---|------|--------|
| 29-30 | 5 个 key 齐全 + 中英文映射正确 | PASSED |

## Findings

无失败用例。

## Coverage Gaps

- `get_current_user` — 依赖数据库 Session，需 mock 后测试
- `create_access_token` / `decode_access_token` — 依赖 JWT_SECRET_KEY 配置，需集成测试
- `LoginResponse` / `RegisterResponse` / `ProfileResponse` — 仅数据类，无需独立测试

## Recommendations

1. **Immediate**: 为 `get_current_user` 添加 mock 测试（无效 token / 用户不存在 / 用户已禁用）
2. **High Priority**: 配置 pytest-cov，开启覆盖率统计
3. **Medium Priority**: 添加 API 端点集成测试（用 FastAPI TestClient）

## Sign-off

- [x] All critical issues addressed
- [ ] Coverage meets threshold (80%) — 待配置 pytest-cov
- [ ] Performance meets SLA — 不适用