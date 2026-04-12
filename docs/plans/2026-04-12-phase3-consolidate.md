# Mistake Notebook 阶段 3 巩固完善实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 巩固阶段 1-2 成果，提升可维护性和可靠性

**Architecture:** 在现有三层架构基础上，完善文档、测试和性能

**Tech Stack:** Python 3.9+, pytest, mypy

---

## 📋 任务分解

### Task 3-1: 技能使用说明更新

**Files:**
- Modify: `SKILL.md` - 更新阶段 1-2 新增功能
- Modify: `README.md` - 更新功能列表和使用示例
- Modify: `examples.md` - 新增图表、confidence、难度筛选示例

**Steps:**
- [ ] 更新 SKILL.md Quick Start 和 Workflow 部分
- [ ] 在 README.md 中添加阶段 2 新增的 3 种图表说明
- [ ] 在 examples.md 中添加：
  - `--confidence` 使用示例
  - `--difficulty` 使用示例
  - 图表生成示例
- [ ] Commit: `docs: 更新技能使用说明`

---

### Task 3-2: 开发者贡献指南

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `docs/development.md`

**Steps:**
- [ ] 创建 CONTRIBUTING.md：
  - 环境搭建（依赖安装）
  - 测试运行（pytest 命令）
  - Git 工作流（分支、Commit 规范）
  - 代码风格（类型注解、docstring）
- [ ] 创建 docs/development.md：
  - 架构说明
  - 新增知识点模板指南
  - 调试技巧
- [ ] Commit: `docs: 添加开发者贡献指南`

---

### Task 3-3: 端到端集成测试

**Files:**
- Create: `tests/e2e/test_full_workflow.py`
- Create: `tests/e2e/conftest.py`

**Steps:**
- [ ] 创建 tests/e2e/ 目录
- [ ] 编写完整流程测试：
  1. 初始化学生档案
  2. 录入 3 道错题
  3. 查询今日复习
  4. 更新复习进度（带 confidence）
  5. 生成举一反三练习（带难度筛选）
  6. 导出月度报告（验证图表）
- [ ] 使用临时目录，不污染真实数据
- [ ] Commit: `test: 添加端到端集成测试`

---

### Task 3-4: 性能优化 - 大批量复习查询

**Files:**
- Modify: `scripts/services/review_service.py`
- Modify: `scripts/core/file_ops.py`

**Steps:**
- [ ] 分析性能瓶颈（使用 cProfile）
- [ ] 优化文件遍历逻辑（并行扫描）
- [ ] 添加目录缓存（避免重复扫描）
- [ ] 编写性能测试验证优化效果
- [ ] Commit: `perf: 优化大批量复习查询`

---

### Task 3-5: 性能优化 - PDF 生成加速

**Files:**
- Modify: `scripts/core/pdf_engine.py`
- Modify: `scripts/services/report_service.py`

**Steps:**
- [ ] 图表并行生成（使用 concurrent.futures）
- [ ] 缓存已生成图表（避免重复生成）
- [ ] 优化 Playwright 配置（禁用不必要的功能）
- [ ] 编写性能测试验证优化效果
- [ ] Commit: `perf: 优化 PDF 生成速度`

---

### Task 3-6: 发布准备

**Files:**
- Create: `CHANGELOG.md`
- Modify: `README.md` - 更新版本信息

**Steps:**
- [ ] 创建 CHANGELOG.md：
  - 阶段 1: 重构（三层架构、类型注解、测试）
  - 阶段 2: 体验优化（confidence、图表、模板扩展、LLM）
  - 阶段 3: 巩固完善（文档、E2E 测试、性能）
- [ ] 更新 README.md 版本信息
- [ ] 版本号 bump（v2.0.0）
- [ ] Commit: `chore: 发布准备 v2.0.0`

---

## ✅ 验收标准

| 标准 | 验证方法 |
|------|---------|
| 技能说明完整 | SKILL.md 包含所有新功能 |
| 贡献指南可用 | 新人可按指南搭建环境 |
| E2E 测试通过 | 全流程自动化测试通过 |
| 性能提升 | 1000+ 错题查询 < 2 秒 |
| 发布文档完整 | CHANGELOG + README 更新完成 |

---

## 🔗 相关文档

- [architecture.md](./architecture.md) - 架构设计
- [2026-04-12-phase1-refactor.md](./plans/2026-04-12-phase1-refactor.md) - 阶段 1 计划
- [2026-04-12-phase2-experience.md](./plans/2026-04-12-phase2-experience.md) - 阶段 2 计划

---

*本计划由 writing-plans skill 生成*
