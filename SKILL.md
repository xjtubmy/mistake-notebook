---
name: mistake-notebook
description: "中小学错题整理与管理工具。支持拍照录入、智能分类（学科/年级/教材版本/知识点）、错题分析、举一反三生成相似题、艾宾浩斯复习计划、PDF 导出、智能复习提醒。Use when: 录入错题、整理错题本、分析薄弱知识点、生成练习题、导出错题本、制定复习计划、设置复习提醒。Triggers: 错题、错题本、错题整理、错题录入、错题分析、错题导出、复习计划、相似题、举一反三、复习提醒、每日提醒。"
---

# Mistake Notebook - 中小学错题整理

> ⚠️ **首次使用请先检查依赖**：
> ```bash
> python3 skills/mistake-notebook/scripts/check-deps.py
> ```
> 
> 详细依赖说明见：[REQUIREMENTS.md](REQUIREMENTS.md)

**铁律**：每道错题必须标注完整元数据（学科、年级、教材版本、知识点、错误类型），否则无法进行后续分析和举一反三。

## 🚀 快速开始

### Step 1: 检查依赖

```bash
python3 skills/mistake-notebook/scripts/check-deps.py
```

### Step 2: 安装依赖（如未安装）

```bash
# 一键安装（推荐）
pip install playwright markdown2 --break-system-packages
playwright install chromium
```

### Step 3: 创建学生档案

```bash
# 复制模板
cp skills/mistake-notebook/assets/student-profile-template.md \
   data/mistake-notebook/students/曲凌松/profile.md

# 编辑档案，填写学生信息
```

### Step 4: 录入错题

```bash
# 使用 LLM 识别图片并录入
/mistake-notebook 录入 --student 曲凌松 --image photo.jpg
```

---

## 🗣️ 自然语言交互

### Step 1：查询待复习内容（文字列表）

**用户说**：
```
今天有什么要复习的？
今天有什么错题要复习？
今天的复习提醒
```

**奴才回复**（文字列表）：
```
📅 **今日复习提醒**

**学生**：曲凌松
**待复习**：4 道

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📚 数学**（1 道）
• 程序运算与不等式组（第 1 轮）🟡 今日

**📚 物理**（3 道）
• 牛顿第一定律（第 1 轮）🟡 今日
• 惯性与牛顿第一定律（第 1 轮）🟡 今日
• 力的合成（第 1 轮）🟡 今日

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **使用方式**：
• 说"发送物理的复习内容"→ 奴才发送 PDF
• 说"发送数学的复习内容"→ 奴才发送 PDF
• 说"发送所有复习内容"→ 奴才发送 PDF

⏰ 预计用时：10-15 分钟
```

**⚠️ 规则**：
- ✅ 先显示文字列表，让用户选择科目
- ✅ 不要直接发送 PDF（用户可能只需要某一科）

---

### Step 2：发送复习内容（PDF）

**用户说**：
```
发送物理的复习内容
发送数学的复习内容
发送所有复习内容
把今天的错题发给我
```

**奴才自动执行**：
```bash
# 按科目生成 PDF
python3 skills/mistake-notebook/scripts/export-printable.py \
  --student 曲凌松 \
  --subject physics \
  --output exports/physics-review.pdf \
  --format pdf

# 通过 message 工具发送 PDF 到当前对话（filePath 参数）
```

**奴才回复**：
```
📄 **物理复习内容**（PDF 已发送）

包含内容：
✅ 3 道物理错题的完整题目
✅ 学生作答与正确答案
✅ 核心考点
✅ 解题思路
✅ 易错点警示
✅ 记忆口诀
✅ 复习记录表

使用方式：
1. 下载 PDF 到手机/电脑
2. 盖住答案独立重做
3. 对照 PDF 核对答案和解析
4. 在复习记录表打勾签名
5. 复习完成后告诉奴才："物理复习完了"

奴才会自动更新复习进度！💪
```

**⚠️ 规则**：
- ✅ 按用户要求的科目生成 PDF
- ✅ PDF 包含完整解析
- ✅ 使用 `filePath` 参数发送（文件附件）
- ✅ 统一使用 PDF 格式，与举一反三练习保持一致

---

### Step 3：更新复习进度

**用户说**：
```
今天的错题复习完了
错题复习完了
复习完了
```

**奴才自动执行**：
```bash
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --today \
  --mastered good
```

