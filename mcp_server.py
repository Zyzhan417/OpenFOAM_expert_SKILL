#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM Expert MCP Server

将 OpenFOAM Expert Skill 的分析能力封装为 MCP Server，
使 Claude、Cursor 等 AI 可以直接调用。

MCP (Model Context Protocol) 是 Anthropic 主导的 AI 工具协议标准。
本实现采用 stdio 传输模式，支持作为 Claude Desktop 的扩展工具使用。

安装配置 (Claude Desktop):
在 claude_desktop_config.json 中添加:
{
  "mcpServers": {
    "openfoam-expert": {
      "command": "python",
      "args": ["C:/path/to/skill/mcp_server.py"]
    }
  }
}

使用方法:
    # 作为 MCP Server 运行
    python mcp_server.py
    
    # 测试模式
    python mcp_server.py --test
"""

import os
import sys
import json
import asyncio
import argparse
import io
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

# Windows平台设置stdout为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加脚本路径
SCRIPT_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

# 尝试导入 MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)


# ============================================================================
# Tool Definitions - 工具定义
# ============================================================================

TOOLS = [
    {
        "name": "analyze_inheritance",
        "description": """分析 OpenFOAM 类的继承关系。

用途:
- 查找类的基类和继承链
- 发现派生类
- 识别设计模式（Factory, Strategy等）
- 生成扩展建议

