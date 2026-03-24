---
name: openfoam-expert
description: |
  OpenFOAM source code retrieval and analysis skill. Trigger when working on OpenFOAM cases and needing to: (1) look up valid fvModel/fvConstraint/boundary condition types and their dictionary syntax, (2) understand how a specific class is implemented (source code location, inheritance, member functions), (3) verify correct usage of coded/C++ constructs in case files (fvOptions, coded boundary conditions, function objects), (4) find the source code for any OpenFOAM class using regex search, (5) generate dictionary templates with correct required keywords by cross-referencing .H file Usage examples and code template files. ALWAYS verify required keywords against source code templates (e.g., codedFvModelTemplate.C) and .H file Usage blocks before generating any dictionary template. Does NOT modify files directly - returns analysis results for the caller to apply.
  |
  OpenFOAM 源码检索与分析技能。在以下场景触发：(1) 需要查找合法的fvModel/fvConstraint/边界条件类型及其字典语法，(2) 需要了解某个类的实现细节（源码位置、继承关系、成员函数），(3) 需要验证case文件中coded/C++写法的正确性（fvOptions、coded边界条件、function objects），(4) 需要用正则表达式搜索OpenFOAM源码，(5) 需要生成字典模板并确保必填关键字完整正确。生成字典模板时必须对照源码模板文件和.H文件中的Usage示例验证。不直接修改文件，仅返回分析结果供调用方使用。
---

# OpenFOAM Expert

## Overview

OpenFOAM Expert 提供系统化的代码检索、分析和修改建议能力，实现"代码搜索→代码分析→修改建议"的完整闭环。

**核心特性**：
- **MCP Server 支持**：可被 Claude/Cursor 等 AI 直接调用（v2.2.0 新增）
- **统一命令路由器**：单一入口，支持全局钩子（v2.2.0 新增）
- **智能缓存**：基于源码哈希的增量缓存（v2.2.0 新增）
- 双模式代码访问：优先MCP工具，自动回退到本地文件
- 三大分析场景：类继承、边界条件、物理模型
- 标准化修改建议：基于分析结果生成可操作的代码模板
- 集成源码附件：包含OpenFOAM完整源码，无需外部依赖

**环境配置**：
- OpenFOAM源码路径：`{SKILL_ROOT}/attachments/OpenFOAM`
- 脚本默认路径：`{SKILL_ROOT}/scripts`
- 缓存目录：`{SKILL_ROOT}/.openfoam_cache`

## Quick Start

### 统一 CLI 入口（推荐）

```bash
# 使用 ofa 命令（需将 skill 目录加入 PATH 或使用完整路径）
ofa inheritance --class fvMesh --chain
ofa model --type turbulence --name kEpsilon
ofa boundary --name fixedValue --params
ofa version
ofa help
```

### 直接调用脚本

```bash
# 检查版本
python scripts/router.py version

# 类继承分析
python scripts/router.py inheritance --class fvMesh --chain

# 物理模型分析
python scripts/router.py model --type turbulence --name kEpsilon

# 边界条件分析
python scripts/router.py boundary --name fixedValue --params
```

### MCP Server 调用（v2.2.0 新增）

本 Skill 支持作为 MCP Server 运行，供 Claude/Cursor 等 AI 直接调用。

**配置方法（Claude Desktop）**：

编辑 `claude_desktop_config.json`：
```json
{
  "mcpServers": {
    "openfoam-expert": {
      "command": "python",
      "args": ["C:/path/to/skill/mcp_server.py"]
    }
  }
}
```

**可用 MCP 工具**：

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `analyze_inheritance` | 类继承分析 | class_name, show_chain, show_tree |
| `analyze_boundary` | 边界条件分析 | name, show_params, show_examples |
| `analyze_model` | 物理模型分析 | model_type, model_name |
| `suggest_modification` | 修改建议 | target, name, action |
| `search_code` | 代码搜索 | pattern, file_types, scope |
| `get_version` | 版本信息 | 无 |

## CLI Usage

## Core Capabilities

### 1. 类继承关系分析

分析OpenFOAM类的继承关系、设计模式和修改建议。

**触发场景**：
- "某某类继承自哪里"
- "查找某某类的派生类"
- "分析某某类的设计模式"

**输出示例**：
```json
{
  "success": true,
  "class_name": "fvMesh",
  "file_path": "finiteVolume/fvMesh/fvMesh.H",
  "base_classes": ["polyMesh"],
  "inheritance_chain": [...],
  "design_patterns": ["Strategy", "Factory"]
}
```

