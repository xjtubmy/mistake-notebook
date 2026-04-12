"""
练习服务模块 - 举一反三练习生成服务层

提供基于错题知识点的练习生成服务，支持多种风格（基础/变式/提升/混合），
并管理练习模板的加载和使用。
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加 scripts 目录到路径以导入 core 模块
_script_dir = Path(__file__).resolve().parent.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from core.file_ops import get_student_dir


@dataclass
class PracticeItem:
    """单个练习题数据模型。
    
    Attributes:
        question: 题目内容
        answer: 参考答案
        parse: 解析说明
        options: 选项内容（可选，用于选择题）
        style: 题目风格（基础/变式/提升）
    """
    question: str
    answer: str
    parse: str
    options: Optional[str] = None
    style: str = 'mixed'


@dataclass
class PracticeSet:
    """练习题集合数据模型。
    
    Attributes:
        student: 学生姓名
        knowledge_point: 知识点名称
        style: 练习风格
        generated_at: 生成时间
        items: 练习题列表
    """
    student: str
    knowledge_point: str
    style: str
    generated_at: datetime
    items: List[PracticeItem] = field(default_factory=list)
    
    @property
    def count(self) -> int:
        """返回练习题数量。"""
        return len(self.items)
    
    def to_markdown(self) -> str:
        """将练习集转换为 Markdown 格式。
        
        Returns:
            Markdown 格式的练习内容
        """
        content = f"""# 📝 举一反三练习

**学生**：{self.student}  
**知识点**：{self.knowledge_point}  
**生成时间**：{self.generated_at.strftime('%Y-%m-%d %H:%M')}  
**题目数量**：{self.count} 道  
**练习风格**：{self.style}

---

## 练习题

"""
        for i, item in enumerate(self.items, 1):
            content += f"### 第 {i} 题\n\n{item.question}\n\n"
            if item.options:
                content += f"{item.options}\n\n"
            content += f"""<details>
<summary>点击查看答案与解析</summary>

**答案**：{item.answer}

**解析**：{item.parse}

</details>

---

"""
        content += f"""
## 📊 练习记录

| 日期 | 正确率 | 用时 | 签名 |
|------|--------|------|------|
| {datetime.now().strftime('%Y-%m-%d')} | /{self.count} | | |

---

## 💡 使用建议

1. **独立完成后对答案**：不要边做边看答案
2. **错题标记**：做错的题目标记出来，重点复习
3. **定期重做**：同一份练习可以间隔一周重做

---

