#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM 类继承关系分析脚本

功能:
1. 分析类的完整继承链
2. 发现派生类
3. 构建继承树
4. 识别设计模式
5. 生成修改建议

使用方法:
    python inheritance_analyzer.py --class ClassName
    python inheritance_analyzer.py --class ClassName --chain
    python inheritance_analyzer.py --class ClassName --tree --depth 3
    python inheritance_analyzer.py --search "*FvPatchField*" --list
"""

import os
import sys
import re
import json
import argparse
import io
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, Any

# Windows平台设置stdout为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加核心模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.code_accessor import CodeAccessor, AccessMode, SearchResult
from core.code_parser import CodeParser, ClassInfo, FunctionInfo
from core.version import get_version_string, print_version


class InheritanceAnalyzer:
    """类继承关系分析器"""
    
    # 常见的设计模式特征
    DESIGN_PATTERNS = {
        'Strategy': {
            'indicators': ['::New(', 'declareRunTimeSelectionTable', 'autoPtr'],
            'description': '策略模式：运行时选择算法实现'
        },
        'Factory': {
            'indicators': ['::New(', 'addToRunTimeSelectionTable'],
            'description': '工厂模式：动态创建对象'
        },
        'Template Method': {
            'indicators': ['virtual', 'override'],
            'description': '模板方法模式：基类定义算法骨架，派生类实现具体步骤'
        },
        'Adapter': {
            'indicators': ['Adaptor', 'Wrapper'],
            'description': '适配器模式：转换接口'
        },
        'Decorator': {
            'indicators': ['Decorator', 'Wrapper'],
            'description': '装饰器模式：动态添加功能'
        }
    }
    
    def __init__(self, openfoam_src: str = None, access_mode: AccessMode = AccessMode.AUTO):
        """
        初始化分析器
        
        Args:
            openfoam_src: OpenFOAM src目录路径
            access_mode: 代码访问模式
        """
        self.accessor = CodeAccessor(openfoam_src=openfoam_src, access_mode=access_mode)
        self.parser = CodeParser()
        
        # 类信息缓存
        self.classes: Dict[str, ClassInfo] = {}
        self.inheritance_tree: Dict[str, List[str]] = defaultdict(list)
        self._scanned = False
        
    def scan_classes(self, force: bool = False) -> int:
        """
        扫描所有类定义
        
        Args:
            force: 强制重新扫描
            
        Returns:
            发现的类数量
        """
        if self._scanned and not force:
            return len(self.classes)
        
        # 搜索所有类定义
        pattern = r"class\s+\w+\s*(?::\s*(?:public|protected|private)\s+\w+)?\s*\{"
        results = self.accessor.search_code(pattern, file_types=".H", max_results=1000)
        
        for result in results:
            # 读取文件内容进行解析
            content = self.accessor.read_file(result.file_path)
            if content:
                file_info = self.parser.parse_file(content.content, result.file_path)
                for cls in file_info.classes:
                    if cls.name not in self.classes:
                        self.classes[cls.name] = cls
                        # 构建继承树
                        for base in cls.base_classes:
                            self.inheritance_tree[base].append(cls.name)
        
        self._scanned = True
        return len(self.classes)
    
    def get_class_info(self, class_name: str) -> Optional[ClassInfo]:
        """
        获取类信息
        
        Args:
            class_name: 类名
            
        Returns:
            类信息
        """
        if class_name in self.classes:
            return self.classes[class_name]
        
        # 单独搜索该类
        inheritance_info = self.accessor.get_inheritance_info(class_name)
        if inheritance_info:
            class_info = ClassInfo(
                name=class_name,
                file_path=inheritance_info["file_path"],
                line_number=inheritance_info["line_number"],
                base_classes=inheritance_info["base_classes"],
                access_specifiers=inheritance_info["access_specifiers"]
            )
            self.classes[class_name] = class_info
            return class_info
        
        return None
    
    def get_inheritance_chain(self, class_name: str) -> List[ClassInfo]:
        """
        获取继承链（从派生类到基类）
        
        Args:
            class_name: 类名
            
        Returns:
            继承链列表
        """
        chain = []
        current = class_name
        visited = set()
        
        while current and current not in visited:
            visited.add(current)
            
            info = self.get_class_info(current)
            if info:
                chain.append(info)
                # 取第一个基类（主要继承）
                current = info.base_classes[0] if info.base_classes else None
            else:
                break
        
        return chain
    
    def get_derived_classes(self, base_class: str, depth: int = 3) -> Dict[int, List[ClassInfo]]:
        """
        获取派生类
        
        Args:
            base_class: 基类名
            depth: 搜索深度
            
        Returns:
            {深度: [派生类列表]}
        """
        result = defaultdict(list)
        current_level = [base_class]
        
        for d in range(1, depth + 1):
            next_level = []
            for cls_name in current_level:
                derived_names = self.inheritance_tree.get(cls_name, [])
                for name in derived_names:
                    info = self.get_class_info(name)
                    if info:
                        result[d].append(info)
                        next_level.append(name)
            current_level = next_level
        
        return dict(result)
    
    def analyze_design_pattern(self, class_name: str) -> List[Dict[str, str]]:
        """
        分析类使用的设计模式
        
        Args:
            class_name: 类名
            
        Returns:
            设计模式列表
        """
        patterns = []
        
        # 获取类信息
        info = self.get_class_info(class_name)
        if not info:
            return patterns
        
        # 读取类文件内容
        content = self.accessor.read_file(info.file_path)
        if not content:
            return patterns
        
        file_content = content.content
        
        # 检查每种设计模式的特征
        for pattern_name, pattern_info in self.DESIGN_PATTERNS.items():
            matches = []
            for indicator in pattern_info['indicators']:
                if indicator in file_content:
                    matches.append(indicator)
            
            if matches:
                patterns.append({
                    "name": pattern_name,
                    "description": pattern_info['description'],
                    "matched_indicators": matches
                })
        
        return patterns
    
    def analyze_virtual_functions(self, class_name: str) -> Dict[str, Any]:
        """
        分析虚函数
        
        Args:
            class_name: 类名
            
        Returns:
            虚函数分析结果
        """
        info = self.get_class_info(class_name)
        if not info:
            return {}
        
        content = self.accessor.read_file(info.file_path)
        if not content:
            return {}
        
        file_info = self.parser.parse_file(content.content, info.file_path)
        
        # 找到当前类
        target_class = None
        for cls in file_info.classes:
            if cls.name == class_name:
                target_class = cls
                break
        
        if not target_class:
            return {}
        
        # 分析虚函数
        virtual_functions = []
        pure_virtual = []
        overridden = []
        
        for func in target_class.member_functions:
            if func.is_virtual:
                func_dict = func.to_dict()
                
                # 检查是否为纯虚函数
                if "= 0" in content.content or func.name in self._find_pure_virtuals(content.content, class_name):
                    pure_virtual.append(func_dict)
                else:
                    virtual_functions.append(func_dict)
                
                if func.is_override:
                    overridden.append(func_dict)
        
        return {
            "virtual_functions": virtual_functions,
            "pure_virtual": pure_virtual,
            "overridden": overridden
        }
    
    def _find_pure_virtuals(self, content: str, class_name: str) -> List[str]:
        """查找纯虚函数"""
        pure_virtuals = []
        pattern = re.compile(r'virtual\s+\w+\s+(\w+)\s*\([^)]*\)\s*=\s*0')
        for match in pattern.finditer(content):
            pure_virtuals.append(match.group(1))
        return pure_virtuals
    
    def generate_modification_suggestions(self, class_name: str, 
                                          modification_type: str = "extend") -> List[Dict[str, Any]]:
        """
        生成修改建议
        
        Args:
            class_name: 类名
            modification_type: 修改类型 (extend/implement/modify)
            
        Returns:
            修改建议列表
        """
        suggestions = []
        
        info = self.get_class_info(class_name)
        if not info:
            return suggestions
        
        chain = self.get_inheritance_chain(class_name)
        patterns = self.analyze_design_pattern(class_name)
        virtual_info = self.analyze_virtual_functions(class_name)
        
        if modification_type == "extend":
            # 扩展建议：创建派生类
            suggestions.append({
                "type": "create_derived_class",
                "description": f"创建 {class_name} 的派生类",
                "template": self._generate_derived_class_template(class_name, info, virtual_info),
                "steps": [
                    f"1. 创建新类头文件 {class_name}Derived.H",
                    f"2. 继承自 {class_name}",
                    "3. 实现必要的虚函数",
                    "4. 添加到运行时选择表（如适用）",
                    "5. 在Make/files中添加编译"
                ],
                "references": [info.file_path]
            })
        
        elif modification_type == "implement":
            # 实现建议：实现纯虚函数
            pure_virtuals = virtual_info.get("pure_virtual", [])
            if pure_virtuals:
                for pv in pure_virtuals:
                    suggestions.append({
                        "type": "implement_pure_virtual",
                        "description": f"实现纯虚函数 {pv['name']}",
                        "function_signature": f"{pv['return_type']} {pv['name']}({', '.join(pv['parameters'])})",
                        "template": self._generate_function_impl_template(class_name, pv),
                        "steps": [
                            f"1. 在 {class_name}.C 中添加函数实现",
                            "2. 实现具体逻辑",
                            "3. 测试验证"
                        ],
                        "references": [info.file_path]
                    })
        
        elif modification_type == "modify":
            # 修改建议：修改现有功能
            suggestions.append({
                "type": "modify_existing",
                "description": f"修改 {class_name} 的实现",
                "considerations": [
                    "检查继承链中是否有其他类依赖此功能",
                    "如果修改虚函数，确认是否影响派生类",
                    "考虑是否需要修改基类接口"
                ],
                "files_to_modify": [
                    {"path": info.file_path, "description": "头文件声明"},
                    {"path": info.file_path.replace('.H', '.C'), "description": "实现文件"}
                ],
                "references": [info.file_path]
            })
        
        return suggestions
    
    def _generate_derived_class_template(self, class_name: str, 
                                          info: ClassInfo, 
                                          virtual_info: Dict) -> str:
        """生成派生类模板"""
        derived_name = f"{class_name}Derived"
        
        template = f'''//- {derived_name} - {class_name}的派生类

#ifndef {derived_name}_H
#define {derived_name}_H

#include "{class_name}.H"

namespace Foam
{{

class {derived_name}
:
    public {class_name}
{{
    // 私有成员

public:

    //- Runtime type information
    TypeName("{derived_name}");

    // 构造函数
    {derived_name}
    (
        const fvPatch& p,
        const DimensionedField<Type, volMesh>& iF
    );

    //- 拷贝构造函数
    {derived_name}(const {derived_name}& ptf);

    //- 析构函数
    virtual ~{derived_name}() = default;

    // 成员函数
'''

        # 添加虚函数覆盖
        pure_virtuals = virtual_info.get("pure_virtual", [])
        for pv in pure_virtuals[:3]:  # 只显示前3个示例
            template += f'''
    //- {pv['name']}
    virtual {pv['return_type']} {pv['name']}({', '.join(pv['parameters'])}) override;
'''

        template += '''};

} // End namespace Foam

#endif
'''
        return template
    
    def _generate_function_impl_template(self, class_name: str, func_info: Dict) -> str:
        """生成函数实现模板"""
        return f'''// {class_name}::{func_info['name']} 实现
{func_info['return_type']} {class_name}::{func_info['name']}({', '.join(func_info['parameters'])})
{{
    // TODO: 实现具体逻辑
    
    // 示例返回（根据实际类型修改）
    return {self._get_default_return(func_info['return_type'])};
}}
'''
    
    def _get_default_return(self, return_type: str) -> str:
        """获取默认返回值"""
        defaults = {
            'void': '',
            'bool': 'false',
            'label': '0',
            'scalar': '0.0',
            'vector': 'vector::zero',
            'tensor': 'tensor::zero',
            'autoPtr': 'autoPtr<...>::New()'
        }
        return defaults.get(return_type, f'{return_type}()')
    
    def search_classes(self, pattern: str) -> List[ClassInfo]:
        """
        搜索匹配模式的类
        
        Args:
            pattern: 搜索模式（支持通配符）
            
        Returns:
            匹配的类列表
        """
        import fnmatch
        return [info for name, info in self.classes.items() 
                if fnmatch.fnmatch(name, pattern)]


def format_output(result: Dict[str, Any], format_type: str = "json") -> str:
    """格式化输出"""
    if format_type == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    elif format_type == "text":
        return _format_text(result)
    else:
        return json.dumps(result, ensure_ascii=False)


def _format_text(result: Dict[str, Any]) -> str:
    """文本格式化输出"""
    lines = []
    
    if "class_name" in result:
        lines.append(f"类: {result['class_name']}")
        lines.append(f"文件: {result.get('file_path', 'N/A')}:{result.get('line_number', 0)}")
        
    if "inheritance_chain" in result:
        lines.append("\n继承链:")
        chain = result["inheritance_chain"]
        lines.append(" → ".join([c["name"] for c in chain]))
        for c in chain:
            lines.append(f"  {c['name']}: {c['file_path']}:{c['line_number']}")
    
    if "derived_classes" in result:
        lines.append("\n派生类:")
        for depth, classes in result["derived_classes"].items():
            lines.append(f"  深度 {depth}: {', '.join([c['name'] for c in classes])}")
    
    if "design_patterns" in result:
        lines.append("\n设计模式:")
        for p in result["design_patterns"]:
            lines.append(f"  - {p['name']}: {p['description']}")
    
    if "modification_suggestions" in result:
        lines.append("\n修改建议:")
        for s in result["modification_suggestions"]:
            lines.append(f"  [{s['type']}] {s['description']}")
    
    return "\n".join(lines)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='OpenFOAM 类继承关系分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --class fvMesh --chain
  %(prog)s --class kEpsilon --tree --depth 3
  %(prog)s --search "*FvPatchField*" --list
  %(prog)s --class turbulenceModel --suggest extend
        """
    )
    
    parser.add_argument('--root', type=str,
                        default=os.environ.get('FOAM_SRC', '/opt/openfoam/src'),
                        help='OpenFOAM src 目录路径')
    parser.add_argument('--mode', choices=['auto', 'mcp', 'local'], default='auto',
                        help='代码访问模式')
    
    # 分析命令
    parser.add_argument('--class', dest='class_name', type=str,
                        help='要分析的类名')
    parser.add_argument('--chain', action='store_true',
                        help='显示继承链')
    parser.add_argument('--tree', action='store_true',
                        help='显示派生树')
    parser.add_argument('--depth', type=int, default=3,
                        help='派生树搜索深度')
    parser.add_argument('--search', type=str,
                        help='搜索匹配模式的类名')
    parser.add_argument('--list', action='store_true',
                        help='列出搜索结果详情')
    parser.add_argument('--patterns', action='store_true',
                        help='分析设计模式')
    parser.add_argument('--suggest', choices=['extend', 'implement', 'modify'],
                        help='生成修改建议')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                        help='输出格式')
    parser.add_argument('-v', '--version', action='store_true',
                        help='显示版本信息')
    
    args = parser.parse_args()
    
    # 显示版本信息
    if args.version:
        print_version()
        return
    
    # 创建分析器
    analyzer = InheritanceAnalyzer(
        openfoam_src=args.root,
        access_mode=AccessMode(args.mode)
    )
    
    result = {"success": True}
    
    # 执行分析
    if args.class_name:
        info = analyzer.get_class_info(args.class_name)
        
        if not info:
            result = {
                "success": False,
                "error": f"未找到类: {args.class_name}"
            }
        else:
            result["class_name"] = args.class_name
            result["file_path"] = info.file_path
            result["line_number"] = info.line_number
            result["base_classes"] = info.base_classes
            result["is_template"] = info.is_template
            
            if args.chain:
                chain = analyzer.get_inheritance_chain(args.class_name)
                result["inheritance_chain"] = [c.to_dict() for c in chain]
            
            if args.tree:
                derived = analyzer.get_derived_classes(args.class_name, args.depth)
                result["derived_classes"] = {
                    d: [c.to_dict() for c in classes]
                    for d, classes in derived.items()
                }
            
            if args.patterns:
                patterns = analyzer.analyze_design_pattern(args.class_name)
                result["design_patterns"] = patterns
            
            if args.suggest:
                suggestions = analyzer.generate_modification_suggestions(
                    args.class_name, args.suggest
                )
                result["modification_suggestions"] = suggestions
    
    elif args.search:
        analyzer.scan_classes()
        matches = analyzer.search_classes(args.search)
        
        result["search_pattern"] = args.search
        result["total_matches"] = len(matches)
        
        if args.list:
            result["matches"] = [m.to_dict() for m in matches]
        else:
            result["class_names"] = [m.name for m in matches]
    
    else:
        parser.print_help()
        return
    
    print(format_output(result, args.format))


if __name__ == '__main__':
    main()
