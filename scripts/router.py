#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM Expert Skill 统一命令路由器

功能:
1. 统一 CLI 和 MCP 调用入口
2. 支持全局钩子（缓存、日志、权限）
3. 标准化输出格式
4. 向后兼容现有脚本

使用方法:
    # CLI 模式
    python router.py inheritance --class fvMesh --chain
    python router.py model --type turbulence --name kEpsilon
    python router.py boundary --name fixedValue --params
    
    # 作为模块导入
    from router import OpenFOAMRouter
    router = OpenFOAMRouter()
    result = router.execute("inheritance", {"class": "fvMesh", "chain": True})
"""

import os
import sys
import json
import argparse
import io
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

# Windows平台设置stdout为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加核心模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.code_accessor import CodeAccessor, AccessMode
from core.version import get_version_string, get_version_info, print_version


class ActivityLogger:
    """活动日志记录器"""
    
    def __init__(self, log_dir: str = None):
        script_dir = Path(__file__).parent
        skill_root = script_dir.parent
        self.log_dir = Path(log_dir) if log_dir else skill_root / ".openfoam_cache" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log = []
        
    def log(self, command: str, args: dict, result: dict, duration_ms: float = None):
        """记录执行日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "args": args,
            "success": result.get("success", False),
            "duration_ms": duration_ms
        }
        self.current_log.append(entry)
        
        # 写入日志文件
        log_file = self.log_dir / f"activity_{datetime.now().strftime('%Y%m%d')}.jsonl"
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception:
            pass  # 日志写入失败不影响主流程
            
    def get_recent(self, limit: int = 10) -> List[dict]:
        """获取最近的执行记录"""
        return self.current_log[-limit:]


class AnalysisCache:
    """分析结果缓存"""
    
    def __init__(self, cache_dir: str = None):
        script_dir = Path(__file__).parent
        skill_root = script_dir.parent
        self.cache_dir = Path(cache_dir) if cache_dir else skill_root / ".openfoam_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, dict] = {}
        
    def _get_cache_key(self, command: str, args: dict) -> str:
        """生成缓存键"""
        import hashlib
        args_str = json.dumps(args, sort_keys=True)
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
        return f"{command}_{args_hash}"
    
    def get(self, command: str, args: dict) -> Optional[dict]:
        """获取缓存结果"""
        key = self._get_cache_key(command, args)
        
        # 先检查内存缓存
        if key in self._memory_cache:
            return self._memory_cache[key]
            
        # 检查文件缓存
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                self._memory_cache[key] = result
                return result
            except Exception:
                pass
                
        return None
    
    def set(self, command: str, args: dict, result: dict):
        """设置缓存"""
        key = self._get_cache_key(command, args)
        self._memory_cache[key] = result
        
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 缓存写入失败不影响主流程
            
    def clear(self):
        """清除缓存"""
        self._memory_cache.clear()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception:
                pass


