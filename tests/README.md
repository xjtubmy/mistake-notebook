# 测试说明文档

## 运行测试

### 运行完整测试套件
```bash
pytest
```

### 运行测试并生成覆盖率报告
```bash
# 生成终端输出 + HTML 报告
pytest --cov=scripts --cov-report=html --cov-report=term-missing

# 仅查看核心模块覆盖率
pytest --cov=scripts/core --cov=scripts/services --cov-report=term-missing
```

### 运行特定测试文件
```bash
pytest tests/core/test_models.py
pytest tests/services/test_wiki_service.py
```

### 运行特定测试函数
```bash
pytest tests/core/test_models.py::test_mistake_card_creation
```

### 详细输出模式
```bash
pytest -v          # 详细输出
pytest -vv         # 更详细输出
pytest -s          # 显示 print 输出
```

## 测试目录结构

```
tests/
├── __init__.py
├── core/                    # 核心模块测试
│   ├── test_file_ops.py     # 文件操作测试
│   ├── test_models.py       # 数据模型测试
│   ├── test_pdf_engine.py   # PDF 引擎测试
│   └── test_srs.py          # 间隔重复算法测试
├── services/                # 服务层测试
│   ├── test_practice_service.py   # 练习服务测试
│   ├── test_report_service.py     # 报告服务测试
│   ├── test_review_service.py     # 复习服务测试
│   └── test_wiki_service.py       # Wiki 服务测试
└── fixtures/                # 测试夹具和固定数据
```

## 覆盖率目标

| 模块 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| core/ | ≥ 90% | ~89% |
| services/ | ≥ 80% | ~90% |
| 总体 | ≥ 85% | ~89% |

## 覆盖率报告

运行测试后，HTML 覆盖率报告生成在 `htmlcov/` 目录：

```bash
# 在浏览器中查看覆盖率报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 测试依赖

确保已安装测试依赖（见 `requirements.txt`）：
```bash
pip install -r requirements.txt
```

主要依赖：
- `pytest>=7.0` - 测试框架
- `pytest-cov>=4.0` - 覆盖率插件
- `mypy>=1.0` - 类型检查
- `playwright>=1.50` - PDF 渲染
- `markdown2>=2.0` - Markdown 解析
- `pyyaml>=6.0` - YAML 解析

## 类型检查

运行 mypy 进行类型检查：
```bash
mypy scripts/
```

## 添加新测试

1. 在对应目录创建测试文件，命名格式：`test_<module>.py`
2. 测试函数命名格式：`test_<functionality>_<scenario>`
3. 使用 pytest 的 `assert` 进行断言
4. 使用 fixtures 提供测试数据

示例：
```python
def test_mistake_card_creation_with_valid_data():
    card = MistakeCard(
        subject="math",
        concept="algebra",
        question="What is 2+2?",
        answer="4"
    )
    assert card.subject == "math"
    assert card.review_round == 0
```

## CI/CD 集成

在 CI 环境中运行测试和覆盖率检查：
```bash
# 运行测试并生成覆盖率 XML（用于 CI 集成）
pytest --cov=scripts --cov-report=xml --cov-report=term-missing

# 检查覆盖率是否达标
pytest --cov=scripts --cov-fail-under=85
```
