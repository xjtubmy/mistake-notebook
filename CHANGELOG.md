# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-04-12

### Added

#### 阶段 3: 巩固完善
- 完整项目文档（CONTRIBUTING.md、docs/ 目录）
- E2E 端到端测试 16 个，覆盖核心工作流
- 性能优化：脚本启动速度提升 40%
- 开发者贡献指南
- 学生档案初始化脚本（init-student.py）
- 举一反三模板库扩展至 30 个知识点

#### 阶段 2: 体验优化
- **掌握度追踪**：`--confidence` 参数支持（low/medium/high），动态调整复习间隔
- **图表可视化**：三种图表类型嵌入 PDF 报告
  - 饼图：学科分布、知识点占比
  - 柱状图：错误类型对比、周趋势
  - 热力图：复习密度、日历视图
- **难度分级**：`--difficulty` 参数（1-5 星或 基础/变式/提升）
- **LLM Fallback**：无模板知识点自动调用 LLM 生成变式题
- **知识点别名支持**：如"欧姆"="欧姆定律"，"完成时"="现在完成时"
- **PDF 美化**：改进 CSS 模板，支持中文排版

#### 阶段 1: 架构重构
- **三层架构**：core/（核心逻辑）、services/（业务服务）、cli/（命令行接口）
- **全面类型注解**：Python 3.8+ mypy 严格模式
- **单元测试覆盖**：89% 代码覆盖率

### Changed

- 导出脚本统一使用 `export-printable.py`（移除 `export-pdf.py`）
- 复习更新支持批量操作和掌握度设置
- 举一反三模板从 7 个扩展至 30 个知识点（物理 10、数学 8、英语 7、化学 5）
- 目录结构优化：`data/mistake-notebook/` → `students/{学生}/`

### Deprecated

- `export-pdf.py`（已迁移至 `export-printable.py`）
- 旧版单文件架构（已重构为三层架构）

### Removed

- 对 pdfkit/wkhtmltopdf 的依赖（改用 Playwright）
- 硬编码的学生目录（改为动态 `students/{学生}/`）

### Fixed

- 复习到期日计算逻辑（`review-round: 0` 时按 `created + 1 天`）
- 知识点别名映射错误
- PDF 导出中文乱码问题

### Security

- 依赖版本锁定（requirements.txt）
- 敏感信息隔离（学生数据本地存储）

---

## [1.0.0] - 2026-04-01

### Added

- 初始版本发布
- 基础错题录入与归档功能
- 艾宾浩斯间隔复习机制
- 今日复习查询功能
- 复习进度更新功能
- 基础分析报告（薄弱知识点、月报）
- 飞书/微信提醒集成
- 7 个知识点举一反三模板
