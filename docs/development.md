# 开发指南

本文档提供 Mistake Notebook 的详细开发信息，包括架构设计、新增知识点模板指南、调试技巧和常见问题。

---

## 🏗️ 架构说明

### 三层架构概述

Mistake Notebook 采用清晰的三层架构设计：

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Layer (cli/)                     │
│  命令行入口、参数解析、用户交互                          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                 Service Layer (services/)               │
│  业务逻辑、流程编排、数据转换                            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Core Layer (core/)                     │
│  核心算法、数据模型、基础操作                            │
└─────────────────────────────────────────────────────────┘
```

### 各层职责

#### 1. Core Layer（核心层）

**位置**: `scripts/core/`

**职责**: 
- 核心算法实现
- 数据模型定义
- 基础文件操作
- 无外部业务依赖

**核心模块**:

| 模块 | 职责 | 关键函数/类 |
|------|------|------------|
| `srs.py` | 间隔复习算法 | `calculate_next_due()`, `is_due_today()` |
| `models.py` | 数据模型 | `Mistake`, `Student`, `KnowledgePoint` |
| `file_ops.py` | 文件操作 | `parse_frontmatter()`, `write_frontmatter()` |
| `pdf_engine.py` | PDF 生成 | `render_pdf()`, `generate_charts()` |

**示例**:
```python
# scripts/core/srs.py
from datetime import date, timedelta
from typing import Optional

def calculate_next_due(
    current_round: int,
    last_review: date,
    confidence: str = 'low',
    schedule: Optional[ReviewSchedule] = None
) -> date:
    """计算下次复习日期。"""
    base_intervals = [1, 3, 7, 15, 30]  # 默认间隔
    # ... 实现细节
```

---

#### 2. Service Layer（服务层）

**位置**: `scripts/services/`

**职责**:
- 业务逻辑编排
- 调用 Core 层模块
- 数据格式转换
- 为 CLI 层提供接口

**核心服务**:

| 服务 | 职责 | 关键方法 |
|------|------|---------|
| `review_service.py` | 复习管理 | `get_due_reviews()`, `update_review()` |
| `practice_service.py` | 练习生成 | `generate_practice()`, `get_available_templates()` |
| `report_service.py` | 报告生成 | `generate_monthly_report()`, `generate_analysis_report()` |
| `wiki_service.py` | 知识库管理 | `create_concept_page()`, `lint_wiki()` |

**示例**:
```python
# scripts/services/review_service.py
from core.srs import calculate_next_due, is_due_today
from core.file_ops import find_mistake_files, parse_frontmatter
from core.models import Mistake

class ReviewService:
    def __init__(self, student_name: str, base_dir: Optional[Path] = None):
        self.student_name = student_name
        self.base_dir = base_dir or Path.cwd()
        
    def get_due_reviews(self, target_date: Optional[date] = None) -> List[Mistake]:
        """获取待复习题目列表。"""
        student_dir = get_student_dir(self.student_name, self.base_dir)
        mistake_files = find_mistake_files(student_dir)
        
        due_reviews = []
        for file_path in mistake_files:
            content = file_path.read_text(encoding='utf-8')
            metadata = parse_frontmatter(content)
            mistake = Mistake.from_dict(metadata)
            
            if is_due_today(mistake.due_date, target_date):
                due_reviews.append(mistake)
        
        return due_reviews
