# Mistake Notebook 阶段 1 重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 mistake-notebook 重构为三层架构（core/services/cli），添加类型注解和单元测试

**Architecture:** 提取核心模块（srs/models/file_ops/pdf_engine）到 `core/`，业务逻辑封装到 `services/`，CLI 脚本迁移到 `cli/` 并调用服务层

**Tech Stack:** Python 3.8+, pathlib, dataclasses, pytest, pytest-cov, mypy

---

## 📁 文件结构

### 新增文件

| 文件 | 职责 |
|------|------|
| `scripts/core/__init__.py` | Core 包初始化 |
| `scripts/core/srs.py` | 间隔复习算法（从 mistake_srs.py 迁移） |
| `scripts/core/models.py` | 数据模型（Mistake, Subject, ErrorType） |
| `scripts/core/file_ops.py` | 文件操作工具 |
| `scripts/core/pdf_engine.py` | PDF 生成引擎（从 pdf_export.py 迁移） |
| `scripts/services/__init__.py` | Services 包初始化 |
| `scripts/services/review_service.py` | 复习管理服务 |
| `scripts/services/practice_service.py` | 练习生成服务 |
| `scripts/services/report_service.py` | 报告生成服务 |
| `scripts/services/wiki_service.py` | Wiki 模式服务 |
| `scripts/cli/__init__.py` | CLI 包初始化 |
| `tests/__init__.py` | 测试包初始化 |
| `tests/core/test_srs.py` | SRS 算法测试 |
| `tests/core/test_models.py` | 数据模型测试 |
| `tests/core/test_file_ops.py` | 文件操作测试 |
| `tests/fixtures/sample_data.py` | 测试数据 fixture |
| `docs/architecture.md` | 架构设计文档（✅ 已创建） |

### 修改文件

| 文件 | 修改内容 |
|------|---------|
| `scripts/init-student.py` | 迁移至 `cli/`，调用服务层 |
| `scripts/update-review.py` | 迁移至 `cli/`，调用 ReviewService |
| `scripts/generate-practice.py` | 迁移至 `cli/`，调用 PracticeService |
| `scripts/export-printable.py` | 迁移至 `cli/`，调用 pdf_engine |
| `scripts/migrate-to-wiki.py` | 迁移至 `cli/`，调用 WikiService |
| `scripts/weak-points.py` | 迁移至 `cli/`，调用 ReportService |
| `scripts/monthly-report.py` | 迁移至 `cli/`，调用 ReportService |
| `requirements.txt` | 添加 pytest, pytest-cov, mypy |

---

## 📋 任务分解

### Task 1: 创建目录结构

**Files:**
- Create: `scripts/core/__init__.py`
- Create: `scripts/services/__init__.py`
- Create: `scripts/cli/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/core/__init__.py`
- Create: `tests/services/__init__.py`
- Create: `tests/fixtures/__init__.py`

- [ ] **Step 1: 创建 core 目录**

```bash
mkdir -p scripts/core scripts/services scripts/cli
mkdir -p tests/core tests/services tests/fixtures
```

- [ ] **Step 2: 创建 __init__.py 文件**

```bash
touch scripts/core/__init__.py scripts/services/__init__.py scripts/cli/__init__.py
touch tests/__init__.py tests/core/__init__.py tests/services/__init__.py tests/fixtures/__init__.py
```

- [ ] **Step 3: 验证目录结构**

```bash
tree scripts/ tests/
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: 创建三层架构目录结构"
```

---

### Task 2: 迁移核心模块 - srs.py

**Files:**
- Create: `scripts/core/srs.py`
- Test: `tests/core/test_srs.py`

- [ ] **Step 1: 复制并重构 mistake_srs.py**

```bash
cp scripts/mistake_srs.py scripts/core/srs.py
```

修改 `scripts/core/srs.py`：
- 添加类型注解
- 添加 docstring
- 导出公共 API

- [ ] **Step 2: 编写 SRS 测试**

创建 `tests/core/test_srs.py`：

```python
from datetime import date, timedelta
from scripts.core.srs import calculate_next_due, is_due_today, ReviewSchedule

def test_calculate_next_due_round0():
    today = date(2026, 4, 12)
    next_due = calculate_next_due(0, today)
    assert next_due == today + timedelta(days=1)

def test_calculate_next_due_with_confidence():
    today = date(2026, 4, 12)
    next_due = calculate_next_due(1, today, confidence='high')
    # high confidence 应延长间隔
    assert next_due > today + timedelta(days=3)

def test_is_due_today_true():
    today = date(2026, 4, 12)
    assert is_due_today(today) is True

def test_is_due_today_false():
    today = date(2026, 4, 12)
    tomorrow = today + timedelta(days=1)
    assert is_due_today(tomorrow) is False
```

