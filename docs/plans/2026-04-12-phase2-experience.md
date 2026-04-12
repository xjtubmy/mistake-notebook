# Mistake Notebook 阶段 2 体验优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 优化用户体验，解决复习提醒智能度、PDF 美观度、举一反三质量三大痛点

**Architecture:** 在阶段 1 重构的三层架构基础上，增强服务层功能，新增图表生成能力

**Tech Stack:** Python 3.9+, plotly>=5.0, pytest, mypy

---

## 📋 任务分解

### Task 2-1: 复习提醒智能化

**Files:**
- Modify: `scripts/core/srs.py` - 增强 `calculate_next_due()` 支持 confidence
- Modify: `scripts/services/review_service.py` - 更新 `update_review()` 支持 confidence 参数
- Modify: `scripts/cli/update_review.py` - 添加 `--confidence` CLI 参数
- Test: `tests/core/test_srs.py` - 增加 confidence 相关测试
- Test: `tests/services/test_review_service.py` - 增加 confidence 测试

**Steps:**
- [ ] 在 `ReviewSchedule` 中添加 `confidence_multipliers` 默认值
- [ ] 修改 `calculate_next_due()` 使用乘数调整间隔
- [ ] 更新 `update_review()` 接受并保存 confidence
- [ ] CLI 添加 `--confidence` 参数（low/medium/high）
- [ ] 编写测试验证不同 confidence 的间隔计算
- [ ] 运行测试并验证 CLI 功能
- [ ] Commit: `feat: 复习提醒支持掌握度动态调整`

---

### Task 2-2: 集成 plotly 图表库

**Files:**
- Modify: `requirements.txt` - 添加 `plotly>=5.0`
- Create: `scripts/core/chart_engine.py` - 图表生成引擎
- Test: `tests/core/test_chart_engine.py`

**Steps:**
- [ ] 更新 requirements.txt 添加 plotly
- [ ] 创建 `ChartEngine` 类，实现：
  - `pie_chart()` - 饼图
  - `bar_chart()` - 柱状图
  - `line_chart()` - 折线图
  - `heatmap()` - 热力图
- [ ] 图表输出为 PNG（可嵌入 PDF）
- [ ] 编写单元测试
- [ ] Commit: `feat(core): 集成 plotly 图表引擎`

---

### Task 2-3: 改进 PDF CSS 模板

**Files:**
- Modify: `scripts/core/pdf_engine.py` - 增强 CSS 模板
- Create: `scripts/core/pdf_templates.py` - 模板定义

**Steps:**
- [ ] 设计新 CSS 模板：
  - 改进字体（支持中文）
  - 增加配色方案
  - 优化表格样式
  - 增加页眉页脚
- [ ] 在 `PDFEngine` 中应用新模板
- [ ] 生成测试 PDF 验证效果
- [ ] Commit: `feat: 改进 PDF CSS 模板`

---

### Task 2-4: 生成学科分布饼图

**Files:**
- Modify: `scripts/services/report_service.py` - 添加图表生成
- Test: `tests/services/test_report_service.py`

**Steps:**
- [ ] 在 `generate_analysis_report()` 中添加学科分布饼图
- [ ] 使用 `ChartEngine.pie_chart()`
- [ ] 图表嵌入 PDF 报告
- [ ] 编写测试验证图表生成
- [ ] Commit: `feat: 添加学科分布饼图`

---

### Task 2-5: 生成错误类型柱状图

**Files:**
- Modify: `scripts/services/report_service.py`
- Test: `tests/services/test_report_service.py`

**Steps:**
- [ ] 在 `generate_weak_points_report()` 中添加错误类型柱状图
- [ ] 使用 `ChartEngine.bar_chart()`
- [ ] 图表嵌入 PDF 报告
- [ ] Commit: `feat: 添加错误类型柱状图`

---

### Task 2-6: 生成复习进度热力图

**Files:**
- Modify: `scripts/services/report_service.py`
- Modify: `scripts/services/review_service.py` - 添加复习历史查询

**Steps:**
- [ ] 在 `ReviewService` 中添加 `get_review_history()` 方法
- [ ] 在月度报告中添加复习热力图
- [ ] 使用 `ChartEngine.heatmap()` 或日历热力图
- [ ] Commit: `feat: 添加复习进度热力图`

---

### Task 2-7: 扩展举一反三模板至 30+

**Files:**
- Modify: `scripts/services/practice_service.py` - 扩展模板

**新增知识点**（12 个）：
- 物理：光的反射、电路分析、能量守恒
- 数学：不等式、概率统计、三角函数
- 英语：状语从句、名词性从句、虚拟语气
- 化学：化学方程式配平、溶液浓度

**Steps:**
- [ ] 为每个新增知识点编写 3-5 道模板题（基础/变式/提升）
- [ ] 更新 `PRACTICE_TEMPLATES` 字典
- [ ] 更新知识点别名映射
- [ ] 编写测试验证新模板
- [ ] Commit: `feat: 扩展举一反三模板至 30+ 知识点`

---

### Task 2-8: LLM Fallback 机制

**Files:**
- Modify: `scripts/services/practice_service.py` - 添加 LLM 生成

**Steps:**
- [ ] 实现 `generate_with_llm()` 方法（无模板时调用）
- [ ] 设计 LLM prompt 模板
- [ ] 集成到 `generate_practice()` 流程
- [ ] 编写测试验证 fallback 机制
- [ ] Commit: `feat: 添加 LLM Fallback 生成变式题`

---

### Task 2-9: 难度分级和去重

**Files:**
- Modify: `scripts/services/practice_service.py`
- Modify: `scripts/core/models.py` - 添加难度字段

**Steps:**
- [ ] 在 `PracticeItem` 中添加 `difficulty` 字段（1-5 星）
- [ ] 为所有模板题标记难度
- [ ] 实现去重机制（基于题目 hash）
- [ ] 更新 CLI 支持 `--difficulty` 筛选
- [ ] Commit: `feat: 添加难度分级和去重机制`

---

## ✅ 验收标准

| 标准 | 验证方法 |
|------|---------|
| 复习支持 confidence | CLI `--confidence high` 正常工作 |
| PDF 包含图表 | 生成报告包含饼图 + 柱状图 |
| CSS 模板改进 | 视觉对比确认美观度提升 |
| 知识点 ≥ 30 个 | `get_available_templates()` 返回 30+ |
| LLM Fallback | 无模板知识点调用 LLM 生成 |
| 难度分级 | 题目包含 difficulty 字段 |
| 测试覆盖 | 新增测试 ≥ 50 个，覆盖率 ≥ 85% |

---

## 🔗 相关文档

- [architecture.md](../architecture.md) - 架构设计
- [2026-04-12-phase1-refactor.md](./2026-04-12-phase1-refactor.md) - 阶段 1 计划

---

*本计划由 writing-plans skill 生成*
