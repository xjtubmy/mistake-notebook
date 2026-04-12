#!/usr/bin/env python3
"""
举一反三练习生成脚本

用法:
    python3 generate-practice.py --student <学生名> --knowledge <知识点> [--count <数量>] [--style <风格>] [--md-only]

功能:
    - 基于错题知识点动态生成相似题
    - 每次生成不同的题目（避免固化）
    - 支持多种风格（基础/变式/提升）
    - 默认同时生成 Markdown 与同名的 PDF（Playwright）；可用 --md-only 跳过 PDF
"""

import argparse
import hashlib
import sys
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# 添加项目根目录到路径以支持 scripts 模块导入
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts import output_naming as out_names
from scripts.core.pdf_engine import PDFEngine

_pdf_engine = PDFEngine()


# 知识点→练习模板映射
PRACTICE_TEMPLATES = {
    # ========== 物理 ==========
    '力的合成': {
        '基础': [
            {
                'question': '一个物体在水平向右 {f1}N 的拉力作用下向右做匀速直线运动，若撤去拉力，在撤去瞬间物体受到的摩擦力大小为______N，方向向______。',
                'answer': '{f1}N，方向向左（与运动方向相反）',
                'parse': '匀速直线运动→摩擦力=拉力，方向与运动方向相反'
            },
            {
                'question': '用 {f1}N 的水平力推着一个重 {g}N 的木箱在水平地面上做匀速直线运动，木箱受到的摩擦力大小为______N。',
                'answer': '{f1}',
                'parse': '水平方向二力平衡：摩擦力=推力'
            },
        ],
        '变式': [
            {
                'question': '一个木块在水平桌面上向右做匀速直线运动，受到水平向右 {f1}N 的拉力。若突然将拉力增大到 {f2}N，此时木块受到的合力为______N，方向向______。',
                'answer': '{diff}N，方向向右',
                'parse': '合力 = 新拉力 - 摩擦力 = {f2} - {f1} = {diff}N'
            },
            {
                'question': '物体在水平拉力 F 作用下做匀速直线运动，若拉力突然变为 2F，则物体将做______运动（选填"加速"、"减速"或"匀速"）。',
                'answer': '加速',
                'parse': '拉力>摩擦力，合力向前，物体加速'
            },
        ],
        '提升': [
            {
                'question': '如图所示，物体 A 在水平拉力 F 作用下向左做匀速直线运动。若突然撤去拉力 F，同时在物体上施加一个水平向右的力 F\' = F，则撤去瞬间物体受到的合力大小为（ ）',
                'options': 'A. 0  B. F  C. 2F  D. 无法确定',
                'answer': 'C（2F）',
                'parse': '摩擦力 f = F（向右），外加力 F\' = F（向右），合力 = 2F'
            },
            {
                'question': '木块在水平桌面上运动，受到水平拉力 F1 = {f1}N 向左，摩擦力 f = {f2}N 向右。若再施加一个水平向右的力 F2 = {f3}N，则木块受到的合力为______N，方向向______。',
                'answer': '{result}N，方向向{dir}',
                'parse': '合力 = |F1 - (f + F2)|，方向由较大力决定'
            },
        ],
    },
    '牛顿第一定律': {
        '基础': [
            {
                'question': '一切物体在没有受到外力作用时，总保持______状态或______状态。',
                'answer': '静止；匀速直线运动',
                'parse': '牛顿第一定律的内容'
            },
            {
                'question': '惯性是物体保持原有______的性质，惯性的大小只与物体的______有关。',
                'answer': '运动状态；质量',
                'parse': '惯性是性质，不是力；质量是惯性大小的唯一量度'
            },
        ],
        '变式': [
            {
                'question': '关于惯性，下列说法正确的是（ ）',
                'options': 'A. 静止的物体没有惯性  B. 速度越大惯性越大  C. 质量越大惯性越大  D. 月球上没有惯性',
                'answer': 'C',
                'parse': '惯性是物体的固有属性，只与质量有关，与速度、位置无关'
            },
        ],
        '提升': [
            {
                'question': '踢出去的足球在地面上继续滚动，这是因为足球具有______；足球最终停下来，是因为受到______的作用。',
                'answer': '惯性；摩擦力（阻力）',
                'parse': '惯性使足球保持运动，阻力使足球减速'
            },
        ],
    },
    '欧姆定律': {
        '基础': [
            {
                'question': '一段导体两端电压为 {u}V 时，通过它的电流为 {i}A，则这段导体的电阻为______Ω。',
                'answer': '{r}Ω',
                'parse': '欧姆定律：R = U/I = {u}/{i} = {r}Ω'
            },
            {
                'question': '一个电阻为 {r}Ω 的导体，通过它的电流为 {i}A，则它两端的电压为______V。',
                'answer': '{u}V',
                'parse': '欧姆定律变形：U = I×R = {i}×{r} = {u}V'
            },
        ],
        '变式': [
            {
                'question': '某导体两端电压从 {u1}V 增大到 {u2}V 时，通过它的电流从 {i1}A 增大到______A。',
                'answer': '{i2}A',
                'parse': '电阻不变：R = {u1}/{i1} = {r}Ω，I₂ = U₂/R = {u2}/{r} = {i2}A'
            },
            {
                'question': '关于欧姆定律，下列说法正确的是（ ）',
                'options': 'A. 导体电阻与电压成正比  B. 导体电阻与电流成反比  C. 导体电阻由导体本身决定  D. 电压为零时电阻为零',
                'answer': 'C',
                'parse': '电阻是导体本身的性质，与电压、电流无关'
            },
        ],
        '提升': [
            {
                'question': '如图所示，电源电压保持不变，当滑动变阻器的滑片 P 向右移动时，电流表示数将______，电压表示数将______。（选填"变大"、"变小"或"不变"）',
                'answer': '变小；变小',
                'parse': '滑片右移→R 增大→I 减小→U=IR 减小'
            },
        ],
    },
    '浮力': {
        '基础': [
            {
                'question': '一个物体浸没在水中，排开水的体积为 {v}cm³，则它受到的浮力为______N。（ρ水=1.0×10³kg/m³，g=10N/kg）',
                'answer': '{f}N',
                'parse': '阿基米德原理：F浮 = ρ液gV排 = 1.0×10³×10×{v}×10⁻⁶ = {f}N'
            },
            {
                'question': '一个重 {g}N 的物体漂浮在水面上，它受到的浮力为______N。',
                'answer': '{g}N',
                'parse': '漂浮条件：F浮 = G = {g}N'
            },
        ],
        '变式': [
            {
                'question': '同一物体分别浸没在水和盐水中，受到的浮力较大的是______中。（选填"水"或"盐水"）',
                'answer': '盐水',
                'parse': 'V排相同，ρ盐水>ρ水，由 F浮=ρ液gV排可知，盐水中浮力更大'
            },
            {
                'question': '一个物体在水中悬浮，在盐水中将______。（选填"上浮"、"下沉"或"悬浮"）',
                'answer': '上浮',
                'parse': '悬浮时ρ物=ρ水，ρ盐水>ρ水，故ρ物<ρ盐水，物体上浮'
            },
        ],
        '提升': [
            {
                'question': '一个边长为 10cm 的正方体木块，密度为 0.6×10³kg/m³，放入水中静止时，露出水面的体积为______cm³。',
                'answer': '400',
                'parse': '漂浮：F浮=G，ρ水gV排=ρ木gV总，V排/V总=ρ木/ρ水=0.6，V露=0.4×1000=400cm³'
            },
        ],
    },
    '压强': {
        '基础': [
            {
                'question': '一个重 {g}N 的物体放在水平桌面上，与桌面的接触面积为 {s}cm²，则它对桌面的压强为______Pa。',
                'answer': '{p}Pa',
                'parse': 'p = F/S = {g}/({s}×10⁻⁴) = {p}Pa'
            },
            {
                'question': '液体压强公式为 p = ______，其中 h 表示______。',
                'answer': 'ρgh；深度',
                'parse': '液体压强公式：p = ρgh，h 是从液面到该点的竖直深度'
            },
        ],
        '变式': [
            {
                'question': '同一个物体分别正放和倒放在水平桌面上，对桌面的压力______，压强______。（选填"相等"或"不相等"）',
                'answer': '相等；不相等',
                'parse': '压力 F=G 不变，受力面积改变，故压强改变'
            },
        ],
        '提升': [
            {
                'question': '一个密闭容器中装满水，倒置后水对容器底部的压强______，压力______。（选填"变大"、"变小"或"不变"）',
                'answer': '不变；变小',
                'parse': '深度不变→压强不变；底面积变小→压力变小'
            },
        ],
    },
    '杠杆': {
        '基础': [
            {
                'question': '杠杆的平衡条件是：______×______ = ______×______。',
                'answer': '动力；动力臂；阻力；阻力臂',
                'parse': '杠杆平衡条件：F₁L₁ = F₂L₂'
            },
            {
                'question': '省力杠杆的动力臂______阻力臂，费力杠杆的动力臂______阻力臂。（选填"大于"或"小于"）',
                'answer': '大于；小于',
                'parse': 'L₁>L₂ 时省力，L₁<L₂ 时费力'
            },
        ],
        '变式': [
            {
                'question': '用撬棒撬石头，动力臂是阻力臂的 5 倍，若石头重 {g}N，则至少需要______N 的力才能撬动。',
                'answer': '{f}N',
                'parse': 'F₁L₁ = F₂L₂，F₁ = F₂×L₂/L₁ = {g}/5 = {f}N'
            },
        ],
        '提升': [
            {
                'question': '一个不均匀的杠杆，支点在中间，左端挂重 {gl}N 的物体，右端挂重 {gr}N 的物体时杠杆平衡。若将两端物体同时浸没在水中，杠杆将______。（选填"保持平衡"、"左端下沉"或"右端下沉"）',
                'answer': '保持平衡',
                'parse': '两物体受到浮力后，等效重力同比例减小，力矩比不变'
            },
        ],
    },
    '电功率': {
        '基础': [
            {
                'question': '一个标有"220V {p}W"的灯泡，正常工作时的电流为______A，电阻为______Ω。',
                'answer': '{i}A；{r}Ω',
                'parse': 'I = P/U = {p}/220 = {i}A，R = U²/P = 220²/{p} = {r}Ω'
            },
            {
                'question': '电功率的计算公式有 P = ______ = ______ = ______。',
                'answer': 'W/t；UI；I²R',
                'parse': '电功率基本公式及变形'
            },
        ],
        '变式': [
            {
                'question': '两个灯泡 L₁"220V 40W"和 L₂"220V 100W"串联在 220V 电路中，更亮的是______。',
                'answer': 'L₁',
                'parse': '串联 I 相同，P=I²R，R₁>R₂，故 L₁ 实际功率更大、更亮'
            },
        ],
        '提升': [
            {
                'question': '一个电热水壶标有"220V 1000W"，若实际电压为 200V，则实际功率为______W。（保留整数）',
                'answer': '826',
                'parse': 'R = U额²/P额 = 220²/1000 = 48.4Ω，P实 = U实²/R = 200²/48.4 ≈ 826W'
            },
        ],
    },
    
    # ========== 数学 ==========
    '一元一次方程': {
        '基础': [
            {
                'question': '解方程：{a_eq_val}x + {b_eq_val} = {c_eq_val}',
                'answer': 'x = {x_eq}',
                'parse': '移项：{a_eq_val}x = {c_eq_val}-{b_eq_val} = {cx}，系数化为 1：x = {cx}/{a_eq_val} = {x_eq}'
            },
            {
                'question': '若 x = {x_eq} 是方程 {a_eq_val}x - {b_eq_val} = {c_eq_val} 的解，则 {a_eq_val}×{x_eq} - {b_eq_val} = ______。',
                'answer': '{c_eq_val}',
                'parse': '将 x = {x_eq} 代入方程左边：{a_eq_val}×{x_eq} - {b_eq_val} = {c_eq_val}'
            },
        ],
        '变式': [
            {
                'question': '解方程：{a_eq_val}(x - {b_eq_val}) = {c_eq_val}',
                'answer': 'x = {x2}',
                'parse': '去括号：{a_eq_val}x - {ab} = {c_eq_val}，移项：{a_eq_val}x = {c_eq_val}+{ab} = {cx2}，x = {x2}'
            },
            {
                'question': '关于 x 的方程 {a_eq_val}x + {b_eq_val} = {c_eq_val} 的解是正数，则 b 的取值范围是______。',
                'answer': 'b < {c_eq_val}',
                'parse': 'x = ({c_eq_val}-{b_eq_val})/{a_eq_val} > 0，因{a_eq_val}>0，故{c_eq_val}-{b_eq_val}>0，即{b_eq_val} < {c_eq_val}'
            },
        ],
        '提升': [
            {
                'question': '已知关于 x 的方程 {a_eq_val}x + {b_eq_val} = {c_eq_val} 的解比关于 x 的方程 {a2}x + {b2} = {c2} 的解大 2，则 m = ______。',
                'answer': '需具体计算',
                'parse': '分别解出两个方程的解，根据差值为 2 列方程求解'
            },
        ],
    },
    '二次函数': {
        '基础': [
            {
                'question': '二次函数 y = x² - {b_quad_val}x + {c_quad_val} 的顶点坐标为______。',
                'answer': '({h_quad}, {k_quad})',
                'parse': '顶点公式：x = -b/(2a) = {b_quad_val}/2 = {h_quad}，代入得 y = {k_quad}'
            },
            {
                'question': '抛物线 y = ax² + bx + c 的开口方向由______决定，当 a > 0 时开口向______。',
                'answer': 'a；上',
                'parse': 'a>0 开口向上，a<0 开口向下'
            },
        ],
        '变式': [
            {
                'question': '将抛物线 y = x² 向右平移 {h_quad} 个单位，再向上平移 {k_quad} 个单位，所得抛物线的解析式为______。',
                'answer': 'y = (x-{h_quad})² + {k_quad}',
                'parse': '平移规律：左加右减，上加下减'
            },
            {
                'question': '抛物线 y = x² - {b_quad_val}x + {c_quad_val} 与 x 轴的交点个数为______。',
                'answer': '{ans_delta}',
                'parse': 'Δ = b²-4ac = {b_quad_val}²-4×1×{c_quad_val} = {delta}，{judge}'
            },
        ],
        '提升': [
            {
                'question': '已知抛物线 y = ax² + bx + c 经过点 (1, {y1}) 和 (-1, {y2})，且对称轴为直线 x = {h_quad}，则 a = ______。',
                'answer': '需具体计算',
                'parse': '代入两点坐标，结合对称轴公式 x=-b/(2a) 联立求解'
            },
        ],
    },
    '勾股定理': {
        '基础': [
            {
                'question': '在 Rt△ABC 中，∠C=90°，若 a={a_tri_val}, b={b_tri_val}，则斜边 c = ______。',
                'answer': '{c_tri_val}',
                'parse': '勾股定理：c = √(a²+b²) = √({a_tri_val}²+{b_tri_val}²) = √{c2_tri} = {c_tri_val}'
            },
            {
                'question': '勾股定理的内容是：直角三角形两直角边的______等于斜边的______。',
                'answer': '平方和；平方',
                'parse': '勾股定理：a² + b² = c²'
            },
        ],
        '变式': [
            {
                'question': '一个直角三角形的两条边长分别为 {a_tri_val} 和 {b_tri_val}，则第三边长为______。',
                'answer': '{c_tri_val} 或 {c_alt_tri}',
                'parse': '需分类讨论：{a_tri_val} 和 {b_tri_val} 可能都是直角边，也可能{b_tri_val}是斜边'
            },
            {
                'question': '下列各组数中，能作为直角三角形三边长的是（ ）',
                'options': 'A. 3,4,6  B. 5,12,13  C. 6,8,11  D. 7,9,12',
                'answer': 'B',
                'parse': '验证：5²+12²=25+144=169=13²，符合勾股定理'
            },
        ],
        '提升': [
            {
                'question': '如图，折叠矩形 ABCD，使点 B 落在 AD 边上的点 F 处，若 AB={a_tri_val}, BC={b_tri_val}，则折痕 AE 的长为______。',
                'answer': '需具体计算',
                'parse': '设 BE=x，则 EF=x，AF={b_tri_val}-x，在 Rt△AEF 中用勾股定理列方程'
            },
        ],
    },
    '三角形全等': {
        '基础': [
            {
                'question': '判定两个三角形全等的方法有：______、______、______、______。',
                'answer': 'SSS；SAS；ASA；AAS',
                'parse': '全等三角形判定：SSS、SAS、ASA、AAS，直角三角形还有 HL'
            },
            {
                'question': '已知△ABC≌△DEF，若 AB={a_tri_val}cm，则 DE = ______cm。',
                'answer': '{a_tri_val}',
                'parse': '全等三角形对应边相等'
            },
        ],
        '变式': [
            {
                'question': '如图，已知 AB=AC，要使△ABD≌△ACD，还需添加的条件是______。（写出一个即可）',
                'answer': 'BD=CD 或∠BAD=∠CAD 或 AD⊥BC',
                'parse': '可用 SSS、SAS 或 ASA 判定'
            },
        ],
        '提升': [
            {
                'question': '如图，在△ABC 中，AB=AC，D、E 分别在 AB、AC 上，且 AD=AE，BE 与 CD 相交于点 F。求证：BF=CF。',
                'answer': '证明见解析',
                'parse': '先证△ABE≌△ACD(SAS)，得∠B=∠C，再证△BDF≌△CEF(AAS)'
            },
        ],
    },
    '平行四边形': {
        '基础': [
            {
                'question': '平行四边形的对边______，对角______。',
                'answer': '相等；相等',
                'parse': '平行四边形性质：对边平行且相等，对角相等'
            },
            {
                'question': '在□ABCD 中，若∠A = {angle_para_val}°，则∠B = ______°，∠C = ______°。',
                'answer': '{angle_b_para}；{angle_para_val}',
                'parse': '平行四边形邻角互补，对角相等'
            },
        ],
        '变式': [
            {
                'question': '在□ABCD 中，对角线 AC、BD 相交于点 O，若 AC={ac_para_val}, BD={bd_para_val}，则 AO = ______，BO = ______。',
                'answer': '{ao_para_val}; {bo_para_val}',
                'parse': '平行四边形对角线互相平分'
            },
        ],
        '提升': [
            {
                'question': '如图，在□ABCD 中，E、F 分别是 AB、CD 的中点，连接 AF、CE。求证：四边形 AECF 是平行四边形。',
                'answer': '证明见解析',
                'parse': '证 AE∥CF 且 AE=CF 即可'
            },
        ],
    },
    
    # ========== 英语 ==========
    '现在完成时': {
        '基础': [
            {
                'question': 'I ______ (live) here for {num} years.',
                'answer': 'have lived',
                'parse': 'for+时间段，用现在完成时'
            },
            {
                'question': 'She ______ (finish) her homework already.',
                'answer': 'has finished',
                'parse': 'already 是现在完成时的标志词，主语 she 用 has'
            },
        ],
        '变式': [
            {
                'question': '—______ you ever ______ to Beijing? —Yes, I ______ there last year.',
                'answer': 'Have; been; went',
                'parse': '第一空问经历用现在完成时，第二空有 last year 用一般过去时'
            },
            {
                'question': 'He ______ (be) to Shanghai twice, but he ______ (not visit) the Bund yet.',
                'answer': 'has been; hasn\'t visited',
                'parse': 'twice 表经历用完成时，yet 用于否定句'
            },
        ],
        '提升': [
            {
                'question': 'My father ______ (go) to Beijing on business. He ______ (be) back in two days.',
                'answer': 'has gone; will be',
                'parse': 'has gone 表示去了未回，in two days 用一般将来时'
            },
        ],
    },
    '一般过去时': {
        '基础': [
            {
                'question': 'I ______ (go) to the cinema yesterday.',
                'answer': 'went',
                'parse': 'yesterday 是一般过去时的标志词'
            },
            {
                'question': 'She ______ (not do) her homework last night.',
                'answer': 'didn\'t do',
                'parse': 'last night 用一般过去时，否定用 didn\'t + 动词原形'
            },
        ],
        '变式': [
            {
                'question': '—When ______ you ______ (buy) this book? —I ______ (buy) it last week.',
                'answer': 'did; buy; bought',
                'parse': 'last week 用一般过去时，疑问句用 did 提问'
            },
        ],
        '提升': [
            {
                'question': 'While I ______ (walk) in the park, it ______ (begin) to rain.',
                'answer': 'was walking; began',
                'parse': 'while 引导过去进行时，主句用一般过去时表示突然发生的动作'
            },
        ],
    },
    '定语从句': {
        '基础': [
            {
                'question': 'The man ______ is talking to our teacher is my father.',
                'answer': 'who/that',
                'parse': '先行词是人，在从句中作主语，用 who 或 that'
            },
            {
                'question': 'This is the book ______ I bought yesterday.',
                'answer': 'which/that',
                'parse': '先行词是物，在从句中作宾语，用 which 或 that'
            },
        ],
        '变式': [
            {
                'question': 'I still remember the day ______ we first met.',
                'answer': 'when/on which',
                'parse': '先行词是时间，在从句中作时间状语，用 when'
            },
            {
                'question': 'This is the house ______ Lu Xun once lived.',
                'answer': 'where/in which',
                'parse': '先行词是地点，在从句中作地点状语，用 where'
            },
        ],
        '提升': [
            {
                'question': 'The boy ______ parents are dead was brought up by his grandmother.',
                'answer': 'whose',
                'parse': '先行词与 parents 是所属关系，用 whose'
            },
        ],
    },
    '被动语态': {
        '基础': [
            {
                'question': 'English ______ (speak) all over the world.',
                'answer': 'is spoken',
                'parse': '一般现在时被动：am/is/are + 过去分词'
            },
            {
                'question': 'The book ______ (write) by Lu Xun in 1921.',
                'answer': 'was written',
                'parse': '一般过去时被动：was/were + 过去分词'
            },
        ],
        '变式': [
            {
                'question': 'A new hospital ______ (build) in our town next year.',
                'answer': 'will be built',
                'parse': '一般将来时被动：will be + 过去分词'
            },
            {
                'question': 'The flowers ______ (water) every day.',
                'answer': 'are watered',
                'parse': 'every day 一般现在时，flowers 复数用 are'
            },
        ],
        '提升': [
            {
                'question': 'The old man ______ (see) to enter the building at about 9 p.m.',
                'answer': 'was seen',
                'parse': 'see sb do 变被动要加 to：sb be seen to do'
            },
        ],
    },
    
    # ========== 化学 ==========
    '化学方程式': {
        '基础': [
            {
                'question': '写出氢气燃烧的化学方程式：______',
                'answer': '2H₂ + O₂ → 2H₂O',
                'parse': '氢气与氧气在点燃条件下生成水'
            },
            {
                'question': '配平化学方程式：Fe + O₂ → Fe₃O₄',
                'answer': '3Fe + 2O₂ → Fe₃O₄',
                'parse': '用观察法或最小公倍数法配平'
            },
        ],
        '变式': [
            {
                'question': '写出实验室用过氧化氢制取氧气的化学方程式：______',
                'answer': '2H₂O₂ → 2H₂O + O₂↑',
                'parse': 'MnO₂作催化剂'
            },
        ],
        '提升': [
            {
                'question': '某金属 R 与稀盐酸反应生成 RCl₃和氢气，写出该反应的化学方程式：______',
                'answer': '2R + 6HCl → 2RCl₃ + 3H₂↑',
                'parse': '根据产物 RCl₃可知 R 显 +3 价'
            },
        ],
    },
}

