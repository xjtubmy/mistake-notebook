# mistake-notebook Skill 开发规范

## 📝 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0.0 | 2026-03-31 | 初始版本发布 |
| v1.0.1 | 2026-03-31 | 修正复习提醒交互流程 |

---

## 🗣️ 完整交互流程

### 场景 1：用户查询待复习内容

**用户**：今天有什么要复习的？

**奴才处理流程**：
```
1. 调用 daily-review-reminder.py --dry-run 获取待复习列表
2. 按学科分组统计
3. 返回文字列表（不要发长图）
```

**奴才回复**：
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
• 说"发送物理的复习内容"→ 奴才发送物理错图的长图
• 说"发送数学的复习内容"→ 奴才发送数学错图的长图
• 说"发送所有复习内容"→ 奴才发送全部错图的长图

⏰ 预计用时：10-15 分钟
```

**⚠️ 注意事项**：
- ❌ 不要直接发送长图
- ✅ 先显示文字列表，让用户选择科目
- ✅ 告知用户如何获取长图

---

### 场景 2：用户要求发送复习内容

**用户**：发送物理的复习内容

**奴才处理流程**：
```
1. 调用 share.py --subject physics 生成长图
2. 通过 message 工具发送长图到当前对话
3. 回复使用说明
```

**奴才回复**：
```
📱 **物理复习内容**（长图已发送）

包含内容：
✅ 3 道物理错题的完整题目
✅ 学生作答与正确答案
✅ 核心考点
✅ 解题思路
✅ 易错点警示
✅ 记忆口诀

使用方式：
1. 打开长图，盖住答案独立重做
2. 对照长图核对答案和解析
3. 在复习记录表打勾签名
4. 复习完成后告诉奴才："物理复习完了"

奴才会自动更新复习进度！💪
```

**⚠️ 注意事项**：
- ✅ 长图包含完整解析
- ✅ 告知用户使用方式
- ✅ 提醒用户复习完成后告诉奴才

---

### 场景 3：用户完成复习

**用户**：物理复习完了

**奴才处理流程**：
```
1. 调用 update-review.py --subject physics --today 更新进度
2. 计算下次复习日期
3. 回复更新结果
```

**奴才回复**：
```
✅ 复习进度已更新！

**今日完成复习**：3 道（物理）
  • 牛顿第一定律（第 1 轮→第 2 轮）
  • 惯性与牛顿第一定律（第 1 轮→第 2 轮）
  • 力的合成（第 1 轮→第 2 轮）

**下次复习日期**：2026-04-04（3 天后）

继续保持，按时复习哦！💪
```

---

## 📋 常用自然语言命令

| 用户说 | 奴才执行 | 输出 |
|--------|---------|------|
| "今天有什么要复习的？" | 查询待复习列表 | 📋 文字列表 |
| "今天的复习提醒" | 查询待复习列表 | 📋 文字列表 |
| "发送物理的复习内容" | 生成物理长图 | 📱 长图 |
| "发送数学的复习内容" | 生成数学长图 | 📱 长图 |
| "发送所有复习内容" | 生成全部长图 | 📱 长图 |
| "物理复习完了" | 更新物理进度 | ✅ 更新结果 |
| "今天的错题复习完了" | 更新全部进度 | ✅ 更新结果 |
| "数学复习完了，掌握得不好" | 更新数学，标记较差 | ✅ 更新结果 |
| "力的合成那道题怎么样了" | 查询单题状态 | 📊 进度详情 |
| "生成 3 月份错题报告" | 生成月度报告 | 📊 报告 |

---

## 🎯 核心功能

| 功能 | 说明 | 脚本 |
|------|------|------|
| 📸 拍照录入 | 上传题目图片，LLM 直接识别题目内容，自动/手动分类 | - |
| 🏷️ 智能分类 | 学科 → 年级 → 学期 → 单元/自定义分类 | `classify.py` |
| 📊 错题分析 | 统计薄弱知识点、错误类型分布、趋势分析 | `analyze.py` |
| 📅 复习提醒 | 艾宾浩斯遗忘曲线，生成今日/本周复习计划 | `review-reminder.py` |
| 🔍 标签检索 | 按标签/知识点/错误类型/状态多维度筛选 | `search.py` |
| 📝 举一反三 | 基于错题生成相似练习题 | `generate-practice.py` |
| 📤 导出打印 | 导出 PDF/Markdown/HTML，支持按条件筛选 | `export-printable.py` |
| 📱 长图分享 | 生成手机分享长图（含完整解析） | `share.py` |
| 📊 月度报告 | 生成月度错题总结报告 | `monthly-report.py` |
| 🎯 薄弱点分析 | 找出最薄弱的知识点 TOP5 | `weak-points.py` |
| 📝 家长简报 | 生成简洁的家长汇报 | `parent-brief.py` |
| ⏰ 智能提醒 | 每天 18:00 自动发送复习提醒 | `daily-review-reminder.py` |
| ✅ 进度更新 | 批量更新复习进度 | `update-review.py` |

---

## 📁 目录结构

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
    ├── generate-image.py             # 长图生成
    ├── share.py                      # 分享长图
    ├── generate-practice.py          # 举一反三
    ├── export-practice-pdf.py        # 练习 PDF
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

## 🛠️ 脚本工具说明

### analyze.py - 生成分析报告

```bash
python3 skills/mistake-notebook/scripts/analyze.py \
  --student <学生名> \
  [--subject <学科>] \
  [--output <输出路径>]
