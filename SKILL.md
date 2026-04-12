---
name: mistake-notebook
version: 2.0.0
description: "Use this skill for a student's 错题本 workflow in Obsidian or `data/mistake-notebook/`, especially when the user is recording wrong answers, managing spaced review, or asking what should be reviewed today. Trigger for: 录入或归档错题 from photos or text; filling or explaining `type: mistake-record` YAML/frontmatter; "今天有什么要复习的", "今天的复习提醒", or "复习完了"; exporting subject review PDFs; generating 举一反三 or 变式题; analyzing 薄弱知识点 or 月报; setting Feishu/WeChat daily reminders or `crontab`; and first-run checks with `check-deps`, `export-printable`, `generate-practice`, `weak-points`, `monthly-report`, `daily-review-reminder`, or `update-review`. Prefer this skill even if the user does not name it but mentions student profiles, review-round, `due-date`, or `mistake-record`. Do not use for one-off tutoring, generic study plans, Anki, grade spreadsheets, receipt OCR, or unrelated repo engineering."
---

# Mistake Notebook

面向中小学错题整理与复习管理的工作流型 skill。重点不是"讲题"，而是把错题录入、归档、复习、分析、导出和提醒串成一套可持续使用的流程。

## Quick Start

优先在这些场景使用本 skill：

- **第一次使用**：运行 `init-student.py` 创建学生档案
- 录入或整理错题到 Obsidian 或 `data/mistake-notebook/`
- 补全或解释 `type: mistake-record` 的 YAML/frontmatter
- 查询"今天有什么要复习的"或"今天的复习提醒"
- 导出某科或全部复习 PDF
- 用户说"复习完了"，需要自动更新复习进度（支持 `--confidence` 设置掌握度）
- 生成举一反三（支持 `--difficulty` 难度筛选）、薄弱点分析、分析报告、月报
- **图表生成**：分析报告支持饼图、柱状图、热力图三种可视化图表
- 配置每日提醒、飞书/微信渠道、`crontab`
- 检查依赖或环境

不要在这些场景使用本 skill：

- 只想讲一道题，不建档、不归档、不更新错题本
- 通用学习计划、背单词、Anki
- 成绩单、Excel、排名统计
- 通用 OCR、小票/票据
- 与 `mistake-notebook` 数据规范无关的工程任务

## Core Rules

1. 每道错题都要有完整元数据。缺字段时先追问再入库。
2. 用户问"今天有什么要复习的"时，先给文字列表，不要直接发 PDF。
3. 回答「今日待复习」时，**只呈现与脚本一致的待复习列表**（有效到期日 ≤ 今天，含超期）。**不要**自作主张追加「其他错题进度」「尚未到期的题」「全盘错题概况」等额外小节--会与「今天该复习什么」的语义混淆；用户若要其他视图应单独说明。
4. 只有在用户明确要求发送某科或全部复习内容时，才导出 PDF。
5. 用户说"复习完了"时，优先自动批量更新今日到期内容。
6. 更新复习后，要告诉用户复习统计和下次复习日期。
7. 优先复用现有脚本，不要临时发明平行工作流。
8. 回复语气保持亲和、直接、专业，不使用强人设称呼。

## Workflow

### 1. 第一次使用：初始化学生档案

当用户第一次使用或提到"新建学生"、"创建档案"时：

1. 推荐运行 `init-student.py`（交互式）
2. 或非交互模式：`init-student.py --name "张三" --grade "八年级" --non-interactive`
3. 说明档案位置和下一步操作

### 2. 环境检查

当用户提到依赖、安装失败、PDF 导出失败时：

1. 先运行 `check-deps.py`
2. 缺依赖时再给安装命令
3. 详细安装说明读 `docs/requirements.md`

### 3. 录入错题

当用户提供照片、截图、题目文本，或要求"录入错题""整理错题本"时：

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

### 4. 查询待复习内容

当用户说"今天有什么要复习的""今天的复习提醒"时：

1. 先生成今日待复习列表：**仅包含有效到期日 ≤ 今天的题目**（含已超期）；**未到期的题目不得列出**
2. 按学科分组
3. 只返回文字列表；**勿在列表外加「其他错题进度」等补充块**（与规则 3 一致）
4. 明确提示可继续说"发送物理的复习内容""发送所有复习内容"

详细触发词和回复逻辑读：

- `docs/auto-review-update.md`
- `docs/review-update-guide.md`

### 5. 发送复习内容

当用户明确要求发送某科或全部复习内容时：

1. 使用 **`export-printable.py`**（已删除 `export-pdf.py`，不再使用 pdfkit/wkhtmltopdf）
2. 默认导出 PDF
3. 未指定 `--output` 时，复习导出写入 `exports/`，文件名为**中文日期 + 学科**（如 `2026年4月1日-数学.pdf`、`…-全科.pdf`）；飞书侧需按当日日期拼接路径或解析 `OUTPUT_PATH=`。其他报告类脚本的默认名见 `reference.md` 与 `scripts/output_naming.py`
4. 环境支持附件时发送文件，否则返回路径
5. 告诉用户如何使用：下载、独立重做、对照解析、复习后再告知完成

更多例子读 `examples.md`。

### 6. 更新复习进度

当用户说"复习完了""今天的错题复习完了""物理复习完了"时：

1. 自动推断今天/学科（必要时补问）
2. 优先批量更新
3. 运行 `update-review.py`
4. 返回更新数量、涉及学科、下次复习日期
5. **支持掌握度设置**：用户可指定 `--confidence low/medium/high`，影响下次复习间隔