**奴才回复**：
```
✅ 复习进度已更新！

今日完成复习：3 道
  • 数学：1 道（程序运算与不等式组）
  • 物理：2 道（牛顿第一定律 ×2）

下次复习日期：2026-04-03（3 天后）

继续保持，按时复习哦！💪
```

---

### 常用自然语言命令

| 用户说 | 奴才执行 |
|--------|---------|
| "今天有什么要复习的？" | 📋 显示文字列表 |
| "今天的复习提醒" | 📋 显示文字列表 |
| "发送物理的复习内容" | 📄 生成 PDF（物理） |
| "发送数学的复习内容" | 📄 生成 PDF（数学） |
| "发送所有复习内容" | 📄 生成 PDF（全部） |
| "今天的错题复习完了" | ✅ 更新今日所有错题 |
| "物理复习完了" | ✅ 更新今日物理错题 |
| "数学复习完了，掌握得不好" | ✅ 更新数学，标记为较差 |
| "力的合成那道题怎么样了" | 📊 显示该错题的复习进度 |

---

## 📅 艾宾浩斯复习计划

### 复习间隔

| 轮次 | 间隔 | 记忆保留率 | 复习重点 |
|------|------|-----------|---------|
| 录入 → 第 1 轮 | 1 天 | ~33% | 阻止快速遗忘 |
| 第 1 轮 → 第 2 轮 | 3 天 | ~25% | 巩固短期记忆 |
| 第 2 轮 → 第 3 轮 | 7 天 | ~20% | 形成长期记忆 |
| 第 3 轮 → 第 4 轮 | 15 天 | ~18% | 强化神经连接 |
| 第 4 轮 → 第 5 轮 | 30 天 | ~15% | 永久记忆 |

### 举一反三练习安排

| 轮次 | 复习内容 | 举一反三 | 说明 |
|------|---------|---------|------|
| **第 1 轮** | 重做原题 | ❌ 不安排 | 重点回忆原题思路 |
| **第 2 轮** | 重做原题 | ✅ 安排（变式题 2 道） | 初步巩固，需要变式练习 |
| **第 3 轮** | 重做原题 | ✅ 安排（提升题 3 道） | 长期记忆形成，强化训练 |
| **第 4 轮** | 重做原题 | ❌ 不安排 | 已基本掌握，无需额外练习 |
| **第 5 轮** | 重做原题 | ❌ 不安排 | 永久记忆，完成周期 |

### 生成举一反三练习

```bash
# 第 2 轮复习（变式为主）
python3 skills/mistake-notebook/scripts/generate-practice.py \
  --student 曲凌松 \
  --knowledge 力的合成 \
  --count 2 \
  --style 变式

# 第 3 轮复习（提升为主）
python3 skills/mistake-notebook/scripts/generate-practice.py \
  --student 曲凌松 \
  --knowledge 力的合成 \
  --count 3 \
  --style 混合
```

---

## 复习内容导出（PDF 格式）

**默认配置**：
- 格式：PDF
- 发送方式：文件附件（`filePath` 参数）
- 大小：~300KB

**适用场景**：
- ✅ 下载后查看
- ✅ 打印
- ✅ 飞书/微信发送
- ✅ 日常复习

**注意**：
- ❌ 不再使用长图（PNG）格式
- ✅ 统一使用 PDF 格式，与举一反三练习保持一致

---

## 文件格式规范（Obsidian MD）

### YAML Frontmatter 属性

**mistake.md 必需属性**：

```yaml
---
type: mistake-record
id: 20260331-001              # 错题 ID（时间戳 + 序号）
student: 曲凌松                 # 学生姓名
subject: physics               # 学科
stage: middle                  # 学段：elementary/middle/high
grade: grade-8                 # 年级
semester: semester-2           # 学期
unit: unit-02                  # 单元
unit-name: 二力平衡             # 单元名称
knowledge-point: 力的合成       # 知识点
error-type: 受力分析错误         # 错误类型
tags:                          # 标签（用于图谱关联）
  - 受力分析
  - 力的合成
status: 待复习                  # 状态：待复习/复习中/已掌握
difficulty: ⭐⭐⭐               # 难度：⭐~⭐⭐⭐⭐⭐
source: 《运动和力》课前测试卷    # 题目来源
created: 2026-03-31            # 创建日期
updated: 2026-03-31            # 最后更新
due-date: 2026-04-01           # 下次复习日期
review-round: 0                # 已复习轮次 (0-5)
mastered: false                # 是否已掌握
---
```

**README.md（单元索引）必需属性**：

