---
name: mistake-notebook
description: "中小学错题整理与管理工具。支持拍照录入、智能分类（学科/年级/教材版本/知识点）、错题分析、举一反三生成相似题、艾宾浩斯复习计划、PDF 导出、智能复习提醒。Use when: 录入错题、整理错题本、分析薄弱知识点、生成练习题、导出错题本、制定复习计划、设置复习提醒、更新复习进度。Triggers: 错题、错题本、错题整理、错题录入、错题分析、错题导出、复习计划、相似题、举一反三、复习提醒、每日提醒、复习完了、今天复习完了。"
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
pip install playwright markdown2 pdfkit --break-system-packages
playwright install chromium

# 如需 PDF 导出（可选）
sudo apt-get install wkhtmltopdf  # Ubuntu/Debian
# 或
brew install wkhtmltopdf  # macOS
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

## 核心功能

| 功能 | 说明 | 脚本 |
|------|------|------|
| 📸 拍照录入 | 上传题目图片，LLM 直接识别题目内容，自动/手动分类 | - |
| 🏷️ 智能分类 | 学科 → 年级 → 学期 → 单元/自定义分类 | `classify.py` |
| 📊 错题分析 | 统计薄弱知识点、错误类型分布、趋势分析 | `analyze.py` |
| 📅 复习提醒 | 艾宾浩斯遗忘曲线，生成今日/本周复习计划 | `review-reminder.py` |
| 🔍 标签检索 | 按标签/知识点/错误类型/状态多维度筛选 | `search.py` |
| 📝 举一反三 | 基于错题生成相似练习题 | - |
| 📤 导出打印 | 导出 PDF/Markdown/HTML，支持按条件筛选 | `export-pdf.py` |

## 参数系统

```bash
/mistake-notebook <command> [arguments]
```

| 参数 | 说明 | 示例 |
|------|------|------|
| `--student <name>` | 学生姓名（必需） | `--student 张三` |
| `--subject <subject>` | 学科：math/chinese/english/physics/chemistry/biology/history/geography/politics | `--subject math` |
| `--grade <grade>` | 年级：elementary-1~6, middle-7~9, high-10~12 | `--grade middle-8` |
| `--semester <sem>` | 学期：1（上）/ 2（下） | `--semester 1` |
| `--unit <unit>` | 单元：unit-01 ~ unit-12 或自定义 | `--unit unit-03` |
| `--custom <name>` | 自定义分类名（可选） | `--custom 阅读专项` |
| `--knowledge-point <kp>` | 知识点名称 | `--knowledge-point 一次方程` |
| `--error-type <type>` | 错误类型：概念不清/计算错误/审题错误/公式错误/逻辑错误/书写错误 | `--error-type 计算错误` |
| `--image <path>` | 题目图片路径 | `--image photo.jpg` |
| `--format <format>` | 导出格式：pdf/markdown/html | `--format pdf` |
| `--count <n>` | 生成相似题数量 | `--count 5` |

**注意**：教材版本从学生档案 (`profile.md`) 中自动读取，无需手动指定。

## 工作流

```
录入 -> 分类 -> 分析 -> 复习 -> 导出
  |        |        |        |        |
  v        v        v        v        v
LLM 识别  自动分类  薄弱点  艾宾浩斯  PDF/Markdown
```

### Step 1: 录入错题 ⚠️ REQUIRED

**命令**：`/mistake-notebook 录入 --student <name> --image <path> [其他参数]`

1. **检查学生档案**：
   ```bash
   test -f "mistake-notebook/students/{student}/profile.md"
   ```
   - 若不存在，创建档案模板，提示用户补充信息（年级、学校、教材版本）
   - 若存在，读取档案，自动填充年级和教材版本

2. **LLM 识别题目**：
   - 直接调用多模态 LLM 识别图片中的题目内容
   - 提取题目文本、已知条件、问题、（若有）学生作答
   - 保存为 `mistake.md`

3. **分类标注**（确认门）：
   - 自动识别学科、年级、知识点（基于 OCR 文本）
   - **必须用户确认**分类结果，通过 AskUserQuestion：
     ```
     header: "错题分类确认"
     question: "请确认以下分类是否正确？"
     fields:
       - label: "学科"
         value: "数学"
       - label: "年级"
         value: "初二"
       - label: "教材版本"
         value: "人教版"
       - label: "知识点"
         value: "一次方程"
       - label: "错误类型"
         value: "计算错误"
     -> 提供"确认"和"修改"选项
     ```