```

---

#### 3. CLI Layer（命令行层）

**位置**: `scripts/cli/` 和 `scripts/*.py`

**职责**:
- 命令行参数解析
- 用户交互
- 调用 Service 层
- 结果呈现

**示例**:
```python
# scripts/cli/update_review.py
import argparse
from services.review_service import ReviewService

def main():
    parser = argparse.ArgumentParser(description='更新复习进度')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--subject', help='学科（可选）')
    parser.add_argument('--confidence', choices=['low', 'medium', 'high'],
                       default='medium', help='掌握度')
    args = parser.parse_args()
    
    service = ReviewService(args.student)
    due_reviews = service.get_due_reviews()
    
    if args.subject:
        due_reviews = [m for m in due_reviews if m.subject.value == args.subject]
    
    for mistake in due_reviews:
        service.update_review(mistake.id, confidence=args.confidence)
    
    print(f"✅ 已更新 {len(due_reviews)} 道题的复习进度")
```

---

### 依赖方向

```
CLI → Service → Core
```

- **单向依赖**: 上层依赖下层，下层不依赖上层
- **接口清晰**: 每层通过明确定义的接口通信
- **可测试性**: 每层可独立测试

---

## 📝 新增知识点模板指南

### 模板位置

举一反三模板位于 `resources/practice-templates/` 目录：

```
resources/practice-templates/
├── physics/
│   ├── 力的合成.md
│   ├── 牛顿第一定律.md
│   ├── 欧姆定律.md
│   └── ...
├── math/
│   ├── 一元一次方程.md
│   ├── 二次函数.md
│   └── ...
├── english/
│   ├── 现在完成时.md
│   ├── 一般过去时.md
│   └── ...
└── chemistry/
    ├── 化学方程式.md
    ├── 溶液浓度.md
    └── ...
```

### 模板结构

每个模板文件包含以下部分：

```markdown
---
knowledge_point: 知识点名称
subject: 学科
difficulty_range: [1, 5]  # 难度范围
tags: [标签 1, 标签 2]
---

# {{knowledge_point}} 变式练习

## 题目 1（难度：⭐）

**题目**: 

**答案**:

**解析**:

---

## 题目 2（难度：⭐⭐⭐）

**题目**: 

**答案**:

**解析**:

---

## 题目 3（难度：⭐⭐⭐⭐⭐）

**题目**: 

**答案**:

**解析**:
```

### 新增模板步骤

#### 1. 创建模板文件

```bash
# 进入模板目录
cd resources/practice-templates/<学科>/

# 创建新模板
touch "新知识点.md"
```

#### 2. 填写模板内容

```markdown
---
knowledge_point: 二次函数
subject: math
difficulty_range: [2, 5]
tags: [函数，图像，最值]
---

# 二次函数 变式练习

## 题目 1（难度：⭐⭐）

**题目**: 已知二次函数 y = x² - 4x + 3，求其顶点坐标。

**答案**: 顶点坐标为 (2, -1)

**解析**: 
- 顶点公式：x = -b/(2a) = 4/2 = 2
- 代入得 y = 2² - 4×2 + 3 = -1

---

## 题目 2（难度：⭐⭐⭐）

**题目**: 二次函数 y = ax² + bx + c 的图像经过点 (1, 0) 和 (3, 0)，且顶点在直线 y = 2 上，求 a、b、c 的值。

**答案**: a = -2, b = 8, c = -6

**解析**:
- 由题意知对称轴为 x = 2
- 顶点为 (2, 2)
- 代入三点求解...

---

## 题目 3（难度：⭐⭐⭐⭐⭐）

**题目**: [综合应用题]

**答案**: 

**解析**: 
```

#### 3. 注册模板

在 `scripts/generate-practice.py` 中确认模板自动被发现：

```python
def get_available_templates() -> List[str]:
    """获取所有可用模板。"""
    templates_dir = Path(__file__).parent.parent / 'resources' / 'practice-templates'
    templates = []
    
    for subject_dir in templates_dir.iterdir():
        if subject_dir.is_dir():
            for template_file in subject_dir.glob('*.md'):
                templates.append(template_file.stem)
    
    return templates
```

#### 4. 测试模板

```bash
# 测试新模板
python3 scripts/generate-practice.py \
  --student "测试学生" \
  --knowledge "新知识点" \
  --style "变式"
```

### 模板质量要求

- ✅ 至少包含 3 道题（低/中/高难度各一）
- ✅ 难度标注准确（1-5 星）
- ✅ 解析详细，步骤清晰
- ✅ 符合教学大纲
- ✅ 无版权争议

---

## 🐛 调试技巧

### 1. 启用调试日志

在脚本开头添加：

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 使用
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告")
logger.error("错误")
```

### 2. 使用 pdb 调试

```python
# 在需要调试的地方插入
import pdb; pdb.set_trace()

# 或使用 breakpoint()（Python 3.7+）
breakpoint()
```

**常用命令**:
```
n (next)      # 执行下一行
s (step)      # 进入函数
c (continue)  # 继续执行
p (print)     # 打印变量
l (list)      # 显示代码
q (quit)      # 退出调试
```

### 3. 测试驱动调试

```bash
# 运行单个测试并查看详细输出
pytest tests/core/test_srs.py::test_calculate_next_due -v -s

# 失败后进入调试
pytest tests/core/test_srs.py --pdb

# 遇到错误时进入调试
pytest tests/ -x --pdb
```

### 4. 类型检查调试

```bash
# 详细类型错误信息
mypy scripts/ --show-error-codes --show-traceback

# 忽略特定错误
mypy scripts/ --disable-error-code=attr-defined
```

### 5. PDF 导出调试

```bash
# 启用 Playwright 调试
export PLAYWRIGHT_DEBUG=1
python3 scripts/export-printable.py --student "测试学生"

# 生成 HTML 预览（不转 PDF）
python3 scripts/export-printable.py --student "测试学生" --html-only
```

### 6. 数据验证

```bash
# 检查 frontmatter 格式
python3 -c "
import yaml
from pathlib import Path

content = Path('mistakes/20260412-001.md').read_text()
frontmatter = content.split('---')[1]
data = yaml.safe_load(frontmatter)
print(data)
"
```

---

## ❓ 常见问题 FAQ

### Q1: 依赖安装失败

**问题**: `pip install -r requirements.txt` 报错

**解决**:
```bash
# 1. 升级 pip
pip install --upgrade pip

# 2. 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 单独安装有问题的包
pip install playwright
playwright install chromium
```

---

### Q2: Playwright PDF 导出中文乱码

**问题**: 导出的 PDF 中文显示为方框

**解决**:
```bash
# 1. 安装中文字体（Ubuntu/Debian）
sudo apt-get install fonts-wqy-zenhei fonts-wqy-microhei

# 2. 安装中文字体（macOS）
# 系统自带中文字体，无需额外安装

# 3. 检查 CSS 中的字体配置
# 确保包含中文字体族
font-family: "Noto Sans SC", "WenQuanYi Micro Hei", sans-serif;
```

---

### Q3: 测试覆盖率不达标

**问题**: 覆盖率低于 80%

**解决**:
```bash
# 1. 查看未覆盖的行
pytest --cov=scripts --cov-report=term-missing

# 2. 针对性补充测试
# 重点测试：
# - 边界条件
# - 异常处理
# - 主要业务逻辑

# 3. 排除不需要测试的文件
pytest --cov=scripts --cov-report=html \
  --cov-config=.coveragerc
```

**.coveragerc**:
```ini
[run]
omit =
    scripts/__init__.py
    scripts/*/__init__.py
    scripts/check-deps.py
