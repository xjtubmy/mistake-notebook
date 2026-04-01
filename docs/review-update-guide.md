# Review Update Guide

## Natural Language First

优先支持用户直接说：

```text
今天的错题复习完了
物理错题复习完了
数学复习完了，掌握得一般
```

默认不要求用户自己记命令。

## Batch Update

完成今日所有复习：

```bash
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --today \
  --mastered good
```

## Subject-Scoped Batch Update

```bash
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --today \
  --subject physics \
  --mastered good
```

## Single-Record Update

只在用户明确只完成了某一道题时再用单题更新：

```bash
python3 skills/mistake-notebook/scripts/update-review.py \
  --student 曲凌松 \
  --id 20260331-001 \
  --round 1 \
  --mastered good
```

## Parameter Notes

| 参数 | 用法 |
|------|------|
| `--today` | 更新今日到期的所有错题 |
| `--subject <学科>` | 按学科筛选 |
| `--mastered <poor/fair/good/excellent>` | 记录掌握情况 |
| `--id <错题 ID>` | 更新单题 |
| `--round <轮次>` | 配合单题更新使用 |

## Mastered Guidance

| 值 | 说明 |
|----|------|
| `poor` | 很差，需要更快回顾 |
| `fair` | 一般，需要正常继续复习 |
| `good` | 良好，默认值 |
| `excellent` | 优秀，可视情况减少重复 |

## Response Expectations

更新完成后，回复里应包含：

- 更新了几道题
- 涉及哪些学科
- 下次复习日期

## Anti-Patterns

- 让用户逐题手工更新本可批量处理的内容
- 用户只说“复习完了”却不尝试自动推断上下文
- 更新后不告诉用户下次复习日期
