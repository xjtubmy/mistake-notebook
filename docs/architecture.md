# Mistake Notebook 架构设计

> 版本：1.0  
> 日期：2026-04-12  
> 状态：阶段 1（核心模块重构）设计

---

## 📋 概述

本文档描述 mistake-notebook 技能的架构重构设计（方案 C - 分阶段混合）。

**目标**：
1. 提升代码质量（模块化、类型注解、测试覆盖）
2. 改善用户体验（智能复习、美观报告、高质量练习）
3. 降低维护成本（清晰分层、可测试、可扩展）

---

## 🏗️ 架构分层

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Layer (cli/)                     │
│  init_student.py │ update_review.py │ generate_practice │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                 Service Layer (services/)               │
│  ReviewService │ PracticeService │ ReportService │ Wiki │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Core Layer (core/)                     │
│    srs.py │ models.py │ file_ops.py │ pdf_engine.py    │
└─────────────────────────────────────────────────────────┘
```

### 分层职责

| 层级 | 职责 | 依赖方向 |
|------|------|---------|
| **CLI** | 命令行入口、参数解析、用户交互 | → Service |
| **Service** | 业务逻辑、流程编排、数据转换 | → Core |
| **Core** | 核心算法、数据模型、基础操作 | 无外部依赖 |

---

## 📦 核心模块设计

### 1. `core/srs.py` - 间隔复习算法

**职责**：复习计划计算、到期判断、掌握度调整

**关键函数**：
```python
def calculate_next_due(
    current_round: int,
    last_review: date,
    confidence: str = 'low',
    schedule: ReviewSchedule = None
) -> date

def is_due_today(due_date: date, target_date: Optional[date] = None) -> bool

def get_review_rounds_total() -> int
```

**增强点**：
- 支持 `confidence` 参数动态调整间隔
- 提供 `ReviewSchedule` 配置类，支持自定义间隔

---

### 2. `core/models.py` - 数据模型

**职责**：定义错题、学生、知识点等核心数据结构

**核心模型**：
- `Mistake` - 错题（含元数据、内容、状态）
- `Student` - 学生档案
- `KnowledgePoint` - 知识点（Wiki 模式）
- `ReviewRecord` - 复习记录

**枚举类型**：
- `Subject` - 学科（MATH, CHINESE, ENGLISH, PHYSICS, CHEMISTRY, BIOLOGY）
- `ErrorType` - 错误类型（CONCEPT, CALC, READ, FORMULA, LOGIC, FORMAT）
- `Confidence` - 掌握度（LOW, MEDIUM, HIGH）

---

### 3. `core/file_ops.py` - 文件操作

**职责**：文件读写、frontmatter 解析、路径管理

**关键函数**：
```python
def parse_frontmatter(content: str) -> Dict[str, Any]
def write_frontmatter(content: str, metadata: Dict[str, Any]) -> str
def find_mistake_files(student_dir: Path, **filters) -> List[Path]
def get_student_dir(student_name: str, base: Optional[Path] = None) -> Path
```

**设计原则**：
- 所有路径操作使用 `pathlib.Path`
- 自动创建缺失目录
- 统一编码为 UTF-8

---

### 4. `core/pdf_engine.py` - PDF 生成引擎

**职责**：Markdown 转 PDF、图表生成、报告排版

**关键能力**：
- 基于 Playwright 的 PDF 渲染
- 支持 `plotly` 交互式图表（嵌入为 PNG）
- 可定制 CSS 模板
- 支持中文排版优化

**增强点**（阶段 2）：
- 增加统计图表（错题分布、掌握度趋势）
- 改进 CSS 模板（更美观的排版）

---

## 🔧 服务层设计

### `services/review_service.py`

```python
class ReviewService:
    def __init__(self, student_name: str, base_dir: Optional[Path] = None)
    
    def get_due_reviews(self, target_date: Optional[date] = None) -> List[Mistake]
    def update_review(self, mistake_id: str, result: str = 'pass') -> ReviewResult
    def batch_update(self, mistake_ids: List[str]) -> BatchResult
    def get_review_stats(self, period: str = 'week') -> ReviewStats
