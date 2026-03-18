#!/usr/bin/env python3
"""
OpenFOAM 类继承关系分析脚本

功能:
1. 从 OpenFOAM 源码中提取类继承关系
2. 构建继承树并输出
3. 支持搜索特定类的继承链

使用方法:
    python analyze_class_hierarchy.py --class ClassName [--root /path/to/openfoam/src]
    python analyze_class_hierarchy.py --list-children BaseClassName [--root /path/to/openfoam/src]
    python analyze_class_hierarchy.py --tree ClassName [--root /path/to/openfoam/src]
"""

import os
import re
import argparse
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    base_classes: List[str]
    file_path: str
    line_number: int
    is_template: bool
    access_specifiers: List[str]  # public/protected/private


class OpenFOAMClassAnalyzer:
    """OpenFOAM 类继承分析器"""
    
    # 匹配类定义的正则表达式
    CLASS_PATTERN = re.compile(
        r'class\s+(\w+)\s*'  # 类名
        r'(?:<[^>]*>)?\s*'   # 可选模板参数
        r'(?::\s*((?:public|protected|private)\s+\w+(?:\s*,\s*(?:public|protected|private)\s+\w+)*))?\s*'  # 继承列表
        r'\{'
    )
    
    # 匹配模板类声明的正则表达式
    TEMPLATE_PATTERN = re.compile(r'template\s*<[^>]*>')
    
    def __init__(self, openfoam_src_path: str):
        """
        初始化分析器
        
        Args:
            openfoam_src_path: OpenFOAM src 目录路径
        """
        self.src_path = openfoam_src_path
        self.classes: Dict[str, ClassInfo] = {}
        self.inheritance_tree: Dict[str, List[str]] = defaultdict(list)
        
    def scan_directory(self, directory: str = None) -> None:
        """
        扫描目录并提取类信息
        
        Args:
            directory: 要扫描的目录，默认为 src_path
        """
        if directory is None:
            directory = self.src_path
            
        for root, dirs, files in os.walk(directory):
            # 跳过一些不需要的目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith('.H'):  # OpenFOAM 类定义在 .H 文件中
                    file_path = os.path.join(root, file)
                    self._parse_file(file_path)
    
    def _parse_file(self, file_path: str) -> None:
        """
        解析单个文件，提取类定义
        
        Args:
            file_path: 文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            # 检查是否是模板类
            is_template = bool(self.TEMPLATE_PATTERN.search(content))
            
            # 查找所有类定义
            for match in self.CLASS_PATTERN.finditer(content):
                class_name = match.group(1)
                inheritance_list = match.group(2)
                
                # 计算行号
                line_num = content[:match.start()].count('\n') + 1
                
                # 解析基类
                base_classes = []
                access_specifiers = []
                
                if inheritance_list:
                    for item in inheritance_list.split(','):
                        parts = item.strip().split()
                        if len(parts) >= 2:
                            access = parts[0]  # public/protected/private
                            base_name = parts[1]
                            base_classes.append(base_name)
                            access_specifiers.append(access)
                
                # 创建类信息
                class_info = ClassInfo(
                    name=class_name,
                    base_classes=base_classes,
                    file_path=file_path,
                    line_number=line_num,
                    is_template=is_template,
                    access_specifiers=access_specifiers
                )
                
                self.classes[class_name] = class_info
                
                # 构建继承树 (基类 -> 派生类列表)
                for base in base_classes:
                    self.inheritance_tree[base].append(class_name)
                    
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
    
    def get_class_info(self, class_name: str) -> Optional[ClassInfo]:
        """
        获取类信息
        
        Args:
            class_name: 类名
            
        Returns:
            类信息，如果不存在返回 None
        """
        return self.classes.get(class_name)
    
    def get_inheritance_chain(self, class_name: str) -> List[str]:
        """
        获取类的完整继承链 (从派生类到基类)
        
        Args:
            class_name: 类名
            
        Returns:
            继承链列表
        """
        chain = [class_name]
        current = class_name
        
        while True:
            info = self.classes.get(current)
            if info is None or not info.base_classes:
                break
            
            # 取第一个基类 (主要继承)
            base = info.base_classes[0]
            chain.append(base)
            current = base
            
            # 防止循环继承
            if len(chain) > 100:
                break
                
        return chain
    
    def get_derived_classes(self, class_name: str, depth: int = 1) -> Dict[int, List[str]]:
        """
        获取类的所有派生类
        
        Args:
            class_name: 基类名
            depth: 搜索深度
            
        Returns:
            {深度: [派生类列表]} 字典
        """
        result = defaultdict(list)
        current_level = [class_name]
        
        for d in range(1, depth + 1):
            next_level = []
            for cls in current_level:
                derived = self.inheritance_tree.get(cls, [])
                next_level.extend(derived)
                result[d].extend(derived)
            current_level = next_level
            
        return dict(result)
    
    def print_inheritance_tree(self, class_name: str, max_depth: int = 5) -> None:
        """
        打印类的继承树
        
        Args:
            class_name: 类名
            max_depth: 最大打印深度
        """
        def print_tree(cls: str, prefix: str, depth: int, is_last: bool):
            if depth > max_depth:
                return
                
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{cls}")
            
            derived = self.inheritance_tree.get(cls, [])
            for i, child in enumerate(derived):
                new_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(child, new_prefix, depth + 1, i == len(derived) - 1)
        
        print(f"\n继承树 (基类: {class_name}):")
        print(class_name)
        derived = self.inheritance_tree.get(class_name, [])
        for i, child in enumerate(derived):
            print_tree(child, "", 1, i == len(derived) - 1)
    
    def print_inheritance_chain(self, class_name: str) -> None:
        """
        打印类的继承链
        
        Args:
            class_name: 类名
        """
        chain = self.get_inheritance_chain(class_name)
        
        print(f"\n继承链 ({class_name}):")
        print(" → ".join(chain))
        
        # 打印每个类的详细信息
        for cls in chain:
            info = self.classes.get(cls)
            if info:
                rel_path = os.path.relpath(info.file_path, self.src_path)
                print(f"  {cls}: {rel_path}:{info.line_number}")
    
    def search_class(self, pattern: str) -> List[str]:
        """
        搜索匹配模式的类名
        
        Args:
            pattern: 搜索模式 (支持通配符 * 和 ?)
            
        Returns:
            匹配的类名列表
        """
        import fnmatch
        return [name for name in self.classes.keys() 
                if fnmatch.fnmatch(name, pattern)]


def main():
    parser = argparse.ArgumentParser(
        description='OpenFOAM 类继承关系分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --class fvMesh --tree
  %(prog)s --class kEpsilon --chain
  %(prog)s --search "*FvPatchField*" --list
  %(prog)s --children turbulenceModel --depth 2
        """
    )
    
    parser.add_argument('--root', type=str, 
                        default=os.environ.get('FOAM_SRC', '/opt/openfoam/src'),
                        help='OpenFOAM src 目录路径 (默认: $FOAM_SRC 或 /opt/openfoam/src)')
    
    parser.add_argument('--class', dest='class_name', type=str,
                        help='要分析的类名')
    
    parser.add_argument('--chain', action='store_true',
                        help='显示类的继承链')
    
    parser.add_argument('--tree', action='store_true',
                        help='显示类的派生树')
    
    parser.add_argument('--children', type=str,
                        help='列出指定基类的派生类')
    
    parser.add_argument('--depth', type=int, default=3,
                        help='派生树搜索深度 (默认: 3)')
    
    parser.add_argument('--search', type=str,
                        help='搜索匹配模式的类名')
    
    parser.add_argument('--list', action='store_true',
                        help='列出搜索结果')
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = OpenFOAMClassAnalyzer(args.root)
    
    print(f"扫描 OpenFOAM 源码: {args.root}")
    analyzer.scan_directory()
    print(f"发现 {len(analyzer.classes)} 个类定义\n")
    
    # 执行分析
    if args.class_name:
        if args.chain:
            analyzer.print_inheritance_chain(args.class_name)
        
        if args.tree:
            analyzer.print_inheritance_tree(args.class_name, args.depth)
            
        if not args.chain and not args.tree:
            # 默认显示基本信息
            info = analyzer.get_class_info(args.class_name)
            if info:
                print(f"\n类: {info.name}")
                print(f"文件: {os.path.relpath(info.file_path, args.root)}:{info.line_number}")
                print(f"基类: {', '.join(info.base_classes) if info.base_classes else '无'}")
                print(f"模板: {'是' if info.is_template else '否'}")
            else:
                print(f"未找到类: {args.class_name}")
    
    elif args.children:
        derived = analyzer.get_derived_classes(args.children, args.depth)
        print(f"\n'{args.children}' 的派生类:")
        for depth, classes in derived.items():
            print(f"  深度 {depth}: {', '.join(classes)}")
    
    elif args.search:
        matches = analyzer.search_class(args.search)
        print(f"\n匹配 '{args.search}' 的类 ({len(matches)} 个):")
        if args.list:
            for cls in sorted(matches):
                info = analyzer.classes.get(cls)
                if info:
                    print(f"  {cls}: {os.path.relpath(info.file_path, args.root)}")
        else:
            print(f"  {', '.join(sorted(matches))}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