- [ ] **Step 3: 运行测试验证失败**

```bash
cd /home/ubuntu/clawd/skills/mistake-notebook
pytest tests/core/test_srs.py -v
```

- [ ] **Step 4: 实现 srs.py 功能**

确保 `scripts/core/srs.py` 包含：

```python
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

@dataclass
class ReviewSchedule:
    intervals: list[int] = None
    confidence_multipliers: dict[str, float] = None
    
    def __post_init__(self):
        self.intervals = self.intervals or [1, 3, 7, 15, 30]
        self.confidence_multipliers = {
            'low': 1.0,
            'medium': 1.2,
            'high': 1.5,
        }

def calculate_next_due(
    current_round: int,
    last_review: date,
    confidence: str = 'low',
    schedule: ReviewSchedule = None
) -> date:
    if schedule is None:
        schedule = ReviewSchedule()
    
    if current_round >= len(schedule.intervals):
        return date.max
    
    interval = schedule.intervals[current_round]
    multiplier = schedule.confidence_multipliers.get(confidence, 1.0)
    adjusted_interval = int(interval * multiplier)
    
    return last_review + timedelta(days=adjusted_interval)

def is_due_today(due_date: date, target_date: Optional[date] = None) -> bool:
    if target_date is None:
        target_date = date.today()
    return due_date <= target_date
```

- [ ] **Step 5: 运行测试验证通过**

```bash
pytest tests/core/test_srs.py -v --cov=scripts.core.srs
```

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(core): 迁移 SRS 算法并添加类型注解"
```

---

### Task 3: 创建数据模型 - models.py

**Files:**
- Create: `scripts/core/models.py`
- Test: `tests/core/test_models.py`

- [ ] **Step 1: 创建数据模型**

创建 `scripts/core/models.py`：

```python
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from enum import Enum

class Subject(str, Enum):
    MATH = 'math'
    CHINESE = 'chinese'
    ENGLISH = 'english'
    PHYSICS = 'physics'
    CHEMISTRY = 'chemistry'
    BIOLOGY = 'biology'

class ErrorType(str, Enum):
    CONCEPT = '概念不清'
    CALC = '计算错误'
    READ = '审题错误'
    FORMULA = '公式错误'
    LOGIC = '逻辑错误'
    FORMAT = '书写错误'

