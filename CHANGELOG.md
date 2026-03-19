# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-03-18

### Added
- MCP Server 封装 (`mcp_server.py`)，支持 Claude/Cursor 等 AI 直接调用
- 统一命令路由器 (`scripts/router.py`)，单一入口点
- 缓存管理模块 (`scripts/cache_manager.py`)，支持两级缓存
- 输出格式化器 (`scripts/output_formatter.py`)，支持 AI 友好格式
- `--format ai` 选项，优化 Token 效率

### Changed
- 优化 CLI 脚本，消除硬编码路径
- 改进错误处理和跨平台兼容性
- 更新文档结构

### Fixed
- 修复路径检测问题

## [2.1.0] - 2026-03-10

### Added
- 统一版本管理模块 (`scripts/core/version.py`)
- 增强错误处理和调试模式
- 完善参考文档

### Changed
- 重构 SKILL.md 文档结构

### Fixed
- 修复硬编码路径问题

## [2.0.0] - 2026-03-07

### Added
- 迁移到 User Level Skill
- 集成 OpenFOAM 源码附件 (24,000+ 文件)
- 自动路径检测
- 完全自包含，无需外部依赖

### Changed
- 重构目录结构

## [1.0.0] - 2025-08-05

### Added
- 初始版本 (Project Level)
- 基础类继承分析功能
- 边界条件分析功能
- 物理模型分析功能
- 代码修改建议生成
