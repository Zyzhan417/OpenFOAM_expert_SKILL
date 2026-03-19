#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM 边界条件分析脚本

功能:
1. 分析边界条件类型和实现机制
2. 提取参数配置信息
3. 查找使用示例
4. 生成修改建议

使用方法:
    python boundary_analyzer.py --name fixedValue
    python boundary_analyzer.py --name inletOutlet --params
    python boundary_analyzer.py --search "*Inlet*"
    python boundary_analyzer.py --name fixedValue --suggest
"""

import os
import sys
import re
import json
import argparse
import io
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any

# 添加核心模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.code_accessor import CodeAccessor, AccessMode
from core.code_parser import CodeParser, BoundaryConditionInfo
from core.version import get_version_string, print_version


class BoundaryAnalyzer:
    """边界条件分析器"""
    
    # 边界条件基类类型
    BC_BASE_TYPES = {
        'fixedValueFvPatchField': '固定值边界条件',
        'zeroGradientFvPatchField': '零梯度边界条件',
        'inletOutletFvPatchField': '入口出口边界条件',
        'mixedFvPatchField': '混合边界条件',
        'directionMixedFvPatchField': '方向混合边界条件',
        'calculatedFvPatchField': '计算边界条件',
        'cyclicFvPatchField': '周期边界条件',
        'symmetryFvPatchField': '对称边界条件',
        'emptyFvPatchField': '空边界条件（2D问题）',
        'processorFvPatchField': '并行处理边界条件'
    }
    
    # 边界条件目录映射
    BC_DIRECTORIES = {
        'basic': '基础边界条件',
        'derived': '派生边界条件',
        'fixedValue': '固定值类型',
        'inletOutlet': '入口出口类型',
        'turbulent': '湍流边界条件',
        'temperature': '温度边界条件',
        'wall': '壁面边界条件'
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
        
        # 缓存
        self._bc_cache: Dict[str, BoundaryConditionInfo] = {}
        
    def find_boundary_condition(self, bc_name: str) -> Optional[BoundaryConditionInfo]:
        """
        查找边界条件
        
        Args:
            bc_name: 边界条件名称
            
        Returns:
            边界条件信息
        """
        # 检查缓存
        if bc_name in self._bc_cache:
            return self._bc_cache[bc_name]
        
        # 搜索边界条件类定义
        pattern = rf"class\s+{bc_name}\s*:\s*public\s+\w+FvPatchField"
        results = self.accessor.search_code(pattern, file_types=".H", scope="source", max_results=5)
        
        if not results:
            # 尝试添加FvPatchField后缀搜索
            pattern = rf"class\s+{bc_name}FvPatchField\s*:\s*public"
            results = self.accessor.search_code(pattern, file_types=".H", scope="source", max_results=5)
        
        if not results:
            return None
        
        # 读取文件内容解析
        for result in results:
            content = self.accessor.read_file(result.file_path)
            if content:
                bc_info = self.parser.parse_boundary_condition(content.content, result.file_path)
                if bc_info and (bc_info.name == bc_name or bc_info.name == f"{bc_name}FvPatchField"):
                    self._bc_cache[bc_name] = bc_info
                    return bc_info
        
        return None
    
    def analyze_parameters(self, bc_name: str) -> Dict[str, Any]:
        """
        分析边界条件参数
        
        Args:
            bc_name: 边界条件名称
            
        Returns:
            参数分析结果
        """
        result = {
            "boundary_condition": bc_name,
            "parameters": [],
            "required_parameters": [],
            "optional_parameters": [],
            "default_values": {}
        }
        
        bc_info = self.find_boundary_condition(bc_name)
        if not bc_info:
            return result
        
        result["file_path"] = bc_info.file_path
        result["base_class"] = bc_info.base_class
        
        # 提取参数信息
        # 读取实现文件获取更详细的参数信息
        impl_file = bc_info.file_path.replace('.H', '.C')
        impl_content = self.accessor.read_file(impl_file)
        
        if impl_content:
            # 解析lookup调用
            content = impl_content.content
            
            # 必需参数（lookup）
            lookup_pattern = re.compile(r'\.lookup\s*\(\s*["\'](\w+)["\']\s*\)')
            for match in lookup_pattern.finditer(content):
                param_name = match.group(1)
                if param_name not in [p["name"] for p in result["required_parameters"]]:
                    result["required_parameters"].append({
                        "name": param_name,
                        "type": "scalar or field",
                        "description": self._guess_param_description(param_name)
                    })
            
            # 可选参数（lookupOrDefault）
            default_pattern = re.compile(
                r'lookupOrDefault\s*<\w+>\s*\(\s*["\'](\w+)["\']\s*,\s*([^)]+)\)'
            )
            for match in default_pattern.finditer(content):
                param_name = match.group(1)
                default_val = match.group(2).strip()
                if param_name not in [p["name"] for p in result["optional_parameters"]]:
                    result["optional_parameters"].append({
                        "name": param_name,
                        "type": "scalar or field",
                        "default": default_val,
                        "description": self._guess_param_description(param_name)
                    })
                    result["default_values"][param_name] = default_val
        
        result["parameters"] = result["required_parameters"] + result["optional_parameters"]
        
        return result
    
    def _guess_param_description(self, param_name: str) -> str:
        """根据参数名猜测描述"""
        descriptions = {
            'value': '边界值',
            'refValue': '参考值',
            'inletValue': '入口值',
            'phi': '通量场名称',
            'rho': '密度场名称',
            'k': '湍动能',
            'epsilon': '耗散率',
            'omega': '比耗散率',
            'nut': '湍流粘度',
            'T': '温度',
            'p': '压力',
            'U': '速度',
            'fixedValue': '固定值',
            'gradient': '梯度值',
            'alpha': '混合系数',
            'friction': '摩擦系数',
            'q': '热通量',
            'emissivity': '发射率'
        }
        return descriptions.get(param_name, param_name)
    
    def find_usage_examples(self, bc_name: str, max_examples: int = 5) -> List[Dict[str, Any]]:
        """
        查找使用示例
        
        Args:
            bc_name: 边界条件名称
            max_examples: 最大示例数量
            
        Returns:
            使用示例列表
        """
        examples = []
        
        # 在tutorials中搜索
        pattern = rf"type\s+{bc_name};"
        results = self.accessor.search_code(pattern, scope="tutorials", max_results=max_examples)
        
        for result in results:
            # 读取上下文获取完整配置
            content = self.accessor.read_file(result.file_path, 
                                              start_line=max(1, result.line_number - 10),
                                              end_line=result.line_number + 10)
            if content:
                examples.append({
                    "file_path": result.file_path,
                    "line_number": result.line_number,
                    "context": content.content,
                    "description": self._extract_example_description(content.content, bc_name)
                })
        
        return examples
    
    def _extract_example_description(self, context: str, bc_name: str) -> str:
        """提取示例描述"""
        # 尝试从注释中提取
        lines = context.split('\n')
        for line in lines:
            if '//' in line and bc_name in context:
                return line.split('//')[1].strip()
        return ""
    
    def list_boundary_conditions(self, category: str = None) -> List[Dict[str, str]]:
        """
        列出边界条件
        
        Args:
            category: 类别过滤
            
        Returns:
            边界条件列表
        """
        bc_list = []
        
        # 搜索所有边界条件
        pattern = r"addToRunTimeSelectionTable.*FvPatchField"
        results = self.accessor.search_code(pattern, file_types=".C", scope="source", max_results=200)
        
        for result in results:
            # 提取边界条件名
            match = re.search(r'addToRunTimeSelectionTable\s*\(\s*\w+\s*,\s*(\w+)\s*,', result.content)
            if match:
                bc_name = match.group(1)
                
                # 判断类别
                bc_category = self._categorize_bc(bc_name, result.file_path)
                
                if category and category.lower() not in bc_category.lower():
                    continue
                
                bc_list.append({
                    "name": bc_name,
                    "category": bc_category,
                    "file_path": result.file_path
                })
        
        return bc_list
    
    def _categorize_bc(self, bc_name: str, file_path: str) -> str:
        """对边界条件分类"""
        # 根据路径判断
        for dir_name, category in self.BC_DIRECTORIES.items():
            if dir_name in file_path:
                return category
        
        # 根据名称判断
        name_lower = bc_name.lower()
        if 'inlet' in name_lower or 'outlet' in name_lower:
            return '入口出口类型'
        if 'fixed' in name_lower:
            return '固定值类型'
        if 'wall' in name_lower:
            return '壁面边界条件'
        if 'turbulent' in name_lower or 'k' in name_lower or 'epsilon' in name_lower:
            return '湍流边界条件'
        if 'temperature' in name_lower or 'heat' in name_lower:
            return '温度边界条件'
        
        return '其他'
    
    def get_base_class_info(self, bc_name: str) -> Dict[str, Any]:
        """
        获取基类信息
        
        Args:
            bc_name: 边界条件名称
            
        Returns:
            基类信息
        """
        bc_info = self.find_boundary_condition(bc_name)
        if not bc_info:
            return {}
        
        base_class = bc_info.base_class
        
        result = {
            "boundary_condition": bc_name,
            "base_class": base_class,
            "base_class_type": self.BC_BASE_TYPES.get(base_class, "未知类型"),
            "base_class_file": None,
            "inheritance_chain": [bc_name, base_class]
        }
        
        # 查找基类文件
        pattern = rf"class\s+{base_class}\s*:"
        base_results = self.accessor.search_code(pattern, file_types=".H", scope="source", max_results=1)
        if base_results:
            result["base_class_file"] = base_results[0].file_path
        
        # 继续向上追踪继承链
        current_base = base_class
        visited = {bc_name, base_class}
        while current_base:
            pattern = rf"class\s+{current_base}\s*:\s*public\s+(\w+)"
            results = self.accessor.search_code(pattern, file_types=".H", scope="source", max_results=1)
            if results:
                match = re.search(pattern, results[0].content)
                if match:
                    next_base = match.group(1)
                    if next_base not in visited:
                        result["inheritance_chain"].append(next_base)
                        visited.add(next_base)
                        current_base = next_base
                    else:
                        break
                else:
                    break
            else:
                break
        
        return result
    
    def generate_modification_suggestions(self, bc_name: str, 
                                          modification_type: str = "create") -> List[Dict[str, Any]]:
        """
        生成修改建议
        
        Args:
            bc_name: 边界条件名称
            modification_type: 修改类型
            
        Returns:
            修改建议列表
        """
        suggestions = []
        
        bc_info = self.find_boundary_condition(bc_name)
        if not bc_info:
            return [{
                "type": "not_found",
                "description": f"未找到边界条件: {bc_name}",
                "suggestion": "请检查边界条件名称是否正确"
            }]
        
        params = self.analyze_parameters(bc_name)
        base_info = self.get_base_class_info(bc_name)
        
        if modification_type == "create":
            # 创建新边界条件
            new_bc_name = f"{bc_name}Custom"
            
            suggestions.append({
                "type": "create_new_bc",
                "description": f"基于 {bc_name} 创建新的边界条件",
                "template": self._generate_bc_template(new_bc_name, bc_info, params),
                "steps": [
                    f"1. 创建头文件 {new_bc_name}FvPatchField.H",
                    f"2. 创建实现文件 {new_bc_name}FvPatchField.C",
                    f"3. 继承自 {bc_info.base_class}",
                    "4. 实现构造函数和必要方法",
                    "5. 添加到运行时选择表",
                    "6. 编译测试"
                ],
                "files_to_create": [
                    f"{new_bc_name}FvPatchField.H",
                    f"{new_bc_name}FvPatchField.C"
                ],
                "references": [bc_info.file_path]
            })
        
        elif modification_type == "modify":
            # 修改现有边界条件
            suggestions.append({
                "type": "modify_existing",
                "description": f"修改 {bc_name} 边界条件",
                "considerations": [
                    "确认修改不影响已有案例",
                    "保持向后兼容性",
                    "更新文档说明"
                ],
                "files_to_modify": [
                    {"path": bc_info.file_path, "description": "头文件"},
                    {"path": bc_info.file_path.replace('.H', '.C'), "description": "实现文件"}
                ],
                "parameters": params["parameters"],
                "references": [bc_info.file_path]
            })
        
        elif modification_type == "use":
            # 使用建议
            required = params.get("required_parameters", [])
            optional = params.get("optional_parameters", [])
            
            config_template = f'''type            {bc_name};
'''
            for p in required:
                config_template += f'{p["name"]:<15} <value>;  // {p["description"]}\n'
            for p in optional:
                config_template += f'// {p["name"]:<13} {p["default"]};  // {p["description"]} (optional)\n'
            
            suggestions.append({
                "type": "usage_guide",
                "description": f"如何使用 {bc_name} 边界条件",
                "config_template": config_template,
                "required_parameters": required,
                "optional_parameters": optional,
                "examples": self.find_usage_examples(bc_name, 2)
            })
        
        return suggestions
    
    def _generate_bc_template(self, new_bc_name: str, 
                               bc_info: BoundaryConditionInfo, 
                               params: Dict) -> str:
        """生成边界条件模板"""
        return f'''//- {new_bc_name}FvPatchField - 自定义边界条件

#ifndef {new_bc_name}FvPatchField_H
#define {new_bc_name}FvPatchField_H

#include "{bc_info.base_class}.H"

namespace Foam
{{

template<class Type>
class {new_bc_name}FvPatchField
:
    public {bc_info.base_class}<Type>
{{
    // 私有成员
    Field<Type> customValue_;

public:

    //- Runtime type information
    TypeName("{new_bc_name}");

    // 构造函数
    {new_bc_name}FvPatchField
    (
        const fvPatch& p,
        const DimensionedField<Type, volMesh>& iF
    );

    {new_bc_name}FvPatchField
    (
        const fvPatch& p,
        const DimensionedField<Type, volMesh>& iF,
        const dictionary& dict
    );

    {new_bc_name}FvPatchField
    (
        const {new_bc_name}FvPatchField& ptf,
        const fvPatch& p,
        const DimensionedField<Type, volMesh>& iF,
        const fvPatchFieldMapper& m
    );

    {new_bc_name}FvPatchField
    (
        const {new_bc_name}FvPatchField& ptf
    );

    {new_bc_name}FvPatchField
    (
        const {new_bc_name}FvPatchField& ptf,
        const DimensionedField<Type, volMesh>& iF
    );

    virtual tmp<fvPatchField<Type>> clone() const
    {{
        return tmp<fvPatchField<Type>> (
            new {new_bc_name}FvPatchField<Type>(*this)
        );
    }}

    virtual tmp<fvPatchField<Type>> clone
    (
        const DimensionedField<Type, volMesh>& iF
    ) const
    {{
        return tmp<fvPatchField<Type>> (
            new {new_bc_name}FvPatchField<Type>(*this, iF)
        );
    }}

    // 成员函数
    virtual void updateCoeffs();

    virtual void write(Ostream& os) const;
}};

}} // End namespace Foam

#endif
'''


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
    
    if "boundary_condition" in result:
        lines.append(f"边界条件: {result['boundary_condition']}")
        
    if "base_class" in result:
        lines.append(f"基类: {result['base_class']}")
        
    if "file_path" in result:
        lines.append(f"文件: {result['file_path']}")
    
    if "required_parameters" in result:
        lines.append("\n必需参数:")
        for p in result["required_parameters"]:
            lines.append(f"  - {p['name']}: {p.get('description', '')}")
    
    if "optional_parameters" in result:
        lines.append("\n可选参数:")
        for p in result["optional_parameters"]:
            lines.append(f"  - {p['name']}: {p.get('description', '')} (默认: {p.get('default', '')})")
    
    if "usage_examples" in result:
        lines.append("\n使用示例:")
        for ex in result["usage_examples"][:3]:
            lines.append(f"  文件: {ex['file_path']}")
    
    if "modification_suggestions" in result:
        lines.append("\n修改建议:")
        for s in result["modification_suggestions"]:
            lines.append(f"  [{s['type']}] {s['description']}")
    
    return "\n".join(lines)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='OpenFOAM 边界条件分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --name fixedValue
  %(prog)s --name inletOutlet --params
  %(prog)s --search "*Inlet*"
  %(prog)s --name fixedValue --suggest create
        """
    )
    
    parser.add_argument('--root', type=str,
                        default=os.environ.get('FOAM_SRC', '/opt/openfoam/src'),
                        help='OpenFOAM src 目录路径')
    parser.add_argument('--mode', choices=['auto', 'mcp', 'local'], default='auto',
                        help='代码访问模式')
    
    # 分析命令
    parser.add_argument('--name', type=str,
                        help='边界条件名称')
    parser.add_argument('--params', action='store_true',
                        help='显示参数信息')
    parser.add_argument('--base', action='store_true',
                        help='显示基类信息')
    parser.add_argument('--examples', action='store_true',
                        help='查找使用示例')
    parser.add_argument('--search', type=str,
                        help='搜索边界条件')
    parser.add_argument('--list', action='store_true',
                        help='列出所有边界条件')
    parser.add_argument('--category', type=str,
                        help='按类别过滤')
    parser.add_argument('--suggest', choices=['create', 'modify', 'use'],
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
    analyzer = BoundaryAnalyzer(
        openfoam_src=args.root,
        access_mode=AccessMode(args.mode)
    )
    
    result = {"success": True}
    
    # 执行分析
    if args.name:
        bc_info = analyzer.find_boundary_condition(args.name)
        
        if not bc_info:
            result = {
                "success": False,
                "error": f"未找到边界条件: {args.name}"
            }
        else:
            result["boundary_condition"] = args.name
            result["base_class"] = bc_info.base_class
            result["file_path"] = bc_info.file_path
            result["line_number"] = bc_info.line_number
            
            if args.params:
                params = analyzer.analyze_parameters(args.name)
                result["parameters"] = params["parameters"]
                result["required_parameters"] = params["required_parameters"]
                result["optional_parameters"] = params["optional_parameters"]
                result["default_values"] = params["default_values"]
            
            if args.base:
                base_info = analyzer.get_base_class_info(args.name)
                result["base_class_type"] = base_info.get("base_class_type")
                result["inheritance_chain"] = base_info.get("inheritance_chain", [])
            
            if args.examples:
                result["usage_examples"] = analyzer.find_usage_examples(args.name)
            
            if args.suggest:
                result["modification_suggestions"] = analyzer.generate_modification_suggestions(
                    args.name, args.suggest
                )
    
    elif args.search:
        bc_list = analyzer.list_boundary_conditions(args.category)
        matches = [bc for bc in bc_list if args.search.lower() in bc["name"].lower()]
        result["search_pattern"] = args.search
        result["total_matches"] = len(matches)
        result["matches"] = matches[:20]  # 限制输出数量
    
    elif args.list:
        bc_list = analyzer.list_boundary_conditions(args.category)
        result["total"] = len(bc_list)
        result["boundary_conditions"] = bc_list
    
    else:
        parser.print_help()
        return
    
    print(format_output(result, args.format))


if __name__ == '__main__':
    main()
