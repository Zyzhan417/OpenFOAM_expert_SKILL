#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM 代码修改建议生成器

功能:
1. 整合各分析器的结果
2. 生成标准化修改建议
3. 提供代码模板
4. 输出完整的修改方案

使用方法:
    python code_modifier.py --target class --name kEpsilon --action extend
    python code_modifier.py --target boundary --name fixedValue --action create
    python code_modifier.py --target model --type turbulence --name kOmegaSST --action modify
    python code_modifier.py --input analysis_result.json
"""

import os
import sys
import json
import argparse
import io
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加核心模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.code_accessor import CodeAccessor, AccessMode
from core.version import get_version_string, print_version
from inheritance_analyzer import InheritanceAnalyzer
from boundary_analyzer import BoundaryAnalyzer
from model_analyzer import ModelAnalyzer


class CodeModifier:
    """代码修改建议生成器"""
    
    # 修改类型模板
    MODIFICATION_TEMPLATES = {
        'create_class': {
            'description': '创建新类',
            'required_files': ['Header.H', 'Implementation.C', 'Make/files', 'Make/options'],
            'steps': [
                '创建头文件，定义类结构',
                '创建实现文件，实现成员函数',
                '添加到编译系统',
                '注册到运行时选择表（如需要）',
                '编译测试'
            ]
        },
        'extend_class': {
            'description': '扩展现有类',
            'required_files': ['Header.H', 'Implementation.C'],
            'steps': [
                '创建派生类头文件',
                '继承目标类',
                '重写虚函数',
                '添加新成员和方法',
                '注册到选择表',
                '编译测试'
            ]
        },
        'modify_class': {
            'description': '修改现有类实现',
            'required_files': ['ExistingHeader.H', 'ExistingImplementation.C'],
            'steps': [
                '分析依赖关系',
                '备份原始文件',
                '修改头文件（如需要）',
                '修改实现文件',
                '测试回归',
                '更新文档'
            ]
        },
        'create_boundary': {
            'description': '创建新边界条件',
            'required_files': ['BCFvPatchField.H', 'BCFvPatchField.C'],
            'steps': [
                '创建边界条件头文件',
                '继承合适的基类',
                '实现构造函数',
                '实现updateCoeffs()',
                '实现write()',
                '注册到选择表',
                '编译测试'
            ]
        },
        'modify_boundary': {
            'description': '修改边界条件',
            'required_files': ['ExistingBC.H', 'ExistingBC.C'],
            'steps': [
                '分析当前实现',
                '确认修改不影响现有案例',
                '修改实现',
                '测试验证'
            ]
        },
        'extend_model': {
            'description': '扩展物理模型',
            'required_files': ['Model.H', 'Model.C'],
            'steps': [
                '创建派生模型类',
                '添加新参数和成员',
                '重写correct()等方法',
                '配置参数读取',
                '注册模型',
                '测试验证'
            ]
        },
        'modify_model_params': {
            'description': '修改模型参数',
            'required_files': ['configFile'],
            'steps': [
                '定位参数位置',
                '理解参数物理意义',
                '修改参数值',
                '验证计算结果'
            ]
        }
    }
    
    def __init__(self, openfoam_src: str = None, access_mode: AccessMode = AccessMode.AUTO):
        """
        初始化修改建议生成器
        
        Args:
            openfoam_src: OpenFOAM src目录路径
            access_mode: 代码访问模式
        """
        self.accessor = CodeAccessor(openfoam_src=openfoam_src, access_mode=access_mode)
        self.inheritance_analyzer = InheritanceAnalyzer(openfoam_src=openfoam_src, access_mode=access_mode)
        self.boundary_analyzer = BoundaryAnalyzer(openfoam_src=openfoam_src, access_mode=access_mode)
        self.model_analyzer = ModelAnalyzer(openfoam_src=openfoam_src, access_mode=access_mode)
        
    def generate_suggestions(self, 
                            target_type: str,
                            target_name: str,
                            action: str,
                            model_type: str = None,
                            analysis_result: Dict = None) -> Dict[str, Any]:
        """
        生成修改建议
        
        Args:
            target_type: 目标类型 (class/boundary/model)
            target_name: 目标名称
            action: 操作类型 (create/extend/modify)
            model_type: 模型类型（仅用于model目标）
            analysis_result: 预分析结果（可选）
            
        Returns:
            修改建议结果
        """
        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "target": {
                "type": target_type,
                "name": target_name,
                "action": action
            },
            "suggestions": []
        }
        
        # 获取分析结果
        if not analysis_result:
            analysis_result = self._analyze_target(target_type, target_name, model_type)
        
        result["analysis"] = analysis_result
        
        # 根据目标类型和操作生成建议
        if target_type == "class":
            suggestions = self._generate_class_suggestions(target_name, action, analysis_result)
        elif target_type == "boundary":
            suggestions = self._generate_boundary_suggestions(target_name, action, analysis_result)
        elif target_type == "model":
            suggestions = self._generate_model_suggestions(target_name, action, model_type, analysis_result)
        else:
            suggestions = [{
                "type": "error",
                "description": f"未知的目标类型: {target_type}"
            }]
        
        result["suggestions"] = suggestions
        
        # 添加通用建议
        result["general_recommendations"] = self._get_general_recommendations(target_type, action)
        
        return result
    
    def _analyze_target(self, target_type: str, target_name: str, 
                        model_type: str = None) -> Dict[str, Any]:
        """分析目标"""
        analysis = {}
        
        if target_type == "class":
            info = self.inheritance_analyzer.get_class_info(target_name)
            if info:
                analysis["class_info"] = info.to_dict()
                analysis["inheritance_chain"] = [
                    c.to_dict() for c in self.inheritance_analyzer.get_inheritance_chain(target_name)
                ]
                analysis["design_patterns"] = self.inheritance_analyzer.analyze_design_pattern(target_name)
                analysis["virtual_functions"] = self.inheritance_analyzer.analyze_virtual_functions(target_name)
                
        elif target_type == "boundary":
            info = self.boundary_analyzer.find_boundary_condition(target_name)
            if info:
                analysis["bc_info"] = info.to_dict()
                analysis["parameters"] = self.boundary_analyzer.analyze_parameters(target_name)
                analysis["base_class_info"] = self.boundary_analyzer.get_base_class_info(target_name)
                
        elif target_type == "model":
            if model_type == 'turbulence':
                analysis = self.model_analyzer.analyze_turbulence_model(target_name)
            elif model_type == 'multiphase':
                analysis = self.model_analyzer.analyze_multiphase_model(target_name)
            elif model_type == 'thermophysical':
                analysis = self.model_analyzer.analyze_thermophysical_model(target_name)
        
        return analysis
    
    def _generate_class_suggestions(self, class_name: str, action: str,
                                    analysis: Dict) -> List[Dict[str, Any]]:
        """生成类修改建议"""
        suggestions = []
        
        if action == "extend":
            template_key = "extend_class"
            class_info = analysis.get("class_info", {})
            
            suggestions.append({
                "type": "create_derived_class",
                "description": f"创建 {class_name} 的派生类",
                "priority": "high",
                "template": self._generate_derived_class_code(class_name, analysis),
                "implementation_template": self._generate_implementation_code(class_name, analysis),
                "make_files_template": self._generate_make_files(class_name, "Derived"),
                "steps": self.MODIFICATION_TEMPLATES[template_key]['steps'],
                "required_files": self._get_required_files(template_key, class_name, "Derived"),
                "references": [class_info.get("file_path", "")]
            })
            
            # 检查虚函数
            virtual_info = analysis.get("virtual_functions", {})
            pure_virtuals = virtual_info.get("pure_virtual", [])
            
            if pure_virtuals:
                suggestions.append({
                    "type": "implement_pure_virtual",
                    "description": "需要实现的纯虚函数",
                    "priority": "critical",
                    "functions": pure_virtuals,
                    "note": "所有纯虚函数必须在派生类中实现"
                })
                
        elif action == "modify":
            class_info = analysis.get("class_info", {})
            
            suggestions.append({
                "type": "modify_implementation",
                "description": f"修改 {class_name} 的实现",
                "priority": "medium",
                "considerations": [
                    "检查继承链中是否有其他类依赖此功能",
                    "如果修改虚函数，确认是否影响派生类",
                    "考虑是否需要修改基类接口",
                    "建议创建派生类而非直接修改基类"
                ],
                "files_to_modify": [
                    {"path": class_info.get("file_path", ""), "description": "头文件声明"},
                    {"path": class_info.get("file_path", "").replace('.H', '.C'), "description": "实现文件"}
                ],
                "backup_recommendation": "修改前请备份原始文件",
                "steps": self.MODIFICATION_TEMPLATES['modify_class']['steps']
            })
            
        elif action == "create":
            suggestions.append({
                "type": "create_new_class",
                "description": f"创建新类 {class_name}",
                "priority": "high",
                "template": self._generate_new_class_code(class_name),
                "steps": self.MODIFICATION_TEMPLATES['create_class']['steps'],
                "required_files": self._get_required_files("create_class", class_name)
            })
        
        return suggestions
    
    def _generate_boundary_suggestions(self, bc_name: str, action: str,
                                       analysis: Dict) -> List[Dict[str, Any]]:
        """生成边界条件修改建议"""
        suggestions = []
        
        if action == "create":
            bc_info = analysis.get("bc_info", {})
            params = analysis.get("parameters", {})
            
            suggestions.append({
                "type": "create_boundary_condition",
                "description": f"创建新边界条件 {bc_name}Custom",
                "priority": "high",
                "header_template": self._generate_bc_header_template(bc_name, analysis),
                "implementation_template": self._generate_bc_implementation_template(bc_name, analysis),
                "steps": self.MODIFICATION_TEMPLATES['create_boundary']['steps'],
                "required_files": [
                    f"{bc_name}CustomFvPatchField.H",
                    f"{bc_name}CustomFvPatchField.C"
                ],
                "parameter_example": self._generate_bc_config_example(bc_name, params)
            })
            
        elif action == "modify":
            bc_info = analysis.get("bc_info", {})
            params = analysis.get("parameters", {})
            
            suggestions.append({
                "type": "modify_boundary_condition",
                "description": f"修改边界条件 {bc_name}",
                "priority": "medium",
                "current_parameters": params.get("parameters", []),
                "files_to_modify": [
                    {"path": bc_info.get("file_path", ""), "description": "头文件"},
                    {"path": bc_info.get("file_path", "").replace('.H', '.C'), "description": "实现文件"}
                ],
                "steps": self.MODIFICATION_TEMPLATES['modify_boundary']['steps']
            })
            
        elif action == "use":
            params = analysis.get("parameters", {})
            base_info = analysis.get("base_class_info", {})
            
            suggestions.append({
                "type": "usage_guide",
                "description": f"如何使用 {bc_name} 边界条件",
                "config_example": self._generate_bc_config_example(bc_name, params),
                "required_parameters": params.get("required_parameters", []),
                "optional_parameters": params.get("optional_parameters", []),
                "notes": [
                    f"基类: {base_info.get('base_class', 'unknown')}",
                    f"类型: {base_info.get('base_class_type', 'unknown')}"
                ]
            })
        
        return suggestions
    
    def _generate_model_suggestions(self, model_name: str, action: str,
                                    model_type: str, analysis: Dict) -> List[Dict[str, Any]]:
        """生成模型修改建议"""
        suggestions = []
        
        if action == "extend":
            suggestions.append({
                "type": "extend_model",
                "description": f"扩展 {model_name} 模型",
                "priority": "high",
                "header_template": self._generate_model_header_template(model_name, model_type, analysis),
                "implementation_template": self._generate_model_implementation_template(model_name, model_type, analysis),
                "steps": self.MODIFICATION_TEMPLATES['extend_model']['steps'],
                "config_template": self._generate_model_config_template(model_name, model_type, analysis)
            })
            
        elif action == "modify":
            params = analysis.get("parameters", [])
            
            suggestions.append({
                "type": "modify_model_parameters",
                "description": f"修改 {model_name} 模型参数",
                "priority": "medium",
                "current_parameters": params,
                "config_example": self._generate_model_config_template(model_name, model_type, analysis),
                "steps": self.MODIFICATION_TEMPLATES['modify_model_params']['steps']
            })
        
        return suggestions
    
    def _get_general_recommendations(self, target_type: str, action: str) -> List[str]:
        """获取通用建议"""
        recommendations = [
            "在修改前备份原始文件",
            "使用版本控制系统跟踪变更",
            "修改后进行充分测试",
            "更新相关文档",
            "考虑向后兼容性"
        ]
        
        if target_type == "class":
            recommendations.extend([
                "检查继承链中的依赖关系",
                "确保虚函数正确实现",
                "添加适当的访问控制"
            ])
        elif target_type == "boundary":
            recommendations.extend([
                "确认边界条件的适用场景",
                "测试不同网格条件下的行为",
                "验证边界值的正确性"
            ])
        elif target_type == "model":
            recommendations.extend([
                "验证物理意义的一致性",
                "测试数值稳定性",
                "与已知解对比验证"
            ])
        
        return recommendations
    
    # ==================== 代码模板生成方法 ====================
    
    def _generate_derived_class_code(self, class_name: str, analysis: Dict) -> str:
        """生成派生类代码模板"""
        derived_name = f"{class_name}Derived"
        class_info = analysis.get("class_info", {})
        base_classes = class_info.get("base_classes", [])
        base_class = base_classes[0] if base_classes else class_name
        
        virtual_funcs = analysis.get("virtual_functions", {})
        pure_virtuals = virtual_funcs.get("pure_virtual", [])
        
        code = f'''//- {derived_name} - {class_name}的派生类

#ifndef {derived_name}_H
#define {derived_name}_H

#include "{class_name}.H"

namespace Foam
{{

class {derived_name}
:
    public {base_class}
{{
    // 私有成员
    
public:

    //- Runtime type information
    TypeName("{derived_name}");

    // 构造函数
'''

        # 添加构造函数声明
        code += f'''    {derived_name}(const fvPatch& p, const DimensionedField<Type, volMesh>& iF);
    {derived_name}(const {derived_name}& ptf);
    
    virtual ~{derived_name}() = default;
'''

        # 添加需要实现的纯虚函数
        if pure_virtuals:
            code += "\n    // 需要实现的虚函数\n"
            for func in pure_virtuals[:3]:  # 显示前3个
                code += f'''    virtual {func.get('return_type', 'void')} {func['name']}({', '.join(func.get('parameters', []))}) override;
'''
        
        code += '''};

} // End namespace Foam

#endif
'''
        return code
    
    def _generate_implementation_code(self, class_name: str, analysis: Dict) -> str:
        """生成实现文件模板"""
        derived_name = f"{class_name}Derived"
        
        return f'''//- {derived_name} 实现

#include "{derived_name}.H"
#include "addToRunTimeSelectionTable.H"

namespace Foam
{{

// 添加到运行时选择表
addToRunTimeSelectionTable(fvPatchField, {derived_name}, patch);

// 构造函数
{derived_name}::{derived_name}
(
    const fvPatch& p,
    const DimensionedField<Type, volMesh>& iF
)
:
    {class_name}(p, iF)
{{}}

{derived_name}::{derived_name}(const {derived_name}& ptf)
:
    {class_name}(ptf)
{{}}

// 其他成员函数实现...

}} // End namespace Foam
'''
    
    def _generate_make_files(self, class_name: str, suffix: str) -> str:
        """生成Make/files模板"""
        derived_name = f"{class_name}{suffix}"
        return f'''# Make/files

{derived_name}/{derived_name}.C

EXE = $(FOAM_USER_APPBIN)/{derived_name}
'''
    
    def _generate_new_class_code(self, class_name: str) -> str:
        """生成新类模板"""
        return f'''//- {class_name} - 新类定义

#ifndef {class_name}_H
#define {class_name}_H

#include "fvPatchField.H"

namespace Foam
{{

class {class_name}
{{
private:

    // 私有成员
    
public:

    // 构造函数
    {class_name}();
    
    // 成员函数
    void doSomething();
}};

}} // End namespace Foam

#endif
'''
    
    def _generate_bc_header_template(self, bc_name: str, analysis: Dict) -> str:
        """生成边界条件头文件模板"""
        new_bc = f"{bc_name}Custom"
        bc_info = analysis.get("bc_info", {})
        base_class = bc_info.get("base_class", "fixedValueFvPatchField")
        
        return f'''//- {new_bc}FvPatchField - 自定义边界条件

#ifndef {new_bc}FvPatchField_H
#define {new_bc}FvPatchField_H

#include "{base_class}.H"

namespace Foam
{{

template<class Type>
class {new_bc}FvPatchField
:
    public {base_class}<Type>
{{
public:

    TypeName("{new_bc}");

    // 构造函数
    {new_bc}FvPatchField
    (
        const fvPatch& p,
        const DimensionedField<Type, volMesh>& iF
    );

    {new_bc}FvPatchField
    (
        const fvPatch& p,
        const DimensionedField<Type, volMesh>& iF,
        const dictionary& dict
    );

    // 成员函数
    virtual void updateCoeffs();
    virtual void write(Ostream& os) const;
}};

}} // End namespace Foam

#endif
'''
    
    def _generate_bc_implementation_template(self, bc_name: str, analysis: Dict) -> str:
        """生成边界条件实现模板"""
        new_bc = f"{bc_name}Custom"
        
        return f'''//- {new_bc}FvPatchField 实现

#include "{new_bc}FvPatchField.H"
#include "addToRunTimeSelectionTable.H"

namespace Foam
{{

makePatchTypeField(fvPatchField, {new_bc}FvPatchField);

template<class Type>
void {new_bc}FvPatchField<Type>::updateCoeffs()
{{
    if (this->updated())
    {{
        return;
    }}

    // TODO: 实现边界条件更新逻辑
    
    fvPatchField<Type>::updateCoeffs();
}}

template<class Type>
void {new_bc}FvPatchField<Type>::write(Ostream& os) const
{{
    fvPatchField<Type>::write(os);
    // 写入额外参数
}}

}} // End namespace Foam
'''
    
    def _generate_bc_config_example(self, bc_name: str, params: Dict) -> str:
        """生成边界条件配置示例"""
        required = params.get("required_parameters", [])
        optional = params.get("optional_parameters", [])
        
        config = f'''"{bc_name}"
{{
    type            {bc_name};
'''
        
        for p in required:
            config += f'    {p["name"]:<15} <value>;  // {p.get("description", "")}\n'
        
        for p in optional:
            config += f'    // {p["name"]:<13} {p.get("default", "")};  // 可选\n'
        
        config += '}'
        return config
    
    def _generate_model_header_template(self, model_name: str, model_type: str, 
                                        analysis: Dict) -> str:
        """生成模型头文件模板"""
        new_model = f"{model_name}Custom"
        base_class = analysis.get("base_class", f"{model_type}Model")
        
        return f'''//- {new_model} - 自定义模型

#ifndef {new_model}_H
#define {new_model}_H

#include "{base_class}.H"

namespace Foam
{{

class {new_model}
:
    public {base_class}
{{
public:

    TypeName("{new_model}");

    // 构造函数和成员函数
    virtual void correct();
}};

}} // End namespace Foam

#endif
'''
    
    def _generate_model_implementation_template(self, model_name: str, model_type: str,
                                                analysis: Dict) -> str:
        """生成模型实现模板"""
        new_model = f"{model_name}Custom"
        
        return f'''//- {new_model} 实现

#include "{new_model}.H"

namespace Foam
{{

addToRunTimeSelectionTable({model_type}Model, {new_model}, dictionary);

void {new_model}::correct()
{{
    // TODO: 实现模型计算逻辑
}}

}} // End namespace Foam
'''
    
    def _generate_model_config_template(self, model_name: str, model_type: str,
                                        analysis: Dict) -> str:
        """生成模型配置模板"""
        params = analysis.get("parameters", [])
        
        config_file = {
            'turbulence': 'turbulenceProperties',
            'multiphase': 'transportProperties',
            'thermophysical': 'thermophysicalProperties'
        }.get(model_type, 'properties')
        
        config = f'''// {config_file}

simulationType  RAS;
RAS
{{
    {model_name}
    {{
'''
        
        for p in params[:5]:
            config += f'        // {p["name"]:<12} {p.get("default", "")};\n'
        
        config += '''    }
}
'''
        return config
    
    def _get_required_files(self, template_key: str, class_name: str, 
                            suffix: str = "") -> List[str]:
        """获取需要的文件列表"""
        template = self.MODIFICATION_TEMPLATES.get(template_key, {})
        required = template.get("required_files", [])
        
        # 替换占位符
        result = []
        for f in required:
            if "Header" in f:
                result.append(f.replace("Header", f"{class_name}{suffix}"))
            elif "Implementation" in f:
                result.append(f.replace("Implementation", f"{class_name}{suffix}"))
            elif "BC" in f:
                result.append(f.replace("BC", f"{class_name}{suffix}"))
            elif "Model" in f:
                result.append(f.replace("Model", f"{class_name}{suffix}"))
            else:
                result.append(f)
        
        return result
    
    def generate_from_analysis_file(self, analysis_file: str) -> Dict[str, Any]:
        """从分析结果文件生成建议"""
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        # 从分析结果提取信息
        target_type = analysis.get("target_type", "class")
        target_name = analysis.get("target_name", "Unknown")
        action = analysis.get("action", "extend")
        model_type = analysis.get("model_type")
        
        return self.generate_suggestions(target_type, target_name, action, model_type, analysis)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='OpenFOAM 代码修改建议生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --target class --name kEpsilon --action extend
  %(prog)s --target boundary --name fixedValue --action create
  %(prog)s --target model --type turbulence --name kOmegaSST --action modify
  %(prog)s --input analysis_result.json
        """
    )
    
    parser.add_argument('--root', type=str,
                        default=os.environ.get('FOAM_SRC', '/opt/openfoam/src'),
                        help='OpenFOAM src 目录路径')
    parser.add_argument('--mode', choices=['auto', 'mcp', 'local'], default='auto',
                        help='代码访问模式')
    
    # 分析命令
    parser.add_argument('--target', choices=['class', 'boundary', 'model'],
                        help='目标类型')
    parser.add_argument('--name', type=str,
                        help='目标名称')
    parser.add_argument('--type', dest='model_type',
                        choices=['turbulence', 'multiphase', 'thermophysical'],
                        help='模型类型（仅用于model目标）')
    parser.add_argument('--action', choices=['create', 'extend', 'modify', 'use'],
                        default='extend',
                        help='操作类型')
    parser.add_argument('--input', type=str,
                        help='分析结果文件路径')
    parser.add_argument('--output', type=str,
                        help='输出文件路径')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                        help='输出格式')
    parser.add_argument('-v', '--version', action='store_true',
                        help='显示版本信息')
    
    args = parser.parse_args()
    
    # 显示版本信息
    if args.version:
        print_version()
        return
    
    # 创建修改建议生成器
    modifier = CodeModifier(
        openfoam_src=args.root,
        access_mode=AccessMode(args.mode)
    )
    
    # 生成建议
    if args.input:
        result = modifier.generate_from_analysis_file(args.input)
    elif args.target and args.name:
        result = modifier.generate_suggestions(
            args.target, args.name, args.action, args.model_type
        )
    else:
        parser.print_help()
        return
    
    # 输出结果
    if args.format == 'json':
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = _format_text_output(result)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
    else:
        print(output)


def _format_text_output(result: Dict) -> str:
    """文本格式化输出"""
    lines = []
    
    target = result.get("target", {})
    lines.append(f"目标: {target.get('type', '')} - {target.get('name', '')}")
    lines.append(f"操作: {target.get('action', '')}")
    lines.append(f"时间: {result.get('timestamp', '')}")
    
    lines.append("\n" + "=" * 50)
    lines.append("修改建议:")
    lines.append("=" * 50)
    
    for i, suggestion in enumerate(result.get("suggestions", []), 1):
        lines.append(f"\n{i}. [{suggestion.get('type', '')}] {suggestion.get('description', '')}")
        
        if "steps" in suggestion:
            lines.append("   步骤:")
            for step in suggestion["steps"]:
                lines.append(f"     - {step}")
        
        if "template" in suggestion:
            lines.append("   代码模板:")
            for line in suggestion["template"].split('\n')[:10]:
                lines.append(f"     {line}")
            if len(suggestion["template"].split('\n')) > 10:
                lines.append("     ...")
    
    lines.append("\n" + "=" * 50)
    lines.append("通用建议:")
    lines.append("=" * 50)
    for rec in result.get("general_recommendations", []):
        lines.append(f"  - {rec}")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    main()