```

---

### Q4: Git 冲突解决

**问题**: merge/rebase 时遇到冲突

**解决**:
```bash
# 1. 查看冲突文件
git status

# 2. 编辑冲突文件，解决标记
# <<<<<<< HEAD
# 你的修改
# =======
# 对方的修改
# >>>>>>> branch-name

# 3. 标记解决
git add <file>

# 4. 继续 rebase
git rebase --continue

# 5. 或中止 rebase
git rebase --abort
```

---

### Q5: Mypy 类型错误

**问题**: `error: Argument 1 to "func" has incompatible type`

**解决**:
```python
# 1. 检查类型注解
def process(items: List[str]) -> None:
    ...

# 2. 使用正确的类型
process(["a", "b"])  # ✅
process([1, 2])      # ❌

# 3. 如需灵活类型，使用 Union 或 Any
from typing import Union, Any

def process(items: Union[List[str], List[int]]) -> None:
    ...

# 4. 如确实需要忽略，使用 type: ignore
process(some_var)  # type: ignore[arg-type]
```

---

### Q6: 复习日期计算错误

**问题**: 复习日期与实际不符

**调试步骤**:
```bash
# 1. 检查 SRS 算法
python3 -c "
from scripts.core.srs import calculate_next_due
from datetime import date

result = calculate_next_due(
    current_round=3,
    last_review=date(2026, 4, 1),
    confidence='medium'
)
print(f'下次复习日期：{result}')
"

# 2. 检查 frontmatter 中的日期格式
# 应为 YYYY-MM-DD
grep "due-date:" mistakes/*.md

# 3. 运行测试
pytest tests/core/test_srs.py -v
```

---

### Q7: Wiki 链接失效

**问题**: Obsidian 中链接无法跳转

**解决**:
```bash
# 1. 验证链接格式
# 正确：[[知识点名称]]
# 错误：[[知识点]]（名称不匹配）

# 2. 运行链接检查
python3 scripts/verify-links.py --student "学生姓名"

# 3. 运行 Wiki 健康检查
python3 scripts/lint-wiki.py --student "学生姓名"

# 4. 修复孤儿页
# 根据 lint 报告添加缺失的链接
```

---

### Q8: 性能优化

**问题**: 大批量操作时速度慢

**优化建议**:
```python
# 1. 批量文件操作
# ❌ 逐个读取
for file in files:
    content = file.read_text()
    
# ✅ 并行读取
from concurrent.futures import ThreadPoolExecutor

def read_file(path):
    return path.read_text()

with ThreadPoolExecutor() as executor:
    contents = list(executor.map(read_file, files))

# 2. 缓存计算结果
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_next_due(...):
    ...

# 3. 减少数据库/文件 IO
# 一次性加载所需数据
```

---

## 🔗 相关文档

- [架构设计](architecture.md) - 详细架构说明
- [贡献指南](../CONTRIBUTING.md) - 环境搭建和提交流程
- [需求说明](requirements.md) - 依赖和故障排除
- [示例](../examples.md) - 命令行使用示例

---

*最后更新：2026-04-12*
