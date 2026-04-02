# Mistake Notebook Reference

## Current Defaults

- 默认复习内容导出格式是 PDF
- 默认交互顺序是先文字列表，再按需发送 PDF
- 默认复习更新方式是用户自然语言触发，自动调用 `update-review.py`
- 默认文案风格是亲和、直接、专业，不使用强人设称呼
- `SKILL.md` 是运行时入口；本文件补充维护约束和结构说明
- 生成的错题（`data/mistake-notebook/` 下 `type: mistake-record` 等）为 Obsidian 友好格式：frontmatter 即库内 **Properties**；正文与相关笔记使用 **`[[双向链接]]`**，支持反向链接与图谱

## Recommended Scripts

| 功能 | 推荐脚本 | 说明 |
|------|---------|------|
| 依赖检查 | `check-deps.py` | 首次使用或环境异常时优先执行 |
| 导出复习内容 | `export-printable.py` | 默认 PDF；省略 `--output` 时见下表「默认输出文件名」 |
| 生成举一反三 | `generate-practice.py` | 默认 `practice/{日期}-{知识点}-举一反三.md` + 同名 `.pdf`（`--md-only` 跳过 PDF） |
| 薄弱点分析 | `weak-points.py` | 默认 `reports/{日期}-薄弱知识点TOPn.md` |
| 分析报告 | `analyze.py` | 默认 `reports/{日期}-{学科|全科}-错题分析报告.md` |
| 月度报告 | `monthly-report.py` | 默认 `reports/{年}年{月}月-{学科|全科}-错题分析报告.md`；可选 `--subject` |
| 每日提醒 | `daily-review-reminder.py` | 支持 `--dry-run` 和消息渠道 |
| 复习进度更新 | `update-review.py` | 今日/按学科批量或单题更新 |

## Legacy But Not Default

这些脚本仍在仓库里，但不是当前默认工作流：

- `share.py`
- `generate-image.py`
- `review-reminder.py`

如果未来重新启用，必须先同步更新 `SKILL.md` 与本文件，避免规则分叉。

### 已移除的脚本

- **`export-pdf.py`**（pdfkit / wkhtmltopdf）：错题复习 PDF 请只用 **`export-printable.py`**。
- **`export-practice-pdf.py`**：已由 **`generate-practice.py`** 默认同时生成 Markdown 与 PDF 取代。

## 默认输出文件名约定

逻辑见 `scripts/output_naming.py`。`{日期}` 为中文 `2026年4月1日` 这种形式（导出日或 `--date`）。

| 场景 | 目录 | 默认文件名模式 |
|------|------|----------------|
| 复习 PDF/MD 导出 | `students/<学生>/exports/` | `{日期}-全科` / `{日期}-数学` / `{日期}-物理` …；带 `--unit` 时后缀 `-单元…` |
| 综合分析 | `…/reports/` | `{日期}-{学科|全科}-错题分析报告.md` |
| 月度总结 | `…/reports/` | `{年}年{月}月-{学科|全科}-错题分析报告.md`（如 `2026年3月-数学-错题分析报告.md`） |
| 薄弱知识点 | `…/reports/` | `{日期}-薄弱知识点TOP5.md`（数字随 `--top`） |
| 家长简报 | `…/reports/` | `{日期}-家长简报.md` |
| 检索结果 | `…/search/` | `{日期}-{HHMM}-检索结果.md`（同日多次不互相覆盖） |
| 举一反三 | `…/practice/` | `{日期}-{知识点}-举一反三.md` 与 **同名 `.pdf`**（与 `export-printable` 共用 Playwright 导出逻辑） |

飞书/cron 上传「今日数学复习 PDF」时，需在脚本里按**当天日期**拼出文件名（或解析终端 `OUTPUT_PATH=`），因默认名含日期、每日会换新文件。

## Minimal Record Requirements

每道错题至少确认这些字段：

- 学生
- 学科
- 学段或年级
- 学期或教材版本
- 知识点
- 错误类型
- 复习状态相关字段

最小合法 frontmatter 示例：

```yaml
---
type: mistake-record
id: 20260331-001
student: 曲凌松
subject: physics
stage: middle
grade: grade-8
semester: semester-2
knowledge-point: 力的合成
error-type: 受力分析错误
status: 待复习
created: 2026-03-31
updated: 2026-03-31
due-date: 2026-04-01
review-round: 0
---
```

### `due-date` 与 SRS 完成（重要）

- **`due-date`**：下一轮到期的复习日；完成全部间隔后应写成 `completed`（或历史数据里的 `done`），此后不再进入「今日待复习」列表。
- **「今天有什么要复习」**：只列出**有效到期日 ≤ 今天**的题目（含已超期仍待复习的）；**尚未到期**（有效到期日在今天之后）的题目不显示。
- **第一轮（`review-round: 0`）**：待复习队列里的到期日**严格**按 `created` 日期 **+1 天** 计算，与文件里旧的 `due-date` 不一致时，以 `created+1` 为准。需要把 frontmatter 改一致时运行：  
  `python3 skills/mistake-notebook/scripts/update-review.py --student <姓名> --fix-first-due`

## Directory Layout

```text
mistake-notebook/
├── SKILL.md
├── reference.md
├── examples.md
├── README.md
├── requirements.txt
├── scripts/
├── docs/
│   ├── requirements.md
│   ├── auto-review-update.md
│   ├── review-update-guide.md
│   ├── cron-setup.md
│   └── plans/
└── resources/
    ├── student-profile-template.md
    ├── error-types.md
    ├── similar-problems-template.md
    └── curriculum/
```

## Data Layout

```text
data/mistake-notebook/
└── students/
    └── {student-name}/
        ├── profile.md
        ├── mistakes/
        ├── reports/
        ├── practice/
        └── exports/
```

## Read Order By Scenario

- 环境安装、依赖缺失、PDF/Playwright 问题：读 `docs/requirements.md`
- 自然语言触发“今天有什么要复习的”“复习完了”：读 `docs/auto-review-update.md`
- 复习进度更新、批量/单题更新：读 `docs/review-update-guide.md`
- 定时提醒、飞书/微信渠道、`crontab`、`--dry-run`：读 `docs/cron-setup.md`
- 学生档案不存在或需要新建：读 `resources/student-profile-template.md`
- 错误类型标注、分析归因：读 `resources/error-types.md`
- 生成举一反三、变式题、分层练习：读 `resources/similar-problems-template.md`
- 按教材版本或单元分类：读 `resources/curriculum/` 下对应学科文件
- 需要项目总览或脚本入口总表：读 `README.md`

## Anti-Patterns

- 元数据不完整时直接保存错题
- 用户只问“今天复习什么”就直接导出 PDF
- 在「今日待复习」回复里额外加「其他错题进度」「未到期题目」等，与脚本只返回当日到期/超期列表不一致，造成混淆
- 用户未明确要求就主动发送文件
- 让用户手动逐题更新本可批量更新的复习记录
- 把本 skill 当普通讲题 skill 使用
- 引入新的默认工作流，却没有同步更新 `SKILL.md`

## Maintenance Checklist

- [ ] 入口规则是否仍与 `SKILL.md` 一致
- [ ] 默认导出格式是否仍为 PDF
- [ ] 复习更新是否仍以自然语言自动触发为主
- [ ] 是否避免使用强人设文案
- [ ] 如调整默认工作流，是否同步更新引用文档