4. **保存错题**：
   ```
   mistake-notebook/
   └── students/
       └── {student}/
           └── mistakes/
               └── {subject}/
                   └── {stage}/              # elementary/middle/high
                       └── {grade}/          # grade-7, grade-8, ...
                           └── {semester}/   # semester-1（上）/ semester-2（下）
                               ├── unit-01/  # 第一单元
                               │   ├── README.md          # ⚠️ 单元索引（必需）
                               │   └── {timestamp}_{id}/
                               │       ├── image.jpg          # 原图
                               │       ├── mistake.md         # 错题记录（Obsidian MD）
                               │       └── analysis.md        # 快速复习卡片
                               ├── unit-02/
                               │   └── README.md
                               └── custom/   # 自定义分类
                                   ├── 阅读专项/
                                   │   └── README.md
                                   └── 语法专项/
                                       └── README.md
   ```

**教材版本**：从 `students/{student}/profile.md` 中读取，不体现在目录结构中。

**文件格式**：采用 Obsidian MD 格式，包含 YAML Frontmatter 和双向链接 `[[链接]]`。

5. **更新分析索引**：
   - 追加到 `students/{student}/analysis.md` 的错题列表
   - 更新知识点统计（该知识点错题数 +1）

### Step 2: 错题分析

**命令**：`/mistake-notebook 分析 --student <name> [--subject <subject>] [--period <period>]`

1. **读取学生档案和错题数据**

2. **生成分析报告** -> `students/{student}/reports/analysis-{timestamp}.md`：
   - **整体统计**：错题总数、按学科分布、按错误类型分布
   - **学科分析**（若指定 `--subject`）：
     - 知识点掌握情况（错题数排序，找出薄弱点）
     - 错误类型分布（概念不清？计算错误？）
     - 时间趋势（近 4 周错题数量变化）
   - **教材版本对照**：同一知识点在不同教材版本的覆盖情况

3. **可视化输出** -> `students/{student}/reports/analysis-{timestamp}.html`：
   - 知识点热力图（红色=薄弱，绿色=掌握）
   - 错误类型饼图
   - 时间趋势折线图

4. **生成改进建议**：
   - 针对薄弱知识点，推荐专项练习
   - 针对错误类型，给出针对性建议（如"计算错误多→建议每天 5 分钟口算练习"）

### Step 3: 生成相似题（举一反三） ⚠️ BLOCKING

**命令**：`/mistake-notebook 练习 --student <name> --knowledge-point <kp> --count <n>`

**确认门**：生成相似题前必须确认：
```
Use AskUserQuestion:
header: "生成相似题"
question: "将基于以下错题生成 {count} 道相似练习题，是否继续？"
fields:
  - label: "原题知识点"
    value: "{knowledge-point}"
  - label: "原题错误类型"
    value: "{error-type}"
  - label: "题目数量"
    value: "{count}"
-> 提供"生成"和"取消"选项
```

1. **加载相似题模板**：
   ```bash
   read references/similar-problems/{subject}/{knowledge-point}.md
   ```
   - 若无针对该知识点的模板，使用通用模板

2. **生成相似题**：
   - 保持考点不变，修改题目数据/场景
   - 难度梯度：1-2 道基础题，2-3 道变式题，1 道拓展题
   - 每道题附带答案和解析

3. **保存练习** -> `students/{student}/practice/{timestamp}_{knowledge-point}.md`

4. **可选**：生成 PDF 版本方便打印

### Step 4: 制定复习计划（艾宾浩斯）

**命令**：`/mistake-notebook 复习计划 --student <name> [--week <week>]`

1. **读取所有错题的最后复习时间**

2. **根据艾宾浩斯遗忘曲线计算复习时间**：
   | 复习轮次 | 间隔时间 |
   |---------|---------|
   | 第 1 轮 | 1 天后 |
   | 第 2 轮 | 3 天后 |
   | 第 3 轮 | 7 天后 |
   | 第 4 轮 | 15 天后 |
   | 第 5 轮 | 30 天后 |

3. **生成复习计划** -> `students/{student}/review-schedule.md`：
   ```markdown
   ## 今日需复习（{date}）
   | 学科 | 知识点 | 错题 ID | 复习轮次 | 上次复习 |
   |------|--------|--------|---------|---------|
   | 数学 | 一次方程 | 20260331-001 | 第 2 轮 | 3 天前 |
   | 英语 | 定语从句 | 20260328-003 | 第 1 轮 | 1 天前 |

   ## 本周复习计划
   | 日期 | 学科 | 知识点 | 题目数 |
   |------|------|--------|--------|
   | 3/31 | 数学 | 一次方程 | 3 |
   | 4/1  | 英语 | 定语从句 | 5 |
   | ...  | ...  | ...    | ... |
   ```

