# Mistake Notebook Examples

## Common User Intents

| 用户说 | 应执行的动作 | 默认输出 |
|--------|--------------|----------|
| `今天有什么要复习的？` | 查询待复习列表 | 文字列表 |
| `今天的复习提醒` | 查询待复习列表 | 文字列表 |
| `发送物理的复习内容` | 导出物理复习 PDF | 文件或文件路径 |
| `发送所有复习内容` | 导出全部复习 PDF | 文件或文件路径 |
| `复习完了` | 更新今日复习进度 | 更新结果 |
| `物理复习完了` | 更新物理复习进度 | 更新结果 |
| `数学复习完了，掌握得一般` | 更新数学今日到期复习进度 | 更新结果 |
| `数学复习完了，这次掌握得很好` | 更新复习进度，设置 `confidence: high` | 更新结果 + 下次复习日期 |
| `看下 TOP5 薄弱知识点` | 运行薄弱点分析 | 分析结果 + **柱状图** |
| `生成 3 月月报` | 生成月度报告 | 报告 + **饼图** + **热力图** |
| `给我出 2 道变式题` | 生成举一反三练习 | 练习题 |
| `出几道简单的欧姆定律题目` | 生成举一反三练习，难度 1-2 | 练习题（基础） |
| `出几道提升题，挑战一下` | 生成举一反三练习，难度 4-5 | 练习题（提升） |

## Response Skeletons

### 1. 查询待复习内容

```text
📅 今日复习提醒

学生：<姓名>
待复习：<数量> 道

数学（1 道）
- <知识点>（第 1 轮）

物理（2 道）
- <知识点>（第 2 轮）

可继续：
- 发送数学的复习内容
- 发送物理的复习内容
- 发送所有复习内容
```

不要在本回复里另加「其他错题进度」「未到期题目」等块；范围应与脚本查询的「今日待复习」一致。

### 2. 发送复习内容

```text
已为你导出 <学科/全部> 复习 PDF。

建议这样用：
1. 先独立重做，不看答案
2. 再对照解析核对思路
3. 复习完成后直接告诉我"复习完了"或"物理复习完了"
```

### 3. 更新复习进度

```text
✅ 复习进度已更新！

今日完成复习：<总数> 道
<学科统计>

下次复习日期：<日期>
```

## Typical Commands

### 环境检查

```bash
python3 skills/mistake-notebook/scripts/check-deps.py
```

### 导出复习 PDF

默认文件名：**日期 + 学科**（中文日期，可不写 `--output`）：

```bash
python3 skills/mistake-notebook/scripts/export-printable.py \
  --student 曲凌松 \
  --subject physics \
  --format pdf
# 示例：exports/2026年4月1日-物理.pdf（随运行当日变化）
# 指定文件名中的日期：加 --date 2026-04-01
# 终端会打印 OUTPUT_PATH=<绝对路径>
```

自定义路径：

```bash
python3 skills/mistake-notebook/scripts/export-printable.py \
  --student 曲凌松 \
  --subject physics \
  --output exports/physics-review.pdf \
  --format pdf
```

### 批量更新今日复习

```bash
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --today
```

### 更新复习进度（带掌握度）

```bash
# 单题更新，设置掌握度为高
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --id 20260331-001 \
  --confidence high

# 批量更新今日复习，统一设置掌握度
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --today \
  --confidence medium

# 按学科更新，设置掌握度
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --today \
  --subject physics \
  --confidence low
```

**掌握度说明**：
- `low`：间隔 × 1.0（需要更频繁复习）
- `medium`：间隔 × 1.2（正常间隔）
- `high`：间隔 × 1.5（延长间隔）

### 校正第一轮 due-date（与 created+1 对齐）

```bash
python3 skills/mistake-notebook/scripts/update-review.py --student 曲凌松 --fix-first-due
```

### 按学科更新复习

```bash
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --today \
  --subject physics
```

### 生成薄弱点分析

```bash
python3 skills/mistake-notebook/scripts/weak-points.py --student 曲凌松
```

### 生成月度报告

```bash
python3 skills/mistake-notebook/scripts/monthly-report.py --student 曲凌松
```

### 生成举一反三练习（带难度筛选）

```bash
# 按难度范围筛选（1 最简单，5 最难）
python3 skills/mistake-notebook/scripts/generate-practice.py \
  --student 曲凌松 \
  --knowledge "欧姆定律" \
  --difficulty 1-3 \
  --count 5

# 按风格筛选（自动映射到难度）
python3 skills/mistake-notebook/scripts/generate-practice.py \
  --student 曲凌松 \
  --knowledge "二次函数" \
  --style 基础 \
  --count 3

python3 skills/mistake-notebook/scripts/generate-practice.py \
  --student 曲凌松 \
  --knowledge "二次函数" \
  --style 提升 \
  --count 3

# 只生成 Markdown，不生成 PDF
python3 skills/mistake-notebook/scripts/generate-practice.py \
  --student 曲凌松 \
  --knowledge "三角形全等" \
  --difficulty 2-4 \
  --md-only
```

**难度映射**：
| 风格 | 难度范围 | 说明 |
|------|---------|------|
| `基础` | 1-2 | 巩固基本概念 |
| `变式` | 3 | 中等难度，变式训练 |
| `提升` | 4-5 | 挑战高分，综合应用 |
| `混合` | 1-5 | 随机难度 |

## 图表生成示例

### 学科分布饼图

```bash
# 生成分析报告，包含学科分布饼图
python3 skills/mistake-notebook/scripts/analyze.py \
  --student 曲凌松 \
  --output reports/analysis.pdf

# 饼图展示各学科错题数量占比
```

### 错误类型柱状图

```bash
# 生成薄弱点分析，包含错误类型柱状图
python3 skills/mistake-notebook/scripts/weak-points.py \
  --student 曲凌松 \
  --output reports/weak-points.pdf

# 柱状图展示各类错误（概念不清、计算错误、审题失误等）的分布
```

### 复习热力图

```bash
# 生成月度报告，包含复习热力图
python3 skills/mistake-notebook/scripts/monthly-report.py \
  --student 曲凌松 \
  --month 2026-04 \
  --output reports/monthly-2026-04.pdf

# 热力图展示每日复习密度，颜色深浅表示复习题量
```

### 图表类型说明

| 图表 | 用途 | 生成脚本 |
|------|------|---------|
| 🥧 饼图 | 学科分布、知识点占比 | `analyze.py` |
| 📊 柱状图 | 错误类型对比、周趋势 | `weak-points.py` |
| 🔥 热力图 | 复习密度、日历视图 | `monthly-report.py` |

---

## Phrasing Examples

- 用户只问"今天有什么要复习的"时：先列文字，不直接导出文件
- 用户明确说"发送物理的复习内容"时：导出 PDF，并给使用说明
- 用户说"复习完了"时：自动批量更新，不要求逐题确认
- 用户要求"生成 2 道变式题"时：按知识点和错误类型生成分层练习
- 用户说"这次掌握得很好"时：更新复习进度并设置 `confidence: high`
- 用户说"出几道简单的题"时：生成难度 1-2 的变式题
- 用户说"想要图表看看"时：生成分析报告或月度报告（包含饼图/柱状图/热力图）
