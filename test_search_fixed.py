#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试修复后的搜索功能"""

import os
import re

# OpenFOAM 源码路径
openfoam_src = r'C:\Users\18370\.codebuddy\skills\openfoam-expert\attachments\OpenFOAM\src'

# 测试修复后的正则表达式
class_name = 'fvMesh'
pattern = rf"class\s+{class_name}\s*[\s\S]{{0,50}}?(:|\{{)"
print(f"搜索模式: {pattern}")

# 在文件中搜索
fvMesh_path = os.path.join(openfoam_src, 'finiteVolume/fvMesh/fvMesh.H')
with open(fvMesh_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    lines = content.split('\n')
    
regex = re.compile(pattern, re.IGNORECASE | re.DOTALL)

# 需要搜索多行内容
match = regex.search(content)
if match:
    # 找到匹配的行号
    pos = match.start()
    line_num = content[:pos].count('\n') + 1
    print(f"找到匹配在第 {line_num} 行")
    # 显示匹配内容
    matched_lines = match.group(0).split('\n')
    for i, line in enumerate(matched_lines[:5], line_num):
        print(f"  {i}: {line}")
else:
    print("未找到匹配")

# 使用修复后的 CodeAccessor 测试
print("\n" + "="*60)
print("使用 CodeAccessor 测试:")
print("="*60)

import sys
sys.path.insert(0, r'C:\Users\18370\.codebuddy\skills\openfoam-expert\scripts')
from core.code_accessor import CodeAccessor

acc = CodeAccessor(openfoam_src, access_mode='local')

for class_name in ['fvMesh', 'polyMesh', 'kEpsilon']:
    print(f"\n查找类: {class_name}")
    result = acc.find_class_definition(class_name)
    if result:
        print(f"  [OK] 找到: {result[0]}:{result[1]}")
    else:
        print(f"  [FAIL] 未找到")
