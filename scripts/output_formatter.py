#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM Expert Skill 输出格式化器

功能:
1. 多种输出格式支持 (JSON/Text/Compact/AI)
2. Token 高效的 AI 友好格式
3. 结构化输出，便于解析
4. 支持高亮和上下文

使用方法:
    from output_formatter import OutputFormatter
    
    formatter = OutputFormatter()
    
    # 格式化结果
    output = formatter.format(result, format_type="ai")
    
    # 流式输出
    formatter.stream_print(result, format_type="text")
"""

import os
import sys
import json
import io
from typing import Dict, List, Optional, Any
from enum import Enum

# Windows平台设置stdout为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class OutputFormat(Enum):
    """输出格式枚举"""
    JSON = "json"           # 标准 JSON，带缩进
    COMPACT = "compact"     # 紧凑 JSON，无缩进
    TEXT = "text"           # 人类可读文本
    AI = "ai"               # AI 友好格式，Token 高效
    MARKDOWN = "markdown"   # Markdown 格式


class OutputFormatter:
    """
    输出格式化器
    
    支持多种输出格式，优化 AI 消费场景
    """
    
    # 关键字段优先级（用于 AI 输出）
    PRIORITY_FIELDS = [
        "success", "error", "class_name", "model_name", "boundary_name",
        "file_path", "line_number", "base_classes", "inheritance_chain",
        "design_patterns", "parameters", "modification_suggestions"
    ]
    
    def __init__(self, max_line_length: int = 80):
        """
        初始化格式化器
        
        Args:
            max_line_length: 最大行长度（用于文本格式）
        """
        self.max_line_length = max_line_length
    
    def format(self, result: dict, format_type: str = "json") -> str:
        """
        格式化结果
        
        Args:
            result: 分析结果字典
            format_type: 输出格式类型
            
        Returns:
            格式化后的字符串
        """
        format_enum = OutputFormat(format_type)
        
        if format_enum == OutputFormat.JSON:
            return self._format_json(result)
        elif format_enum == OutputFormat.COMPACT:
            return self._format_compact(result)
        elif format_enum == OutputFormat.TEXT:
            return self._format_text(result)
        elif format_enum == OutputFormat.AI:
            return self._format_ai(result)
        elif format_enum == OutputFormat.MARKDOWN:
            return self._format_markdown(result)
        else:
            return self._format_json(result)
    
    def _format_json(self, result: dict) -> str:
        """标准 JSON 格式"""
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def _format_compact(self, result: dict) -> str:
        """紧凑 JSON 格式"""
        return json.dumps(result, ensure_ascii=False, separators=(',', ':'))
    
    def _format_text(self, result: dict) -> str:
        """人类可读文本格式"""
        lines = []
        
        # 错误处理
        if not result.get("success"):
            lines.append(f"[ERROR] {result.get('error', '未知错误')}")
            return "\n".join(lines)
        
        # 类继承分析结果
        if "class_name" in result:
            lines.append(self._section_header("类继承分析"))
            lines.append(f"  类名: {result['class_name']}")
            lines.append(f"  文件: {result.get('file_path', 'N/A')}")
            if "line_number" in result:
                lines[-1] += f":{result['line_number']}"
            lines.append(f"  模板: {'是' if result.get('is_template') else '否'}")
            
            if "base_classes" in result:
                bases = result["base_classes"]
                lines.append(f"  基类: {', '.join(bases) if bases else '无'}")
                
            if "inheritance_chain" in result:
                lines.append("\n  继承链:")
                chain = result["inheritance_chain"]
                chain_str = " → ".join([c["name"] for c in chain])
                lines.append(f"    {chain_str}")
                for c in chain:
                    lines.append(f"      {c['name']}: {c.get('file_path', '?')}:{c.get('line_number', '?')}")
                    
            if "derived_classes" in result:
                lines.append("\n  派生类:")
                for depth, classes in result["derived_classes"].items():
                    names = [c["name"] for c in classes[:5]]  # 最多显示5个
                    lines.append(f"    深度 {depth}: {', '.join(names)}")
                    if len(classes) > 5:
                        lines.append(f"             ... 还有 {len(classes) - 5} 个")
                        
            if "design_patterns" in result:
                lines.append("\n  设计模式:")
                for p in result["design_patterns"]:
                    lines.append(f"    - {p['name']}: {p['description']}")
                    lines.append(f"      特征: {', '.join(p.get('matched_indicators', []))}")
        
        # 模型分析结果
        elif "model_name" in result:
            lines.append(self._section_header("物理模型分析"))
            lines.append(f"  模型: {result['model_name']}")
            lines.append(f"  类型: {result.get('model_type', 'N/A')}")
            lines.append(f"  类别: {result.get('category', 'N/A')}")
            
            if "description" in result:
                lines.append(f"  描述: {result['description']}")
                
            if "equations" in result:
                lines.append(f"  方程: {', '.join(result['equations'])}")
                
            if "parameters" in result:
                lines.append("\n  参数:")
                for p in result["parameters"][:10]:  # 最多显示10个
                    default = p.get('default', '')
                    desc = p.get('description', '')
                    lines.append(f"    {p['name']}: {default} # {desc}" if desc else f"    {p['name']}: {default}")
                if len(result["parameters"]) > 10:
                    lines.append(f"    ... 还有 {len(result['parameters']) - 10} 个参数")
        
        # 边界条件分析结果
        elif "boundary_name" in result:
            lines.append(self._section_header("边界条件分析"))
            lines.append(f"  名称: {result['boundary_name']}")
            
            if "parameters" in result:
                lines.append("\n  参数:")
                for p in result["parameters"]:
                    lines.append(f"    {p['name']}: {p.get('type', 'unknown')}")
                    if 'default' in p:
                        lines.append(f"      默认值: {p['default']}")
                    if 'description' in p:
                        lines.append(f"      描述: {p['description']}")
        
        # 修改建议
        if "modification_suggestions" in result:
            lines.append("\n" + self._section_header("修改建议"))
            for i, s in enumerate(result["modification_suggestions"], 1):
                lines.append(f"\n  [{i}] {s['type']}: {s['description']}")
                
                if "steps" in s:
                    lines.append("  步骤:")
                    for step in s["steps"]:
                        lines.append(f"    {step}")
                        
                if "template" in s:
                    lines.append("  模板:")
                    template_lines = s["template"].split("\n")[:10]  # 最多显示10行
                    for tl in template_lines:
                        lines.append(f"    {tl}")
                    if len(s["template"].split("\n")) > 10:
                        lines.append("    ...")
        
        # 相关文件
        if "related_files" in result:
            lines.append("\n  相关文件:")
            for f in result["related_files"][:5]:
                lines.append(f"    {f['file']} ({f.get('type', '?')})")
        
        # 性能信息
        if "duration_ms" in result:
            lines.append(f"\n  耗时: {result['duration_ms']:.2f}ms")
        if "from_cache" in result:
            lines.append("  [来自缓存]")
            
        return "\n".join(lines)
    
    def _format_ai(self, result: dict) -> str:
        """
        AI 友好格式
        
        设计原则:
        1. 一行一信息，便于解析
        2. 关键信息优先
        3. 使用简单分隔符
        4. 避免冗余空白
        """
        lines = []
        
        # 状态行
        if result.get("success"):
            lines.append("STATUS: OK")
        else:
            lines.append(f"STATUS: ERROR")
            lines.append(f"ERROR: {result.get('error', 'unknown')}")
            return "\n".join(lines)
        
        # 类继承分析
        if "class_name" in result:
            lines.append(f"CLASS: {result['class_name']}")
            lines.append(f"FILE: {result.get('file_path', 'N/A')}:{result.get('line_number', 0)}")
            
            if "base_classes" in result:
                lines.append(f"BASES: {','.join(result['base_classes'])}")
                
            if "inheritance_chain" in result:
                chain = "→".join([c["name"] for c in result["inheritance_chain"]])
                lines.append(f"CHAIN: {chain}")
                
            if "design_patterns" in result:
                patterns = ",".join([p["name"] for p in result["design_patterns"]])
                lines.append(f"PATTERNS: {patterns}")
        
        # 模型分析
        elif "model_name" in result:
            lines.append(f"MODEL: {result['model_name']}")
            lines.append(f"TYPE: {result.get('model_type', 'N/A')}")
            lines.append(f"CATEGORY: {result.get('category', 'N/A')}")
            
            if "equations" in result:
                lines.append(f"EQUATIONS: {','.join(result['equations'])}")
                
            if "parameters" in result and result["parameters"]:
                # 只显示参数名和默认值
                params = [f"{p['name']}={p.get('default', '?')}" for p in result["parameters"][:5]]
                lines.append(f"PARAMS: {','.join(params)}")
        
        # 边界条件分析
        elif "boundary_name" in result:
            lines.append(f"BOUNDARY: {result['boundary_name']}")
            
            if "parameters" in result and result["parameters"]:
                params = [p["name"] for p in result["parameters"]]
                lines.append(f"PARAMS: {','.join(params)}")
        
        # 修改建议摘要
        if "modification_suggestions" in result:
            suggestions = result["modification_suggestions"]
            lines.append(f"SUGGESTIONS: {len(suggestions)}")
            for s in suggestions[:3]:  # 最多3条
                lines.append(f"SUGGEST: {s['type']} - {s['description'][:50]}")
        
        # 性能信息
        if "duration_ms" in result:
            lines.append(f"DURATION: {result['duration_ms']:.0f}ms")
            
        return "\n".join(lines)
    
    def _format_markdown(self, result: dict) -> str:
        """Markdown 格式"""
        lines = []
        
        if not result.get("success"):
            lines.append("## ❌ 错误")
            lines.append(f"\n```\n{result.get('error', '未知错误')}\n```")
            return "\n".join(lines)
        
        # 类继承分析
        if "class_name" in result:
            lines.append(f"## 类: `{result['class_name']}`\n")
            lines.append(f"**文件**: `{result.get('file_path', 'N/A')}:{result.get('line_number', 0)}`\n")
            
            if "base_classes" in result:
                bases = [f"`{b}`" for b in result["base_classes"]]
                lines.append(f"**基类**: {', '.join(bases)}\n")
                
            if "inheritance_chain" in result:
                lines.append("### 继承链\n")
                chain = result["inheritance_chain"]
                for c in chain:
                    lines.append(f"- `{c['name']}` ({c.get('file_path', '?')})")
                lines.append("")
                
            if "design_patterns" in result:
                lines.append("### 设计模式\n")
                for p in result["design_patterns"]:
                    lines.append(f"- **{p['name']}**: {p['description']}")
                lines.append("")
        
        # 模型分析
        elif "model_name" in result:
            lines.append(f"## 模型: `{result['model_name']}`\n")
            lines.append(f"**类型**: {result.get('model_type', 'N/A')}")
            lines.append(f"**类别**: {result.get('category', 'N/A')}\n")
            
            if "description" in result:
                lines.append(f"{result['description']}\n")
                
            if "parameters" in result:
                lines.append("### 参数\n")
                lines.append("| 参数 | 默认值 | 描述 |")
                lines.append("|------|--------|------|")
                for p in result["parameters"]:
                    lines.append(f"| `{p['name']}` | `{p.get('default', '-')}` | {p.get('description', '')} |")
        
        return "\n".join(lines)
    
    def _section_header(self, title: str) -> str:
        """生成节标题"""
        line = "─" * (self.max_line_length - 4)
        return f"\n┌{line}┐\n│ {title.center(self.max_line_length - 6)} │\n└{line}┘"
    
    def stream_print(self, result: dict, format_type: str = "text"):
        """
        流式打印结果
        
        用于大型结果，逐步输出
        """
        output = self.format(result, format_type)
        
        # 按段落分割，逐步输出
        paragraphs = output.split("\n\n")
        for para in paragraphs:
            print(para)
            print()  # 段落间空行


def format_output(result: dict, format_type: str = "json") -> str:
    """
    便捷函数：格式化输出
    
    Args:
        result: 分析结果
        format_type: 输出格式
        
    Returns:
        格式化字符串
    """
    formatter = OutputFormatter()
    return formatter.format(result, format_type)


if __name__ == "__main__":
    # 测试输出格式化器
    formatter = OutputFormatter()
    
    # 测试数据
    test_result = {
        "success": True,
        "class_name": "kEpsilon",
        "file_path": "turbulenceModels/RAS/kEpsilon/kEpsilon.H",
        "line_number": 62,
        "base_classes": ["RASModel"],
        "is_template": False,
        "inheritance_chain": [
            {"name": "kEpsilon", "file_path": "turbulenceModels/RAS/kEpsilon/kEpsilon.H", "line_number": 62},
            {"name": "RASModel", "file_path": "turbulenceModels/RAS/RASModel.H", "line_number": 50},
            {"name": "turbulenceModel", "file_path": "turbulenceModels/turbulenceModel.H", "line_number": 45}
        ],
        "design_patterns": [
            {"name": "Factory", "description": "工厂模式", "matched_indicators": ["::New("]},
            {"name": "Strategy", "description": "策略模式", "matched_indicators": ["virtual"]}
        ],
        "duration_ms": 123.45
    }
    
    print("=" * 60)
    print("JSON 格式:")
    print("=" * 60)
    print(formatter.format(test_result, "json"))
    
    print("\n" + "=" * 60)
    print("AI 格式:")
    print("=" * 60)
    print(formatter.format(test_result, "ai"))
    
    print("\n" + "=" * 60)
    print("TEXT 格式:")
    print("=" * 60)
    print(formatter.format(test_result, "text"))