### 2. 边界条件分析

分析边界条件的实现、参数配置和使用方法。

**触发场景**：
- "某某边界条件怎么实现"
- "某某边界条件有哪些参数"
- "如何使用某某边界条件"

**输出示例**：
```json
{
  "success": true,
  "boundary_condition": "fixedValue",
  "base_class": "fixedValueFvPatchField",
  "parameters": [...],
  "required_parameters": ["value"]
}
```

### 3. 物理模型分析

分析湍流模型、多相流模型、热物理模型的实现和配置。

**触发场景**：
- "kEpsilon模型的实现"
- "interFoam的算法"
- "热物理模型的参数"

**输出示例**：
```json
{
  "success": true,
  "model_name": "kEpsilon",
  "model_type": "turbulence",
  "category": "RANS",
  "equations": ["k方程", "epsilon方程"],
  "parameters": [...]
}
```

### 4. 代码修改建议生成

基于分析结果生成标准化的修改建议和代码模板。

**触发场景**：
- "如何扩展某某类"
- "如何创建新的边界条件"
- "如何修改模型参数"

## Script Usage

### 通用参数

所有脚本支持以下通用参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--root` | OpenFOAM src目录路径 | 自动检测 |
| `--mode` | 代码访问模式 (auto/mcp/local) | `auto` |
| `--format` | 输出格式 (json/text) | `json` |
| `-v, --version` | 显示版本信息 | - |

### 脚本调用规范

**关键**：使用相对路径或自动检测路径，避免硬编码绝对路径。

**推荐方式**：
```bash
# 方式1：相对路径（从SKILL_ROOT执行）
cd {SKILL_ROOT}
python scripts/inheritance_analyzer.py --class fvMesh --chain

# 方式2：使用环境变量
export OPENFOAM_SKILL_ROOT=/path/to/skill
python $OPENFOAM_SKILL_ROOT/scripts/inheritance_analyzer.py --class fvMesh --chain

# 方式3：使用绝对路径（通用但需根据实际位置调整）
python /absolute/path/to/skill/scripts/inheritance_analyzer.py --class fvMesh --chain
```

**注意**：脚本会自动检测Skill根目录和源码位置，通常无需手动指定 `--root` 参数。

## Workflow

### 验证字典模板的强制流程

**教训（2026-03-24）**：coded fvModel 模板中遗漏了 `cellZone`（必填项），
导致用户运行时 `FOAM FATAL IO ERROR: cellZone not specified`。根因是模板编写时
未严格对照源码中的模板文件和 .H 文件中的官方 Usage 示例。

生成任何 OpenFOAM 字典模板时，**必须**按以下顺序验证：

```
Step 1: 找到 .H 文件中的 Usage/Description 示例
    └─ 这是最权威的字典写法参考
       例: codedFvModel.H 第30-64行的 \verbatim 块

Step 2: 找到对应的代码模板文件 (etc/codeTemplates/dynamicCode/)
    └─ 确认模板构造函数中读取了哪些字典关键字
       例: codedFvModelTemplate.C 中 zone_(mesh, coeffs(dict)) 要求 cellZone

Step 3: 确认 coeffs(dict) 的范围
    └─ fvModel 通常查找 <type>Coeffs 子字典，找不到则使用顶层字典
       例: coded 类型查找 codedCoeffs 子字典，或使用顶层字典本身

Step 4: 检查基类构造函数是否有额外的必读关键字
    └─ 例: fvCellZone 构造函数要求 cellZone, fvConstraint 基类可能要求其他项

Step 5: 列出所有必填项，写入模板
    └─ 不要从"通用 fvModel 知识"推断某个类型的关键字
       不要将其他 fvModel 类型的关键字（如 selectionMode）套用到 coded 类型
```

**已知的跨类型关键字混淆**：

| 关键字 | 实际适用的类型 | 不适用的类型 |
|--------|---------------|-------------|
| `selectionMode` | 多数 fvModel/fvConstraint | `coded`（使用 `cellZone`） |
| `cellZone` | `coded`, 部分 fvModel | 不使用 zone 的 fvModel |
| `field` | `coded` | 不需要指定场名的 fvModel |

### 标准工作流程

```
Step 1: 需求分析
    ├─ 理解用户目标
    └─ 确定分析类型

Step 2: 代码分析
    ├─ 选择合适的分析脚本
    ├─ 执行分析
    └─ 获取结果

Step 3: 结果解读
    ├─ 理解分析输出
    └─ 提取关键信息

