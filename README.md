# mistake-notebook

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

面向中小学错题整理的 **Cursor / Claude Code skill**：把错题录入、艾宾浩斯间隔复习、导出、分析和每日提醒串成一套可持续流程。默认思路是「先对话、后脚本」——日常由自然语言驱动，底层由 `scripts/` 里的工具落地。

**Obsidian**：仓库内所有 `.md`（含 `SKILL.md`、`docs/`、`resources/`、示例与说明）均按常规 Markdown + YAML frontmatter 编写，与 Obsidian 兼容；可将本仓库或其中的 `data/mistake-notebook/` 错题目录作为（或并入）Obsidian 库，用 Obsidian 浏览、双向链接与编辑。脚本生成的检索结果、报告等同样为 Markdown，导入后亦可直接管理。

## 能做什么

| 方向 | 能力 |
|------|------|
| 录入与归档 | 从照片或文字整理错题，补齐 `type: mistake-record` 元数据（学科、知识点、错因等），落到 `data/mistake-notebook/` |
| 复习节奏 | 按间隔复习（`review-round`、`due-date`）；全部轮次结束后用 `due-date: completed`（或 `done`）标记完成 |
| 今日复习 | 查询「今天有什么要复习的」——先给文字列表，按需再导出 PDF |
| 复习进度 | 说「复习完了」「物理复习完了」等，自动批量更新今日到期题目 |
| 巩固与诊断 | 举一反三 / 变式题、薄弱知识点、综合分析、月度报告 |
| 提醒 | 飞书、微信或 `crontab` 等渠道的每日复习提醒（可 dry-run 预览文案） |

## 怎么用（自然语言）

在已加载本 skill 的对话里，可以直接说意图，不必先记命令。常见说法例如：

- **查今天**：「今天有什么要复习的？」「给我今天的错题复习提醒。」
- **只要列表**：「先别发 PDF，按学科列一下今天要复习的题。」
- **要资料**：「把物理今天要复习的导出成 PDF。」
- **做完更新**：「今天的错题复习完了。」「数学那几道刚复习过，帮我更新进度。」
- **录入**：「这道题拍下来了，帮我按八下目录归档并写好 frontmatter。」
- **分析**：「跑一下薄弱知识点 TOP5。」「出一份上月错题月报。」

具体触发词、回复里该包含什么（例如更新后要说明下次复习日），见 [docs/auto-review-update.md](docs/auto-review-update.md)。**给 AI 的完整行为规则**在 [SKILL.md](SKILL.md)。

## 开发者与自助运行脚本

若你要本地跑脚本、写 cron、或调试环境：

- **依赖与故障排除**：[docs/requirements.md](docs/requirements.md)
- **命令行示例**（导出 PDF、`update-review`、`daily-review-reminder` 等）：[examples.md](examples.md)
- **目录约定与维护注意**：[reference.md](reference.md)

首次建议在本机执行依赖检查（路径按你仓库里 skill 的实际位置调整）：

```bash
python3 path/to/mistake-notebook/scripts/check-deps.py
```

## 文档索引

| 文件 | 内容 |
|------|------|
| [SKILL.md](SKILL.md) | 智能体运行时规则与工作流步骤 |
| [reference.md](reference.md) | 默认约定、frontmatter、目录结构 |
| [examples.md](examples.md) | 自然语言例句 + 脚本命令示例 |
| [docs/auto-review-update.md](docs/auto-review-update.md) | 「复习提醒 / 复习完了」类意图与响应 |
| [docs/review-update-guide.md](docs/review-update-guide.md) | 复习更新参数与反模式 |
| [docs/cron-setup.md](docs/cron-setup.md) | 定时提醒与渠道配置 |

## 仓库结构（简）

```text
mistake-notebook/
├── SKILL.md          # 智能体入口
├── reference.md
├── examples.md
├── docs/
├── resources/        # 模板、错因类型、课标映射等
└── scripts/          # 导出、更新复习、提醒、分析等
```

## License

MIT. See [LICENSE](LICENSE).
