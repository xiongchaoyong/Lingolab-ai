---
name: module-analysis
description: 根据 Word 文档中的图片占位文字，生成对应的 drawio 图并插入文档。输入：模块编号（如 模块1）。
---

# 功能模块分析技能

## 描述

`docs/功能模块需求分析/Lingolab-AI-功能需求规格说明.docx` 已包含完整文字内容，图片位置用 `[ 图 X.X-X 描述 ]` 占位标记。本技能负责：生成占位对应的 drawio 图 → 导出 PNG → 插入 Word 替换占位文字。

## 指令

### 步骤 0：确认范围

如果用户未指定，询问要处理哪些图（可指定模块、或具体图表编号）。

### 步骤 1：读取 Word 文档

用 python-docx 读取 `Lingolab-AI-功能需求规格说明.docx`，找到目标占位段落（含 `[ 图 X.X-X ... ]`）。

### 步骤 2：生成 drawio 图

严格遵循 `drawio-layout-rules`（黑白配色、PingFang SC 字体、紧凑竖向布局）：
- UML 用例图 → `docs/功能模块需求分析/drawio/图X.X-X-描述.drawio`
- 流程图 → 同上目录

每张图生成完立即导出 PNG（`/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -s 2`）。

### 步骤 3：插入 Word 文档

用 python-docx 操作：找到 `[ 图 X.X-X ... ]` 占位段落 → 在该段落前插入图片 → 将占位文字替换为正式图注（去掉方括号），图注居中。

**图片宽度**：用例图 5.5 inch，流程图 6.0 inch（宽图可适当缩小）。

### 步骤 4：更新 ai-log.md

记录操作摘要。

## 行为准则

- **不生成**独立 Word 文档，只操作已有的 `Lingolab-AI-功能需求规格说明.docx`
- 每次只处理一个模块（~3-8 张图），避免上下文膨胀
- 图片格式：PNG @2x scale
- 所有 drawio 源文件保留在 `docs/功能模块需求分析/drawio/` 供后续修改
- 不产生中间 md 文件