4. **提醒功能**（可选）：
   - 生成日历文件（.ics），可导入手机日历
   - 或通过系统通知提醒

### Step 5: 导出错题本

**命令**：`/mistake-notebook 导出 --student <name> --format <format> [筛选条件]`

**筛选条件**：
- `--subject <subject>`：按学科
- `--grade <grade>`：按年级
- `--knowledge-point <kp>`：按知识点
- `--error-type <type>`：按错误类型
- `--period <period>`：按时间范围（如 `2026-03`）

1. **根据筛选条件收集错题**

2. **生成导出文件**：
   - **PDF**：排版美观，适合打印
   - **Markdown**：便于编辑和分享
   - **HTML**：可在浏览器查看，支持交互

3. **保存位置** -> `students/{student}/exports/{timestamp}_{type}.{format}`

## 目录结构

### Skill 目录（代码）

```
skills/mistake-notebook/
├── SKILL.md
├── students/
│   └── {student-name}/
│       ├── profile.md              # 学生档案（含教材版本）
│       ├── mistakes/               # 错题原图 + 文本
│       │   ├── math/
│       │   │   └── middle/
│       │   │       └── grade-8/
│       │   │           ├── semester-1/        # 八上
│       │   │           │   ├── unit-01/       # 第一单元
│       │   │           │   ├── unit-02/       # 第二单元
│       │   │           │   └── custom/        # 自定义分类
│       │   │           └── semester-2/        # 八下
│       │   ├── english/
│       │   └── ...
│       ├── analysis.md             # 综合分析索引
│       ├── practice/               # 生成的练习题
│       ├── reports/                # 分析报告
│       ├── review-schedule.md      # 复习计划
│       └── exports/                # 导出的文件
├── references/
│   ├── curriculum/                 # 课程标准 + 教材版本（参考用）
│   │   ├── math/
│   │   ├── english/
│   │   └── ...
│   ├── error-types.md              # 错误类型定义
│   └── similar-problems/           # 相似题模板
└── scripts/
    ├── classify.py                 # 自动分类
    └── export-pdf.py               # 导出 PDF
```

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

## 学生档案模板

```markdown
# 学生档案：{name}

## 基本信息
- 学校：XX 中学
- 年级：初二
- 创建时间：2026-03-31

## 教材版本
| 学科 | 版本 |
|------|------|
| 数学 | 人教版 |
| 英语 | 外研版 |
| 物理 | 苏教版 |

## 学期单元映射（可选，用于自动分类）
| 学科 | 学期 | 单元范围 | 自定义分类 |
|------|------|---------|-----------|
| 数学 | 八上 | unit-01:三角形, unit-02:全等三角形 | 几何证明专项 |
| 英语 | 八上 | unit-01:Module1-2, unit-02:Module3-4 | 阅读专项，语法专项 |

## 学习特点
- 薄弱学科：数学
- 薄弱知识点：一次方程、三角形
- 常见错误类型：计算错误、审题错误

## 统计
- 错题总数：0
- 本周新增：0
- 已掌握：0
```

## 错误类型定义

| 错误类型 | 说明 | 应对策略 |
|---------|------|---------|
| 概念不清 | 对基本概念理解错误 | 回归课本，重新学习概念定义 + 例题 |
| 计算错误 | 计算过程出错 | 每天 5 分钟口算练习，养成验算习惯 |
| 审题错误 | 没看懂题目要求 | 圈画关键词，读完题后复述题意 |
| 公式错误 | 公式记错或用错 | 制作公式卡片，理解公式推导过程 |
| 逻辑错误 | 推理过程有漏洞 | 学习逻辑连接词，练习证明题 |
| 书写错误 | 步骤不规范导致扣分 | 对照标准答案，规范答题格式 |

## 反模式（禁止行为）

- ❌ 不标注知识点就保存错题（无法后续分析）
- ❌ 不记录错误原因（无法针对性改进）
- ❌ 只录入不复习（错题本变成"错题坟墓"）
- ❌ 不区分教材版本（不同版本知识点顺序不同）

## 交付前检查清单

- [ ] 学生档案已创建或更新
- [ ] 错题元数据完整（学科、年级、学期、单元/自定义分类、知识点、错误类型）
- [ ] LLM 识别的题目文本已用户确认
- [ ] 分类结果已用户确认
- [ ] 分析索引已更新
- [ ] 复习计划已生成（若适用）

## 使用示例

