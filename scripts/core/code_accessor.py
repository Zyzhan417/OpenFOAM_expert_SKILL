#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFOAM代码访问器

提供统一的代码访问接口，支持MCP和本地文件双模式
优先使用MCP工具，失败时自动回退到本地文件读取
"""

import os
import re
import json
import subprocess
import tempfile
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field


class AccessMode(Enum):
    """代码访问模式"""
    MCP = "mcp"           # MCP工具模式
    LOCAL = "local"       # 本地文件模式
    AUTO = "auto"         # 自动选择（优先MCP，回退本地）


@dataclass
class SearchResult:
    """搜索结果"""
    file_path: str
    line_number: int
    content: str
    context: List[str] = field(default_factory=list)
    

@dataclass
class FileContent:
    """文件内容"""
    path: str
    content: str
    lines: List[str] = field(default_factory=list)
    total_lines: int = 0
    

class CodeAccessor:
    """
    OpenFOAM代码访问器
    
    支持两种访问模式：
    1. MCP模式：通过MCP工具search_openfoam_code和read_openfoam_file
    2. 本地模式：直接读取本地OpenFOAM源码文件
    
    v2.2.0 新增:
    - 集成 CacheManager 支持持久化缓存
    - 基于源码哈希的缓存失效检测
    """
    
    # MCP工具服务器名称
    MCP_SERVER = "openfoam-analyzer"
    
    def __init__(self, 
                 openfoam_src: str = None,
                 access_mode: AccessMode = AccessMode.AUTO,
                 mcp_available: bool = None,
                 enable_cache: bool = True):
        """
        初始化代码访问器
        
        Args:
            openfoam_src: OpenFOAM src目录路径，默认从以下位置读取：
                         1. 环境变量FOAM_SRC
                         2. Skill attachments目录
            access_mode: 访问模式
            mcp_available: MCP是否可用，None表示自动检测
            enable_cache: 是否启用持久化缓存
        """
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        skill_root = os.path.dirname(os.path.dirname(script_dir))
        default_src = os.path.join(skill_root, "attachments", "OpenFOAM", "src")
        
        # 确定源码路径：优先环境变量，其次Skill attachments
        self.openfoam_src = openfoam_src or os.environ.get('FOAM_SRC') or default_src
        
        # 如果默认路径不存在，使用Linux默认路径
        if not os.path.exists(self.openfoam_src):
            self.openfoam_src = '/opt/openfoam/src'
        
        self.access_mode = access_mode
        self._mcp_available = mcp_available
        self._mcp_checked = mcp_available is not None
        
        # 内存缓存
        self._file_cache: Dict[str, FileContent] = {}
        self._class_location_cache: Dict[str, str] = {}
        
        # 持久化缓存 (v2.2.0)
        self._persistent_cache = None
        if enable_cache:
            try:
                import sys
                sys.path.insert(0, os.path.dirname(script_dir))
                from cache_manager import CacheManager
                self._persistent_cache = CacheManager()
            except ImportError:
                pass  # 缓存模块不可用时回退到内存缓存
        
    def _check_mcp_available(self) -> bool:
        """检查MCP工具是否可用"""
        if self._mcp_checked:
            return self._mcp_available
            
        try:
            # 尝试调用MCP工具获取描述
            result = self._call_mcp_tool("search_openfoam_code", {
                "pattern": "class",
                "file_types": ".H",
                "scope": "source",
                "max_results": 1
            })
            self._mcp_available = result is not None
        except Exception:
            self._mcp_available = False
            
        self._mcp_checked = True
        return self._mcp_available
    
    def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict]:
        """
        调用MCP工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具返回结果，失败返回None
        """
        # MCP工具调用需要通过外部接口实现
        # 这里提供一个桥接机制，实际调用由AI完成
        return None  # 默认返回None，由外部注入实现
        
    def set_mcp_callback(self, callback):
        """
        设置MCP调用回调函数
        
        Args:
            callback: 回调函数，签名为 (tool_name, arguments) -> result
        """
        self._mcp_call = callback
        
    def search_code(self, 
                    pattern: str, 
                    file_types: str = ".H,.C",
                    scope: str = "source",
                    max_results: int = 50) -> List[SearchResult]:
        """
        搜索代码
        
        Args:
            pattern: 搜索模式（正则表达式）
            file_types: 文件类型，逗号分隔
            scope: 搜索范围 (source/tutorials/applications/all)
            max_results: 最大结果数
            
        Returns:
            搜索结果列表
        """
        results = []
        
        # 尝试MCP模式
        if self.access_mode in (AccessMode.MCP, AccessMode.AUTO):
            if self._check_mcp_available():
                mcp_results = self._search_via_mcp(pattern, file_types, scope, max_results)
                if mcp_results:
                    return mcp_results
                    
        # 回退到本地模式
        if self.access_mode in (AccessMode.LOCAL, AccessMode.AUTO):
            return self._search_via_local(pattern, file_types, scope, max_results)
            
        return results
    
    def _search_via_mcp(self, pattern: str, file_types: str, 
                        scope: str, max_results: int) -> Optional[List[SearchResult]]:
        """通过MCP搜索代码"""
        try:
            result = self._call_mcp_tool("search_openfoam_code", {
                "pattern": pattern,
                "file_types": file_types,
                "scope": scope,
                "max_results": max_results
            })
            
            if result and "results" in result:
                return [
                    SearchResult(
                        file_path=r["file_path"],
                        line_number=r.get("line_number", 0),
                        content=r.get("content", ""),
                        context=r.get("context", [])
                    )
                    for r in result["results"]
                ]
        except Exception as e:
            pass
            
        return None
    
    def _search_via_local(self, pattern: str, file_types: str,
                          scope: str, max_results: int) -> List[SearchResult]:
        """本地文件搜索"""
        results = []
        
        # 确定搜索目录
        search_dirs = []
        base_dir = self.openfoam_src
        
        if scope == "source" or scope == "all":
            search_dirs.append(base_dir)
        if scope == "tutorials" or scope == "all":
            tutorials_dir = os.path.join(os.path.dirname(base_dir), "tutorials")
            if os.path.exists(tutorials_dir):
                search_dirs.append(tutorials_dir)
        if scope == "applications" or scope == "all":
            app_dir = os.path.join(os.path.dirname(base_dir), "applications")
            if os.path.exists(app_dir):
                search_dirs.append(app_dir)
                
        # 解析文件类型
        extensions = [ext.strip() for ext in file_types.split(",")]
        
        # 编译正则表达式
        try:
            regex = re.compile(pattern, re.IGNORECASE | re.DOTALL)
        except re.error:
            return results

        # 搜索文件
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue

            for root, dirs, files in os.walk(search_dir):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    # 检查文件类型
                    if not any(file.endswith(ext) for ext in extensions):
                        continue

                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')

                        # 多行搜索
                        for match in regex.finditer(content):
                            # 计算匹配起始位置的行号
                            pos = match.start()
                            line_num = content[:pos].count('\n') + 1

                            # 获取匹配内容（取第一行或前80个字符）
                            matched_text = match.group(0)
                            first_line = matched_text.split('\n')[0][:80]

                            # 获取上下文
                            start = max(0, line_num - 3)
                            end = min(len(lines), line_num + 3)
                            context = lines[start:end]

                            results.append(SearchResult(
                                file_path=os.path.relpath(file_path, base_dir),
                                line_number=line_num,
                                content=first_line,
                                context=context
                            ))

                            if len(results) >= max_results:
                                return results
                    except Exception:
                        continue

        return results
    
    def read_file(self, 
                  file_path: str, 
                  start_line: int = None, 
                  end_line: int = None,
                  highlight_keywords: List[str] = None) -> Optional[FileContent]:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径（相对或绝对）
            start_line: 起始行号
            end_line: 结束行号
            highlight_keywords: 高亮关键词列表
            
        Returns:
            文件内容，失败返回None
        """
        # 检查缓存
        cache_key = file_path
        if cache_key in self._file_cache:
            cached = self._file_cache[cache_key]
            return self._extract_lines(cached, start_line, end_line)
        
        # 尝试MCP模式
        if self.access_mode in (AccessMode.MCP, AccessMode.AUTO):
            if self._check_mcp_available():
                content = self._read_via_mcp(file_path, start_line, end_line, highlight_keywords)
                if content:
                    return content
        
        # 回退到本地模式
        if self.access_mode in (AccessMode.LOCAL, AccessMode.AUTO):
            return self._read_via_local(file_path, start_line, end_line)
            
        return None
    
    def _read_via_mcp(self, file_path: str, start_line: int, end_line: int,
                      highlight_keywords: List[str]) -> Optional[FileContent]:
        """通过MCP读取文件"""
        try:
            result = self._call_mcp_tool("read_openfoam_file", {
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "highlight_keywords": highlight_keywords or []
            })
            
            if result and "content" in result:
                content = result["content"]
                lines = content.split('\n')
                return FileContent(
                    path=file_path,
                    content=content,
                    lines=lines,
                    total_lines=len(lines)
                )
        except Exception:
            pass
            
        return None
    
    def _read_via_local(self, file_path: str, start_line: int, 
                        end_line: int) -> Optional[FileContent]:
        """本地文件读取"""
        # 处理相对路径
        if not os.path.isabs(file_path):
            full_path = os.path.join(self.openfoam_src, file_path)
        else:
            full_path = file_path
            
        if not os.path.exists(full_path):
            error_msg = f"文件不存在: {full_path}"
            self._log_debug(error_msg)
            raise FileNotFoundError(error_msg)
            
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            file_content = FileContent(
                path=file_path,
                content=content,
                lines=lines,
                total_lines=len(lines)
            )
            
            # 缓存完整文件
            self._file_cache[file_path] = file_content
            
            return self._extract_lines(file_content, start_line, end_line)
        except Exception as e:
            self._log_debug(f"读取文件异常: {e}")
            if self._debug:
                raise
            return None
    
    def _extract_lines(self, file_content: FileContent, 
                       start_line: int, end_line: int) -> FileContent:
        """提取指定行范围"""
        if start_line is None and end_line is None:
            return file_content
            
        start = (start_line or 1) - 1
        end = end_line or len(file_content.lines)
        
        extracted_lines = file_content.lines[start:end]
        
        return FileContent(
            path=file_content.path,
            content='\n'.join(extracted_lines),
            lines=extracted_lines,
            total_lines=len(extracted_lines)
        )
    
    def find_class_definition(self, class_name: str) -> Optional[Tuple[str, int]]:
        """
        查找类定义位置
        
        Args:
            class_name: 类名
            
        Returns:
            (文件路径, 行号) 或 None
        """
        # 检查缓存
        if class_name in self._class_location_cache:
            return self._class_location_cache[class_name]
        
        # 搜索类定义 - 支持跨行的格式
        # 格式1: class ClassName : public BaseClass {
        # 格式2: class ClassName\n:\n    public BaseClass\n{
        # 格式3: class ClassName {
        # 格式4: class ClassName\n{\n
        # 格式5: template<...> class ClassName
        pattern = rf"class\s+{class_name}\s*[\s\S]{{0,50}}?(:|\{{)"
        results = self.search_code(pattern, file_types=".H", max_results=5)
        
        if results:
            # 优先选择最直接的匹配
            for r in results:
                if re.search(rf"\b{class_name}\b", r.content):
                    location = (r.file_path, r.line_number)
                    self._class_location_cache[class_name] = location
                    return location
                    
        return None
    
    def find_function_implementation(self, 
                                     class_name: str, 
                                     function_name: str) -> List[Tuple[str, int]]:
        """
        查找函数实现位置
        
        Args:
            class_name: 类名
            function_name: 函数名
            
        Returns:
            [(文件路径, 行号), ...]
        """
        pattern = rf"{class_name}::{function_name}\s*\("
        results = self.search_code(pattern, file_types=".C", max_results=10)
        
        return [(r.file_path, r.line_number) for r in results]
    
    def get_inheritance_info(self, class_name: str) -> Optional[Dict[str, Any]]:
        """
        获取类的继承信息
        
        Args:
            class_name: 类名
            
        Returns:
            继承信息字典
        """
        location = self.find_class_definition(class_name)
        if not location:
            return None
            
        file_path, line_num = location
        content = self.read_file(file_path, line_num, line_num + 50)
        
        if not content:
            return None
            
        # 解析继承信息
        info = {
            "class_name": class_name,
            "file_path": file_path,
            "line_number": line_num,
            "base_classes": [],
            "access_specifiers": []
        }
        
        # 查找继承列表
        full_text = '\n'.join(content.lines)
        match = re.search(
            rf"class\s+{class_name}\s*"
            r"(?:<[^>]*>)?\s*"
            r":\s*((?:public|protected|private)\s+\w+(?:\s*,\s*(?:public|protected|private)\s+\w+)*)",
            full_text
        )
        
        if match:
            inheritance_list = match.group(1)
            for item in inheritance_list.split(','):
                parts = item.strip().split()
                if len(parts) >= 2:
                    info["access_specifiers"].append(parts[0])
                    info["base_classes"].append(parts[1])
                    
        return info
    
    def clear_cache(self):
        """清除缓存（内存缓存和持久化缓存）"""
        self._file_cache.clear()
        self._class_location_cache.clear()
        if self._persistent_cache:
            self._persistent_cache.invalidate()
    
    def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计字典
        """
        stats = {
            "memory_cache_size": len(self._file_cache),
            "class_cache_size": len(self._class_location_cache),
            "persistent_cache": None
        }
        if self._persistent_cache:
            stats["persistent_cache"] = self._persistent_cache.get_stats()
        return stats
    
    def find_class_definition_cached(self, class_name: str) -> Optional[Tuple[str, int]]:
        """
        查找类定义位置（带持久化缓存）
        
        Args:
            class_name: 类名
            
        Returns:
            (文件路径, 行号) 或 None
        """
        cache_key = f"class_def:{class_name}"
        
        # 检查持久化缓存
        if self._persistent_cache:
            cached = self._persistent_cache.get(cache_key)
            if cached:
                return (cached["file_path"], cached["line_number"])
        
        # 执行查找
        result = self.find_class_definition(class_name)
        
        # 存入持久化缓存
        if result and self._persistent_cache:
            self._persistent_cache.set(cache_key, {
                "file_path": result[0],
                "line_number": result[1]
            })
        
        return result