# 知识点别名映射（支持多种叫法）
KNOWLEDGE_ALIASES = {
    # 物理
    '欧姆': '欧姆定律',
    '欧姆定律': '欧姆定律',
    '浮力': '浮力',
    '压强': '压强',
    '杠杆': '杠杆',
    '电功率': '电功率',
    '力的合成': '力的合成',
    '牛顿第一定律': '牛顿第一定律',
    '惯性': '牛顿第一定律',
    # 数学
    '一元一次方程': '一元一次方程',
    '方程': '一元一次方程',
    '二次函数': '二次函数',
    '抛物线': '二次函数',
    '勾股定理': '勾股定理',
    '三角形全等': '三角形全等',
    '全等三角形': '三角形全等',
    '平行四边形': '平行四边形',
    # 英语
    '现在完成时': '现在完成时',
    '完成时': '现在完成时',
    '一般过去时': '一般过去时',
    '过去时': '一般过去时',
    '定语从句': '定语从句',
    '从句': '定语从句',
    '被动语态': '被动语态',
    '被动': '被动语态',
    # 化学
    '化学方程式': '化学方程式',
    '方程式': '化学方程式',
}


def generate_practice(knowledge_point: str, style: str = '混合', count: int = 3, difficulty: Optional[Tuple[int, int]] = None) -> list:
    """生成练习题
    
    Args:
        knowledge_point: 知识点名称
        style: 练习风格（基础/变式/提升/混合）
        count: 题目数量
        difficulty: 难度范围 (min, max)，例如 (1, 2) 简单，(4, 5) 困难
    """
    # 支持知识点别名
    actual_knowledge = KNOWLEDGE_ALIASES.get(knowledge_point, knowledge_point)
    templates = PRACTICE_TEMPLATES.get(actual_knowledge, None)
    
    if not templates:
        # 通用模板（如果没有特定知识点模板）
        return generate_generic_practice(style, count)
    
    # 收集所有可用题目
    all_practices = []
    if style == '混合':
        for s in ['基础', '变式', '提升']:
            all_practices.extend(templates.get(s, []))
    else:
        all_practices.extend(templates.get(style, []))
    
    # 根据难度筛选
    if difficulty is not None:
        min_diff, max_diff = difficulty
        difficulty_map = {'基础': (1, 2), '变式': (3, 3), '提升': (4, 5)}
        filtered = []
        for s in ['基础', '变式', '提升']:
            style_diff = difficulty_map.get(s, (3, 3))
            # 检查风格难度范围是否与请求的难度范围有交集
            if min_diff <= style_diff[1] and max_diff >= style_diff[0]:
                filtered.extend(templates.get(s, []))
        if filtered:
            all_practices = filtered
        # 如果筛选后为空，回退到原始列表
    
    # 随机选择题目（带去重，带风格标记）
    seen_hashes = set()
    practices_with_style = []  # (template, style)
    max_attempts = count * 3
    attempts = 0
    
    # 构建带风格的模板列表
    templated_with_style = []
    if style == '混合':
        for s in ['基础', '变式', '提升']:
            for t in templates.get(s, []):
                templated_with_style.append((t, s))
    else:
        for t in templates.get(style, []):
            templated_with_style.append((t, style))
    
    # 根据难度筛选
    if difficulty is not None:
        min_diff, max_diff = difficulty
        difficulty_map = {'基础': (1, 2), '变式': (3, 3), '提升': (4, 5)}
        filtered = []
        for t, t_style in templated_with_style:
            style_diff = difficulty_map.get(t_style, (3, 3))
            if min_diff <= style_diff[1] and max_diff >= style_diff[0]:
                filtered.append((t, t_style))
        if filtered:
            templated_with_style = filtered
    
    while len(practices_with_style) < count and attempts < max_attempts and templated_with_style:
        attempts += 1
        p, p_style = random.choice(templated_with_style)
        # 简单去重：基于题目模板
        template_key = p.get('question', '')[:50]
        if template_key not in seen_hashes:
            seen_hashes.add(template_key)
            practices_with_style.append((p, p_style))
    
    # 填充参数（随机生成数值）
    result = []
    for p, p_style in practices_with_style:
        practice = p.copy()
        
        # 物理 - 力学参数
        f1 = random.choice([5, 10, 15, 20, 25, 30])
        f2 = f1 + random.choice([5, 10, 15])
        f3 = random.choice([5, 10, 15])
        diff = f2 - f1
        result_force = abs(f1 - (f2 + f3))
        direction = '右' if (f2 + f3) > f1 else '左'
        g_weight = random.choice([50, 100, 150, 200])
        
        # 物理 - 电学参数
        u = random.choice([3, 6, 9, 12, 220])
        i = random.choice([0.1, 0.2, 0.3, 0.5, 1, 2])
        r = round(u / i, 1) if i > 0 else 10
        u1 = u
        u2 = u + random.choice([3, 6, 9])
        i1 = i
        i2 = round(u2 / r, 2)
        
        # 物理 - 浮力参数
        v = random.choice([100, 200, 300, 500])
        f_buoyancy = round(1.0 * 10 * v * 0.001, 1)
        
        # 物理 - 压强参数
        s_area = random.choice([10, 20, 50, 100])
        p_pressure = round(g_weight / (s_area * 0.0001), 1)
        
        # 物理 - 杠杆参数
        f_lever = round(g_weight / 5, 1)
        
        # 数学 - 方程参数
        a_eq = random.choice([2, 3, 4, 5])
        b_eq = random.choice([3, 5, 7, 9])
        c_eq = a_eq * random.choice([1, 2, 3, 4]) + b_eq
        x_sol = (c_eq - b_eq) / a_eq
        cx = c_eq - b_eq
        ab = a_eq * random.choice([2, 3, 4])
        cx2 = c_eq + ab
        x2_sol = cx2 / a_eq
        
        # 数学 - 二次函数参数
        b_quad = random.choice([2, 4, 6, 8])
        c_quad = random.choice([1, 2, 3, 4, 5])
        h = b_quad / 2
        k = h * h - b_quad * h + c_quad
        delta = b_quad * b_quad - 4 * c_quad
        ans_delta = '2 个' if delta > 0 else ('1 个' if delta == 0 else '0 个')
        judge = 'Δ>0，有两个交点' if delta > 0 else ('Δ=0，有一个交点' if delta == 0 else 'Δ<0，无交点')
        
        # 数学 - 勾股定理参数
        a_tri = random.choice([3, 5, 6, 8])
        b_tri = random.choice([4, 12, 8, 15])
        c2 = a_tri * a_tri + b_tri * b_tri
        c_tri = int(c2 ** 0.5)
        c2_alt = abs(b_tri * b_tri - a_tri * a_tri)
        c_alt = int(c2_alt ** 0.5) if c2_alt > 0 else 0
        
        # 数学 - 平行四边形参数
        angle_para = random.choice([60, 70, 110, 120])
        angle_b_para = 180 - angle_para
        ac_para = random.choice([10, 12, 16, 20])
        bd_para = random.choice([8, 14, 18, 24])
        ao_para = ac_para / 2
        bo_para = bd_para / 2
        
        # 替换模板中的占位符
        for key in ['question', 'answer', 'parse', 'options']:
            if key in practice:
                practice[key] = practice[key].format(
                    # 力学
                    f1=f1, f2=f2, f3=f3, diff=diff, 
                    result=result_force, dir=direction,
                    g=g_weight,
                    # 电学
                    u=u, i=i, r=r, u1=u1, u2=u2, i1=i1, i2=i2,
                    # 浮力
                    v=v, f_buoy=f_buoyancy,
                    # 压强
                    s=s_area, p_val=p_pressure,
                    # 杠杆
                    f_lever_val=f_lever, gl=g_weight, gr=g_weight//2,
                    # 电功率
                    p_pow=random.choice([40, 60, 100, 1000]),
                    i_pow=round(random.choice([40, 60, 100])/220, 2),
                    r_pow=round(220*220/random.choice([40, 60, 100]), 1),
                    # 数学 - 方程
                    a_eq_val=a_eq, b_eq_val=b_eq, c_eq_val=c_eq, x_eq=x_sol, cx=cx,
                    ab=ab, cx2=cx2, x2=x2_sol,
                    a2=a_eq+1, b2=b_eq+2, c2=c_eq+3,
                    # 数学 - 二次函数
                    b_quad_val=b_quad, c_quad_val=c_quad, h_quad=h, k_quad=k,
                    delta=delta, ans_delta=ans_delta, judge=judge,
                    # 数学 - 勾股定理
                    a_tri_val=a_tri, b_tri_val=b_tri, c_tri_val=c_tri, 
                    c2_tri=c2, c2_alt_tri=c2_alt, c_alt_tri=c_alt,
                    # 数学 - 平行四边形
                    angle_para_val=angle_para, angle_b_para=angle_b_para,
                    ac_para_val=ac_para, bd_para_val=bd_para, ao_para_val=ao_para, bo_para_val=bo_para,
                    # 英语 - 通用
                    num=random.choice([2, 3, 5, 10]),
                )
        
        # 添加难度标记（根据风格）
        difficulty_map = {'基础': random.randint(1, 2), '变式': 3, '提升': random.randint(4, 5), '混合': 3}
        practice['difficulty'] = difficulty_map.get(p_style, 3)
        practice['style'] = p_style
        
        # 计算题目 hash（用于去重）
        q = practice.get('question', '')
        a = practice.get('answer', '')
        pa = practice.get('parse', '')
        practice['hash'] = hashlib.md5(f"{q}|{a}|{pa}".encode('utf-8')).hexdigest()[:12]
        
        result.append(practice)
    
    return result