```

**示例**：
```bash
# 生成全部学科的分析报告
python3 skills/mistake-notebook/scripts/analyze.py --student 曲凌松

# 仅生成数学学科的分析报告
python3 skills/mistake-notebook/scripts/analyze.py --student 曲凌松 --subject math
```

---

### review-reminder.py - 生成复习提醒

```bash
python3 skills/mistake-notebook/scripts/review-reminder.py \
  --student <学生名> \
  [--today <日期>] \
  [--weekly] \
  [--output <输出路径>]
```

**示例**：
```bash
# 生成今日复习提醒
python3 skills/mistake-notebook/scripts/review-reminder.py --student 曲凌松

# 生成本周复习计划
python3 skills/mistake-notebook/scripts/review-reminder.py --student 曲凌松 --weekly
```

---

### share.py - 生成分享长图

```bash
python3 skills/mistake-notebook/scripts/share.py \
  --student <学生名> \
  [--subject <学科>] \
  [--output <输出路径>]
```

**示例**：
```bash
# 生成今日复习长图（所有科目）
python3 skills/mistake-notebook/scripts/share.py \
  --student 曲凌松 \
  --output exports/today-review-share.png

# 生成物理复习长图
python3 skills/mistake-notebook/scripts/share.py \
  --student 曲凌松 \
  --subject physics \
  --output exports/physics-review-share.png
```

---

### update-review.py - 更新复习进度

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

## ⚠️ 反模式（禁止行为）

### 错题录入
- ❌ 不标注知识点就保存错题（无法后续分析）
- ❌ 不记录错误原因（无法针对性改进）
- ❌ 只录入不复习（错题本变成"错题坟墓"）
- ❌ 不区分教材版本（不同版本知识点顺序不同）

### 复习提醒
- ❌ 用户问"有什么要复习的"时直接发长图（应该先显示文字列表）
- ❌ 用户没说发送时就发长图（应该等用户明确要求）
- ❌ 长图缺少核心考点或解析（无法有效复习）
- ❌ 不告知用户使用方式（盖住答案、对照解析）

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
- [ ] 告知用户如何获取长图
- [ ] 用户要求后才发送长图
- [ ] 长图包含完整解析（核心考点、解题思路、易错点、记忆口诀）
- [ ] 长图适合手机预览（宽度 800px）
- [ ] 告知用户使用方式（盖住答案、对照解析、打勾签名）

### 复习更新
- [ ] 自动识别自然语言（"复习完了"、"错题复习完了"）
- [ ] 批量更新今日所有错题
- [ ] 自动计算下次复习日期（艾宾浩斯曲线）
- [ ] 显示复习统计和下次复习日期

---

**最后更新**：2026-03-31
