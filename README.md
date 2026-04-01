# mistake-notebook

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

`mistake-notebook` 是一个面向中小学错题本工作流的 skill 仓库，覆盖错题录入、分类、复习、分析、导出和提醒。当前默认工作流是：

1. 录入错题并补齐元数据
2. 查询今日待复习内容，先返回文字列表
3. 用户明确要求时再导出复习 PDF
4. 用户说“复习完了”后自动更新复习进度

## What It Includes

- 错题录入与归档
- `type: mistake-record` frontmatter 说明
- 复习提醒与批量更新
- 举一反三、薄弱点分析、月报
- 飞书/微信渠道的定时提醒配置
- 课程映射、错误类型、学生档案模板等参考资料

## Quick Start

安装依赖：

```bash
pip install playwright markdown2 --break-system-packages
playwright install chromium
```

检查环境：

```bash
python3 skills/mistake-notebook/scripts/check-deps.py
```

几个常用命令：

```bash
# 导出复习 PDF
python3 skills/mistake-notebook/scripts/export-printable.py --student <学生名> --subject physics --output exports/physics-review.pdf --format pdf

# 生成薄弱点分析
python3 skills/mistake-notebook/scripts/weak-points.py --student <学生名>

# 批量更新今日复习
python3 skills/mistake-notebook/scripts/update-review.py --student <学生名> --today

# 预览今日复习提醒
python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student <学生名> --dry-run
```

## Read This First

- [SKILL.md](SKILL.md)：运行时入口规则
- [reference.md](reference.md)：维护约束、目录结构、反模式
- [examples.md](examples.md)：高频自然语言例子与命令示例
- [docs/requirements.md](docs/requirements.md)：依赖安装与常见环境问题
- [docs/auto-review-update.md](docs/auto-review-update.md)：自然语言触发与自动响应
- [docs/review-update-guide.md](docs/review-update-guide.md)：复习更新参数与最佳实践
- [docs/cron-setup.md](docs/cron-setup.md)：定时提醒与渠道配置

## Repository Layout

```text
mistake-notebook/
├── SKILL.md
├── reference.md
├── examples.md
├── README.md
├── docs/
│   ├── requirements.md
│   ├── auto-review-update.md
│   ├── review-update-guide.md
│   ├── cron-setup.md
│   └── plans/
├── resources/
│   ├── student-profile-template.md
│   ├── error-types.md
│   ├── similar-problems-template.md
│   └── curriculum/
└── scripts/
```

## Notes

- 当前默认导出格式是 PDF，不是长图
- `share.py`、`generate-image.py` 等历史脚本仍在仓库中，但不是默认工作流
- 如果调整默认流程，记得同步更新 `SKILL.md`、`reference.md` 和相关 `docs/`

## License

MIT. See [LICENSE](LICENSE).
