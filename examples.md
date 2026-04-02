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
| `看下 TOP5 薄弱知识点` | 运行薄弱点分析 | 分析结果 |
| `生成 3 月月报` | 生成月度报告 | 报告 |
| `给我出 2 道变式题` | 生成举一反三练习 | 练习题 |

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
3. 复习完成后直接告诉我“复习完了”或“物理复习完了”
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

稳定路径（推荐接飞书：每次覆盖同一文件，可不写 `--output`）：

```bash
python3 skills/mistake-notebook/scripts/export-printable.py \
  --student 曲凌松 \
  --subject physics \
  --format pdf
# 默认输出：data/mistake-notebook/students/曲凌松/exports/latest-physics.pdf
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

## Phrasing Examples

- 用户只问“今天有什么要复习的”时：先列文字，不直接导出文件
- 用户明确说“发送物理的复习内容”时：导出 PDF，并给使用说明
- 用户说“复习完了”时：自动批量更新，不要求逐题确认
- 用户要求“生成 2 道变式题”时：按知识点和错误类型生成分层练习
