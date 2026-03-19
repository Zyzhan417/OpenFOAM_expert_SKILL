#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细测试搜索功能"""

import os
import re

# OpenFOAM 源码路径
openfoam_src = r'C:\Users\18370\.codebuddy\skills\openfoam-expert\attachments\OpenFOAM\src'

# 测试 1: 检查目录是否存在
print("测试 1: 检查源码目录")
print(f"  源码目录存在: {os.path.exists(openfoam_src)}")

# 测试 2: 检查 fvMesh.H 文件
fvMesh_path = os.path.join(openfoam_src, 'finiteVolume/fvMesh/fvMesh.H')
print(f"\n测试 2: 检查 fvMesh.H 文件")
print(f"  文件路径: {fvMesh_path}")
print(f"  文件存在: {os.path.exists(fvMesh_path)}")

# 测试 3: 读取文件内容并搜索
if os.path.exists(fvMesh_path):
    print(f"\n测试 3: 在文件中搜索类定义")
    with open(fvMesh_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        lines = content.split('\n')
        
    pattern = r"class\s+fvMesh\s*(:|\{)"
    for i, line in enumerate(lines, 1):
        if re.search(pattern, line):
            print(f"  找到匹配在第 {i} 行:")
            print(f"    {line.strip()}")
            
# 测试 4: 模拟 CodeAccessor 的搜索逻辑
print(f"\n测试 4: 模拟搜索逻辑")
extensions = ['.H']
pattern = r"class\s+fvMesh\s*(:|\{)"
regex = re.compile(pattern, re.IGNORECASE)

found_count = 0
max_results = 5

for root, dirs, files in os.walk(openfoam_src):
    # 跳过隐藏目录
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    
    for file in files:
        # 检查文件类型
        if not any(file.endswith(ext) for ext in extensions):
            continue
            
        file_path = os.path.join(root, file)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                if regex.search(line):
                    print(f"  找到匹配: {os.path.relpath(file_path, openfoam_src)}:{i+1}")
                    print(f"    内容: {line.strip()[:80]}")
                    found_count += 1
                    
                    if found_count >= max_results:
                        break
        except Exception as e:
            continue
            
        if found_count >= max_results:
            break
            
    if found_count >= max_results:
        break

print(f"\n总共找到: {found_count} 个匹配")
