# GitHub 发布准备清单

## 需要删除的文件

这些文件包含你的系统路径，不适合公开发布：

```
❌ MIGRATION_REPORT.md    # 迁移报告，包含系统路径
❌ MIGRATION.md           # 迁移说明，包含系统路径  
❌ USAGE.md               # 使用说明，包含大量硬编码路径
❌ QUICKSTART.md          # 快速开始，包含硬编码路径
❌ switch_version.bat     # 版本切换脚本，特定于你的环境
❌ switch_version.ps1     # 版本切换脚本，特定于你的环境
```

**删除命令**（在 skill 目录执行）：

```powershell
# PowerShell
Remove-Item MIGRATION_REPORT.md, MIGRATION.md, USAGE.md, QUICKSTART.md, switch_version.bat, switch_version.ps1 -ErrorAction SilentlyContinue
```

## 需要保留的核心文件

```
✅ README.md              # 项目说明（已创建，无敏感信息）
✅ LICENSE                # MIT 许可证（已创建）
✅ CHANGELOG.md           # 版本变更记录（已创建）
✅ .gitignore             # Git 忽略规则（已创建）
✅ requirements.txt       # Python 依赖（已创建）
✅ SKILL.md               # Skill 定义文档
✅ VERSION.md             # 版本信息
✅ mcp_server.py          # MCP Server 入口
✅ ofa.bat / ofa.ps1      # CLI 入口（已优化，无硬编码路径）
✅ test_skill.py          # 测试脚本（无敏感路径）
✅ scripts/               # Python 分析脚本
✅ templates/             # 代码模板
✅ references/            # 参考文档
✅ attachments/ATTACHMENTS.md  # 源码获取说明（已创建）
```

## 源码附件处理

`attachments/OpenFOAM/` 目录包含 24,000+ 文件，建议：

### 方案 A：不包含在 Git 仓库中（推荐）

`.gitignore` 已配置排除此目录，用户需自行下载源码。

### 方案 B：使用 Git LFS

如果希望包含源码：

```bash
# 安装 Git LFS
git lfs install

# 追踪大文件
git lfs track "attachments/OpenFOAM/**/*.H"
git lfs track "attachments/OpenFOAM/**/*.C"

# 提交
git add .gitattributes
git add attachments/OpenFOAM/
```

### 方案 C：发布 Release 包

1. 在 GitHub 创建 Release
2. 将源码打包为 `openfoam-source.tar.gz` 上传
3. 用户下载后解压到 `attachments/OpenFOAM/`

## 发布步骤

```bash
# 1. 初始化 Git 仓库（如果尚未初始化）
cd ~/.codebuddy/skills/openfoam-expert
git init

# 2. 删除敏感文件
rm MIGRATION_REPORT.md MIGRATION.md USAGE.md QUICKSTART.md switch_version.bat switch_version.ps1

# 3. 添加文件
git add .

# 4. 提交
git commit -m "Initial release v2.2.0"

# 5. 关联远程仓库
git remote add origin https://github.com/Zyzhan417/OpenFOAM_expert_SKILL.git

# 6. 推送
git push -u origin main
```

## 最终目录结构

```
openfoam-expert/
├── README.md              # 项目说明
├── LICENSE                # MIT 许可证
├── CHANGELOG.md           # 变更记录
├── .gitignore             # Git 忽略规则
├── requirements.txt       # Python 依赖
├── SKILL.md               # Skill 定义
├── VERSION.md             # 版本信息
├── mcp_server.py          # MCP Server
├── ofa.bat                # Windows CLI
├── ofa.ps1                # PowerShell CLI
├── test_skill.py          # 测试脚本
├── scripts/
│   ├── router.py
│   ├── cache_manager.py
│   ├── output_formatter.py
│   ├── inheritance_analyzer.py
│   ├── boundary_analyzer.py
│   ├── model_analyzer.py
│   ├── code_modifier.py
│   └── core/
│       ├── code_accessor.py
│       ├── code_parser.py
│       └── version.py
├── templates/
├── references/
└── attachments/
    └── ATTACHMENTS.md     # 源码获取说明
```

## 检查清单

- [ ] 删除包含系统路径的文件
- [ ] 确认 `.gitignore` 正确配置
- [ ] 确认 `README.md` 中的仓库地址正确
- [ ] 确认 `LICENSE` 中的年份和作者正确
- [ ] 测试 `python scripts/router.py version` 正常运行
- [ ] 决定源码附件的处理方案
