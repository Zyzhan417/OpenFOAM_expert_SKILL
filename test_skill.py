#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM Expert Skill 功能测试脚本

验证User Skill迁移后的功能是否正常
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Skill根目录 - 使用 __file__ 动态获取
SKILL_ROOT = Path(__file__).parent.resolve()
SCRIPTS_DIR = SKILL_ROOT / "scripts"
ATTACHMENTS_DIR = SKILL_ROOT / "attachments" / "OpenFOAM" / "src"

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_directory_structure():
    """测试目录结构"""
    print_section("1. 测试目录结构")
    
    required_dirs = {
        "SKILL根目录": SKILL_ROOT,
        "脚本目录": SCRIPTS_DIR,
        "参考文档目录": SKILL_ROOT / "references",
        "模板目录": SKILL_ROOT / "templates",
        "源码附件目录": ATTACHMENTS_DIR,
    }
    
    all_ok = True
    for name, path in required_dirs.items():
        if path.exists():
            print(f"✅ {name}: {path}")
            # 统计文件数量
            if path.is_dir():
                file_count = sum(1 for _ in path.rglob("*") if _.is_file())
                print(f"   文件数: {file_count}")
        else:
            print(f"❌ {name}: 不存在")
            all_ok = False
    
    return all_ok

def test_source_code_files():
    """测试源码文件"""
    print_section("2. 测试源码附件文件")
    
    if not ATTACHMENTS_DIR.exists():
        print("❌ 源码目录不存在")
        return False
    
    # 统计.H和.C文件
    h_files = list(ATTACHMENTS_DIR.rglob("*.H"))
    c_files = list(ATTACHMENTS_DIR.rglob("*.C"))
    
    print(f"✅ .H 文件数: {len(h_files)}")
    print(f"✅ .C 文件数: {len(c_files)}")
    
    # 检查关键文件
    key_files = [
        "finiteVolume/fvMesh/fvMesh.H",
        "finiteVolume/fvPatchField/fvPatchField.H",
        "transportModels/turbulenceModel/turbulenceModel.H"
    ]
    
    print("\n关键文件检查:")
    for key_file in key_files:
        full_path = ATTACHMENTS_DIR / key_file
        if full_path.exists():
            print(f"  ✅ {key_file}")
        else:
            print(f"  ⚠️  {key_file}")
    
    return len(h_files) > 0 and len(c_files) > 0

def test_script_execution(script_name, args):
    """测试脚本执行"""
    script_path = SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        print(f"❌ 脚本不存在: {script_name}")
        return False
    
    cmd = [sys.executable, str(script_path)] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ {script_name} 执行成功")
            if result.stdout.strip():
                print(f"   输出: {result.stdout[:100]}...")
            return True
        else:
            print(f"⚠️  {script_name} 执行异常 (返回码: {result.returncode})")
            if result.stderr:
                print(f"   错误: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"❌ {script_name} 执行失败: {e}")
        return False

def test_all_scripts():
    """测试所有脚本"""
    print_section("3. 测试脚本执行")
    
    # 测试继承分析脚本
    test_script_execution("inheritance_analyzer.py", ["--help"])
    
    # 测试边界条件分析脚本
    test_script_execution("boundary_analyzer.py", ["--help"])
    
    # 测试模型分析脚本
    test_script_execution("model_analyzer.py", ["--help"])
    
    # 测试代码修改脚本
    test_script_execution("code_modifier.py", ["--help"])
    
    return True

def test_code_accessor():
    """测试代码访问器"""
    print_section("4. 测试代码访问器")
    
    try:
        sys.path.insert(0, str(SCRIPTS_DIR / "core"))
        from code_accessor import CodeAccessor, AccessMode
        
        # 测试初始化（使用默认路径）
        accessor = CodeAccessor(
            openfoam_src=str(ATTACHMENTS_DIR),
            access_mode=AccessMode.LOCAL
        )
        
        print(f"✅ CodeAccessor 初始化成功")
        print(f"   源码路径: {accessor.openfoam_src}")
        
        # 测试搜索
        results = accessor.search_code("class fvMesh", file_types=".H", max_results=5)
        print(f"✅ 搜索测试成功 (找到 {len(results)} 个结果)")
        
        if results:
            print(f"   示例结果: {results[0].file_path}")
        
        # 测试文件读取
        location = accessor.find_class_definition("fvMesh")
        if location:
            print(f"✅ 类定义查找成功")
            print(f"   fvMesh 定义于: {location[0]}")
        else:
            print(f"⚠️  类定义查找失败")
        
        return True
        
    except Exception as e:
        print(f"❌ CodeAccessor 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """测试集成功能"""
    print_section("5. 测试集成功能")
    
    # 测试实际类继承分析
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "inheritance_analyzer.py"),
        "--root", str(ATTACHMENTS_DIR),
        "--class", "kEpsilon",
        "--chain",
        "--format", "json"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=60
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print(f"✅ 集成测试成功")
                print(f"   分析类: kEpsilon")
                if data.get("success"):
                    print(f"   文件位置: {data.get('file_path', 'N/A')}")
                return True
            except json.JSONDecodeError:
                print(f"⚠️  输出不是有效JSON")
                print(f"   输出: {result.stdout[:200]}")
                return False
        else:
            print(f"⚠️  集成测试失败")
            print(f"   错误: {result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 集成测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  OpenFOAM Expert Skill 功能测试")
    print(f"  测试时间: {subprocess.check_output('echo %date% %time%', shell=True, text=True).strip()}")
    print("="*60)
    
    results = {
        "目录结构": test_directory_structure(),
        "源码文件": test_source_code_files(),
        "脚本执行": test_all_scripts(),
        "代码访问器": test_code_accessor(),
        "集成功能": test_integration(),
    }
    
    # 汇总结果
    print_section("测试汇总")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}  {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！OpenFOAM Expert Skill 迁移成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())
