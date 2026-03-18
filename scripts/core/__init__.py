#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM代码分析核心模块

提供统一的代码访问接口和解析功能
"""

from .code_accessor import CodeAccessor, AccessMode
from .code_parser import CodeParser, ClassInfo, FunctionInfo, FileInfo

__all__ = [
    'CodeAccessor',
    'AccessMode',
    'CodeParser', 
    'ClassInfo',
    'FunctionInfo',
    'FileInfo'
]