```yaml
---
type: unit-index
subject: physics
stage: middle
grade: grade-8
semester: semester-2
unit: unit-02
unit-name: 二力平衡
student: 曲凌松
created: 2026-03-31
updated: 2026-03-31
---
```

### 双向链接规范

- 学生主页：`[[../../../../../profile|曲凌松]]`
- 单元索引：`[[../README|二力平衡单元]]`
- 错题记录：`[[20260331-001]]`
- 跨单元链接：`[[../unit-01/README|牛顿第一定律]]`

---

## 🛠️ 脚本工具说明

### analyze.py - 生成分析报告

```bash
python3 skills/mistake-notebook/scripts/analyze.py --student <学生名> [--subject <学科>] [--output <输出路径>]
```

**示例**：
```bash
# 生成全部学科的分析报告
python3 skills/mistake-notebook/scripts/analyze.py --student 曲凌松

# 仅生成数学学科的分析报告
python3 skills/mistake-notebook/scripts/analyze.py --student 曲凌松 --subject math
```

---

### export-printable.py - 可打印文档导出（PDF）

```bash
python3 skills/mistake-notebook/scripts/export-printable.py \
  --student <学生名> \
  [--subject <学科>] \
  --output <输出路径> \
  --format pdf
```

**示例**：
```bash
# 生成今日复习内容 PDF（所有科目）
python3 skills/mistake-notebook/scripts/export-printable.py \
  --student 曲凌松 \
  --output exports/today-review.pdf \
  --format pdf

# 生成物理复习内容 PDF
python3 skills/mistake-notebook/scripts/export-printable.py \
  --student 曲凌松 \
  --subject physics \
  --output exports/physics-review.pdf \
  --format pdf
```

**注意**：
- ✅ 统一使用 PDF 格式发送复习内容
- ✅ 使用 `filePath` 参数发送（文件附件）
- ❌ 不再使用 share.py 生成长图

---

### generate-practice.py - 举一反三练习生成

```bash
python3 skills/mistake-notebook/scripts/generate-practice.py \
  --student <学生名> \
  --knowledge <知识点> \
  --count <数量> \
  [--style <风格>] \
  [--output <输出路径>]
```

**示例**：
```bash
# 生成 5 道混合风格练习
python3 skills/mistake-notebook/scripts/generate-practice.py \
  --student 曲凌松 \
  --knowledge 力的合成 \
  --count 5

# 生成 3 道变式题
python3 skills/mistake-notebook/scripts/generate-practice.py \
  --student 曲凌松 \
  --knowledge 力的合成 \
  --count 3 \
  --style 变式
```

---

### monthly-report.py - 月度报告生成

```bash
python3 skills/mistake-notebook/scripts/monthly-report.py \
  --student <学生名> \
  --month <年月> \
  [--output <输出路径>]
```

**示例**：
```bash
# 生成 3 月份报告
python3 skills/mistake-notebook/scripts/monthly-report.py \
  --student 曲凌松 \
  --month 2026-03
```

---

### weak-points.py - 薄弱知识点分析

```bash
python3 skills/mistake-notebook/scripts/weak-points.py \
  --student <学生名> \
  [--top <数量>] \
  [--output <输出路径>]
```

**示例**：
```bash
# 分析 TOP5 薄弱知识点
python3 skills/mistake-notebook/scripts/weak-points.py \
  --student 曲凌松 \
  --top 5
```

---

### daily-review-reminder.py - 每日复习提醒（智能判断）

```bash
python3 skills/mistake-notebook/scripts/daily-review-reminder.py \
  --student <学生名> \
  [--channel <渠道>]
```

**示例**：
```bash
# 发送到飞书
python3 skills/mistake-notebook/scripts/daily-review-reminder.py \
  --student 曲凌松 \
  --channel feishu
```

**定时任务配置**（crontab -e）：
```bash
# 每天 18:00 自动发送复习提醒
0 18 * * * cd /home/ubuntu/clawd && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --channel feishu >> /tmp/review-reminder.log 2>&1
```

---

### update-review.py - 复习进度更新

```bash
python3 skills/mistake-notebook/scripts/update-review.py \
  --student <学生名> \
  --today \
  [--subject <学科>] \
  [--mastered good]
```

**示例**：
```bash
# 一键完成今日所有复习
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --today \
  --mastered good

# 完成今日物理复习
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --today \
  --subject physics \
  --mastered good
```

---

## 📁 完整目录结构

### Skill 目录（代码）

