#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM Expert Skill 测试脚本

用于验证 Skill 核心功能是否正常工作。

使用方法:
    python test_skill.py
"""

import os
import sys
from pathlib import Path

# 获取 Skill 根目录
SKILL_ROOT = Path(__file__).parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
SRC_DIR = SKILL_ROOT / "attachments" / "OpenFOAM" / "src"

# 添加脚本路径
sys.path.insert(0, str(SCRIPTS_DIR))


def test_version():
    """测试版本模块"""
    print("1. 测试版本模块...")
    try:
        from core.version import get_version_info, get_version_string
        info = get_version_info()
        print(f"   [OK] 版本: {info['skill_version']}")
        print(f"   [OK] OpenFOAM: {info['openfoam_version']}")
        print(f"   [OK] Skill Root: {info['skill_root']}")
        return True
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        return False


def test_code_accessor():
    """测试代码访问器"""
    print("\n2. 测试代码访问器...")
    try:
        from core.code_accessor import CodeAccessor, AccessMode
        accessor = CodeAccessor(access_mode=AccessMode.LOCAL)
        
        # 检查源码路径
        if os.path.exists(accessor.openfoam_src):
            print(f"   [OK] 源码路径: {accessor.openfoam_src}")
        else:
            print(f"   [WARN] 源码路径不存在: {accessor.openfoam_src}")
            print("   [INFO] 请确保 OpenFOAM 源码在 attachments/OpenFOAM/src/ 目录下")
        
        return True
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        return False


def test_router():
    """测试路由器"""
    print("\n3. 测试路由器...")
    try:
        from router import OpenFOAMRouter
        router = OpenFOAMRouter(enable_cache=True)
        
        # 测试版本命令
        result = router.execute("version", {})
        if result.get("success"):
            print("   [OK] 版本命令正常")
        else:
            print(f"   [WARN] 版本命令失败: {result.get('error')}")
        
        # 测试命令列表
        commands = router.list_commands()
        print(f"   [OK] 可用命令: {list(commands['commands'].keys())}")
        
        return True
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        return False


def test_analyzers():
    """测试分析器模块"""
    print("\n4. 测试分析器模块...")
    try:
        # 测试继承分析器
        from inheritance_analyzer import InheritanceAnalyzer
        print("   [OK] 继承分析器加载成功")
        
        # 测试边界分析器
        from boundary_analyzer import BoundaryAnalyzer
        print("   [OK] 边界分析器加载成功")
        
        # 测试模型分析器
        from model_analyzer import ModelAnalyzer
        print("   [OK] 模型分析器加载成功")
        
        return True
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        return False


def test_cache():
    """测试缓存模块"""
    print("\n5. 测试缓存模块...")
    try:
        from cache_manager import CacheManager
        cache = CacheManager()
        print(f"   [OK] 缓存目录: {cache.cache_dir}")
        return True
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        return False


def test_output_formatter():
    """测试输出格式化器"""
    print("\n6. 测试输出格式化器...")
    try:
        from output_formatter import OutputFormatter
        formatter = OutputFormatter()
        
        # 测试各种格式
        test_result = {"success": True, "test": "data"}
        json_out = formatter.format(test_result, "json")
        text_out = formatter.format(test_result, "text")
        ai_out = formatter.format(test_result, "ai")
        
        print("   [OK] JSON 格式正常")
        print("   [OK] Text 格式正常")
        print("   [OK] AI 格式正常")
        
        return True
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("  OpenFOAM Expert Skill - 功能测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("版本模块", test_version()))
    results.append(("代码访问器", test_code_accessor()))
    results.append(("路由器", test_router()))
    results.append(("分析器模块", test_analyzers()))
    results.append(("缓存模块", test_cache()))
    results.append(("输出格式化器", test_output_formatter()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {name}: {status}")
    
    print(f"\n  总计: {passed}/{total} 通过")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
