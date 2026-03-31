# mistake-notebook - 中小学错题整理与管理工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**mistake-notebook** 是一个基于 AI 的中小学错题整理与管理工具，支持拍照录入、智能分类、错题分析、举一反三练习生成、艾宾浩斯复习计划、智能提醒等功能。

---

## ✨ 功能特性

- ✅ **拍照录入**：LLM 自动识别题目内容
- ✅ **智能分类**：学科 → 年级 → 学期 → 单元/自定义分类
- ✅ **错题分析**：薄弱知识点、错误类型分布、趋势分析
- ✅ **举一反三**：基于错题生成相似练习题
- ✅ **艾宾浩斯复习**：自动安排复习计划（1/3/7/15/30 天）
- ✅ **智能提醒**：每天 18:00 自动发送复习提醒到飞书/微信
- ✅ **PDF/长图导出**：可打印 PDF 和手机分享长图
- ✅ **自然语言交互**：直接说"复习完了"自动更新进度

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install playwright markdown2 --break-system-packages

# 安装浏览器（长图和 PDF 生成需要）
playwright install chromium
```

### 2. 克隆仓库

```bash
git clone https://github.com/xjtubmy/mistake-notebook.git
cp -r mistake-notebook /path/to/your/workspace/skills/
```

### 3. 配置定时任务（每日复习提醒）

```bash
crontab -e

# 添加以下行（每天 18:00 自动发送复习提醒）
0 18 * * * cd /path/to/your/workspace && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student <学生名> --channel feishu >> /tmp/review-reminder.log 2>&1
```

### 4. 开始使用

```bash
# 录入错题
/mistake-notebook 录入 --student <学生名> --image photo.jpg

# 生成分析报告
python3 skills/mistake-notebook/scripts/analyze.py --student <学生名>

# 生成举一反三练习
python3 skills/mistake-notebook/scripts/generate-practice.py --student <学生名> --knowledge <知识点> --count 5

# 更新复习进度（或直接向 AI 说"复习完了"）
python3 skills/mistake-notebook/scripts/update-review.py --student <学生名> --today --mastered good
```

---

## 📖 使用文档

详细使用指南请查看：[SKILL.md](skills/mistake-notebook/SKILL.md)

### 核心功能

| 功能 | 命令 | 说明 |
|------|------|------|
| 录入错题 | `/mistake-notebook 录入` | 拍照录入，自动分类 |
| 错题分析 | `analyze.py` | 生成分析报告 |
| 举一反三 | `generate-practice.py` | 生成相似练习题 |
| 复习提醒 | `daily-review-reminder.py` | 每日自动提醒 |
| 进度更新 | `update-review.py` | 更新复习进度 |
| 月度报告 | `monthly-report.py` | 生成月度总结 |
| 薄弱点分析 | `weak-points.py` | 找出薄弱知识点 |
| 家长简报 | `parent-brief.py` | 生成家长汇报 |

---

## 📁 目录结构

```
mistake-notebook/
├── SKILL.md                    # Skill 说明文档
├── README.md                   # 本文件
├── REQUIREMENTS.md             # 依赖说明
├── CRON-SETUP.md              # 定时任务配置
├── REVIEW-UPDATE-GUIDE.md     # 复习更新指南
├── AUTO-REVIEW-UPDATE.md      # 自动响应工作流
└── scripts/
    ├── analyze.py              # 分析报告生成
    ├── classify.py             # 自动分类
    ├── daily-review-reminder.py # 每日复习提醒
    ├── export-practice-pdf.py  # 练习 PDF 导出
    ├── export-printable.py     # 可打印文档导出
    ├── generate-image.py       # 长图生成
    ├── generate-practice.py    # 举一反三练习生成
    ├── monthly-report.py       # 月度报告生成
    ├── parent-brief.py         # 家长简报生成
    ├── search.py               # 错题检索
    ├── share.py                # 分享长图生成
    ├── update-review.py        # 复习进度更新
    └── weak-points.py          # 薄弱知识点分析
```

---

## 📱 飞书/微信集成

### 飞书配置

1. 确保 OpenClaw 已配置飞书机器人
2. 定时任务中使用 `--channel feishu`

### 微信配置

1. 确保 OpenClaw 已配置微信渠道
2. 定时任务中使用 `--channel openclaw-weixin`

---

## 🧪 测试

```bash
# 测试依赖检查
python3 skills/mistake-notebook/scripts/check-deps.py --student <学生名>

# 测试复习提醒（预览模式）
python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student <学生名> --dry-run

# 测试复习更新（预览模式）
python3 skills/mistake-notebook/scripts/update-review.py --student <学生名> --today --dry-run
```

---

## ❓ 常见问题

### Q1: 依赖安装失败？

```bash
# 使用 --break-system-packages 参数
pip install playwright markdown2 --break-system-packages

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install playwright markdown2
```

### Q2: playwright 下载失败？

```bash
# 使用国内镜像
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
playwright install chromium
```

### Q3: 定时任务不执行？

```bash
# 检查 crontab 配置
crontab -l

# 查看日志
tail -f /tmp/review-reminder.log
```

---

## 📝 更新日志

### v1.0.0 (2026-03-31)

- ✨ 初始版本发布
- ✅ 支持错题录入、智能分类
- ✅ 支持错题分析报告
- ✅ 支持举一反三练习生成
- ✅ 支持艾宾浩斯复习计划
- ✅ 支持智能复习提醒（飞书/微信）
- ✅ 支持 PDF/长图导出
- ✅ 支持自然语言交互

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- 感谢 OpenClaw 提供的 AgentSkills 框架
- 感谢所有贡献者

---

## 📬 联系方式

- GitHub: https://github.com/xjtubmy/mistake-notebook
- Issues: https://github.com/xjtubmy/mistake-notebook/issues