```
skills/mistake-notebook/
├── SKILL.md                          # Skill 说明
├── README.md                         # GitHub 说明
├── REQUIREMENTS.md                   # 依赖说明
├── CRON-SETUP.md                    # 定时任务配置
├── REVIEW-UPDATE-GUIDE.md           # 复习更新指南
├── AUTO-REVIEW-UPDATE.md            # 自动响应工作流
├── .gitignore                        # Git 忽略配置
├── LICENSE                           # MIT 许可证
├── requirements.txt                  # Python 依赖
└── scripts/
    ├── classify.py                   # 自动分类
    ├── analyze.py                    # 分析报告
    ├── review-reminder.py            # 复习提醒
    ├── search.py                     # 错题检索
    ├── export-printable.py           # 可打印文档
    ├── generate-practice.py          # 举一反三
    ├── monthly-report.py             # 月度报告
    ├── weak-points.py                # 薄弱点分析
    ├── parent-brief.py               # 家长简报
    ├── daily-review-reminder.py      # 每日提醒
    ├── update-review.py              # 进度更新
    └── check-deps.py                 # 依赖检查
```

### 数据目录（运行时创建）

```
data/mistake-notebook/
└── students/
    └── {student-name}/
        ├── profile.md                # 学生档案
        ├── mistakes/                 # 错题记录
        │   └── {subject}/
        │       └── {stage}/
        │           └── {grade}/
        │               └── {semester}/
        │                   ├── README.md  # 学期索引
        │                   ├── unit-01/   # 单元 1
        │                   └── custom/    # 自定义分类
        ├── reports/                    # 分析报告
        ├── search/                     # 检索结果
        ├── practice/                   # 举一反三练习
        ├── today-review.md             # 今日复习提醒
        └── exports/                    # 导出文件
```

**注意**：数据目录 `data/mistake-notebook/` 位于工作目录根下，与 Skill 目录分离。

---

## ⚠️ 反模式（禁止行为）

### 错题录入
- ❌ 不标注知识点就保存错题（无法后续分析）
- ❌ 不记录错误原因（无法针对性改进）
- ❌ 只录入不复习（错题本变成"错题坟墓"）
- ❌ 不区分教材版本（不同版本知识点顺序不同）

### 复习提醒
- ❌ 用户问"有什么要复习的"时直接发 PDF（应该先显示文字列表）
- ❌ 用户没说发送时就发 PDF（应该等用户明确要求）
- ❌ PDF 缺少核心考点或解析（无法有效复习）
- ❌ 不使用 `filePath` 参数发送（应该作为文件附件）
- ❌ 不告知用户使用方式（下载、盖住答案、对照解析）

### 复习更新
- ❌ 让用户手动运行命令（应该自动执行）
- ❌ 一道题一道题更新（应该批量更新）
- ❌ 不显示下次复习日期（用户不知道何时复习）

---

## ✅ 交付前检查清单

### 错题录入
- [ ] 学生档案已创建或更新
- [ ] 错题元数据完整（学科、年级、学期、单元/自定义分类、知识点、错误类型）
- [ ] LLM 识别的题目文本已用户确认
- [ ] 分类结果已用户确认
- [ ] 分析索引已更新
- [ ] 复习计划已生成（若适用）

### 复习提醒
- [ ] 先显示文字列表（待复习错题）
- [ ] 告知用户如何获取 PDF
- [ ] 用户要求后才发送 PDF
- [ ] PDF 包含完整解析（核心考点、解题思路、易错点、记忆口诀）
- [ ] PDF 包含复习记录表
- [ ] 使用 `filePath` 参数发送（文件附件）
- [ ] 告知用户使用方式（下载、盖住答案、对照解析、打勾签名）

### 复习更新
- [ ] 自动识别自然语言（"复习完了"、"错题复习完了"）
- [ ] 批量更新今日所有错题
- [ ] 自动计算下次复习日期（艾宾浩斯曲线）
- [ ] 显示复习统计和下次复习日期

---

## ⏰ 智能提醒功能

### 每日自动复习提醒

**功能说明**：每天固定时间（如 18:00）自动扫描今日到期的错题，发送复习提醒到飞书/微信。

**配置方式**：

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天 18:00）
0 18 * * * cd /home/ubuntu/clawd && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --channel feishu >> /tmp/review-reminder.log 2>&1
```

**手动测试**：

```bash
# 预览今日提醒（不发送）
python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --dry-run

# 手动发送
python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --channel feishu
```

**详细说明**：详见 [CRON-SETUP.md](CRON-SETUP.md)

---

**最后更新**：2026-03-31