def generate_generic_practice(style: str, count: int) -> list:
    """生成通用练习题"""
    return [
        {
            'question': f'【{style}题】请回顾本知识点的核心概念，并完成相关练习。',
            'answer': '参见教材',
            'parse': '建议复习课本相关内容'
        }
    ] * count


def build_practice_markdown(practices: list, student: str, knowledge_point: str) -> str:
    """组装练习 Markdown 正文。"""
    # 计算平均难度
    avg_diff = sum(p.get('difficulty', 3) for p in practices) / len(practices) if practices else 0
    
    content = f"""# 📝 举一反三练习

**学生**：{student}  
**知识点**：{knowledge_point}  
**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}  
**题目数量**：{len(practices)} 道  
**平均难度**：{'⭐' * round(avg_diff)} ({avg_diff:.1f}/5)

---

## 练习题

"""

    for i, p in enumerate(practices, 1):
        diff = p.get('difficulty', 3)
        content += f"""### 第 {i} 题 {'⭐' * diff}

{p['question']}

"""
        if 'options' in p:
            content += f"{p['options']}\n\n"

        content += f"""<details>
<summary>点击查看答案与解析</summary>

**答案**：{p['answer']}

**解析**：{p['parse']}

</details>

---

"""

    content += f"""
## 📊 练习记录

| 日期 | 正确率 | 用时 | 签名 |
|------|--------|------|------|
| {datetime.now().strftime('%Y-%m-%d')} | /{len(practices)} | | |

---

## 💡 使用建议

1. **独立完成后对答案**：不要边做边看答案
2. **错题标记**：做错的题目标记出来，重点复习
3. **定期重做**：同一份练习可以间隔一周重做

---

*本练习由 mistake-notebook 动态生成 · 每次生成题目可能不同*
"""
    return content


