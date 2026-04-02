---
name: mistake-notebook
description: "Use this skill for a student's 错题本 workflow in Obsidian or `data/mistake-notebook/`, especially when the user is recording wrong answers, managing spaced review, or asking what should be reviewed today. Trigger for: 录入或归档错题 from photos or text; filling or explaining `type: mistake-record` YAML/frontmatter; “今天有什么要复习的”, “今天的复习提醒”, or “复习完了”; exporting subject review PDFs; generating 举一反三 or 变式题; analyzing 薄弱知识点 or 月报; setting Feishu/WeChat daily reminders or `crontab`; and first-run checks with `check-deps`, `export-printable`, `generate-practice`, `weak-points`, `monthly-report`, `daily-review-reminder`, or `update-review`. Prefer this skill even if the user does not name it but mentions student profiles, review-round, `due-date`, or `mistake-record`. Do not use for one-off tutoring, generic study plans, Anki, grade spreadsheets, receipt OCR, or unrelated repo engineering."
---

# Mistake Notebook

面向中小学错题整理与复习管理的工作流型 skill。重点不是“讲题”，而是把错题录入、归档、复习、分析、导出和提醒串成一套可持续使用的流程。

## Quick Start

优先在这些场景使用本 skill：

- 录入或整理错题到 Obsidian 或 `data/mistake-notebook/`
- 补全或解释 `type: mistake-record` 的 YAML/frontmatter
- 查询“今天有什么要复习的”或“今天的复习提醒”
- 导出某科或全部复习 PDF
- 用户说“复习完了”，需要自动更新复习进度
- 生成举一反三、薄弱点分析、分析报告、月报
- 配置每日提醒、飞书/微信渠道、`crontab`
- 第一次使用，需要检查依赖或环境

不要在这些场景使用本 skill：

- 只想讲一道题，不建档、不归档、不更新错题本
- 通用学习计划、背单词、Anki
- 成绩单、Excel、排名统计
- 通用 OCR、小票/票据
- 与 `mistake-notebook` 数据规范无关的工程任务

## Core Rules

1. 每道错题都要有完整元数据。缺字段时先追问再入库。
2. 用户问“今天有什么要复习的”时，先给文字列表，不要直接发 PDF。
3. 回答「今日待复习」时，**只呈现与脚本一致的待复习列表**（有效到期日 ≤ 今天，含超期）。**不要**自作主张追加「其他错题进度」「尚未到期的题」「全盘错题概况」等额外小节——会与「今天该复习什么」的语义混淆；用户若要其他视图应单独说明。
4. 只有在用户明确要求发送某科或全部复习内容时，才导出 PDF。
5. 用户说“复习完了”时，优先自动批量更新今日到期内容。
6. 更新复习后，要告诉用户复习统计和下次复习日期。
7. 优先复用现有脚本，不要临时发明平行工作流。
8. 回复语气保持亲和、直接、专业，不使用强人设称呼。

## Workflow

### 1. 环境检查

当用户第一次使用，或提到依赖、安装失败、PDF 导出失败时：

1. 先运行 `check-deps.py`
2. 缺依赖时再给安装命令
3. 详细安装说明读 `docs/requirements.md`

### 2. 录入错题

当用户提供照片、截图、题目文本，或要求“录入错题”“整理错题本”时：

1. 确认学生档案是否存在
2. 抽取题目内容和学生作答
3. 补齐学科、年级/学段、学期/教材、单元、知识点、错误类型
4. 如信息不完整，先问关键缺口
5. 存入 `data/mistake-notebook/` 对应目录
6. 文件格式需便于用户在 Obsidian 中使用：`---` 内字段作为 **Properties**，与单元、档案、举一反三等用 **`[[wikilink]]`** 建立双向链接

需要时读取：

- `resources/student-profile-template.md`
- `resources/error-types.md`
- `resources/curriculum/` 下对应学科文件

### 3. 查询待复习内容

当用户说“今天有什么要复习的”“今天的复习提醒”时：

1. 先生成今日待复习列表：**仅包含有效到期日 ≤ 今天的题目**（含已超期）；**未到期的题目不得列出**
2. 按学科分组
3. 只返回文字列表；**勿在列表外加「其他错题进度」等补充块**（与规则 3 一致）
4. 明确提示可继续说“发送物理的复习内容”“发送所有复习内容”

详细触发词和回复逻辑读：

- `docs/auto-review-update.md`
- `docs/review-update-guide.md`

### 4. 发送复习内容

当用户明确要求发送某科或全部复习内容时：

1. 使用 **`export-printable.py`**（已删除 `export-pdf.py`，不再使用 pdfkit/wkhtmltopdf）
2. 默认导出 PDF
3. 未指定 `--output` 时，复习导出写入 `exports/`，文件名为**中文日期 + 学科**（如 `2026年4月1日-数学.pdf`、`…-全科.pdf`）；飞书侧需按当日日期拼接路径或解析 `OUTPUT_PATH=`。其他报告类脚本的默认名见 `reference.md` 与 `scripts/output_naming.py`
4. 环境支持附件时发送文件，否则返回路径
5. 告诉用户如何使用：下载、独立重做、对照解析、复习后再告知完成

更多例子读 `examples.md`。

### 5. 更新复习进度

当用户说“复习完了”“今天的错题复习完了”“物理复习完了”时：

1. 自动推断今天/学科（必要时补问）
2. 优先批量更新
3. 运行 `update-review.py`
4. 返回更新数量、涉及学科、下次复习日期

`review-round: 0` 时，待复习到期日按 **`created + 1 天`** 计算；若历史文件里 `due-date` 与该日期不一致，可运行 `update-review.py --fix-first-due` 写回。

详细参数和自然语言映射读：

- `docs/auto-review-update.md`
- `docs/review-update-guide.md`

### 6. 举一反三 / 分析 / 报告

当用户要生成变式题、薄弱点分析、分析报告、月报时，优先使用：

- `generate-practice.py`（默认 Markdown + 同名 PDF，Playwright；`--md-only` 可只出 md）
- `weak-points.py`
- `analyze.py`
- `monthly-report.py`

相关参考：

- `resources/similar-problems-template.md`
- `resources/error-types.md`

### 7. 定时提醒 / 飞书 / 微信

当用户要“每天 18:00 自动提醒”“给飞书发今日复习提醒”时：

1. 使用 `daily-review-reminder.py`
2. 需要时先 `--dry-run`
3. 再给 `crontab` 或 `systemd timer` 配置
4. 说明提醒渠道参数

详细配置读 `docs/cron-setup.md`。

## Additional Resources

- `reference.md`：维护约束、目录结构、推荐脚本、反模式
- `examples.md`：高频自然语言入口、典型回复骨架、命令示例
- `docs/requirements.md`：依赖安装与 PDF/Playwright 问题
- `docs/auto-review-update.md`：自然语言触发与自动响应流程
- `docs/review-update-guide.md`：复习更新参数与最佳实践
- `docs/cron-setup.md`：定时提醒与消息渠道配置
- `resources/student-profile-template.md`：学生档案模板
- `resources/error-types.md`：错误类型规范
- `resources/similar-problems-template.md`：举一反三模板
- `resources/curriculum/`：教材版本和单元映射参考

## Self-Check

- 是否判断清楚这是错题本工作流，而不是普通讲题
- 是否补齐了关键元数据
- 是否遵守了“先文字列表，后按需发 PDF”
- 「今日待复习」回复是否未夹带「其他错题进度」等与查询范围不一致的内容
- 是否复用了已有脚本
- 是否在复习更新后给出统计和下次日期
