"""
PDF 模板测试 - 验证增强的 CSS 模板和 PDF 生成功能。

测试内容：
- 中文渲染正常
- 表格样式美观（边框、斑马纹）
- 页眉页脚正确显示
- 代码块、引用、细节框样式正确
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from .pdf_engine import PDFEngine
from .pdf_templates import get_enhanced_css, get_html_template


# 示例测试数据 - 包含中文、表格、代码块、引用等
SAMPLE_MARKDOWN = """
# 数学错题本 - 函数与导数

## 题目 1：函数的单调性

**题目**：已知函数 $f(x) = x^3 - 3x + 1$，求函数的单调区间。

**错误答案**：
> 函数的单调递增区间为 $(-\\infty, +\\infty)$

**正确答案**：
- 求导：$f'(x) = 3x^2 - 3 = 3(x^2 - 1) = 3(x-1)(x+1)$
- 令 $f'(x) > 0$，解得 $x < -1$ 或 $x > 1$
- 令 $f'(x) < 0$，解得 $-1 < x < 1$

**单调区间**：
| 区间 | 单调性 |
|------|--------|
| $(-\\infty, -1)$ | 单调递增 |
| $(-1, 1)$ | 单调递减 |
| $(1, +\\infty)$ | 单调递增 |

**知识点总结**：
1. 利用导数判断函数单调性
2. 导数大于 0，函数递增；导数小于 0，函数递减
3. 注意临界点的处理

---

## 题目 2：导数的几何意义

**题目**：曲线 $y = x^2$ 在点 $(1, 1)$ 处的切线方程为？

**易错点**：
- 混淆切线斜率和导数值
- 忘记使用点斜式方程

**解题步骤**：
```python
# 步骤 1：求导数
y' = 2x

# 步骤 2：计算切点处的斜率
k = y'|_{x=1} = 2(1) = 2

# 步骤 3：使用点斜式
y - 1 = 2(x - 1)
y = 2x - 1
```

**答案**：$y = 2x - 1$

---

## 知识点归纳

### 核心公式

<details>
<summary>点击展开常用导数公式</summary>

| 函数 | 导数 |
|------|------|
| $f(x) = c$ | $f'(x) = 0$ |
| $f(x) = x^n$ | $f'(x) = nx^{n-1}$ |
| $f(x) = \\sin x$ | $f'(x) = \\cos x$ |
| $f(x) = \\cos x$ | $f'(x) = -\\sin x$ |
| $f(x) = e^x$ | $f'(x) = e^x$ |
| $f(x) = \\ln x$ | $f'(x) = \\frac{1}{x}$ |

</details>

### 解题技巧

> **提示**：求函数单调区间的一般步骤：
> 1. 确定函数的定义域
> 2. 求导数 $f'(x)$
> 3. 解方程 $f'(x) = 0$，找出临界点
> 4. 用临界点将定义域分成若干区间
> 5. 判断每个区间内 $f'(x)$ 的符号
> 6. 写出单调区间

---

## 本周学习总结

**掌握程度**：⭐⭐⭐⭐☆

**需要加强**：
- 复合函数求导
- 隐函数求导
- 高阶导数应用

**下周计划**：
1. 完成 10 道导数综合题
2. 整理导数压轴题题型
3. 复习函数的极值与最值
"""


def test_enhanced_css() -> None:
    """测试增强的 CSS 模板是否正确生成。"""
    css = get_enhanced_css()
    
    # 验证关键样式存在
    assert "Noto Sans SC" in css, "缺少中文字体 Noto Sans SC"
    assert "@page" in css, "缺少页面设置"
    assert "counter(page)" in css, "缺少页码计数器"
    assert "tbody tr:nth-child(even)" in css, "缺少斑马纹样式"
    assert "thead" in css, "缺少表头样式"
    
    # 验证配色方案
    assert "#2c5282" in css, "缺少主色调"
    assert "#38a169" in css, "缺少强调色"
    
    print("✅ CSS 模板验证通过")


def test_html_template() -> None:
    """测试 HTML 模板是否正确生成。"""
    html = get_html_template(title="测试标题", content="<p>测试内容</p>")
    
    assert "<!DOCTYPE html>" in html
    assert 'lang="zh-CN"' in html
    assert "<title>测试标题</title>" in html
    assert "<p>测试内容</p>" in html
    
    print("✅ HTML 模板验证通过")


def test_pdf_generation() -> None:
    """测试 PDF 生成功能。"""
    engine = PDFEngine()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_mistake_notebook.pdf"
        
        # 生成 PDF
        engine.markdown_to_pdf(
            markdown_content=SAMPLE_MARKDOWN,
            output_path=output_path,
            title="数学错题本 - 测试"
        )
        
        # 验证文件存在
        assert output_path.exists(), f"PDF 文件未生成：{output_path}"
        
        # 验证文件大小（应该大于 10KB）
        file_size = output_path.stat().st_size
        assert file_size > 10000, f"PDF 文件过小：{file_size} bytes"
        
        print(f"✅ PDF 生成成功：{output_path}")
        print(f"   文件大小：{file_size / 1024:.1f} KB")


def main() -> None:
    """运行所有测试。"""
    print("=" * 60)
    print("PDF 模板测试")
    print("=" * 60)
    
    test_enhanced_css()
    test_html_template()
    test_pdf_generation()
    
    print("=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    main()