def save_practice_md(content: str, output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(content, encoding='utf-8')
    print(f"已生成练习 Markdown：{output_path}")


def parse_difficulty(diff_str: str) -> Optional[Tuple[int, int]]:
    """解析难度参数，支持格式：'3' 或 '1-3' 或 '1,3'"""
    if not diff_str:
        return None
    if '-' in diff_str:
        parts = diff_str.split('-')
        return (int(parts[0]), int(parts[1]))
    elif ',' in diff_str:
        parts = diff_str.split(',')
        return (int(parts[0]), int(parts[1]))
    else:
        d = int(diff_str)
        return (d, d)


def main():
    parser = argparse.ArgumentParser(description='举一反三练习生成')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--knowledge', required=True, help='知识点')
    parser.add_argument('--count', type=int, default=3, help='题目数量（默认 3）')
    parser.add_argument('--style', choices=['基础', '变式', '提升', '混合'], default='混合', help='题目风格')
    parser.add_argument('--difficulty', type=str, help='难度范围：1-5 或范围如 1-3（1 最简单，5 最难）')
    parser.add_argument('--output', help='Markdown 输出路径（可选）；PDF 为同路径 .pdf')
    parser.add_argument(
        '--md-only',
        action='store_true',
        help='只生成 Markdown，不导出 PDF',
    )
    
    args = parser.parse_args()
    
    difficulty = parse_difficulty(args.difficulty) if args.difficulty else None
    diff_info = f"难度:{args.difficulty}" if difficulty else "难度：全部"
    
    print(f"正在为 {args.student} 生成《{args.knowledge}》练习题...")
    print(f"风格：{args.style} | 数量：{args.count} | {diff_info}")
    
    practices = generate_practice(args.knowledge, args.style, args.count, difficulty)
    
    if args.output:
        md_path = args.output
    else:
        md_path = str(out_names.default_practice_path(args.student, args.knowledge))

    content = build_practice_markdown(practices, args.student, args.knowledge)
    save_practice_md(content, md_path)
    md_p = Path(md_path)

    if args.md_only:
        out_names.print_output_path(md_p)
    else:
        out_names.print_output_path(md_p, "OUTPUT_PATH_MD")
        pdf_path = md_p.with_suffix(".pdf")
        try:
            html = _pdf_engine.printable_html_from_markdown(content)
            _pdf_engine.html_to_pdf(html, pdf_path)
        except Exception as e:
            print(f"⚠️ PDF 未生成（已保留 Markdown）: {e}")
            out_names.print_output_path(md_p)


if __name__ == '__main__':
    main()
