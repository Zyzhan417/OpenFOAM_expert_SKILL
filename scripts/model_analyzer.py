#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM 物理模型分析脚本

功能:
1. 分析湍流模型（RANS/LES）
2. 分析多相流模型（VOF/Eulerian）
3. 分析热物理模型
4. 分析粒子群平衡模型
5. 生成修改建议

使用方法:
    python model_analyzer.py --type turbulence --name kEpsilon
    python model_analyzer.py --type multiphase --name interFoam
    python model_analyzer.py --type thermophysical --name heRhoThermo
    python model_analyzer.py --type turbulence --search "*kOmega*"
"""

import os
import sys
import re
import json
import argparse
import io
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any

# Windows平台设置stdout为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加核心模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.code_accessor import CodeAccessor, AccessMode
from core.code_parser import CodeParser, ModelInfo
from core.version import get_version_string, print_version


class ModelAnalyzer:
    """物理模型分析器"""
    
    # 模型类型定义
    MODEL_TYPES = {
        'turbulence': {
            'name': '湍流模型',
            'base_classes': ['turbulenceModel', 'RASModel', 'LESModel', 'linearViscousStress'],
            'directories': ['turbulenceModels'],
            'config_file': 'turbulenceProperties'
        },
        'multiphase': {
            'name': '多相流模型',
            'base_classes': ['multiphaseSystem', 'phaseSystem', 'interPhaseProperties'],
            'directories': ['multiphaseInterFoam', 'multiphaseEulerFoam'],
            'config_file': 'transportProperties'
        },
        'thermophysical': {
            'name': '热物理模型',
            'base_classes': ['basicThermo', 'fluidThermo', 'heThermo', 'rhoThermo'],
            'directories': ['thermophysicalModels'],
            'config_file': 'thermophysicalProperties'
        },
        'populationBalance': {
            'name': '粒子群平衡模型',
            'base_classes': ['populationBalanceModel', 'coalescenceModel', 'breakupModel'],
            'directories': ['populationBalance'],
            'config_file': 'populationBalanceProperties'
        },
        'reaction': {
            'name': '反应模型',
            'base_classes': ['reaction', 'Reaction', 'singleStepReactingMixture'],
            'directories': ['thermophysicalModels/reactionThermo'],
            'config_file': 'reactions'
        }
    }
    
    # 湍流模型详情
    TURBULENCE_MODELS = {
        'kEpsilon': {
            'type': 'RANS', 'equations': ['k方程', 'epsilon方程'],
            'description': '标准k-ε模型，适用于高雷诺数流动'
        },
        'realizableKEpsilon': {
            'type': 'RANS', 'equations': ['k方程', 'epsilon方程'],
            'description': '可实现k-ε模型，改进了应变敏感性'
        },
        'kOmega': {
            'type': 'RANS', 'equations': ['k方程', 'omega方程'],
            'description': '标准k-ω模型，适用于近壁流动'
        },
        'kOmegaSST': {
            'type': 'RANS', 'equations': ['k方程', 'omega方程'],
            'description': 'SST k-ω模型，结合k-ε和k-ω优点'
        },
        'kOmegaSSTLM': {
            'type': 'RANS', 'equations': ['k方程', 'omega方程', 'γ-Reθ方程'],
            'description': 'SST模型+转捩模型'
        },
        'SpalartAllmaras': {
            'type': 'RANS', 'equations': ['nuTilda方程'],
            'description': '单方程模型，适用于外部流动'
        },
        'Smagorinsky': {
            'type': 'LES', 'equations': ['亚网格尺度'],
            'description': '基础LES模型'
        },
        'dynamicLagrangian': {
            'type': 'LES', 'equations': ['亚网格尺度', '动态系数'],
            'description': '动态Lagrangian LES模型'
        },
        'kEqn': {
            'type': 'LES', 'equations': ['k方程'],
            'description': '单方程LES模型'
        }
    }
    
    # 多相流模型详情
    MULTIPHASE_MODELS = {
        'interFoam': {
            'type': 'VOF', 'phases': 2,
            'description': 'VOF方法，两相流界面追踪'
        },
        'interDyMFoam': {
            'type': 'VOF', 'phases': 2,
            'description': 'VOF方法 + 动网格'
        },
        'interIsoFoam': {
            'type': 'VOF', 'phases': 2,
            'description': 'VOF方法 + 几何重构'
        },
        'multiphaseEulerFoam': {
            'type': 'Eulerian', 'phases': 'n',
            'description': '多相欧拉方法，支持任意相数'
        },
        'twoPhaseEulerFoam': {
            'type': 'Eulerian', 'phases': 2,
            'description': '两相欧拉方法'
        },
        'reactingTwoPhaseEulerFoam': {
            'type': 'Eulerian', 'phases': 2,
            'description': '反应两相欧拉方法'
        },
        'driftFlux': {
            'type': 'DriftFlux', 'phases': 2,
            'description': '漂移通量模型'
        }
    }
    
    # 热物理模型详情
    THERMOPHYSICAL_MODELS = {
        'heRhoThermo': {
            'type': '可压缩', 'equations': ['能量', '状态方程'],
            'description': '基于焓的可压缩热物理模型'
        },
        'hePsiThermo': {
            'type': '可压缩', 'equations': ['能量', '状态方程'],
            'description': '基于焓的可压缩模型（压缩性）'
        },
        'rhoThermo': {
            'type': '可压缩', 'equations': ['状态方程'],
            'description': '基础可压缩模型'
        },
        'pureMixture': {
            'type': '混合物', 'equations': ['状态方程'],
            'description': '纯物质混合物'
        },
        'reactingMixture': {
            'type': '反应', 'equations': ['能量', '组分输运', '反应'],
            'description': '反应混合物'
        },
        'multiComponentMixture': {
            'type': '多组分', 'equations': ['组分输运'],
            'description': '多组分混合物'
        },
        'icoPolynomial': {
            'type': '状态方程', 'equations': ['多项式'],
            'description': '不可压缩多项式状态方程'
        },
        'perfectFluid': {
            'type': '状态方程', 'equations': ['理想气体'],
            'description': '完美流体状态方程'
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
        
        # 缓存
        self._model_cache: Dict[str, ModelInfo] = {}
        
    def find_model(self, model_name: str, model_type: str = None) -> Optional[ModelInfo]:
        """
        查找模型
        
        Args:
            model_name: 模型名称
            model_type: 模型类型（可选，用于缩小搜索范围）
            
        Returns:
            模型信息
        """
        cache_key = f"{model_type}:{model_name}" if model_type else model_name
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]
        
        # 确定搜索范围
        if model_type and model_type in self.MODEL_TYPES:
            directories = self.MODEL_TYPES[model_type]['directories']
        else:
            directories = None
        
        # 搜索模型类定义
        pattern = rf"class\s+{model_name}\s*:\s*public"
        results = self.accessor.search_code(pattern, file_types=".H", scope="source", max_results=10)
        
        if not results:
            return None
        
        # 解析找到的模型
        for result in results:
            content = self.accessor.read_file(result.file_path)
            if content:
                detected_type = self._detect_model_type(result.file_path)
                model_info = self.parser.parse_model(content.content, result.file_path, detected_type)
                
                if model_info and model_info.name == model_name:
                    self._model_cache[cache_key] = model_info
                    return model_info
        
        return None
    
    def _detect_model_type(self, file_path: str) -> str:
        """检测模型类型"""
        for model_type, info in self.MODEL_TYPES.items():
            for directory in info['directories']:
                if directory in file_path:
                    return model_type
        return "unknown"
    
    def analyze_turbulence_model(self, model_name: str) -> Dict[str, Any]:
        """
        分析湍流模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型分析结果
        """
        result = {
            "model_name": model_name,
            "model_type": "turbulence"
        }
        
        # 获取预定义信息
        predefined = self.TURBULENCE_MODELS.get(model_name, {})
        result["category"] = predefined.get('type', 'Unknown')
        result["equations"] = predefined.get('equations', [])
        result["description"] = predefined.get('description', '')
        
        # 查找模型实现
        model_info = self.find_model(model_name, 'turbulence')
        if model_info:
            result["file_path"] = model_info.file_path
            result["line_number"] = model_info.line_number
            result["base_class"] = model_info.base_class
            
            # 分析参数
            result["parameters"] = self._extract_model_parameters(model_info)
        
        # 查找相关文件
        result["related_files"] = self._find_related_files(model_name, 'turbulence')
        
        return result
    
    def analyze_multiphase_model(self, model_name: str) -> Dict[str, Any]:
        """
        分析多相流模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型分析结果
        """
        result = {
            "model_name": model_name,
            "model_type": "multiphase"
        }
        
        # 获取预定义信息
        predefined = self.MULTIPHASE_MODELS.get(model_name, {})
        result["category"] = predefined.get('type', 'Unknown')
        result["phases"] = predefined.get('phases', 'unknown')
        result["description"] = predefined.get('description', '')
        
        # 查找求解器主文件
        solver_pattern = rf"int\s+main\s*\(.*\)"
        solver_results = self.accessor.search_code(
            solver_pattern, 
            file_types=".C", 
            scope="applications", 
            max_results=20
        )
        
        for r in solver_results:
            if model_name in r.file_path:
                result["solver_file"] = r.file_path
                break
        
        # 查找相关文件
        result["related_files"] = self._find_related_files(model_name, 'multiphase')
        
        return result
    
    def analyze_thermophysical_model(self, model_name: str) -> Dict[str, Any]:
        """
        分析热物理模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型分析结果
        """
        result = {
            "model_name": model_name,
            "model_type": "thermophysical"
        }
        
        # 获取预定义信息
        predefined = self.THERMOPHYSICAL_MODELS.get(model_name, {})
        result["category"] = predefined.get('type', 'Unknown')
        result["equations"] = predefined.get('equations', [])
        result["description"] = predefined.get('description', '')
        
        # 查找模型实现
        model_info = self.find_model(model_name, 'thermophysical')
        if model_info:
            result["file_path"] = model_info.file_path
            result["line_number"] = model_info.line_number
            result["base_class"] = model_info.base_class
            result["parameters"] = self._extract_model_parameters(model_info)
        
        # 查找相关文件
        result["related_files"] = self._find_related_files(model_name, 'thermophysical')
        
        return result
    
    def _extract_model_parameters(self, model_info: ModelInfo) -> List[Dict[str, str]]:
        """提取模型参数"""
        params = []
        
        content = self.accessor.read_file(model_info.file_path)
        if not content:
            return params
        
        # 查找lookupOrDefault调用
        pattern = re.compile(
            r'lookupOrDefault\s*<\w+>\s*\(\s*["\'](\w+)["\']\s*,\s*([^)]+)\)'
        )
        
        seen = set()
        for match in pattern.finditer(content.content):
            param_name = match.group(1)
            default_val = match.group(2).strip()
            
            if param_name not in seen:
                seen.add(param_name)
                params.append({
                    "name": param_name,
                    "default": default_val,
                    "description": self._guess_param_description(param_name)
                })
        
        return params
    
    def _guess_param_description(self, param_name: str) -> str:
        """猜测参数描述"""
        descriptions = {
            'Cmu': '模型常数 Cμ',
            'C1': '模型常数 C1',
            'C2': '模型常数 C2',
            'sigmaEps': 'epsilon的普朗特数',
            'sigmaK': 'k的普朗特数',
            'beta1': 'k-ω模型常数 β1',
            'beta2': 'k-ε模型常数 β2',
            'gamma1': 'k-ω模型常数 γ1',
            'gamma2': 'k-ε模型常数 γ2',
            'a1': 'SST模型常数 a1',
            'Prt': '湍流普朗特数',
            'C3': '浮力模型常数',
            'sigmas': 'σ的普朗特数',
            'alpha': 'α系数'
        }
        return descriptions.get(param_name, param_name)
    
    def _find_related_files(self, model_name: str, model_type: str) -> List[Dict[str, str]]:
        """查找相关文件"""
        related = []
        
        # 查找头文件
        header_results = self.accessor.search_code(
            rf"{model_name}\.H",
            file_types=".H",
            scope="source",
            max_results=5
        )
        
        for r in header_results:
            if model_name in r.file_path:
                related.append({
                    "file": r.file_path,
                    "type": "header",
                    "description": "模型头文件"
                })
                break
        
        # 查找实现文件
        impl_results = self.accessor.search_code(
            rf"{model_name}::",
            file_types=".C",
            scope="source",
            max_results=5
        )
        
        for r in impl_results:
            if model_name in r.file_path:
                related.append({
                    "file": r.file_path,
                    "type": "implementation",
                    "description": "模型实现文件"
                })
                break
        
        return related
    
    def list_models(self, model_type: str = None) -> List[Dict[str, str]]:
        """
        列出模型
        
        Args:
            model_type: 模型类型过滤
            
        Returns:
            模型列表
        """
        models = []
        
        if model_type == 'turbulence' or model_type is None:
            for name, info in self.TURBULENCE_MODELS.items():
                models.append({
                    "name": name,
                    "type": "turbulence",
                    "category": info['type'],
                    "description": info['description']
                })
        
        if model_type == 'multiphase' or model_type is None:
            for name, info in self.MULTIPHASE_MODELS.items():
                models.append({
                    "name": name,
                    "type": "multiphase",
                    "category": info['type'],
                    "description": info['description']
                })
        
        if model_type == 'thermophysical' or model_type is None:
            for name, info in self.THERMOPHYSICAL_MODELS.items():
                models.append({
                    "name": name,
                    "type": "thermophysical",
                    "category": info['type'],
                    "description": info['description']
                })
        
        return models
    
    def search_models(self, pattern: str, model_type: str = None) -> List[Dict[str, Any]]:
        """
        搜索模型
        
        Args:
            pattern: 搜索模式
            model_type: 模型类型过滤
            
        Returns:
            匹配的模型列表
        """
        import fnmatch
        
        all_models = self.list_models(model_type)
        
        matches = []
        for model in all_models:
            if fnmatch.fnmatch(model['name'].lower(), pattern.lower()) or \
               pattern.lower() in model['name'].lower():
                matches.append(model)
        
        return matches
    
    def generate_modification_suggestions(self, model_name: str, 
                                          model_type: str,
                                          modification_type: str = "extend") -> List[Dict[str, Any]]:
        """
        生成修改建议
        
        Args:
            model_name: 模型名称
            model_type: 模型类型
            modification_type: 修改类型
            
        Returns:
            修改建议列表
        """
        suggestions = []
        
        if model_type == 'turbulence':
            analysis = self.analyze_turbulence_model(model_name)
        elif model_type == 'multiphase':
            analysis = self.analyze_multiphase_model(model_name)
        elif model_type == 'thermophysical':
            analysis = self.analyze_thermophysical_model(model_name)
        else:
            return suggestions
        
        if modification_type == "extend":
            # 扩展模型
            suggestions.append({
                "type": "extend_model",
                "description": f"扩展 {model_name} 模型",
                "template": self._generate_model_template(model_name, model_type, analysis),
                "steps": [
                    f"1. 创建派生类 {model_name}Custom",
                    "2. 继承原模型基类",
                    "3. 添加新的参数和成员",
                    "4. 重写必要的方法",
                    "5. 注册到运行时选择表",
                    "6. 编译测试"
                ],
                "considerations": [
                    "确保新模型与原模型兼容",
                    "保持物理意义一致性",
                    "添加充分测试"
                ],
                "references": analysis.get("related_files", [])
            })
        
        elif modification_type == "modify":
            # 修改模型参数
            params = analysis.get("parameters", [])
            suggestions.append({
                "type": "modify_parameters",
                "description": f"修改 {model_name} 模型参数",
                "current_parameters": params,
                "how_to_modify": f'''在 {self.MODEL_TYPES.get(model_type, {}).get("config_file", "配置文件")} 中修改:

simulationType  RAS;
RAS
{{
    {model_name}
    {{
        // 修改参数
        {" ".join([f"// {p['name']:<15} {p.get('default', '')};" for p in params[:5]])}
    }}
}}''',
                "caution": "修改模型参数可能影响计算稳定性和结果准确性"
            })
        
        elif modification_type == "add_equation":
            # 添加新方程
            suggestions.append({
                "type": "add_equation",
                "description": f"为 {model_name} 添加新方程",
                "steps": [
                    "1. 定义新的场变量",
                    "2. 编写输运方程",
                    "3. 添加源项（如需要）",
                    "4. 配置离散格式",
                    "5. 添加求解器设置"
                ],
                "template": '''// 在求解器主文件中添加
fvScalarMatrix newEqn
(
    fvm::ddt(newField)
  + fvm::div(phi, newField)
  - fvm::laplacian(Dnew, newField)
 ==
    sourceTerm
);

newEqn.relax();
newEqn.solve();'''
            })
        
        return suggestions
    
    def _generate_model_template(self, model_name: str, 
                                  model_type: str, 
                                  analysis: Dict) -> str:
        """生成模型模板"""
        base_class = analysis.get("base_class", f"{model_type}Model")
        new_model = f"{model_name}Custom"
        
        return f'''//- {new_model} - 自定义{model_type}模型

#ifndef {new_model}_H
#define {new_model}_H

#include "{base_class}.H"

namespace Foam
{{

class {new_model}
:
    public {base_class}
{{
protected:

    // 受保护的成员
    
    //- 自定义参数
    dimensionedScalar customParam_;

public:

    //- Runtime type information
    TypeName("{new_model}");

    // 构造函数
    {new_model}
    (
        const alphaField& alpha,
        const rhoField& rho,
        const volVectorField& U,
        const surfaceScalarField& alphaRhoPhi,
        const surfaceScalarField& phi,
        const transportModel& transport,
        const word& propertiesName,
        const word& type = typeName
    );

    //- 析构函数
    virtual ~{new_model}() = default;

    // 成员函数
    
    //- 正确计算
    virtual void correct();

    //- 写入
    virtual bool write();
}};

} // End namespace Foam

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
    
    if "model_name" in result:
        lines.append(f"模型: {result['model_name']}")
        
    if "model_type" in result:
        lines.append(f"类型: {result['model_type']}")
        
    if "category" in result:
        lines.append(f"类别: {result['category']}")
        
    if "description" in result:
        lines.append(f"描述: {result['description']}")
        
    if "file_path" in result:
        lines.append(f"文件: {result['file_path']}")
    
    if "equations" in result:
        lines.append(f"\n方程: {', '.join(result['equations'])}")
    
    if "parameters" in result:
        lines.append("\n参数:")
        for p in result["parameters"]:
            lines.append(f"  - {p['name']}: {p.get('default', '')} ({p.get('description', '')})")
    
    if "modification_suggestions" in result:
        lines.append("\n修改建议:")
        for s in result["modification_suggestions"]:
            lines.append(f"  [{s['type']}] {s['description']}")
    
    return "\n".join(lines)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='OpenFOAM 物理模型分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --type turbulence --name kEpsilon
  %(prog)s --type multiphase --name interFoam
  %(prog)s --type thermophysical --name heRhoThermo
  %(prog)s --type turbulence --search "*kOmega*"
  %(prog)s --list --type turbulence
        """
    )
    
    parser.add_argument('--root', type=str,
                        default=os.environ.get('FOAM_SRC', '/opt/openfoam/src'),
                        help='OpenFOAM src 目录路径')
    parser.add_argument('--mode', choices=['auto', 'mcp', 'local'], default='auto',
                        help='代码访问模式')
    
    # 分析命令
    parser.add_argument('--type', choices=['turbulence', 'multiphase', 'thermophysical', 'populationBalance', 'reaction'],
                        help='模型类型')
    parser.add_argument('--name', type=str,
                        help='模型名称')
    parser.add_argument('--search', type=str,
                        help='搜索模型')
    parser.add_argument('--list', action='store_true',
                        help='列出模型')
    parser.add_argument('--suggest', choices=['extend', 'modify', 'add_equation'],
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
    analyzer = ModelAnalyzer(
        openfoam_src=args.root,
        access_mode=AccessMode(args.mode)
    )
    
    result = {"success": True}
    
    # 执行分析
    if args.name and args.type:
        if args.type == 'turbulence':
            analysis = analyzer.analyze_turbulence_model(args.name)
        elif args.type == 'multiphase':
            analysis = analyzer.analyze_multiphase_model(args.name)
        elif args.type == 'thermophysical':
            analysis = analyzer.analyze_thermophysical_model(args.name)
        else:
            analysis = {"model_name": args.name, "model_type": args.type}
        
        result.update(analysis)
        
        if args.suggest:
            result["modification_suggestions"] = analyzer.generate_modification_suggestions(
                args.name, args.type, args.suggest
            )
    
    elif args.search:
        matches = analyzer.search_models(args.search, args.type)
        result["search_pattern"] = args.search
        result["model_type"] = args.type
        result["total_matches"] = len(matches)
        result["matches"] = matches
    
    elif args.list:
        models = analyzer.list_models(args.type)
        result["model_type"] = args.type or "all"
        result["total"] = len(models)
        result["models"] = models
    
    else:
        parser.print_help()
        return
    
    print(format_output(result, args.format))


if __name__ == '__main__':
    main()