```bash
# 录入错题（自动从 profile 读取教材版本）
/mistake-notebook 录入 --student 张三 --image math_problem.jpg
/mistake-notebook 录入 --student 张三 --subject math --grade middle-8 --semester 1 --unit unit-01 --image photo.jpg

# 录入到自定义分类
/mistake-notebook 录入 --student 张三 --subject english --grade middle-8 --semester 1 --custom 阅读专项 --image reading.jpg

# 查看分析
/mistake-notebook 分析 --student 张三
/mistake-notebook 分析 --student 张三 --subject math
/mistake-notebook 分析 --student 张三 --subject math --semester 1

# 按单元导出
/mistake-notebook 导出 --student 张三 --subject math --grade middle-8 --semester 1 --unit unit-01 --format pdf

# 生成相似题练习
/mistake-notebook 练习 --student 张三 --knowledge-point 一次方程 --count 5

# 查看复习计划
/mistake-notebook 复习计划 --student 张三

# 导出错题本
/mistake-notebook 导出 --student 张三 --format pdf --subject math --period 2026-03
```

---

## 🛠️ 脚本工具说明

### analyze.py - 生成分析报告

```bash
python3 scripts/analyze.py --student <学生名> [--subject <学科>] [--output <输出路径>]
```

**示例**：
```bash
# 生成全部学科的分析报告
python3 skills/mistake-notebook/scripts/analyze.py --student 曲凌松

# 仅生成数学学科的分析报告
python3 skills/mistake-notebook/scripts/analyze.py --student 曲凌松 --subject math

# 指定输出路径
python3 skills/mistake-notebook/scripts/analyze.py --student 曲凌松 --output data/mistake-notebook/students/曲凌松/reports/math-analysis.md
```

**输出内容**：
- 总体统计（错题总数、状态分布）
- 按学科分布
- 错误类型分布
- 知识点 TOP10
- 今日待复习列表
- 难度分布
- 按单元分布

---

### review-reminder.py - 生成复习提醒

```bash
python3 scripts/review-reminder.py --student <学生名> [--today <日期>] [--weekly] [--output <输出路径>]
```

**示例**：
```bash
# 生成今日复习提醒
python3 skills/mistake-notebook/scripts/review-reminder.py --student 曲凌松

# 生成指定日期的复习提醒
python3 skills/mistake-notebook/scripts/review-reminder.py --student 曲凌松 --today 2026-04-01

# 生成本周复习计划
python3 skills/mistake-notebook/scripts/review-reminder.py --student 曲凌松 --weekly
```

**输出内容**：
- 今日待复习列表（按学科分组）
- 紧急程度（超期/今日/提前）
- 复习方法建议
- 复习记录模板

---

### search.py - 错题检索

```bash
python3 scripts/search.py --student <学生名> [筛选条件] [--output <输出路径>]
```

**筛选条件**：
| 参数 | 说明 | 示例 |
|------|------|------|
| `--tag <标签>` | 按标签筛选 | `--tag 受力分析` |
| `--knowledge <知识点>` | 按知识点筛选 | `--knowledge 一次方程` |
| `--error-type <类型>` | 按错误类型筛选 | `--error-type 计算错误` |
| `--subject <学科>` | 按学科筛选 | `--subject math` |
| `--status <状态>` | 按状态筛选 | `--status 待复习` |
| `--unit <单元>` | 按单元筛选 | `--unit unit-02` |
| `--unread` | 仅显示未掌握的 | `--unread` |
| `--list-tags` | 列出所有标签 | `--list-tags` |
| `--list-kp` | 列出所有知识点 | `--list-kp` |

**示例**：
```bash
# 列出所有标签
python3 skills/mistake-notebook/scripts/search.py --student 曲凌松 --list-tags

# 列出所有知识点
python3 skills/mistake-notebook/scripts/search.py --student 曲凌松 --list-kp

# 按标签筛选
python3 skills/mistake-notebook/scripts/search.py --student 曲凌松 --tag 受力分析

# 按知识点筛选
python3 skills/mistake-notebook/scripts/search.py --student 曲凌松 --knowledge 力的合成

# 组合筛选
python3 skills/mistake-notebook/scripts/search.py --student 曲凌松 --subject physics --status 待复习

# 仅显示未掌握的
python3 skills/mistake-notebook/scripts/search.py --student 曲凌松 --unread
```

---

### export-printable.py - 可打印文档导出（推荐）

```bash
python3 skills/mistake-notebook/scripts/export-printable.py --student <学生名> --output <输出路径> [--format <格式>] [筛选条件]
```

**参数**：
| 参数 | 说明 |
|------|------|
| `--student` | 学生姓名（必需） |
| `--output` | 输出文件路径（必需） |
| `--subject` | 按学科筛选 |
| `--format` | 输出格式：md/pdf（默认 md） |

