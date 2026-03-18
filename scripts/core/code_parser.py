#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM代码解析器

解析OpenFOAM源码，提取类定义、函数、继承关系等信息
"""

import re
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class Visibility(Enum):
    """访问可见性"""
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    file_path: str
    line_number: int
    base_classes: List[str] = field(default_factory=list)
    access_specifiers: List[str] = field(default_factory=list)
    is_template: bool = False
    template_parameters: List[str] = field(default_factory=list)
    is_abstract: bool = False
    description: str = ""
    member_functions: List['FunctionInfo'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "base_classes": self.base_classes,
            "access_specifiers": self.access_specifiers,
            "is_template": self.is_template,
            "template_parameters": self.template_parameters,
            "is_abstract": self.is_abstract,
            "description": self.description,
            "member_functions": [f.to_dict() for f in self.member_functions]
        }


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    return_type: str
    parameters: List[str]
    file_path: str
    line_number: int
    is_virtual: bool = False
    is_override: bool = False
    is_const: bool = False
    is_static: bool = False
    visibility: Visibility = Visibility.PUBLIC
    implementation_file: str = ""
    implementation_line: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "return_type": self.return_type,
            "parameters": self.parameters,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "is_virtual": self.is_virtual,
            "is_override": self.is_override,
            "is_const": self.is_const,
            "is_static": self.is_static,
            "visibility": self.visibility.value,
            "implementation_file": self.implementation_file,
            "implementation_line": self.implementation_line
        }


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    total_lines: int
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    namespaces: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path": self.path,
            "total_lines": self.total_lines,
            "classes": [c.to_dict() for c in self.classes],
            "functions": [f.to_dict() for f in self.functions],
            "includes": self.includes,
            "namespaces": self.namespaces
        }


@dataclass
class BoundaryConditionInfo:
    """边界条件信息"""
    name: str
    base_class: str
    file_path: str
    line_number: int
    parameters: List[Dict[str, str]] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "base_class": self.base_class,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "parameters": self.parameters,
            "required_fields": self.required_fields,
            "description": self.description
        }


@dataclass
class ModelInfo:
    """物理模型信息"""
    name: str
    model_type: str  # turbulence, multiphase, thermophysical
    base_class: str
    file_path: str
    line_number: int
    equations: List[str] = field(default_factory=list)
    parameters: List[Dict[str, str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "model_type": self.model_type,
            "base_class": self.base_class,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "equations": self.equations,
            "parameters": self.parameters,
            "dependencies": self.dependencies
        }


class CodeParser:
    """
    OpenFOAM代码解析器
    
    解析OpenFOAM源码文件，提取结构化信息
    """
    
    # 正则表达式模式
    PATTERNS = {
        # 类定义
        'class_def': re.compile(
            r'(?:\/\/\/\s*([^\n]*?)\n)?'  # 可选的Doxygen注释
            r'(template\s*<[^>]*>\s*)?'   # 可选模板声明
            r'class\s+(\w+)\s*'           # 类名
            r'(?:<[^>]*>)?\s*'            # 可选模板参数
            r'(?::\s*((?:public|protected|private)\s+\w+(?:\s*,\s*(?:public|protected|private)\s+\w+)*))?\s*'  # 继承
            r'\{'
        ),
        
        # 模板参数
        'template_params': re.compile(r'template\s*<([^>]*)>'),
        
        # 函数声明
        'function_decl': re.compile(
            r'(virtual\s+)?'              # virtual关键字
            r'(static\s+)?'               # static关键字
            r'(\w+(?:<[^>]*>)?)\s+'       # 返回类型
            r'(\w+)\s*'                   # 函数名
            r'\(([^)]*)\)\s*'             # 参数列表
            r'(const\s+)?'                # const关键字
            r'(override\s+)?'             # override关键字
            r'(?:=\s*0\s*)?;'             # 纯虚函数或分号
        ),
        
        # 函数实现
        'function_impl': re.compile(
            r'(\w+(?:<[^>]*>)?)\s+'       # 返回类型
            r'(\w+)::(\w+)\s*'            # 类名::函数名
            r'\(([^)]*)\)\s*'             # 参数列表
            r'(const\s+)?'                # const关键字
            r'\{'
        ),
        
        # include语句
        'include': re.compile(r'#include\s*[<"]([^>"]+)[>"]'),
        
        # namespace
        'namespace': re.compile(r'namespace\s+(\w+)'),
        
        # 运行时选择表
        'runtime_selection': re.compile(
            r'addToRunTimeSelectionTable\s*\(\s*(\w+)\s*,\s*(\w+)\s*,'
        ),
        
        # 边界条件
        'boundary_condition': re.compile(
            r'class\s+(\w+FvPatchField)\s*:\s*public\s+(\w+FvPatchField)'
        ),
        
        # lookup参数
        'lookup': re.compile(r'\.lookup\s*\(\s*["\'](\w+)["\']\s*\)'),
        'lookupOrDefault': re.compile(
            r'lookupOrDefault\s*<\w+>\s*\(\s*["\'](\w+)["\']\s*,\s*([^)]+)\)'
        ),
        
        # 宏定义
        'define_type_name': re.compile(r'TypeName\s*\(\s*"([^"]+)"\s*\)'),
        'declare_run_time': re.compile(r'declareRunTimeSelectionTable\s*\([^)]+\)'),
        
        # 虚函数判断
        'pure_virtual': re.compile(r'=\s*0'),
    }
    
    def __init__(self):
        """初始化解析器"""
        pass
    
    def parse_file(self, content: str, file_path: str) -> FileInfo:
        """
        解析文件内容
        
        Args:
            content: 文件内容
            file_path: 文件路径
            
        Returns:
            文件信息
        """
        lines = content.split('\n')
        file_info = FileInfo(
            path=file_path,
            total_lines=len(lines)
        )
        
        # 提取includes
        file_info.includes = self._extract_includes(content)
        
        # 提取namespaces
        file_info.namespaces = self._extract_namespaces(content)
        
        # 判断文件类型
        if file_path.endswith('.H'):
            # 头文件：解析类定义
            classes = self._parse_classes(content, file_path)
            file_info.classes = classes
            
            # 提取类中的函数声明
            for cls in classes:
                cls.member_functions = self._parse_member_functions(content, cls)
                
        elif file_path.endswith('.C'):
            # 源文件：解析函数实现
            file_info.functions = self._parse_function_implementations(content, file_path)
            
        return file_info
    
    def _extract_includes(self, content: str) -> List[str]:
        """提取include列表"""
        includes = []
        for match in self.PATTERNS['include'].finditer(content):
            includes.append(match.group(1))
        return includes
    
    def _extract_namespaces(self, content: str) -> List[str]:
        """提取namespace列表"""
        namespaces = []
        for match in self.PATTERNS['namespace'].finditer(content):
            namespaces.append(match.group(1))
        return namespaces
    
    def _parse_classes(self, content: str, file_path: str) -> List[ClassInfo]:
        """解析类定义"""
        classes = []
        
        for match in self.PATTERNS['class_def'].finditer(content):
            description = match.group(1) or ""
            template_part = match.group(2) or ""
            class_name = match.group(3)
            inheritance_list = match.group(4) or ""
            
            # 计算行号
            line_num = content[:match.start()].count('\n') + 1
            
            # 判断是否为模板类
            is_template = bool(template_part)
            template_params = []
            
            if is_template:
                tmpl_match = self.PATTERNS['template_params'].search(template_part)
                if tmpl_match:
                    template_params = [p.strip() for p in tmpl_match.group(1).split(',')]
            
            # 解析基类
            base_classes = []
            access_specifiers = []
            
            if inheritance_list:
                for item in inheritance_list.split(','):
                    parts = item.strip().split()
                    if len(parts) >= 2:
                        access_specifiers.append(parts[0])
                        base_classes.append(parts[1])
            
            # 判断是否为抽象类（需要检查后续的虚函数）
            # 这里简化处理，后续可通过完整解析确定
            
            class_info = ClassInfo(
                name=class_name,
                file_path=file_path,
                line_number=line_num,
                base_classes=base_classes,
                access_specifiers=access_specifiers,
                is_template=is_template,
                template_parameters=template_params,
                description=description.strip()
            )
            
            classes.append(class_info)
        
        return classes
    
    def _parse_member_functions(self, content: str, class_info: ClassInfo) -> List[FunctionInfo]:
        """解析类的成员函数"""
        functions = []
        
        # 找到类定义的范围
        class_start = content.find(f"class {class_info.name}")
        if class_start == -1:
            return functions
            
        # 找到类结束（简化：找到第一个匹配的}）
        brace_count = 0
        class_end = class_start
        in_class = False
        
        for i, char in enumerate(content[class_start:], class_start):
            if char == '{':
                brace_count += 1
                in_class = True
            elif char == '}':
                brace_count -= 1
                if in_class and brace_count == 0:
                    class_end = i
                    break
                    
        class_content = content[class_start:class_end]
        
        # 解析函数声明
        for match in self.PATTERNS['function_decl'].finditer(class_content):
            is_virtual = bool(match.group(1))
            is_static = bool(match.group(2))
            return_type = match.group(3)
            func_name = match.group(4)
            params_str = match.group(5)
            is_const = bool(match.group(6))
            is_override = bool(match.group(7))
            
            # 解析参数
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            
            # 计算行号（相对于文件开头）
            line_in_class = class_content[:match.start()].count('\n')
            line_num = class_info.line_number + line_in_class
            
            func_info = FunctionInfo(
                name=func_name,
                return_type=return_type,
                parameters=params,
                file_path=class_info.file_path,
                line_number=line_num,
                is_virtual=is_virtual,
                is_override=is_override,
                is_const=is_const,
                is_static=is_static
            )
            
            functions.append(func_info)
        
        return functions
    
    def _parse_function_implementations(self, content: str, 
                                         file_path: str) -> List[FunctionInfo]:
        """解析函数实现"""
        functions = []
        
        for match in self.PATTERNS['function_impl'].finditer(content):
            return_type = match.group(1)
            class_name = match.group(2)
            func_name = match.group(3)
            params_str = match.group(4)
            is_const = bool(match.group(5))
            
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            line_num = content[:match.start()].count('\n') + 1
            
            func_info = FunctionInfo(
                name=func_name,
                return_type=return_type,
                parameters=params,
                file_path=file_path,
                line_number=line_num,
                is_const=is_const,
                implementation_file=file_path,
                implementation_line=line_num
            )
            
            functions.append(func_info)
        
        return functions
    
    def parse_boundary_condition(self, content: str, 
                                  file_path: str) -> Optional[BoundaryConditionInfo]:
        """
        解析边界条件
        
        Args:
            content: 文件内容
            file_path: 文件路径
            
        Returns:
            边界条件信息
        """
        match = self.PATTERNS['boundary_condition'].search(content)
        if not match:
            return None
            
        bc_name = match.group(1)
        base_class = match.group(2)
        line_num = content[:match.start()].count('\n') + 1
        
        # 提取参数
        parameters = []
        for lookup_match in self.PATTERNS['lookup'].finditer(content):
            param_name = lookup_match.group(1)
            parameters.append({
                "name": param_name,
                "type": "unknown",
                "default": ""
            })
            
        for lookup_match in self.PATTERNS['lookupOrDefault'].finditer(content):
            param_name = lookup_match.group(1)
            default_val = lookup_match.group(2).strip()
            parameters.append({
                "name": param_name,
                "type": "auto",
                "default": default_val
            })
        
        return BoundaryConditionInfo(
            name=bc_name,
            base_class=base_class,
            file_path=file_path,
            line_number=line_num,
            parameters=parameters
        )
    
    def parse_model(self, content: str, file_path: str,
                    model_type: str) -> Optional[ModelInfo]:
        """
        解析物理模型
        
        Args:
            content: 文件内容
            file_path: 文件路径
            model_type: 模型类型
            
        Returns:
            模型信息
        """
        # 查找类定义
        class_match = self.PATTERNS['class_def'].search(content)
        if not class_match:
            return None
            
        model_name = class_match.group(3)
        inheritance = class_match.group(4) or ""
        
        base_class = ""
        if inheritance:
            parts = inheritance.split(',')
            if parts:
                base_parts = parts[0].strip().split()
                if len(base_parts) >= 2:
                    base_class = base_parts[1]
        
        line_num = content[:class_match.start()].count('\n') + 1
        
        # 提取参数
        parameters = []
        for lookup_match in self.PATTERNS['lookupOrDefault'].finditer(content):
            param_name = lookup_match.group(1)
            default_val = lookup_match.group(2).strip()
            parameters.append({
                "name": param_name,
                "type": "auto",
                "default": default_val
            })
        
        return ModelInfo(
            name=model_name,
            model_type=model_type,
            base_class=base_class,
            file_path=file_path,
            line_number=line_num,
            parameters=parameters
        )
    
    def extract_runtime_selection(self, content: str) -> List[Tuple[str, str]]:
        """
        提取运行时选择表注册信息
        
        Args:
            content: 文件内容
            
        Returns:
            [(基类名, 派生类名), ...]
        """
        selections = []
        for match in self.PATTERNS['runtime_selection'].finditer(content):
            base_class = match.group(1)
            derived_class = match.group(2)
            selections.append((base_class, derived_class))
        return selections
    
    def is_pure_virtual_class(self, content: str) -> bool:
        """
        判断是否为纯虚类（抽象类）
        
        Args:
            content: 文件内容
            
        Returns:
            是否为纯虚类
        """
        # 检查是否有纯虚函数
        if self.PATTERNS['pure_virtual'].search(content):
            return True
        return False
    
    def extract_class_description(self, content: str, class_name: str) -> str:
        """
        提取类的Doxygen描述
        
        Args:
            content: 文件内容
            class_name: 类名
            
        Returns:
            描述文本
        """
        # 查找类定义前的Doxygen注释
        pattern = re.compile(
            r'(///[^\n]*\n|/\*\*[\s\S]*?\*/)\s*'
            rf'(?:template\s*<[^>]*>\s*)?'
            rf'class\s+{class_name}'
        )
        
        match = pattern.search(content)
        if match:
            desc = match.group(1)
            # 清理Doxygen标记
            desc = re.sub(r'///\s*', '', desc)
            desc = re.sub(r'/\*\*|\*/', '', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            return desc
            
        return ""
