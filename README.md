# mistake-notebook

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

面向中小学错题整理的 **Cursor / Claude Code skill**：把错题录入、艾宾浩斯间隔复习、导出、分析和每日提醒串成一套可持续流程。默认思路是「先对话、后脚本」——日常由自然语言驱动，底层由 `scripts/` 里的工具落地。

**Obsidian**：写入 `data/mistake-notebook/` 的**错题笔记**按 Obsidian 习惯组织：文件开头的 YAML frontmatter 在 Obsidian 里可读作**属性（Properties）**，便于按学科、知识点、`due-date` 等筛选；与单元说明、学生档案、举一反三等关联处使用 **`[[wikilink]]`**，在库内形成**反向链接**与图谱。把该数据目录放进你的 vault 即可用 Obsidian 管理、编辑错题。

## 能做什么

| 方向 | 能力 |
|------|------|
| 录入与归档 | 从照片或文字整理错题，补齐 `type: mistake-record` 元数据（学科、知识点、错因等），落到 `data/mistake-notebook/`；生成格式适配 Obsidian **Properties** 与 **`[[双向链接]]`** |
| 复习节奏 | 按间隔复习（`review-round`、`due-date`）；全部轮次结束后用 `due-date: completed`（或 `done`）标记完成 |
| 今日复习 | 查询「今天有什么要复习的」——只列**已到期或已超期**（有效 `due-date` ≤ 今天），未到期的不会出现；先给文字列表，按需再导出 PDF |
| 复习进度 | 说「复习完了」「物理复习完了」等，自动批量更新**今日已到期**的题目 |
| 巩固与诊断 | 举一反三 / 变式题、薄弱知识点、综合分析、月度报告 |
| 提醒 | 飞书、微信或 `crontab` 等渠道的每日复习提醒（可 dry-run 预览文案） |
| 🆕 **知识库模式** | 基于卡帕西 LLM Wiki 理念，把错题本升级成结构化知识库（知识点图谱、双向链接、自动 Lint） |

## 🆕 卡帕西 LLM Wiki 模式（2026-04-08 新增）

基于 Andrej Karpathy 的 [LLM Wiki](https://www.analyticsvidhya.com/blog/2026/04/llm-wiki-by-andrej-karpathy/) 理念，把错题本升级成**结构化知识库**：

| 传统 RAG | LLM Wiki |
|---------|---------|
| 查询时临时检索 | 录入时编译入库 |
| 知识不积累 | 持续累积，预建关联 |
| 临时对话 | 持久 Markdown 文件 |
| 无矛盾检测 | 录入时标记冲突 |

**新增能力**：
- 📚 **知识点图谱**：每个知识点独立成页（`wiki/concepts/`），带掌握度追踪（`confidence`）
- 🔗 **双向链接**：题目↔知识点，Obsidian 图谱可视化
- 🤖 **自动 Lint**：定期扫描矛盾、孤儿页、缺失关联（`lint-wiki.py`）
- 📊 **Dataview 查询**：在 Obsidian 中任意查询统计

**目录结构**：
```
曲凌松/
├── wiki/                    # 知识库（新增）
│   ├── concepts/           # 知识点页面
│   ├── reviews/            # 复习记录
│   └── index.md            # 总索引（Dataview 入口）
├── mistakes/               # 原始错题（保留）
├── practice/               # 变式练习
└── reports/                # 分析报告
```

**使用方式**：
```bash
# 创建知识点页面
python3 scripts/create-concept.py --student "曲凌松" --knowledge "程序运算与不等式组"

# 知识库健康检查
python3 scripts/lint-wiki.py --student "曲凌松"

# 验证链接有效性
python3 scripts/verify-links.py --student "曲凌松"
```

**向后兼容**：现有命令（`今天有什么要复习的 `、` 复习完了`、` 生成月报`）全部保留，只是数据源扩展到 `wiki/` 目录。

---

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

### 🆕 Wiki 模式脚本

| 脚本 | 功能 |
|------|------|
| `create-concept.py` | 基于现有错题自动创建知识点页面 |
| `lint-wiki.py` | 知识库健康检查（孤儿页、缺失关联、过期内容） |
| `verify-links.py` | 验证错题到知识点的链接有效性 |

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
├── docs/             # 详细文档（auto-review-update, cron-setup, etc.）
├── resources/        # 模板、错因类型、课标映射等
├── scripts/          # 导出、更新复习、提醒、分析、Wiki 工具
│   ├── create-concept.py    # 🆕 创建知识点页面
│   ├── lint-wiki.py         # 🆕 知识库健康检查
│   └── verify-links.py      # 🆕 验证链接有效性
└── trigger-optimization/  # 触发词优化配置
```

## License

MIT. See [LICENSE](LICENSE).
