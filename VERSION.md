# OpenFOAM Expert Skill 版本信息

**当前版本**: v2.2.0 (User Level)
**更新日期**: 2026-03-18

## 版本历史

### v2.2.0 (User Level) - 2026-03-18 ✅
- ✅ 新增 MCP Server 封装，支持 Claude/Cursor 直接调用
- ✅ 新增统一命令路由器 (router.py)
- ✅ 新增缓存管理模块 (cache_manager.py)
- ✅ 新增输出格式化器，支持 AI 友好格式
- ✅ 优化 CLI 脚本，消除硬编码路径
- ✅ 改进错误处理和跨平台兼容性

**新特性**：
- **统一版本管理**：所有脚本版本号集中管理，通过 `scripts/core/version.py` 维护
- **调试模式**：`CodeAccessor` 支持 `debug=True` 参数，输出详细调试信息
- **增强错误处理**：统一异常处理，提供清晰的错误消息
- **完善文档**：详细的使用参考和工作流程指南

**使用示例**：
```bash
# 查看版本信息
python scripts/inheritance_analyzer.py --version

# 使用调试模式
# 在 Python 代码中
from code_accessor import CodeAccessor, AccessMode
accessor = CodeAccessor(debug=True)
```

---

### v2.0 (User Level) - 2026-03-07 ✅
- ✅ 迁移到用户级别
- ✅ 集成OpenFOAM源码附件（24,330个文件）
- ✅ 自动路径检测
- ✅ 完全自包含，无需外部依赖
- ✅ 所有项目全局可用

**识别特征**:
- ✅ 包含 `attachments/` 目录
- ✅ 包含 `MIGRATION.md` 文件
- ✅ 包含 `test_skill.py` 测试脚本
- ✅ SKILL.md 第16行显示 "集成源码附件"
- ✅ code_accessor.py 支持自动路径检测

---

### v1.0 (Project Level) - 2025-08-05
- ⚠️ 项目级别
- ⚠️ 依赖外部源码路径 `e:\04_OpenFOAM\CodeAndDoc`
- ⚠️ 仅限单个项目使用
- ⚠️ 需要手动配置源码路径

---

## 如何区分当前使用的版本

### 方法1: 运行 --version 命令
```bash
python scripts/inheritance_analyzer.py --version
```

输出示例：
```
============================================================
  openfoam-expert v2.2.0
============================================================
  Release Date: 2026-03-18
  OpenFOAM Version: 13
  Skill Root: /path/to/skill
  Source Files: 17100 (8762 .H + 8338 .C)
============================================================
```

### 方法2: 检查版本管理模块
```bash
python scripts/core/version.py
```

### 方法3: 检查目录结构
```bash
# v2.1.0 及以上版本
ls scripts/core/version.py  # 存在
ls references/usage-reference.md  # 存在
ls references/modification-workflows.md  # 存在

# v2.0 版本
ls scripts/core/version.py  # 不存在
```

---

## 目录结构（v2.1.0）

```
openfoam-expert/
├── SKILL.md                          # 主文档（精简版）
├── VERSION.md                        # 本文件
├── scripts/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── code_accessor.py         # 代码访问器（增强错误处理）
│   │   ├── code_parser.py
│   │   └── version.py               # [NEW] 统一版本管理
│   ├── inheritance_analyzer.py      # [MODIFY] 支持 --version
│   ├── boundary_analyzer.py         # [MODIFY] 支持 --version
│   ├── model_analyzer.py            # [MODIFY] 支持 --version
│   └── code_modifier.py             # [MODIFY] 支持 --version
├── references/
│   ├── openfoam-structure.md
│   ├── search-patterns.md
│   ├── solver-analysis-guide.md
│   ├── usage-reference.md           # [NEW] 详细参数参考
│   └── modification-workflows.md    # [NEW] 修改工作流详解
├── templates/
│   ├── solver_modification.md
│   ├── boundary_modification.md
│   └── model_modification.md
├── test_skill.py                    # [MODIFY] 动态路径
└── attachments/
    └── OpenFOAM/                    # 源码附件
```

---

## 技术支持

如有问题，请检查：
1. 运行 `python scripts/inheritance_analyzer.py --version` 查看版本信息
2. 查看 `references/usage-reference.md` 了解详细参数
3. 查看 `references/modification-workflows.md` 了解工作流程
4. 运行测试脚本 `python test_skill.py`
5. 使用调试模式排查问题：`CodeAccessor(debug=True)`

---

**最后更新**: 2026-03-18
**维护状态**: v2.2.0 活跃维护