*本练习由 mistake-notebook 动态生成 · 每次生成题目可能不同*
"""
        return content
    
    def save(self, output_path: Optional[Path] = None) -> Path:
        """将练习集保存为 Markdown 文件。
        
        Args:
            output_path: 输出文件路径（可选，默认使用标准命名）
        
        Returns:
            保存的文件路径
        """
        if output_path is None:
            student_dir = get_student_dir(self.student)
            practice_dir = student_dir / "practices" / self.knowledge_point
            practice_dir.mkdir(parents=True, exist_ok=True)
            timestamp = self.generated_at.strftime('%Y%m%d_%H%M%S')
            output_path = practice_dir / f"practice_{timestamp}.md"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_markdown(), encoding='utf-8')
        return output_path


# 知识点→练习模板映射（精简版，仅保留关键知识点）
PRACTICE_TEMPLATES: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    '力的合成': {
        '基础': [
            {'question': '一个物体在水平向右 {f1}N 的拉力作用下向右做匀速直线运动，若撤去拉力，在撤去瞬间物体受到的摩擦力大小为______N。', 'answer': '{f1}N', 'parse': '匀速直线运动→摩擦力=拉力'},
            {'question': '用 {f1}N 的水平力推着一个重 {g}N 的木箱在水平地面上做匀速直线运动，木箱受到的摩擦力大小为______N。', 'answer': '{f1}', 'parse': '水平方向二力平衡：摩擦力=推力'},
        ],
        '变式': [
            {'question': '一个木块在水平桌面上向右做匀速直线运动，受到水平向右 {f1}N 的拉力。若突然将拉力增大到 {f2}N，此时木块受到的合力为______N。', 'answer': '{diff}N', 'parse': '合力 = 新拉力 - 摩擦力 = {f2} - {f1} = {diff}N'},
        ],
        '提升': [
            {'question': '物体在水平拉力 F 作用下做匀速直线运动，若拉力突然变为 2F，则物体将做______运动。', 'answer': '加速', 'parse': '拉力>摩擦力，合力向前，物体加速'},
        ],
    },
    '牛顿第一定律': {
        '基础': [
            {'question': '一切物体在没有受到外力作用时，总保持______状态或______状态。', 'answer': '静止；匀速直线运动', 'parse': '牛顿第一定律的内容'},
            {'question': '惯性是物体保持原有______的性质，惯性的大小只与物体的______有关。', 'answer': '运动状态；质量', 'parse': '惯性是性质，不是力；质量是惯性大小的唯一量度'},
        ],
        '变式': [
            {'question': '关于惯性，下列说法正确的是（ ）', 'options': 'A. 静止的物体没有惯性  B. 速度越大惯性越大  C. 质量越大惯性越大  D. 月球上没有惯性', 'answer': 'C', 'parse': '惯性是物体的固有属性，只与质量有关'},
        ],
        '提升': [
            {'question': '踢出去的足球在地面上继续滚动，这是因为足球具有______。', 'answer': '惯性', 'parse': '惯性使足球保持运动状态'},
        ],
    },
    '欧姆定律': {
        '基础': [
            {'question': '一段导体两端电压为 {u}V 时，通过它的电流为 {i}A，则这段导体的电阻为______Ω。', 'answer': '{r}Ω', 'parse': '欧姆定律：R = U/I = {u}/{i} = {r}Ω'},
            {'question': '一个电阻为 {r}Ω 的导体，通过它的电流为 {i}A，则它两端的电压为______V。', 'answer': '{u}V', 'parse': '欧姆定律变形：U = I×R'},
        ],
        '变式': [
            {'question': '某导体两端电压从 {u1}V 增大到 {u2}V 时，通过它的电流从 {i1}A 增大到______A。', 'answer': '{i2}A', 'parse': '电阻不变：I₂ = U₂/R'},
        ],
        '提升': [
            {'question': '关于欧姆定律，下列说法正确的是（ ）', 'options': 'A. 导体电阻与电压成正比  B. 导体电阻由导体本身决定', 'answer': 'B', 'parse': '电阻是导体本身的性质，与电压、电流无关'},
        ],
    },
    '浮力': {
        '基础': [
            {'question': '一个物体浸没在水中，排开水的体积为 {v}cm³，则它受到的浮力为______N。', 'answer': '{f}N', 'parse': '阿基米德原理：F 浮 = ρ液 gV 排'},
            {'question': '一个重 {g}N 的物体漂浮在水面上，它受到的浮力为______N。', 'answer': '{g}N', 'parse': '漂浮条件：F 浮 = G'},
        ],
        '变式': [
            {'question': '同一物体分别浸没在水和盐水中，受到的浮力较大的是______中。', 'answer': '盐水', 'parse': 'ρ盐水>ρ水，由 F 浮=ρ液 gV 排可知，盐水中浮力更大'},
        ],
        '提升': [
            {'question': '一个边长为 10cm 的正方体木块，密度为 0.6×10³kg/m³，放入水中静止时，露出水面的体积为______cm³。', 'answer': '400', 'parse': '漂浮：V 排/V 总=ρ木/ρ水=0.6，V 露=0.4×1000=400cm³'},
        ],
    },
    '压强': {
        '基础': [
            {'question': '一个重 {g}N 的物体放在水平桌面上，与桌面的接触面积为 {s}cm²，则它对桌面的压强为______Pa。', 'answer': '{p}Pa', 'parse': 'p = F/S'},
            {'question': '液体压强公式为 p = ______。', 'answer': 'ρgh', 'parse': '液体压强公式：p = ρgh'},
        ],
        '变式': [
            {'question': '同一个物体分别正放和倒放在水平桌面上，对桌面的压力______，压强______。', 'answer': '相等；不相等', 'parse': '压力 F=G 不变，受力面积改变，故压强改变'},
        ],
        '提升': [
            {'question': '一个密闭容器中装满水，倒置后水对容器底部的压强______。', 'answer': '不变', 'parse': '深度不变→压强不变'},
        ],
    },
    '杠杆': {
        '基础': [
            {'question': '杠杆的平衡条件是：______。', 'answer': 'F₁L₁ = F₂L₂', 'parse': '杠杆平衡条件：动力×动力臂 = 阻力×阻力臂'},
            {'question': '省力杠杆的动力臂______阻力臂。', 'answer': '大于', 'parse': 'L₁>L₂时省力'},
        ],
        '变式': [
            {'question': '用撬棒撬石头，动力臂是阻力臂的 5 倍，若石头重 {g}N，则至少需要______N 的力才能撬动。', 'answer': '{f}N', 'parse': 'F₁ = F₂×L₂/L₁ = {g}/5'},
        ],
        '提升': [
            {'question': '一个不均匀的杠杆，支点在中间，两端挂等重物体时杠杆平衡。若将两端物体同时浸没在水中，杠杆将______。', 'answer': '保持平衡', 'parse': '两物体受到浮力后，等效重力同比例减小，力矩比不变'},
        ],
    },
    '电功率': {
        '基础': [
            {'question': '一个标有"220V {p}W"的灯泡，正常工作时的电流为______A。', 'answer': '{i}A', 'parse': 'I = P/U'},
            {'question': '电功率的计算公式有 P = ______。', 'answer': 'UI', 'parse': '电功率基本公式'},
        ],
        '变式': [
            {'question': '两个灯泡 L₁"220V 40W"和 L₂"220V 100W"串联在 220V 电路中，更亮的是______。', 'answer': 'L₁', 'parse': '串联 I 相同，P=I²R，R₁>R₂，故 L₁ 实际功率更大'},
        ],
        '提升': [
            {'question': '一个电热水壶标有"220V 1000W"，若实际电压为 200V，则实际功率约为______W。', 'answer': '826', 'parse': 'P 实 = U 实²/R'},
        ],
    },
    '一元一次方程': {
        '基础': [
            {'question': '解方程：{a_eq_val}x + {b_eq_val} = {c_eq_val}', 'answer': 'x = {x_eq}', 'parse': '移项：{a_eq_val}x = {c_eq_val}-{b_eq_val} = {cx}，x = {cx}/{a_eq_val} = {x_eq}'},
            {'question': '若 x = {x_eq} 是方程 {a_eq_val}x - {b_eq_val} = {c_eq_val} 的解，则方程左边等于______。', 'answer': '{c_eq_val}', 'parse': '将 x 代入方程左边验证'},
        ],
        '变式': [
            {'question': '解方程：{a_eq_val}(x - {b_eq_val}) = {c_eq_val}', 'answer': 'x = {x2}', 'parse': '去括号后移项求解'},
        ],
        '提升': [
            {'question': '已知关于 x 的方程 {a_eq_val}x + {b_eq_val} = {c_eq_val} 的解比关于 x 的方程 {a2}x + {b2} = {c2} 的解大 2，求参数值。', 'answer': '需具体计算', 'parse': '分别解出两个方程的解，根据差值为 2 列方程求解'},
        ],
    },
    '二次函数': {
        '基础': [
            {'question': '二次函数 y = x² - {b_quad_val}x + {c_quad_val} 的顶点坐标为______。', 'answer': '({h_quad}, {k_quad})', 'parse': '顶点公式：x = -b/(2a)'},
            {'question': '抛物线 y = ax² + bx + c 的开口方向由______决定。', 'answer': 'a', 'parse': 'a>0 开口向上，a<0 开口向下'},
        ],
        '变式': [
            {'question': '将抛物线 y = x² 向右平移 {h_quad} 个单位，再向上平移 {k_quad} 个单位，所得抛物线的解析式为______。', 'answer': 'y = (x-{h_quad})² + {k_quad}', 'parse': '平移规律：左加右减，上加下减'},
        ],
        '提升': [
            {'question': '抛物线 y = x² - {b_quad_val}x + {c_quad_val} 与 x 轴的交点个数为______。', 'answer': '{ans_delta}', 'parse': 'Δ = b²-4ac，{judge}'},
        ],
    },
    '勾股定理': {
        '基础': [
            {'question': '在 Rt△ABC 中，∠C=90°，若 a={a_tri_val}, b={b_tri_val}，则斜边 c = ______。', 'answer': '{c_tri_val}', 'parse': '勾股定理：c = √(a²+b²)'},
            {'question': '勾股定理的内容是：直角三角形两直角边的______等于斜边的______。', 'answer': '平方和；平方', 'parse': 'a² + b² = c²'},
        ],
        '变式': [
            {'question': '一个直角三角形的两条边长分别为 {a_tri_val} 和 {b_tri_val}，则第三边长为______。', 'answer': '{c_tri_val} 或 {c_alt_tri}', 'parse': '需分类讨论哪条是斜边'},
        ],
        '提升': [
            {'question': '折叠矩形 ABCD，使点 B 落在 AD 边上的点 F 处，若 AB={a_tri_val}, BC={b_tri_val}，则折痕 AE 的长为______。', 'answer': '需具体计算', 'parse': '设 BE=x，在 Rt△AEF 中用勾股定理列方程'},
        ],
    },
    '三角形全等': {
        '基础': [
            {'question': '判定两个三角形全等的方法有：______。', 'answer': 'SSS、SAS、ASA、AAS', 'parse': '全等三角形判定方法'},
            {'question': '已知△ABC≌△DEF，若 AB={a_tri_val}cm，则 DE = ______cm。', 'answer': '{a_tri_val}', 'parse': '全等三角形对应边相等'},
        ],
        '变式': [
            {'question': '如图，已知 AB=AC，要使△ABD≌△ACD，还需添加的条件是______。', 'answer': 'BD=CD 或∠BAD=∠CAD', 'parse': '可用 SSS、SAS 或 ASA 判定'},
        ],
        '提升': [
            {'question': '在△ABC 中，AB=AC，D、E 分别在 AB、AC 上，且 AD=AE，BE 与 CD 相交于点 F。求证：BF=CF。', 'answer': '证明见解析', 'parse': '先证△ABE≌△ACD，再证△BDF≌△CEF'},
        ],
    },
    '平行四边形': {
        '基础': [
            {'question': '平行四边形的对边______，对角______。', 'answer': '相等；相等', 'parse': '平行四边形性质'},
            {'question': '在□ABCD 中，若∠A = {angle_para_val}°，则∠B = ______°。', 'answer': '{angle_b_para}', 'parse': '平行四边形邻角互补'},
        ],
        '变式': [
            {'question': '在□ABCD 中，对角线 AC、BD 相交于点 O，若 AC={ac_para_val}, 则 AO = ______。', 'answer': '{ao_para_val}', 'parse': '平行四边形对角线互相平分'},
        ],
        '提升': [
            {'question': '在□ABCD 中，E、F 分别是 AB、CD 的中点，连接 AF、CE。求证：四边形 AECF 是平行四边形。', 'answer': '证明见解析', 'parse': '证 AE∥CF 且 AE=CF 即可'},
        ],
    },
    '现在完成时': {
        '基础': [
            {'question': 'I ______ (live) here for {num} years.', 'answer': 'have lived', 'parse': 'for+ 时间段，用现在完成时'},
            {'question': 'She ______ (finish) her homework already.', 'answer': 'has finished', 'parse': 'already 是现在完成时的标志词'},
        ],
        '变式': [
            {'question': "—______ you ever ______ to Beijing? —Yes, I ______ there last year.", 'answer': 'Have; been; went', 'parse': '第一空问经历用现在完成时，第二空有 last year 用一般过去时'},
        ],
        '提升': [
            {'question': 'My father ______ (go) to Beijing on business. He ______ (be) back in two days.', 'answer': 'has gone; will be', 'parse': 'has gone 表示去了未回，in two days 用一般将来时'},
        ],
    },
    '一般过去时': {
        '基础': [
            {'question': 'I ______ (go) to the cinema yesterday.', 'answer': 'went', 'parse': 'yesterday 是一般过去时的标志词'},
            {'question': "She ______ (not do) her homework last night.", 'answer': "didn't do", 'parse': 'last night 用一般过去时，否定用 didn\'t + 动词原形'},
        ],
        '变式': [
            {'question': '—When ______ you ______ (buy) this book? —I ______ (buy) it last week.', 'answer': 'did; buy; bought', 'parse': 'last week 用一般过去时，疑问句用 did 提问'},
        ],
        '提升': [
            {'question': 'While I ______ (walk) in the park, it ______ (begin) to rain.', 'answer': 'was walking; began', 'parse': 'while 引导过去进行时，主句用一般过去时'},
        ],
    },
    '定语从句': {
        '基础': [
            {'question': 'The man ______ is talking to our teacher is my father.', 'answer': 'who/that', 'parse': '先行词是人，在从句中作主语，用 who 或 that'},
            {'question': 'This is the book ______ I bought yesterday.', 'answer': 'which/that', 'parse': '先行词是物，在从句中作宾语，用 which 或 that'},
        ],
        '变式': [
            {'question': 'I still remember the day ______ we first met.', 'answer': 'when/on which', 'parse': '先行词是时间，在从句中作时间状语，用 when'},
        ],
        '提升': [
            {'question': 'The boy ______ parents are dead was brought up by his grandmother.', 'answer': 'whose', 'parse': '先行词与 parents 是所属关系，用 whose'},
        ],
    },
    '被动语态': {
        '基础': [
            {'question': 'English ______ (speak) all over the world.', 'answer': 'is spoken', 'parse': '一般现在时被动：am/is/are + 过去分词'},
            {'question': 'The book ______ (write) by Lu Xun in 1921.', 'answer': 'was written', 'parse': '一般过去时被动：was/were + 过去分词'},
        ],
        '变式': [
            {'question': 'A new hospital ______ (build) in our town next year.', 'answer': 'will be built', 'parse': '一般将来时被动：will be + 过去分词'},
        ],
        '提升': [
            {'question': 'The old man ______ (see) to enter the building at about 9 p.m.', 'answer': 'was seen', 'parse': 'see sb do 变被动要加 to：sb be seen to do'},
        ],
    },
    '化学方程式': {
        '基础': [
            {'question': '写出氢气燃烧的化学方程式：______', 'answer': '2H₂ + O₂ → 2H₂O', 'parse': '氢气与氧气在点燃条件下生成水'},
            {'question': '配平化学方程式：Fe + O₂ → Fe₃O₄', 'answer': '3Fe + 2O₂ → Fe₃O₄', 'parse': '用观察法或最小公倍数法配平'},
        ],
        '变式': [
            {'question': '写出实验室用过氧化氢制取氧气的化学方程式：______', 'answer': '2H₂O₂ → 2H₂O + O₂↑', 'parse': 'MnO₂作催化剂'},
        ],
        '提升': [
            {'question': '某金属 R 与稀盐酸反应生成 RCl₃和氢气，写出该反应的化学方程式：______', 'answer': '2R + 6HCl → 2RCl₃ + 3H₂↑', 'parse': '根据产物 RCl₃可知 R 显 +3 价'},
        ],
    },
}

# 知识点别名映射
KNOWLEDGE_ALIASES: Dict[str, str] = {
    '欧姆': '欧姆定律', '欧姆定律': '欧姆定律',
    '浮力': '浮力', '压强': '压强', '杠杆': '杠杆', '电功率': '电功率',
    '力的合成': '力的合成', '牛顿第一定律': '牛顿第一定律', '惯性': '牛顿第一定律',
    '一元一次方程': '一元一次方程', '方程': '一元一次方程',
    '二次函数': '二次函数', '抛物线': '二次函数',
    '勾股定理': '勾股定理', '三角形全等': '三角形全等', '全等三角形': '三角形全等',
    '平行四边形': '平行四边形',
    '现在完成时': '现在完成时', '完成时': '现在完成时',
    '一般过去时': '一般过去时', '过去时': '一般过去时',
    '定语从句': '定语从句', '从句': '定语从句',
    '被动语态': '被动语态', '被动': '被动语态',
    '化学方程式': '化学方程式', '方程式': '化学方程式',
}

VALID_STYLES = frozenset({'基础', '变式', '提升', 'mixed'})


class PracticeService:
    """练习生成服务类。
    
    提供基于错题知识点的举一反三练习生成功能，支持多种风格（基础/变式/提升/混合）。
    
    Attributes:
        student_name: 学生姓名
        base_dir: 基础目录路径（可选）
    
    Example:
        >>> service = PracticeService("张三")
        >>> practice_set = service.generate_practice("欧姆定律", style="mixed", count=3)
        >>> print(f"生成了{practice_set.count}道练习题")
    """
    
    def __init__(self, student_name: str, base_dir: Optional[Path] = None) -> None:
        """初始化练习服务。
        
        Args:
            student_name: 学生姓名
            base_dir: 基础目录路径（可选，默认为 data/mistake-notebook/students）
        
        Example:
            >>> service = PracticeService("张三")
            >>> service.student_name
            '张三'
        """
        self.student_name = student_name
        self.base_dir = base_dir
        self._student_dir = get_student_dir(student_name, base_dir)
    
    def _resolve_knowledge_point(self, knowledge_point: str) -> str:
        """解析知识点名称，支持别名映射。
        
        Args:
            knowledge_point: 知识点名称（可能是别名）
        
        Returns:
            标准知识点名称
        
        Example:
            >>> service = PracticeService("张三")
            >>> service._resolve_knowledge_point("欧姆")
            '欧姆定律'
            >>> service._resolve_knowledge_point("勾股定理")
            '勾股定理'
        """
        return KNOWLEDGE_ALIASES.get(knowledge_point, knowledge_point)
    
    def _generate_params(self) -> Dict[str, Any]:
        """生成随机参数用于填充题目模板。
        
        Returns:
            参数字典，包含所有模板占位符对应的值
        
        Example:
            >>> service = PracticeService("张三")
            >>> params = service._generate_params()
            >>> 'f1' in params
            True
        """
        f1 = random.choice([5, 10, 15, 20, 25, 30])
        f2 = f1 + random.choice([5, 10, 15])
        f3 = random.choice([5, 10, 15])
        diff = f2 - f1
        result_force = abs(f1 - (f2 + f3))
        direction = '右' if (f2 + f3) > f1 else '左'
        g = random.choice([50, 100, 150, 200])
        
        u = random.choice([3, 6, 9, 12, 220])
        i = random.choice([0.1, 0.2, 0.3, 0.5, 1, 2])
        r = round(u / i, 1) if i > 0 else 10
        u1, u2 = u, u + random.choice([3, 6, 9])
        i1, i2 = i, round(u2 / r, 2)
        
        v = random.choice([100, 200, 300, 500])
        f_buoy = round(1.0 * 10 * v * 0.001, 1)
        
        s = random.choice([10, 20, 50, 100])
        p = round(g / (s * 0.0001), 1)
        
        f_lever = round(g / 5, 1)
        
        a_eq = random.choice([2, 3, 4, 5])
        b_eq = random.choice([3, 5, 7, 9])
        c_eq = a_eq * random.choice([1, 2, 3, 4]) + b_eq
        x_sol = (c_eq - b_eq) / a_eq
        cx = c_eq - b_eq
        ab = a_eq * random.choice([2, 3, 4])
        cx2 = c_eq + ab
        x2_sol = cx2 / a_eq
        
        b_quad = random.choice([2, 4, 6, 8])
        c_quad = random.choice([1, 2, 3, 4, 5])
        h = b_quad / 2
        k = h * h - b_quad * h + c_quad
        delta = b_quad * b_quad - 4 * c_quad
        ans_delta = '2 个' if delta > 0 else ('1 个' if delta == 0 else '0 个')
        judge = 'Δ>0，有两个交点' if delta > 0 else ('Δ=0，有一个交点' if delta == 0 else 'Δ<0，无交点')
        
        a_tri = random.choice([3, 5, 6, 8])
        b_tri = random.choice([4, 12, 8, 15])
        c2 = a_tri * a_tri + b_tri * b_tri
        c_tri = int(c2 ** 0.5)
        c2_alt = abs(b_tri * b_tri - a_tri * a_tri)
        c_alt = int(c2_alt ** 0.5) if c2_alt > 0 else 0
        
        angle_para = random.choice([60, 70, 110, 120])
        angle_b_para = 180 - angle_para
        ac_para = random.choice([10, 12, 16, 20])
        ao_para = ac_para / 2
        
        return {
            'f1': f1, 'f2': f2, 'f3': f3, 'diff': diff, 'result': result_force, 'dir': direction,
            'g': g, 'u': u, 'i': i, 'r': r, 'u1': u1, 'u2': u2, 'i1': i1, 'i2': i2,
            'v': v, 'f': f_buoy, 's': s, 'p': p, 'f_lever_val': f_lever, 'gl': g, 'gr': g // 2,
            'p_pow': random.choice([40, 60, 100, 1000]),
            'i_pow': round(random.choice([40, 60, 100]) / 220, 2),
            'r_pow': round(220 * 220 / random.choice([40, 60, 100]), 1),
            'a_eq_val': a_eq, 'b_eq_val': b_eq, 'c_eq_val': c_eq, 'x_eq': x_sol, 'cx': cx,
            'ab': ab, 'cx2': cx2, 'x2': x2_sol, 'a2': a_eq + 1, 'b2': b_eq + 2, 'c2': c_eq + 3,
            'b_quad_val': b_quad, 'c_quad_val': c_quad, 'h_quad': h, 'k_quad': k,
            'delta': delta, 'ans_delta': ans_delta, 'judge': judge, 'y1': k + 1, 'y2': k + 1,
            'a_tri_val': a_tri, 'b_tri_val': b_tri, 'c_tri_val': c_tri, 'c2_tri': c2,
            'c2_alt_tri': c2_alt, 'c_alt_tri': c_alt,
            'angle_para_val': angle_para, 'angle_b_para': angle_b_para,
            'ac_para_val': ac_para, 'ao_para_val': ao_para, 'bd_para_val': random.choice([8, 14, 18, 24]),
            'bo_para_val': random.choice([4, 7, 9, 12]),
            'num': random.choice([2, 3, 5, 10]),
        }
    
    def _fill_template(self, template: Dict[str, str], params: Dict[str, Any]) -> PracticeItem:
        """填充题目模板。
        
        Args:
            template: 题目模板字典
            params: 参数字典
        
        Returns:
            PracticeItem 实例
        
        Example:
            >>> service = PracticeService("张三")
            >>> params = service._generate_params()
            >>> template = {'question': '计算：{g}N', 'answer': '{g}', 'parse': '解析'}
            >>> item = service._fill_template(template, params)
            >>> isinstance(item, PracticeItem)
            True
        """
        def fmt(text: str) -> str:
            try:
                return text.format(**params)
            except KeyError:
                return text
        
        return PracticeItem(
            question=fmt(template.get('question', '')),
            answer=fmt(template.get('answer', '')),
            parse=fmt(template.get('parse', '')),
            options=fmt(template.get('options', '')) if 'options' in template else None,
            style=template.get('style', 'mixed'),
        )
    
    def generate_practice(
        self,
        knowledge_point: str,
        style: str = 'mixed',
        count: int = 3
    ) -> PracticeSet:
        """生成练习题集。
        
        根据指定的知识点、风格与数量生成练习题集。支持知识点别名映射，
        自动填充题目参数，确保每次生成题目具有随机性。
        
        Args:
            knowledge_point: 知识点名称（支持别名，如"欧姆"→"欧姆定律"）
            style: 练习风格，可选 '基础'、'变式'、'提升'、'mixed'（默认）
            count: 题目数量（默认 3）
        
        Returns:
            PracticeSet 实例，包含生成的练习题
        
        Raises:
            ValueError: 当知识点无可用模板时
        
        Example:
            >>> service = PracticeService("张三")
            >>> practice_set = service.generate_practice("欧姆定律", style="mixed", count=3)
            >>> isinstance(practice_set, PracticeSet)
            True
        """
        actual_kp = self._resolve_knowledge_point(knowledge_point)
        templates = PRACTICE_TEMPLATES.get(actual_kp)
        
        if not templates:
            # 返回空练习集（无可用模板）
            return PracticeSet(
                student=self.student_name,
                knowledge_point=knowledge_point,
                style=style,
                generated_at=datetime.now(),
                items=[]
            )
        
        # 收集所有可用题目
        all_templates: List[Dict[str, str]] = []
        if style == 'mixed':
            for s in ['基础', '变式', '提升']:
                all_templates.extend(templates.get(s, []))
        else:
            all_templates.extend(templates.get(style, []))
        
        if not all_templates:
            return PracticeSet(
                student=self.student_name,
                knowledge_point=knowledge_point,
                style=style,
                generated_at=datetime.now(),
                items=[]
            )
        
        # 随机选择题目
        selected = random.sample(all_templates, min(count, len(all_templates)))
        params = self._generate_params()
        
        items = [self._fill_template(t, params) for t in selected]
        
        return PracticeSet(
            student=self.student_name,
            knowledge_point=knowledge_point,
            style=style,
            generated_at=datetime.now(),
            items=items
        )
    
    def get_available_templates(self) -> List[str]:
        """获取所有可用的练习模板知识点列表。
        
        Returns:
            知识点名称列表（已去重排序）
        
        Example:
            >>> service = PracticeService("张三")
            >>> templates = service.get_available_templates()
            >>> isinstance(templates, list)
            True
            >>> len(templates) > 0
            True
        """
        return sorted(PRACTICE_TEMPLATES.keys())