**示例**：
```bash
# 导出 PDF（打印用）
python3 skills/mistake-notebook/scripts/export-printable.py \
  --student 曲凌松 --subject physics \
  --output exports/physics.pdf --format pdf

# 导出 Markdown
python3 skills/mistake-notebook/scripts/export-printable.py \
  --student 曲凌松 --subject physics \
  --output exports/physics.md
```

---

### generate-image.py - 长图生成（分享用）

```bash
python3 skills/mistake-notebook/scripts/generate-image.py --student <学生名> --output <输出路径> [筛选条件]
```

**依赖**：
```bash
pip install playwright
playwright install  # 安装浏览器
```

**示例**：
```bash
# 生成长图（飞书/微信分享）
python3 skills/mistake-notebook/scripts/generate-image.py \
  --student 曲凌松 --subject physics \
  --output exports/physics-share.png
```

---

### share.py - 智能分享（统一长图）

```bash
python3 skills/mistake-notebook/scripts/share.py --student <学生名> --output <输出路径> [筛选条件]
```

**说明**：统一生成长图，适用于所有分享场景（飞书/微信等）

**示例**：
```bash
# 生成长图
python3 skills/mistake-notebook/scripts/share.py \
  --student 曲凌松 --subject physics \
  --output exports/physics-share.png
```

---

### export-pdf.py - 旧版导出脚本（保留兼容）

> ⚠️ 已废弃，请使用 `export-printable.py`

---

## 📁 完整目录结构

```
mistake-notebook/
├── SKILL.md                          #  skill 说明文档
├── scripts/
│   ├── classify.py                   # 自动分类脚本
│   ├── analyze.py                    # 分析报告生成
│   ├── review-reminder.py            # 复习提醒生成
│   ├── search.py                     # 错题检索
│   └── export-pdf.py                 # 导出 PDF/Markdown
├── references/
│   ├── error-types.md                # 错误类型定义
│   ├── curriculum/                   # 教材版本知识点体系
│   └── similar-problems/
│       └── template.md               # 相似题生成模板
└── assets/
    └── student-profile-template.md   # 学生档案模板

### 数据目录（运行时创建）

```
data/mistake-notebook/
└── students/
    └── {student-name}/
    ├── profile.md                    # 学生档案
    ├── mistakes/                     # 错题记录
    │   └── {subject}/
    │       └── {stage}/
    │           └── {grade}/
    │               └── {semester}/
    │                   ├── README.md # 学期索引
    │                   ├── unit-01/  # 单元 1
    │                   │   ├── README.md          # 单元索引
    │                   │   └── {id}/
    │                   │       ├── mistake.md     # 错题记录
    │                   │       └── analysis.md    # 快速复习卡
    │                   └── custom/   # 自定义分类
    ├── reports/                      # 分析报告
    ├── search/                       # 检索结果
    ├── today-review.md               # 今日复习提醒
    └── exports/                      # 导出文件
```

**注意**：数据目录 `data/mistake-notebook/` 位于工作目录根下，与 Skill 目录分离。

---

## 🗣️ 自然语言交互

### 复习进度更新

**用户说**：
```
今天的错题复习完了
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
| "今天的错题复习完了" | 更新今日所有错题为第 1 轮，掌握情况：良好 |
| "物理错题复习完了" | 更新今日物理错题 |
| "数学错题复习完了，掌握得不好" | 更新今日数学错题，掌握情况：较差 |
| "今天有什么要复习的？" | 显示今日待复习错题列表 |
| "力的合成那道题怎么样了" | 显示该错题的复习进度 |
| "生成 3 月份错题报告" | 生成月度分析报告 |

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

# 预览指定日期
python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --date 2026-04-01 --dry-run

# 手动发送
python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --channel feishu
```

**消息示例**：

```
📅 **复习提醒**

**学生**：曲凌松  
**日期**：2026-04-01  
**待复习**：4 道

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📚 数学**（1 道）
• 程序运算与不等式组（第 1 轮）🟡 今日

**📚 物理**（3 道）
• 牛顿第一定律（外力消失时的运动状态）（第 1 轮）🟡 今日
• 牛顿第一定律与惯性概念（第 1 轮）🟡 今日
• 力的合成（第 1 轮）🟡 今日

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **复习建议**
1️⃣ 盖住答案，先独立重做
2️⃣ 对照解析，理解思路
3️⃣ 记录进度，打勾签名
4️⃣ 举一反三，完成练习

⏰ 预计用时：10-15 分钟

加油！坚持就是胜利！💪
```

**详细说明**：详见 [CRON-SETUP.md](CRON-SETUP.md)

---

**最后更新**：2026-03-31
