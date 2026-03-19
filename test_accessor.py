#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 CodeAccessor 查找类定义"""

import sys
import os
sys.path.insert(0, r'C:\Users\18370\.codebuddy\skills\openfoam-expert\scripts')

from core.code_accessor import CodeAccessor

# 创建 accessor
openfoam_src = r'C:\Users\18370\.codebuddy\skills\openfoam-expert\attachments\OpenFOAM\src'
acc = CodeAccessor(openfoam_src, access_mode='local')

# 测试搜索功能
print("测试搜索功能...")
pattern = r"class\s+fvMesh\s*(:|\{)"
results = acc.search_code(pattern, file_types=".H", max_results=5)

print(f"搜索模式: {pattern}")
print(f"搜索结果数量: {len(results)}")
for r in results:
    print(f"  文件: {r.file_path}:{r.line_number}")
    print(f"  内容: {r.content[:80]}")
    print()

# 测试查找类定义
print("\n测试查找类定义...")
classes_to_test = ['fvMesh', 'polyMesh', 'kEpsilon']

for class_name in classes_to_test:
    print(f"\n查找类: {class_name}")
    result = acc.find_class_definition(class_name)
    if result:
        print(f"  找到: {result[0]}:{result[1]}")
    else:
        print(f"  未找到")