class OpenFOAMRouter:
    """
    OpenFOAM Expert 统一命令路由器
    
    支持两种调用方式:
    1. CLI 模式: 通过命令行参数调用
    2. API 模式: 作为 Python 模块导入调用
    """
    
    # 支持的命令列表
    COMMANDS = {
        'inheritance': {
            'description': '类继承关系分析',
            'analyzer': 'inheritance_analyzer',
            'class': 'InheritanceAnalyzer'
        },
        'boundary': {
            'description': '边界条件分析',
            'analyzer': 'boundary_analyzer',
            'class': 'BoundaryAnalyzer'
        },
        'model': {
            'description': '物理模型分析',
            'analyzer': 'model_analyzer',
            'class': 'ModelAnalyzer'
        },
        'modifier': {
            'description': '代码修改建议',
            'analyzer': 'code_modifier',
            'class': 'CodeModifier'
        },
        'search': {
            'description': '源码搜索 (regex pattern)',
            'analyzer': None,
            'class': None
        }
    }
    
    def __init__(self, 
                 openfoam_src: str = None,
                 access_mode: AccessMode = AccessMode.AUTO,
                 enable_cache: bool = True,
                 enable_log: bool = True):
        """
        初始化路由器
        
        Args:
            openfoam_src: OpenFOAM src 目录路径
            access_mode: 代码访问模式
            enable_cache: 是否启用缓存
            enable_log: 是否启用日志
        """
        self.accessor = CodeAccessor(openfoam_src=openfoam_src, access_mode=access_mode)
        self.cache = AnalysisCache() if enable_cache else None
        self.logger = ActivityLogger() if enable_log else None
        self._analyzers: Dict[str, Any] = {}
        
    def _get_analyzer(self, command: str):
        """延迟加载分析器"""
        if command not in self.COMMANDS:
            raise ValueError(f"未知命令: {command}")
            
        if command not in self._analyzers:
            cmd_info = self.COMMANDS[command]
            module_name = cmd_info['analyzer']
            class_name = cmd_info['class']
            
            # 动态导入分析器模块
            try:
                module = __import__(module_name, fromlist=[class_name])
                analyzer_class = getattr(module, class_name)
                
                # 尝试使用统一的访问器
                if hasattr(analyzer_class, '__init__'):
                    import inspect
                    sig = inspect.signature(analyzer_class.__init__)
                    params = list(sig.parameters.keys())
                    
                    if 'openfoam_src' in params and 'access_mode' in params:
                        self._analyzers[command] = analyzer_class(
                            openfoam_src=self.accessor.openfoam_src,
                            access_mode=self.accessor.access_mode
                        )
                    elif 'openfoam_src' in params:
                        self._analyzers[command] = analyzer_class(
                            openfoam_src=self.accessor.openfoam_src
                        )
                    else:
                        self._analyzers[command] = analyzer_class()
                else:
                    self._analyzers[command] = analyzer_class()
                    
            except Exception as e:
                raise RuntimeError(f"加载分析器 {module_name} 失败: {e}")
                
        return self._analyzers[command]
    
    def execute(self, command: str, args: dict, use_cache: bool = True) -> dict:
        """
        执行命令
        
        Args:
            command: 命令名称
            args: 命令参数
            use_cache: 是否使用缓存
            
        Returns:
            执行结果
        """
        import time
        start_time = time.time()
        
        # 检查缓存
        if use_cache and self.cache:
            cached = self.cache.get(command, args)
            if cached:
                cached["from_cache"] = True
                return cached
        
        try:
            # search 命令不需要分析器
            if command == 'search':
                result = self._execute_search(args)
            else:
                # 获取分析器并执行
                analyzer = self._get_analyzer(command)
                result = self._dispatch_to_analyzer(analyzer, command, args)
            
            # 确保结果有 success 字段
            if "success" not in result:
                result["success"] = True
                
            # 设置缓存
            if use_cache and self.cache and result.get("success"):
                self.cache.set(command, args, result)
                
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "command": command,
                "args": args
            }
        
        # 记录日志
        duration_ms = (time.time() - start_time) * 1000
        if self.logger:
            self.logger.log(command, args, result, duration_ms)
            
        result["duration_ms"] = round(duration_ms, 2)
        return result
    
    def _dispatch_to_analyzer(self, analyzer: Any, command: str, args: dict) -> dict:
        """
        分发命令到分析器
        
        根据不同命令类型调用相应的分析方法
        """
        if command == 'inheritance':
            return self._execute_inheritance(analyzer, args)
        elif command == 'boundary':
            return self._execute_boundary(analyzer, args)
        elif command == 'model':
            return self._execute_model(analyzer, args)
        elif command == 'modifier':
            return self._execute_modifier(analyzer, args)
        elif command == 'search':
            return self._execute_search(args)
        else:
            raise ValueError(f"未实现的命令: {command}")

    def _execute_search(self, args: dict) -> dict:
        """执行源码搜索"""
        pattern = args.get('pattern')
        if not pattern:
            return {"success": False, "error": "缺少 --pattern 参数"}

        file_types = args.get('type', '.H,.C')
        scope = args.get('scope', 'source')
        max_results = args.get('max', 50)

        try:
            results = self.accessor.search_code(
                pattern=pattern,
                file_types=file_types,
                scope=scope,
                max_results=max_results
            )

            return {
                "success": True,
                "pattern": pattern,
                "file_types": file_types,
                "scope": scope,
                "count": len(results),
                "results": [
                    {
                        "file_path": r.file_path,
                        "line_number": r.line_number,
                        "content": r.content[:200],
                    }
                    for r in results
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_inheritance(self, analyzer, args: dict) -> dict:
        """执行继承分析"""
        class_name = args.get('class')
        if not class_name:
            return {"success": False, "error": "缺少 --class 参数"}
            
        result = {"success": True, "class_name": class_name}
        
        # 获取类信息
        info = analyzer.get_class_info(class_name)
        if info:
            result["file_path"] = info.file_path
            result["line_number"] = info.line_number
            result["base_classes"] = info.base_classes
            result["is_template"] = info.is_template
        else:
            return {"success": False, "error": f"未找到类: {class_name}"}
        
        # 可选分析
        if args.get('chain'):
            chain = analyzer.get_inheritance_chain(class_name)
            result["inheritance_chain"] = [c.to_dict() for c in chain]
            
        if args.get('tree'):
            depth = args.get('depth', 3)
            derived = analyzer.get_derived_classes(class_name, depth)
            result["derived_classes"] = {
                d: [c.to_dict() for c in classes]
                for d, classes in derived.items()
            }
            
        if args.get('patterns'):
            patterns = analyzer.analyze_design_pattern(class_name)
            result["design_patterns"] = patterns
            
        if args.get('suggest'):
            suggestions = analyzer.generate_modification_suggestions(
                class_name, args['suggest']
            )
            result["modification_suggestions"] = suggestions
            
        return result
    
    def _execute_boundary(self, analyzer, args: dict) -> dict:
        """执行边界条件分析"""
        name = args.get('name')
        if not name:
            return {"success": False, "error": "缺少 --name 参数"}
            
        result = {"success": True, "boundary_name": name}
        
        # 根据参数调用分析方法
        if args.get('params'):
            result["parameters"] = analyzer.analyze_parameters(name)
            
        if args.get('examples'):
            result["examples"] = analyzer.find_usage_examples(name)
            
        if args.get('suggest'):
            suggestions = analyzer.generate_suggestions(name, args['suggest'])
            result["suggestions"] = suggestions
            
        # 默认获取基本信息
        if not any([args.get('params'), args.get('examples'), args.get('suggest')]):
            info = analyzer.find_boundary_condition(name)
            if info:
                result["file_path"] = info.file_path
                result["base_class"] = info.base_class
                result["description"] = info.description
                result["parameters"] = info.parameters
                result["required_parameters"] = info.required_parameters
                result["member_functions"] = info.member_functions
            else:
                return {"success": False, "error": f"未找到边界条件: {name}"}
            
        return result
    
    def _execute_model(self, analyzer, args: dict) -> dict:
        """执行模型分析"""
        model_type = args.get('type')
        model_name = args.get('name')
        
        if not model_name:
            return {"success": False, "error": "缺少 --name 参数"}
            
        result = {"success": True, "model_name": model_name, "model_type": model_type}
        
        # 根据模型类型调用分析方法
        if model_type == 'turbulence':
            analysis = analyzer.analyze_turbulence_model(model_name)
        elif model_type == 'multiphase':
            analysis = analyzer.analyze_multiphase_model(model_name)
        elif model_type == 'thermophysical':
            analysis = analyzer.analyze_thermophysical_model(model_name)
        else:
            analysis = {"model_name": model_name, "model_type": model_type or "unknown"}
            
        result.update(analysis)
        
        if args.get('suggest'):
            suggestions = analyzer.generate_modification_suggestions(
                model_name, model_type, args['suggest']
            )
            result["modification_suggestions"] = suggestions
            
        return result
    
    def _execute_modifier(self, analyzer, args: dict) -> dict:
        """执行代码修改建议"""
        target = args.get('target')
        name = args.get('name')
        action = args.get('action', 'suggest')
        
        if not target or not name:
            return {"success": False, "error": "缺少 --target 或 --name 参数"}
            
        return analyzer.generate_modification(target, name, action, args)
    
    def list_commands(self) -> dict:
        """列出支持的命令"""
        return {
            "success": True,
            "commands": {
                cmd: info['description'] 
                for cmd, info in self.COMMANDS.items()
            }
        }
    
    def clear_cache(self) -> dict:
        """清除缓存"""
        if self.cache:
            self.cache.clear()
            return {"success": True, "message": "缓存已清除"}
        return {"success": True, "message": "缓存未启用"}


def format_output(result: dict, format_type: str = "json") -> str:
    """格式化输出"""
    if format_type == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    elif format_type == "compact":
        return json.dumps(result, ensure_ascii=False, separators=(',', ':'))
    elif format_type == "text":
        return _format_text(result)
    return json.dumps(result, ensure_ascii=False)


def _format_text(result: dict) -> str:
    """文本格式化输出"""
    lines = []
    
    if not result.get("success"):
        lines.append(f"[ERROR] {result.get('error', '未知错误')}")
        return "\n".join(lines)
    
    if "class_name" in result:
        lines.append(f"类: {result['class_name']}")
        lines.append(f"文件: {result.get('file_path', 'N/A')}:{result.get('line_number', 0)}")
        
    if "inheritance_chain" in result:
        lines.append("\n继承链:")
        chain = result["inheritance_chain"]
        lines.append(" → ".join([c["name"] for c in chain]))
        
    if "model_name" in result:
        lines.append(f"模型: {result['model_name']}")
        lines.append(f"类型: {result.get('model_type', 'N/A')}")
        lines.append(f"类别: {result.get('category', 'N/A')}")
        
    if "design_patterns" in result:
        lines.append("\n设计模式:")
        for p in result["design_patterns"]:
            lines.append(f"  - {p['name']}: {p['description']}")
            
    if "modification_suggestions" in result:
        lines.append("\n修改建议:")
        for s in result["modification_suggestions"]:
            lines.append(f"  [{s['type']}] {s['description']}")
            
    if "duration_ms" in result:
        lines.append(f"\n耗时: {result['duration_ms']:.2f}ms")
        
    return "\n".join(lines)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='OpenFOAM Expert Skill 统一命令路由器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持的命令:
  inheritance    类继承关系分析
  boundary       边界条件分析
  model          物理模型分析
  modifier       代码修改建议
  search         源码搜索 (正则表达式)

示例:
  %(prog)s search --pattern "codedFvModel" --type .H
  %(prog)s search --pattern "class.*fvModel.*public" --type .H
  %(prog)s inheritance --class fvMesh --chain
  %(prog)s model --type turbulence --name kEpsilon
  %(prog)s boundary --name fixedValue --params
  %(prog)s modifier --target boundary --name fixedValue --action create
        """
    )
    
    parser.add_argument('command', nargs='?', 
                        choices=list(OpenFOAMRouter.COMMANDS.keys()) + ['help', 'version', 'clear-cache'],
                        help='要执行的命令')

    # 搜索命令参数
    parser.add_argument('--pattern', type=str,
                        help='搜索模式 (正则表达式)')
    parser.add_argument('--scope', type=str, default='source',
                        help='搜索范围 (source/tutorials/applications/all)')
    parser.add_argument('--max', type=int, default=50,
                        help='最大结果数')
    parser.add_argument('--root', type=str,
                        help='OpenFOAM src 目录路径')
    parser.add_argument('--mode', choices=['auto', 'mcp', 'local'], default='auto',
                        help='代码访问模式')
    parser.add_argument('--format', choices=['json', 'text', 'compact'], default='json',
                        help='输出格式')
    parser.add_argument('--no-cache', action='store_true',
                        help='禁用缓存')
    parser.add_argument('-v', '--version', action='store_true',
                        help='显示版本信息')
    
    # 继承分析参数
    parser.add_argument('--class', dest='class_name', type=str,
                        help='要分析的类名')
    parser.add_argument('--chain', action='store_true',
                        help='显示继承链')
    parser.add_argument('--tree', action='store_true',
                        help='显示派生树')
    parser.add_argument('--depth', type=int, default=3,
                        help='派生树搜索深度')
    parser.add_argument('--patterns', action='store_true',
                        help='分析设计模式')
    parser.add_argument('--suggest', choices=['extend', 'implement', 'modify', 'create'],
                        help='生成修改建议')
    
    # 边界条件和模型分析参数
    parser.add_argument('--name', type=str,
                        help='边界条件或模型名称')
    parser.add_argument('--type', type=str,
                        help='模型类型 (turbulence/multiphase/thermophysical)')
    parser.add_argument('--params', action='store_true',
                        help='显示参数信息')
    parser.add_argument('--examples', action='store_true',
                        help='查找示例')
    parser.add_argument('--target', type=str,
                        help='修改目标 (class/boundary/model)')
    parser.add_argument('--action', type=str,
                        help='修改动作 (create/extend/modify)')
    
    args = parser.parse_args()
    
    # 显示版本信息
    if args.version or args.command == 'version':
        print_version()
        return
    
    # 显示帮助
    if args.command == 'help' or args.command is None:
        parser.print_help()
        return
    
    # 清除缓存
    if args.command == 'clear-cache':
        router = OpenFOAMRouter(enable_cache=True)
        result = router.clear_cache()
        print(format_output(result, args.format))
        return
    
    # 创建路由器
    router = OpenFOAMRouter(
        openfoam_src=args.root,
        access_mode=AccessMode(args.mode),
        enable_cache=not args.no_cache
    )
    
    # 构建参数字典
    cmd_args = {}
    if args.class_name:
        cmd_args['class'] = args.class_name
    if args.name:
        cmd_args['name'] = args.name
    if args.type:
        cmd_args['type'] = args.type
    if args.chain:
        cmd_args['chain'] = True
    if args.tree:
        cmd_args['tree'] = True
    if args.depth:
        cmd_args['depth'] = args.depth
    if args.patterns:
        cmd_args['patterns'] = True
    if args.suggest:
        cmd_args['suggest'] = args.suggest
    if args.params:
        cmd_args['params'] = True
    if args.examples:
        cmd_args['examples'] = True
    if args.target:
        cmd_args['target'] = args.target
    if args.action:
        cmd_args['action'] = args.action
    if args.pattern:
        cmd_args['pattern'] = args.pattern
    if args.scope:
        cmd_args['scope'] = args.scope
    if args.max:
        cmd_args['max'] = args.max
    
    # 执行命令
    result = router.execute(args.command, cmd_args)
    print(format_output(result, args.format))


if __name__ == '__main__':
    main()