```

### `services/practice_service.py`

```python
class PracticeService:
    def __init__(self, student_name: str, base_dir: Optional[Path] = None)
    
    def generate_practice(
        self,
        knowledge_point: str,
        style: str = 'mixed',
        count: int = 3
    ) -> PracticeSet
    
    def get_available_templates() -> List[str]
```

### `services/report_service.py`

```python
class ReportService:
    def __init__(self, student_name: str, base_dir: Optional[Path] = None)
    
    def generate_weak_points_report() -> Report
    def generate_monthly_report() -> Report
    def generate_analysis_report() -> Report
```

### `services/wiki_service.py`

```python
class WikiService:
    def __init__(self, student_name: str, base_dir: Optional[Path] = None)
    
    def create_concept_page(knowledge: str, mistakes: List[Mistake]) -> Path
    def migrate_to_wiki() -> MigrationResult
    def lint_wiki() -> LintReport
```

---

## 📁 目录结构

```
mistake-notebook/
├── scripts/
│   ├── core/              # 核心模块
│   │   ├── __init__.py
│   │   ├── srs.py
│   │   ├── models.py
│   │   ├── file_ops.py
│   │   └── pdf_engine.py
│   │
│   ├── services/          # 业务服务
│   │   ├── __init__.py
│   │   ├── review_service.py
│   │   ├── practice_service.py
│   │   ├── report_service.py
│   │   └── wiki_service.py
│   │
│   └── cli/               # 命令行工具
│       ├── __init__.py
│       ├── init_student.py
│       ├── update_review.py
│       ├── generate_practice.py
│       ├── export_printable.py
│       ├── migrate_wiki.py
│       ├── weak_points.py
│       └── monthly_report.py
│
├── tests/                 # 测试
│   ├── __init__.py
│   ├── core/
│   ├── services/
│   └── fixtures/
│
├── docs/
│   ├── architecture.md    # 本文件
│   └── ...
│
├── resources/             # 资源文件
└── requirements.txt
```

---

## 🧪 测试策略

### 测试分层

| 层级 | 测试类型 | 工具 | 目标覆盖率 |
|------|---------|------|-----------|
| Core | 单元测试 | pytest | 90%+ |
| Service | 集成测试 | pytest + fixtures | 80%+ |
| CLI | E2E 测试 | pytest + 临时目录 | 60%+ |

### Fixture 设计

```python
# tests/fixtures/sample_mistake.py
def sample_mistake() -> Mistake:
    return Mistake(
        id='20260412-001',
        student='测试学生',
        subject=Subject.PHYSICS,
        knowledge_point='欧姆定律',
        ...
    )
```

### 关键测试场景

1. **SRS 算法**：不同轮次、不同掌握度的日期计算
2. **文件操作**：frontmatter 解析、多格式兼容
3. **复习更新**：批量更新、边界条件（review-round=0）
4. **PDF 导出**：中文渲染、图表嵌入

---

## 📋 阶段划分

### 阶段 1：核心模块重构（当前）

- [ ] 提取 `core/` 模块
- [ ] 提取 `services/` 模块
- [ ] 迁移 CLI 脚本
- [ ] 添加类型注解
- [ ] 编写单元测试

### 阶段 2：体验优化

- [ ] 复习提醒：掌握度动态调整
- [ ] PDF/报告：集成 plotly 图表
- [ ] 举一反三：扩展模板 + LLM fallback

### 阶段 3：巩固完善

- [ ] 开发者文档
- [ ] 端到端测试
- [ ] 性能优化

---

## 🔗 相关文件

- [SKILL.md](../SKILL.md) - AI 行为规则
- [reference.md](../reference.md) - 数据规范
- [docs/requirements.md](requirements.md) - 依赖说明

---

*本文档由 brainstorming skill 辅助设计，经用户批准后生效*
