# OpenFOAM Expert

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/Zyzhan417/OpenFOAM_expert_SKILL)
[![OpenFOAM](https://img.shields.io/badge/OpenFOAM-9-green.svg)](https://openfoam.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

**OpenFOAM 源码专家技能** - 为 AI 助手提供 OpenFOAM 代码检索、分析和修改建议能力。

## 功能特性

- 🔍 **类继承分析** - 追踪类继承链、生成派生树、扩展建议
- 🧱 **边界条件分析** - 参数解析、使用示例、创建建议
- 🌊 **物理模型分析** - 湍流/多相流/热物理模型解析
- 🤖 **MCP Server 支持** - 可被 Claude/Cursor 等 AI 直接调用
- 💾 **智能缓存** - 基于源码哈希的增量缓存，显著提升响应速度

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/Zyzhan417/OpenFOAM_expert_SKILL.git
cd openfoam-expert

# 安装依赖
pip install -r requirements.txt
```

### 配置 OpenFOAM 源码

方式一：使用内置源码（推荐）

将 OpenFOAM 源码放入 `attachments/OpenFOAM/src/` 目录。

方式二：使用系统安装的 OpenFOAM

```bash
# 设置环境变量
export FOAM_SRC=/opt/openfoam/src
# 或 Windows
set FOAM_SRC=C:\OpenFOAM\src
```

### CLI 使用

```bash
# 版本信息
python scripts/router.py version

# 类继承分析
python scripts/router.py inheritance --class fvMesh --chain

# 物理模型分析
python scripts/router.py model --type turbulence --name kEpsilon

# 边界条件分析
python scripts/router.py boundary --name fixedValue --params

# 搜索代码
python scripts/router.py search --pattern "class.*Mesh" --types .H
```

### MCP Server 配置

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "openfoam-expert": {
      "command": "python",
      "args": ["/path/to/openfoam-expert/mcp_server.py"]
    }
  }
}
```

配置文件位置：
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/claude/claude_desktop_config.json`

## 可用命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `inheritance` | 类继承分析 | `--class fvMesh --chain` |
| `boundary` | 边界条件分析 | `--name fixedValue --params` |
| `model` | 物理模型分析 | `--type turbulence --name kEpsilon` |
| `search` | 代码搜索 | `--pattern "class.*Mesh"` |
| `suggest` | 修改建议 | `--target boundary --name fixedValue --action create` |
| `version` | 版本信息 | - |
| `clear-cache` | 清除缓存 | - |

## 输出格式

支持多种输出格式：

```bash
# JSON 格式（默认）
python scripts/router.py inheritance --class fvMesh --format json

# AI 友好格式（Token 高效）
python scripts/router.py inheritance --class fvMesh --format ai

# Markdown 格式
python scripts/router.py inheritance --class fvMesh --format markdown
```

## 目录结构

```
openfoam-expert/
├── SKILL.md                 # Skill 定义文档
├── mcp_server.py            # MCP Server 入口
├── scripts/
│   ├── router.py            # 统一命令路由器
│   ├── cache_manager.py     # 缓存管理
│   ├── output_formatter.py  # 输出格式化
│   ├── inheritance_analyzer.py
│   ├── boundary_analyzer.py
│   ├── model_analyzer.py
│   └── core/
│       ├── code_accessor.py
│       ├── code_parser.py
│       └── version.py
├── attachments/
│   └── OpenFOAM/src/        # OpenFOAM 源码（需单独下载）
├── templates/               # 代码模板
└── references/              # 参考文档
```

## 作为 CodeBuddy Skill 使用

将此目录放入你的 CodeBuddy skills 目录：

```bash
# Linux/macOS
cp -r openfoam-expert ~/.codebuddy/skills/

# Windows
xcopy /E /I openfoam-expert %USERPROFILE%\.codebuddy\skills\openfoam-expert
```

## 依赖

- Python 3.8+
- 标准库（无额外依赖）

## 许可证

[MIT License](LICENSE)

## 致谢

- [OpenFOAM](https://openfoam.org/) - 开源 CFD 工具箱
- [CodeBuddy](https://www.codebuddy.ai/) - AI 编程助手