`review-round: 0` 时，待复习到期日按 **`created + 1 天`** 计算；若历史文件里 `due-date` 与该日期不一致，可运行 `update-review.py --fix-first-due` 写回。

**掌握度乘数**：
- `low`：间隔 × 1.0（需要更频繁复习）
- `medium`：间隔 × 1.2（正常间隔）
- `high`：间隔 × 1.5（延长间隔）

详细参数和自然语言映射读：

- `docs/auto-review-update.md`
- `docs/review-update-guide.md`

### 7. 举一反三 / 分析 / 报告

当用户要生成变式题、薄弱点分析、分析报告、月报时，优先使用：

- `generate-practice.py`（默认 Markdown + 同名 PDF，Playwright；`--md-only` 可只出 md；**支持 `--difficulty` 难度筛选**）
- `weak-points.py`（**生成错误类型柱状图**）
- `analyze.py`（**生成学科分布饼图**）
- `monthly-report.py`（**生成复习热力图**）

**难度分级**（1-5 星）：
- 基础 (★☆☆☆☆ - ★★☆☆☆)：巩固基本概念
- 变式 (★★★☆☆)：中等难度，变式训练
- 提升 (★★★★☆ - ★★★★★)：挑战高分，综合应用

**图表类型**：
- 🥧 **饼图**：学科分布、知识点占比
- 📊 **柱状图**：错误类型对比、周趋势
- 🔥 **热力图**：复习密度、日历视图

**支持的知识点的（2026-04-12 更新，共 30 个）**：

| 学科 | 知识点 |
|------|--------|
| 物理 (10) | 力的合成、牛顿第一定律、欧姆定律、浮力、压强、杠杆、电功率、光的反射、电路分析、能量守恒 |
| 数学 (8) | 一元一次方程、二次函数、勾股定理、三角形全等、平行四边形、不等式、概率统计、三角函数 |
| 英语 (7) | 现在完成时、一般过去时、定语从句、被动语态、状语从句、名词性从句、虚拟语气 |
| 化学 (5) | 化学方程式、化学方程式配平、溶液浓度、酸碱中和、氧化还原反应 |

> 支持知识点别名（如"欧姆"= "欧姆定律"，"完成时"= "现在完成时"，"方程"= "一元一次方程"）。若知识点无模板，使用 LLM Fallback 机制生成通用练习题。

相关参考：

- `resources/similar-problems-template.md`
- `resources/error-types.md`

### 8. 定时提醒 / 飞书 / 微信

当用户要"每天 18:00 自动提醒""给飞书发今日复习提醒"时：

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

---

## 🆕 卡帕西 Wiki 模式（MVP）

> 2026-04-08 起新增：基于 Andrej Karpathy LLM Wiki 模式的知识库结构

### 目录结构

```
students/{学生}/
├── wiki/                    # 知识库（新增）
│   ├── concepts/           # 知识点页面（独立成页，带掌握度）
│   ├── reviews/            # 复习记录（按月存储，完整轨迹）
│   ├── questions/          # 题目索引（可选）
│   └── index.md            # 总索引（Dataview 查询入口）
├── mistakes/               # 原始错题（保留，向后兼容）
├── practice/               # 变式练习
├── reports/                # 分析报告
└── ...
```

### 向后兼容说明

| 功能 | 原实现 | 新实现 | 兼容性 |
|------|--------|--------|--------|
| 复习查询 | `review-state.json` + `mistakes/` | 同上 + `wiki/reviews/` | ✅ 完全兼容 |
| 月报生成 | 扫描 `mistakes/` | 扫描 `mistakes/` + `wiki/` | ✅ 完全兼容 |
| 更新复习 | `update-review.py` | 同上 + 写入 `wiki/reviews/` | ✅ 完全兼容 |
| 薄弱点分析 | 统计 `error-type` | 统计 `wiki/concepts/confidence` | ✅ 增强版 |

### 新增能力

1. **知识点图谱**：每个知识点独立成页，关联所有相关题目
2. **掌握度追踪**：`confidence` 字段（low/medium/high）
3. **复习轨迹**：完整历史记录（日期、结果、用时）
4. **Dataview 查询**：在 Obsidian 中任意查询
5. **自动 Lint**：定期扫描矛盾、孤儿页、缺失关联

### 迁移步骤（MVP）

1. ✅ 创建 `wiki/` 目录结构
2. ✅ 创建 `index.md` 总索引
3. ✅ 创建示例知识点页面
4. ⏳ 逐步将现有题目关联到知识点
5. ⏳ 配置 Obsidian Dataview 插件

### 维护命令

```bash
# 创建知识点页面（LLM 自动生成）
python3 scripts/create-concept.py --knowledge "程序运算与不等式组"

# 定期 Lint（扫描矛盾、孤儿页）
python3 scripts/lint-wiki.py --student 曲凌松

# 生成变式题并回填到 wiki
python3 scripts/generate-practice.py --student 曲凌松 --wiki-mode
```

## Self-Check

- 是否判断清楚这是错题本工作流，而不是普通讲题
- 是否补齐了关键元数据
- 是否遵守了"先文字列表，后按需发 PDF"
- 「今日待复习」回复是否未夹带「其他错题进度」等与查询范围不一致的内容
- 是否复用了已有脚本
- 是否在复习更新后给出统计和下次日期