返回信息:
- 类定义位置（文件路径、行号）
- 继承链（从当前类到根基类）
- 设计模式分析
- 修改建议（可选）""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "class_name": {
                    "type": "string",
                    "description": "要分析的类名，如 fvMesh, kEpsilon, turbulenceModel"
                },
                "show_chain": {
                    "type": "boolean",
                    "description": "是否显示完整继承链",
                    "default": True
                },
                "show_tree": {
                    "type": "boolean",
                    "description": "是否显示派生树",
                    "default": False
                },
                "depth": {
                    "type": "integer",
                    "description": "派生树搜索深度",
                    "default": 3
                },
                "show_patterns": {
                    "type": "boolean",
                    "description": "是否分析设计模式",
                    "default": True
                },
                "suggest": {
                    "type": "string",
                    "enum": ["extend", "implement", "modify"],
                    "description": "生成修改建议类型"
                }
            },
            "required": ["class_name"]
        }
    },
    {
        "name": "analyze_boundary",
        "description": """分析 OpenFOAM 边界条件。

用途:
- 查看边界条件参数
- 查找使用示例
- 生成创建建议

支持的边界条件:
- fixedValue, fixedGradient, zeroGradient
- inletOutlet, outletInlet
- pressureInletOutletVelocity 等""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "边界条件名称，如 fixedValue, inletOutlet"
                },
                "show_params": {
                    "type": "boolean",
                    "description": "是否显示参数信息",
                    "default": True
                },
                "show_examples": {
                    "type": "boolean",
                    "description": "是否查找示例",
                    "default": False
                },
                "suggest": {
                    "type": "string",
                    "enum": ["create", "extend"],
                    "description": "生成建议类型"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "analyze_model",
        "description": """分析 OpenFOAM 物理模型。

支持的模型类型:
- turbulence: 湍流模型 (kEpsilon, kOmegaSST, SpalartAllmaras等)
- multiphase: 多相流模型 (interFoam, multiphaseEulerFoam等)
- thermophysical: 热物理模型 (heRhoThermo, reactingMixture等)

返回信息:
- 模型方程
- 参数及默认值
- 相关文件
- 扩展建议""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_type": {
                    "type": "string",
                    "enum": ["turbulence", "multiphase", "thermophysical", "populationBalance"],
                    "description": "模型类型"
                },
                "model_name": {
                    "type": "string",
                    "description": "模型名称，如 kEpsilon, interFoam, heRhoThermo"
                },
                "suggest": {
                    "type": "string",
                    "enum": ["extend", "modify", "add_equation"],
                    "description": "生成修改建议类型"
                }
            },
            "required": ["model_type", "model_name"]
        }
    },
    {
        "name": "suggest_modification",
        "description": """生成 OpenFOAM 代码修改建议。

用途:
- 创建新的边界条件
- 扩展现有模型
- 添加新功能

输出:
- 代码模板
- 实施步骤
- 注意事项""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "enum": ["class", "boundary", "model"],
                    "description": "修改目标类型"
                },
                "name": {
                    "type": "string",
                    "description": "目标名称"
                },
                "action": {
                    "type": "string",
                    "enum": ["create", "extend", "modify"],
                    "description": "修改动作"
                },
                "context": {
                    "type": "string",
                    "description": "额外上下文信息"
                }
            },
            "required": ["target", "name", "action"]
        }
    },
    {
        "name": "search_code",
        "description": """在 OpenFOAM 源码中搜索代码。

用途:
- 查找函数定义
- 搜索类声明
- 定位特定模式

支持:
- 正则表达式搜索
- 文件类型过滤
- 范围限定""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "搜索模式（正则表达式）"
                },
                "file_types": {
                    "type": "string",
                    "description": "文件类型，如 .H,.C",
                    "default": ".H"
                },
                "scope": {
                    "type": "string",
                    "enum": ["source", "tutorials", "applications", "all"],
                    "description": "搜索范围",
                    "default": "source"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数",
                    "default": 20
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "get_version",
        "description": "获取 OpenFOAM Expert Skill 版本信息",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


# ============================================================================
# Server Implementation - 服务器实现
# ============================================================================

class OpenFOAMMCPServer:
    """OpenFOAM Expert MCP Server 实现"""
    
    def __init__(self):
        self.router = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """延迟初始化"""
        if self._initialized:
            return
            
        # 导入路由器
        from router import OpenFOAMRouter
        self.router = OpenFOAMRouter(enable_cache=True, enable_log=True)
        self._initialized = True
    
    def analyze_inheritance(self, class_name: str, show_chain: bool = True,
                           show_tree: bool = False, depth: int = 3,
                           show_patterns: bool = True, suggest: str = None) -> dict:
        """分析类继承关系"""
        self._ensure_initialized()
        
        args = {
            "class": class_name,
            "chain": show_chain,
            "tree": show_tree,
            "depth": depth,
            "patterns": show_patterns
        }
        if suggest:
            args["suggest"] = suggest
            
        return self.router.execute("inheritance", args)
    
    def analyze_boundary(self, name: str, show_params: bool = True,
                        show_examples: bool = False, suggest: str = None) -> dict:
        """分析边界条件"""
        self._ensure_initialized()
        
        args = {
            "name": name,
            "params": show_params,
            "examples": show_examples
        }
        if suggest:
            args["suggest"] = suggest
            
        return self.router.execute("boundary", args)
    
    def analyze_model(self, model_type: str, model_name: str, suggest: str = None) -> dict:
        """分析物理模型"""
        self._ensure_initialized()
        
        args = {
            "type": model_type,
            "name": model_name
        }
        if suggest:
            args["suggest"] = suggest
            
        return self.router.execute("model", args)
    
    def suggest_modification(self, target: str, name: str, action: str, 
                            context: str = None) -> dict:
        """生成修改建议"""
        self._ensure_initialized()
        
        args = {
            "target": target,
            "name": name,
            "action": action
        }
        if context:
            args["context"] = context
            
        return self.router.execute("modifier", args)
    
    def search_code(self, pattern: str, file_types: str = ".H",
                   scope: str = "source", max_results: int = 20) -> dict:
        """搜索代码"""
        self._ensure_initialized()
        
        from core.code_accessor import CodeAccessor, AccessMode
        accessor = CodeAccessor(access_mode=AccessMode.LOCAL)
        results = accessor.search_code(pattern, file_types, scope, max_results)
        
        return {
            "success": True,
            "pattern": pattern,
            "total_results": len(results),
            "results": [
                {
                    "file": r.file_path,
                    "line": r.line_number,
                    "content": r.content
                }
                for r in results
            ]
        }
    
    def get_version(self) -> dict:
        """获取版本信息"""
        from core.version import get_version_info
        return {
            "success": True,
            **get_version_info()
        }


# ============================================================================
# MCP Server Entry Point - MCP 服务器入口
# ============================================================================

async def run_mcp_server():
    """运行 MCP Server"""
    if not MCP_AVAILABLE:
        print("Error: MCP SDK not installed.", file=sys.stderr)
        print("Install with: pip install mcp", file=sys.stderr)
        sys.exit(1)
    
    # 创建服务器实例
    server = Server("openfoam-expert")
    impl = OpenFOAMMCPServer()
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """列出可用工具"""
        return [
            Tool(
                name=tool["name"],
                description=tool["description"],
                inputSchema=tool["inputSchema"]
            )
            for tool in TOOLS
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[TextContent]:
        """调用工具"""
        try:
            if name == "analyze_inheritance":
                result = impl.analyze_inheritance(**arguments)
            elif name == "analyze_boundary":
                result = impl.analyze_boundary(**arguments)
            elif name == "analyze_model":
                result = impl.analyze_model(**arguments)
            elif name == "suggest_modification":
                result = impl.suggest_modification(**arguments)
            elif name == "search_code":
                result = impl.search_code(**arguments)
            elif name == "get_version":
                result = impl.get_version()
            else:
                result = {"success": False, "error": f"Unknown tool: {name}"}
                
        except Exception as e:
            result = {"success": False, "error": str(e)}
        
        # 格式化输出
        from output_formatter import format_output
        output = format_output(result, "ai")
        
        return [TextContent(type="text", text=output)]
    
    # 运行服务器
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


# ============================================================================
# CLI Entry Point - 命令行入口
# ============================================================================

def test_tools():
    """测试工具功能"""
    print("=" * 60)
    print("OpenFOAM Expert MCP Server - Test Mode")
    print("=" * 60)
    
    impl = OpenFOAMMCPServer()
    
    # 测试版本
    print("\n1. Testing get_version...")
    result = impl.get_version()
    print(json.dumps(result, indent=2))
    
    # 测试继承分析
    print("\n2. Testing analyze_inheritance (fvMesh)...")
    result = impl.analyze_inheritance("fvMesh", show_chain=True, show_patterns=True)
    print(json.dumps(result, indent=2, ensure_ascii=False)[:500] + "...")
    
    # 测试模型分析
    print("\n3. Testing analyze_model (kEpsilon)...")
    result = impl.analyze_model("turbulence", "kEpsilon")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:500] + "...")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='OpenFOAM Expert MCP Server')
    parser.add_argument('--test', action='store_true', help='Run test mode')
    parser.add_argument('--list-tools', action='store_true', help='List available tools')
    args = parser.parse_args()
    
    if args.list_tools:
        print("Available MCP Tools:")
        for tool in TOOLS:
            print(f"\n  {tool['name']}:")
            print(f"    {tool['description'].split(chr(10))[0]}")
        return
    
    if args.test:
        test_tools()
        return
    
    # 运行 MCP Server
    if MCP_AVAILABLE:
        asyncio.run(run_mcp_server())
    else:
        print("MCP SDK not available. Running in test mode...")
        test_tools()


if __name__ == "__main__":
    main()
