#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM Expert Skill 版本管理模块

提供统一的版本信息管理，所有脚本通过此模块获取版本号
"""

__version__ = "2.2.0"
__skill_name__ = "openfoam-expert"
__release_date__ = "2026-03-18"
__openfoam_version__ = "13"

# 版本历史
VERSION_HISTORY = {
    "2.2.0": {
        "date": "2026-03-18",
        "changes": [
            "新增 MCP Server 封装，支持 Claude/Cursor 直接调用",
            "新增统一命令路由器 (router.py)",
            "新增缓存管理模块 (cache_manager.py)",
            "新增输出格式化器，支持 AI 友好格式",
            "优化 CLI 脚本，消除硬编码路径",
            "改进错误处理和跨平台兼容性"
        ]
    },
    "2.1.0": {
        "date": "2026-03-10",
        "changes": [
            "添加统一版本管理",
            "增强错误处理和调试模式",
            "重构 SKILL.md 文档结构",
            "修复硬编码路径问题",
            "完善参考文档"
        ]
    },
    "2.0.0": {
        "date": "2026-03-07",
        "changes": [
            "迁移到 User Level",
            "集成 OpenFOAM 源码附件 (24,330 个文件)",
            "自动路径检测",
            "完全自包含，无需外部依赖"
        ]
    },
    "1.0.0": {
        "date": "2025-08-05",
        "changes": [
            "初始版本 (Project Level)",
            "基础类继承分析功能",
            "边界条件分析功能",
            "物理模型分析功能"
        ]
    }
}


def get_version_info():
    """
    获取完整的版本信息
    
    Returns:
        dict: 包含版本详细信息的字典
    """
    import os
    from pathlib import Path
    
    # 获取 Skill 根目录
    script_dir = Path(__file__).parent.parent.parent  # core/../scripts/..
    skill_root = script_dir
    
    # 统计源码文件
    src_dir = skill_root / "attachments" / "OpenFOAM" / "src"
    h_files = 0
    c_files = 0
    
    if src_dir.exists():
        try:
            h_files = sum(1 for _ in src_dir.rglob("*.H"))
            c_files = sum(1 for _ in src_dir.rglob("*.C"))
        except:
            pass
    
    return {
        "skill_version": __version__,
        "skill_name": __skill_name__,
        "release_date": __release_date__,
        "openfoam_version": __openfoam_version__,
        "skill_root": str(skill_root),
        "source_files": {
            "header_files": h_files,
            "source_files": c_files,
            "total": h_files + c_files
        }
    }


def get_version_string():
    """
    获取版本字符串
    
    Returns:
        str: 格式化的版本字符串
    """
    return f"{__skill_name__} v{__version__} (OpenFOAM {__openfoam_version__}) - {__release_date}"


def print_version():
    """
    打印版本信息
    """
    info = get_version_info()
    print(f"\n{'='*60}")
    print(f"  {info['skill_name']} v{info['skill_version']}")
    print(f"{'='*60}")
    print(f"  Release Date: {info['release_date']}")
    print(f"  OpenFOAM Version: {info['openfoam_version']}")
    print(f"  Skill Root: {info['skill_root']}")
    print(f"  Source Files: {info['source_files']['total']} ", end='')
    print(f"({info['source_files']['header_files']} .H + {info['source_files']['source_files']} .C)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # 测试版本模块
    print_version()
    
    # 显示版本历史
    print("\n版本历史:")
    for version, details in sorted(VERSION_HISTORY.items(), reverse=True):
        print(f"\n  v{version} ({details['date']}):")
        for change in details['changes']:
            print(f"    - {change}")