Step 4: 修改建议
    ├─ 生成代码模板（按上方验证流程）
    └─ 提供实施步骤

Step 5: 实施指导
    ├─ 文件创建/修改
    └─ 编译测试
```

### 常见场景示例

详细的工作流程和代码模板请参考：
- `references/modification-workflows.md` - 完整修改工作流
- `templates/` - 代码修改模板目录

## MCP Integration

本 Skill 与 MCP 工具协同工作：

```python
# 搜索代码（MCP优先，自动回退本地）
mcp_call_tool(
    serverName="openfoam-analyzer",
    toolName="search_openfoam_code",
    arguments={
        "pattern": "class\\s+\\w+\\s*:\\s*public",
        "file_types": ".H",
        "scope": "source"
    }
)
```

## References

### 详细文档

- `references/openfoam-structure.md` - OpenFOAM 源码目录结构和核心类层次
- `references/search-patterns.md` - 各类检索场景的正则表达式模板库
- `references/solver-analysis-guide.md` - 求解器代码分析的详细指南
- `references/usage-reference.md` - 详细参数说明和使用示例
- `references/modification-workflows.md` - 完整修改工作流程和案例

### 关键源码位置速查

| 组件 | 源码路径 | 说明 |
|------|----------|------|
| coded fvModel | `src/fvModels/general/codedFvModel/` | 动态代码生成fvModel |
| coded 模板 | `etc/codeTemplates/dynamicCode/codedFvModelTemplate.*` | 代码生成模板 |
| fvModel 基类 | `src/fvModels/fvModel/` | fvModel框架基础 |
| 边界条件模板 | `etc/codeTemplates/dynamicCode/codedFvPatchFieldTemplate.*` | 动态边界条件模板 |

### 代码模板

- `templates/solver_modification.md` - 求解器修改模板
- `templates/boundary_modification.md` - 边界条件修改模板
- `templates/model_modification.md` - 物理模型修改模板
- `templates/fvModel_modification.md` - fvModel源项修改模板（含coded fvModel用法）

## Quick Reference

### 常见需求速查

| 用户说... | 执行... |
|-----------|---------|
| "某某类继承自哪里" | `python scripts/inheritance_analyzer.py --class ClassName --chain` |
| "创建新的边界条件" | `python scripts/code_modifier.py --target boundary --name BaseBC --action create` |
| "kEpsilon模型的参数" | `python scripts/model_analyzer.py --type turbulence --name kEpsilon` |
| "如何扩展某某类" | `python scripts/code_modifier.py --target class --name ClassName --action extend` |
| "如何使用coded fvModel" | 查看 `templates/fvModel_modification.md` 或搜索 `codedFvModel` |
| "验证字典写法是否正确" | 对照 .H 文件 Usage 块 + codeTemplates 中的模板文件 |
| "这个参数是什么意思" | 搜索参数读取代码 + 查看 tutorial 配置 |

### 输出格式说明

所有脚本输出均为JSON格式，包含以下标准字段：

```json
{
  "success": true|false,          // 操作是否成功
  "error": "...",                 // 错误信息（失败时）
  "data": {...},                  // 主要数据
  "locations": [...],             // 代码位置信息
  "modification_suggestions": [...] // 修改建议
}
```

## Best Practices

### 分析前准备

1. 首次使用建议运行 `--version` 检查环境
2. 大范围扫描（如全部类定义）会较慢，建议缩小范围
3. 使用精确的搜索模式减少搜索范围

### 修改建议使用

1. 优先使用 `extend` 而非直接 `modify` 现有类
2. 修改前备份原始文件
3. 使用版本控制跟踪变更
4. 修改后进行充分测试

## Troubleshooting

### 常见问题

**Q: 脚本提示找不到源码路径？**
A: 脚本会自动检测源码位置，如需指定可使用 `--root` 参数或设置 `FOAM_SRC` 环境变量。

**Q: 搜索速度很慢？**
A: v2.2.0 版本已添加缓存机制，首次扫描后后续查询会显著加速。也可缩小搜索范围、使用更精确的正则表达式。

**Q: 如何确认使用的版本？**
A: 运行 `ofa version` 或 `python scripts/router.py version`。

**Q: MCP Server 如何调试？**
A: 运行 `python mcp_server.py --test` 进入测试模式，验证工具功能是否正常。

**Q: 如何清除缓存？**
A: 运行 `ofa clear-cache` 或删除 `.openfoam_cache` 目录。

---

**版本**: 2.3.0  
**更新日期**: 2026-03-24  
**维护状态**: 活跃维护