class Confidence(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

@dataclass
class Mistake:
    id: str
    student: str
    subject: Subject
    knowledge_point: str
    unit: Optional[str]
    error_type: ErrorType
    created: date
    due_date: date
    review_round: int = 0
    confidence: Confidence = Confidence.LOW
    question: str = ''
    student_answer: str = ''
    correct_answer: str = ''
    analysis: str = ''
    path: Optional[str] = None
    image_path: Optional[str] = None
    
    def is_completed(self) -> bool:
        return self.due_date == date.max or str(self.due_date) == 'completed'
    
    def days_overdue(self, target_date: Optional[date] = None) -> int:
        if target_date is None:
            target_date = date.today()
        return (target_date - self.due_date).days
```

- [ ] **Step 2: 编写模型测试**

创建 `tests/core/test_models.py`：

```python
from datetime import date, timedelta
from scripts.core.models import Mistake, Subject, ErrorType, Confidence

def test_mistake_is_completed():
    mistake = Mistake(
        id='001', student='测试', subject=Subject.MATH,
        knowledge_point='方程', unit=None, error_type=ErrorType.CALC,
        created=date.today(), due_date=date.max
    )
    assert mistake.is_completed() is True

def test_mistake_days_overdue():
    yesterday = date.today() - timedelta(days=1)
    mistake = Mistake(
        id='002', student='测试', subject=Subject.MATH,
        knowledge_point='方程', unit=None, error_type=ErrorType.CALC,
        created=yesterday, due_date=yesterday
    )
    assert mistake.days_overdue() == 1
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/core/test_models.py -v --cov=scripts.core.models
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(core): 创建数据模型"
```

---

### Task 4: 创建文件操作模块 - file_ops.py

**Files:**
- Create: `scripts/core/file_ops.py`
- Test: `tests/core/test_file_ops.py`

- [ ] **Step 1: 创建 file_ops.py**

提取现有脚本中的 frontmatter 解析、文件查找等函数。

- [ ] **Step 2: 编写测试**

测试 frontmatter 解析、文件查找、路径处理。

- [ ] **Step 3: 运行测试**

```bash
pytest tests/core/test_file_ops.py -v --cov=scripts.core.file_ops
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(core): 创建文件操作模块"
```

---

### Task 5: 创建 PDF 引擎 - pdf_engine.py

**Files:**
- Create: `scripts/core/pdf_engine.py`
- Test: `tests/core/test_pdf_engine.py`

- [ ] **Step 1: 迁移 pdf_export.py**

```bash
cp scripts/pdf_export.py scripts/core/pdf_engine.py
```

重构为 `PDFEngine` 类。

- [ ] **Step 2: 编写测试**

- [ ] **Step 3: 运行测试**

- [ ] **Step 4: Commit**

---

### Task 6: 创建服务层 - ReviewService

**Files:**
- Create: `scripts/services/review_service.py`
- Test: `tests/services/test_review_service.py`

- [ ] **Step 1: 创建 ReviewService**

封装复习查询、更新逻辑。

- [ ] **Step 2: 编写测试**

- [ ] **Step 3: 运行测试**

- [ ] **Step 4: Commit**

---

### Task 7: 创建服务层 - PracticeService

**Files:**
- Create: `scripts/services/practice_service.py`
- Test: `tests/services/test_practice_service.py`

- [ ] **Step 1: 创建 PracticeService**

封装练习生成逻辑。

- [ ] **Step 2: 编写测试**

- [ ] **Step 3: 运行测试**

- [ ] **Step 4: Commit**

---

### Task 8: 创建服务层 - ReportService

**Files:**
- Create: `scripts/services/report_service.py`
- Test: `tests/services/test_report_service.py`

- [ ] **Step 1: 创建 ReportService**

封装报告生成逻辑。

- [ ] **Step 2: 编写测试**

- [ ] **Step 3: 运行测试**

- [ ] **Step 4: Commit**

---

### Task 9: 创建服务层 - WikiService

**Files:**
- Create: `scripts/services/wiki_service.py`
- Test: `tests/services/test_wiki_service.py`

- [ ] **Step 1: 创建 WikiService**

封装 Wiki 模式逻辑。

- [ ] **Step 2: 编写测试**

- [ ] **Step 3: 运行测试**

- [ ] **Step 4: Commit**

---

### Task 10: 迁移 CLI 脚本

**Files:**
- Modify: `scripts/cli/init_student.py`
- Modify: `scripts/cli/update_review.py`
- Modify: `scripts/cli/generate_practice.py`
- Modify: `scripts/cli/export_printable.py`
- Modify: `scripts/cli/migrate_wiki.py`

- [ ] **Step 1: 迁移 init-student.py**

```bash
cp scripts/init-student.py scripts/cli/init_student.py
```

更新导入：`from scripts.services import ...`

- [ ] **Step 2: 迁移其他脚本**

- [ ] **Step 3: 运行所有 CLI 测试**

```bash
pytest tests/cli/ -v
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(cli): 迁移 CLI 脚本"
```

---

### Task 11: 添加类型注解检查

**Files:**
- Modify: `pyproject.toml` 或 `mypy.ini`

- [ ] **Step 1: 配置 mypy**

创建 `mypy.ini`：

```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

- [ ] **Step 2: 运行 mypy**

```bash
mypy scripts/core/ scripts/services/
```

- [ ] **Step 3: 修复类型错误**

- [ ] **Step 4: Commit**

---

### Task 12: 添加覆盖率报告和文档

**Files:**
- Modify: `requirements.txt`
- Create: `README.md` (测试说明)

- [ ] **Step 1: 更新 requirements.txt**

```
pytest>=7.0
pytest-cov>=4.0
mypy>=1.0
playwright>=1.50
markdown2>=2.0
```

- [ ] **Step 2: 运行完整测试套件**

```bash
pytest --cov=scripts --cov-report=html
```

- [ ] **Step 3: 验证覆盖率**

目标：core/ ≥ 90%, services/ ≥ 80%

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "docs: 添加测试配置和覆盖率报告"
```

---

## ✅ 验收标准

- [ ] 所有单元测试通过
- [ ] 核心模块覆盖率 ≥ 80%
- [ ] mypy 类型检查通过
- [ ] 所有现有 CLI 命令正常工作
- [ ] 回归测试通过

---

## 🔗 相关文档

- [architecture.md](../architecture.md) - 架构设计
- [SKILL.md](../SKILL.md) - AI 行为规则

---

*本计划由 writing-plans skill 生成，基于 brainstorming 阶段的设计方案*
