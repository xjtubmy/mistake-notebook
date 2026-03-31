#!/usr/bin/env python3
"""
依赖检查脚本

用法:
    python3 check-deps.py

功能:
    检查所有依赖是否已安装，并给出安装建议
"""

import sys
import subprocess
from pathlib import Path


def check_python_package(name: str) -> bool:
    """检查 Python 包是否已安装"""
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def check_system_command(cmd: str) -> bool:
    """检查系统命令是否可用"""
    try:
        subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
        return True
    except:
        return False


def check_playwright_browser() -> bool:
    """检查 Playwright 浏览器是否已安装"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # 尝试启动浏览器
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except:
        return False


def main():
    print("=" * 60)
    print("🔍 mistake-notebook 依赖检查")
    print("=" * 60)
    print()
    
    # Python 依赖
    print("📦 Python 依赖:")
    print("-" * 40)
    
    deps_status = {}
    
    # playwright
    if check_python_package('playwright'):
        print(f"✅ playwright: 已安装")
        deps_status['playwright'] = True
    else:
        print(f"❌ playwright: 未安装")
        deps_status['playwright'] = False
    
    # markdown2
    if check_python_package('markdown2'):
        print(f"✅ markdown2: 已安装")
        deps_status['markdown2'] = True
    else:
        print(f"❌ markdown2: 未安装")
        deps_status['markdown2'] = False
    
    # pdfkit（已废弃，仅提示）
    if check_python_package('pdfkit'):
        print(f"⚪ pdfkit: 已安装 (已废弃，不再需要)")
    else:
        print(f"⚪ pdfkit: 不需要 (已改用 playwright)")
    
    print()
    
    # 浏览器
    print("🌐 浏览器:")
    print("-" * 40)
    
    if deps_status.get('playwright', False):
        if check_playwright_browser():
            print(f"✅ chromium: 已安装")
            deps_status['chromium'] = True
        else:
            print(f"❌ chromium: 未安装")
            deps_status['chromium'] = False
    else:
        print(f"⚪ chromium: 跳过检查（playwright 未安装）")
        deps_status['chromium'] = None
    
    print()
    
    print()
    
    # 总结和建议
    print("=" * 60)
    print("📊 检查结果总结")
    print("=" * 60)
    print()
    
    # 核心功能检查
    core_ok = deps_status.get('playwright', False) and deps_status.get('markdown2', False) and deps_status.get('chromium', False)
    
    if core_ok:
        print("✅ 所有功能可用：")
        print("   • 录入错题")
        print("   • 自动分类")
        print("   • 分析报告")
        print("   • 复习提醒")
        print("   • 错题检索")
        print("   • 长图分享")
        print("   • PDF 打印")
    else:
        print("❌ 核心功能不可用，缺少依赖")
    
    print()
    
    # 安装建议
    missing_deps = [k for k, v in deps_status.items() if v == False]
    
    if missing_deps:
        print("🔧 安装建议:")
        print("-" * 40)
        
        if 'playwright' in missing_deps or 'markdown2' in missing_deps:
            print("\n1️⃣  安装 Python 依赖:")
            print("   pip install playwright markdown2 --break-system-packages")
        
        if deps_status.get('playwright', False) and 'chromium' in missing_deps:
            print("\n2️⃣  安装浏览器:")
            print("   playwright install chromium")
        
        print("\n💡 提示：所有功能仅需 playwright + markdown2，无需系统依赖！")
        print()
    else:
        print("✅ 所有依赖已安装，可以开始使用！")
    
    print()
    print("=" * 60)
    
    # 返回状态码
    if core_ok:
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
