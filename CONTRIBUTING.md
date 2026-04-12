# 开发者贡献指南

欢迎为 Mistake Notebook 贡献代码！本文档帮助你快速搭建开发环境并了解贡献流程。

---

## 📦 环境搭建

### 前置要求

- **Python**: 3.8+
- **Git**: 2.0+
- **Node.js**: 18+ (可选，用于某些脚本)

### 1. 克隆仓库

```bash
git clone https://github.com/your-org/mistake-notebook.git
cd mistake-notebook
```

### 2. 创建虚拟环境

```bash
# 使用 venv（推荐）
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 或使用 conda
conda create -n mistake-notebook python=3.10
conda activate mistake-notebook
```

### 3. 安装依赖

```bash
# 基础依赖
pip install -r requirements.txt

# 开发依赖（可选）
pip install pytest pytest-cov mypy playwright black ruff
```

### 4. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 5. 验证安装

```bash
python3 scripts/check-deps.py
```

---

## 🧪 测试运行

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/core/
pytest tests/services/
pytest tests/cli/

# 运行特定测试文件
pytest tests/core/test_srs.py
pytest tests/core/test_srs.py -v  # 详细输出
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=scripts --cov-report=html

# 查看覆盖率摘要
pytest --cov=scripts --cov-report=term-missing

# 打开 HTML 报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\index.html  # Windows
```

### 类型检查

```bash
# 运行 mypy 类型检查
mypy scripts/

# 忽略特定目录
mypy scripts/ --exclude scripts/__pycache__
```

### 代码格式化

```bash
# 使用 black 格式化
black scripts/ tests/

# 使用 ruff 检查
ruff check scripts/ tests/

# 自动修复
ruff check --fix scripts/ tests/
```

---

## 🌿 Git 工作流

### 分支策略

```
main              # 主分支，保护状态
├── develop       # 开发分支（可选）
├── feature/*     # 新功能分支
├── bugfix/*      # 修复分支
├── docs/*        # 文档分支
└── release/*     # 发布分支
```

### 分支命名规范

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| 新功能 | `feature/<功能简述>` | `feature/wiki-migration` |
| Bug 修复 | `bugfix/<问题简述>` | `bugfix/srs-calculation` |
| 文档 | `docs/<内容简述>` | `docs/contributing-guide` |
| 重构 | `refactor/<模块简述>` | `refactor/pdf-engine` |
| 测试 | `test/<测试内容>` | `test/review-service` |

### 开发流程

```bash
# 1. 从 main 创建新分支
git checkout main
git pull origin main
git checkout -b feature/your-feature

# 2. 开发并提交
git add -A
git commit -m "feat: 添加新功能"

# 3. 同步 main 分支（避免冲突）
git fetch origin main
git rebase origin/main

# 4. 推送分支
git push -u origin feature/your-feature

# 5. 创建 Pull Request
```

### Commit 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构（非新功能/修复） |
| `test` | 测试相关 |
| `chore` | 构建/工具/配置 |

#### 示例

```bash
# 新功能
git commit -m "feat(wiki): 添加批量迁移脚本"

# Bug 修复
git commit -m "fix(srs): 修复复习日期计算边界条件"

# 文档
git commit -m "docs: 添加开发者贡献指南"

# 重构
git commit -m "refactor(core): 提取文件操作为独立模块"

# 多行提交信息
git commit -m "feat(practice): 支持难度分级

- 添加 --difficulty 参数
- 支持 1-5 星难度筛选
- 映射 style 参数到难度范围

Closes #42"
```

---

## 📝 代码风格

### 类型注解

所有公共函数和类必须添加类型注解：

```python
# ✅ 正确
from typing import List, Optional, Dict, Any
from datetime import date

def calculate_next_due(
    current_round: int,
    last_review: date,
    confidence: str = 'low',
    schedule: Optional[ReviewSchedule] = None
) -> date:
    """计算下次复习日期。
    
    Args:
        current_round: 当前复习轮次
        last_review: 上次复习日期
        confidence: 掌握度 (low/medium/high)
        schedule: 自定义复习计划
        
    Returns:
        下次复习日期
    """
    ...

# ❌ 错误
def calculate_next_due(current_round, last_review, confidence='low', schedule=None):
    ...
```

### Docstring 要求

使用 Google 风格或 NumPy 风格 docstring：

```python
"""模块简述。

详细描述（可选）。
"""

class ReviewService:
    """复习服务类。
    
    负责复习计划的计算、更新和统计。
    
    Attributes:
        student_name: 学生姓名
        base_dir: 基础目录
    """
    
    def get_due_reviews(
        self,
        target_date: Optional[date] = None
    ) -> List[Mistake]:
        """获取待复习题目列表。
        
        Args:
            target_date: 目标日期，默认为今天
            
        Returns:
            待复习题目列表
            
        Raises:
            FileNotFoundError: 学生目录不存在
            
        Example:
            >>> service = ReviewService('张三')
            >>> due = service.get_due_reviews()
            >>> len(due)
            5
        """
        ...
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块/文件 | `snake_case` | `review_service.py` |
| 类 | `PascalCase` | `ReviewService` |
| 函数/变量 | `snake_case` | `calculate_next_due` |
| 常量 | `UPPER_CASE` | `DEFAULT_REVIEW_ROUNDS` |
| 私有成员 | `_prefix` | `_internal_cache` |

### 导入顺序

```python
# 1. 标准库
import os
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# 2. 第三方库
import yaml
import markdown2
from playwright.sync_api import sync_playwright

# 3. 本地模块
from core.models import Mistake, Student
from core.srs import calculate_next_due
```

### 行宽限制

- 最大行宽：**88 字符**（black 默认）
- 使用括号隐式续行，避免反斜杠：

```python
# ✅ 正确
result = some_function(
    arg1, arg2, arg3,
    keyword=value
)

# ❌ 错误
result = some_function(arg1, arg2, arg3, \
                       keyword=value)
```

---

## 🔍 Code Review 检查清单

提交 PR 前自查：

- [ ] 代码通过 `black` 格式化
- [ ] 代码通过 `ruff` 检查
- [ ] 类型检查 `mypy` 通过
- [ ] 测试覆盖率 ≥ 80%（核心模块 ≥ 90%）
- [ ] 所有测试通过
- [ ] Docstring 完整
- [ ] Commit 信息符合规范
- [ ] 更新相关文档（如适用）

---

## 📚 相关文档

- [架构设计](docs/architecture.md) - 三层架构详解
- [开发指南](docs/development.md) - 架构、模板、调试
- [需求说明](docs/requirements.md) - 依赖和故障排除
- [示例](examples.md) - 命令行使用示例

---

## 🆘 需要帮助？

遇到问题？

1. 查看 [FAQ](docs/development.md#常见问题-faq)
2. 检查现有 Issue
3. 创建新 Issue 并标注 `question` 标签

感谢你的贡献！🎉
