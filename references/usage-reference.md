# OpenFOAM Expert Skill 使用参考

本文档提供所有分析脚本的详细参数说明和使用示例。

## 通用参数

所有分析脚本支持以下通用参数：

### 路径和模式参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `--root` | string | OpenFOAM src目录路径 | 自动检测 |
| `--mode` | enum | 代码访问模式：`auto`（自动选择）、`mcp`（MCP工具）、`local`（本地文件） | `auto` |
| `--format` | enum | 输出格式：`json`、`text` | `json` |
| `-v, --version` | flag | 显示版本信息 | - |

### 路径自动检测逻辑

脚本按以下优先级检测OpenFOAM源码路径：

1. `--root` 参数指定的路径
2. 环境变量 `FOAM_SRC`
3. Skill attachments目录：`{SKILL_ROOT}/attachments/OpenFOAM/src`
4. Linux标准路径：`/opt/openfoam/src`

---

## inheritance_analyzer.py

类继承关系分析工具。

### 功能

1. 分析类的完整继承链
2. 发现派生类
3. 构建继承树
4. 识别设计模式
5. 生成修改建议

### 参数详解

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--class` | string | 要分析的类名 | `--class fvMesh` |
| `--chain` | flag | 显示继承链（从当前类到基类） | `--chain` |
| `--tree` | flag | 显示派生树（从当前类到派生类） | `--tree` |
| `--depth` | int | 派生树搜索深度 | `--depth 3` (默认: 3) |
| `--patterns` | flag | 分析设计模式 | `--patterns` |
| `--suggest` | enum | 生成修改建议：`extend`（扩展）、`implement`（实现）、`modify`（修改） | `--suggest extend` |
| `--search` | string | 搜索匹配模式的类名（支持通配符） | `--search "*FvPatchField*"` |
| `--list` | flag | 列出搜索结果详情 | `--list` |

### 使用示例

#### 1. 查看类的继承链

```bash
python scripts/inheritance_analyzer.py --class fvMesh --chain
```

输出：
```json
{
  "success": true,
  "class_name": "fvMesh",
  "file_path": "finiteVolume/fvMesh/fvMesh.H",
  "line_number": 52,
  "base_classes": ["polyMesh"],
  "inheritance_chain": [
    {
      "name": "fvMesh",
      "file_path": "finiteVolume/fvMesh/fvMesh.H",
      "line_number": 52
    },
    {
      "name": "polyMesh",
      "file_path": "OpenFOAM/meshes/polyMesh/polyMesh.H",
      "line_number": 48
    },
    {
      "name": "objectRegistry",
      "file_path": "OpenFOAM/db/objectRegistry/objectRegistry.H",
      "line_number": 51
    }
  ]
}
```

#### 2. 查看派生树

```bash
python scripts/inheritance_analyzer.py --class turbulenceModel --tree --depth 2
```

#### 3. 分析设计模式

```bash
python scripts/inheritance_analyzer.py --class kEpsilon --patterns
```

#### 4. 生成扩展建议

```bash
python scripts/inheritance_analyzer.py --class turbulenceModel --suggest extend
```

#### 5. 搜索类名

```bash
# 搜索所有包含FvPatchField的类
python scripts/inheritance_analyzer.py --search "*FvPatchField*" --list
```

---

## boundary_analyzer.py

边界条件分析工具。

### 功能

1. 分析边界条件类型和实现机制
2. 提取参数配置信息
3. 查找使用示例
4. 生成修改建议

### 参数详解

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--name` | string | 边界条件名称 | `--name fixedValue` |
| `--params` | flag | 显示参数信息 | `--params` |
| `--base` | flag | 显示基类信息 | `--base` |
| `--examples` | flag | 查找使用示例 | `--examples` |
| `--suggest` | enum | 生成修改建议：`create`（创建）、`modify`（修改）、`use`（使用） | `--suggest create` |
| `--search` | string | 搜索边界条件 | `--search "*Inlet*"` |
| `--list` | flag | 列出所有边界条件 | `--list` |
| `--category` | string | 按类别过滤 | `--category turbulent` |

### 边界条件类别

- `basic` - 基础边界条件
- `derived` - 派生边界条件
- `fixedValue` - 固定值类型
- `inletOutlet` - 入口出口类型
- `turbulent` - 湍流边界条件
- `temperature` - 温度边界条件
- `wall` - 壁面边界条件

### 使用示例

#### 1. 查看边界条件参数

```bash
python scripts/boundary_analyzer.py --name fixedValue --params
```

输出：
```json
{
  "success": true,
  "boundary_condition": "fixedValue",
  "file_path": "finiteVolume/fields/fvPatchFields/fixedValue/fixedValueFvPatchField.H",
  "base_class": "fvPatchField",
  "parameters": [
    {
      "name": "value",
      "type": "Field<Type>",
      "required": true,
      "description": "固定值"
    }
  ],
  "required_parameters": ["value"],
  "optional_parameters": []
}
```

#### 2. 查找使用示例

```bash
python scripts/boundary_analyzer.py --name inletOutlet --examples
```

#### 3. 查看基类信息

```bash
python scripts/boundary_analyzer.py --name fixedValue --base
```

#### 4. 生成创建建议

```bash
python scripts/boundary_analyzer.py --name fixedValue --suggest create
```

#### 5. 列出所有湍流边界条件

```bash
python scripts/boundary_analyzer.py --list --category turbulent
```

---

## model_analyzer.py

物理模型分析工具。

### 功能

1. 分析湍流模型（RANS/LES）
2. 分析多相流模型（VOF/Eulerian）
3. 分析热物理模型
4. 分析粒子群平衡模型
5. 生成修改建议

### 参数详解

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--type` | enum | 模型类型：`turbulence`、`multiphase`、`thermophysical`、`populationBalance`、`reaction` | `--type turbulence` |
| `--name` | string | 模型名称 | `--name kEpsilon` |
| `--search` | string | 搜索模型 | `--search "*kOmega*"` |
| `--list` | flag | 列出模型 | `--list` |
| `--suggest` | enum | 生成修改建议：`extend`（扩展）、`modify`（修改）、`add_equation`（添加方程） | `--suggest extend` |

### 模型类型说明

#### turbulence - 湍流模型

**RANS模型**：
- `kEpsilon` - 标准k-ε模型
- `realizableKEpsilon` - 可实现k-ε模型
- `kOmega` - 标准k-ω模型
- `kOmegaSST` - SST k-ω模型
- `kOmegaSSTLM` - SST模型+转捩模型
- `SpalartAllmaras` - 单方程模型

**LES模型**：
- `Smagorinsky` - 基础LES模型
- `dynamicLagrangian` - 动态Lagrangian LES模型
- `kEqn` - 单方程LES模型

#### multiphase - 多相流模型

- `interFoam` - VOF方法，两相流
- `interDyMFoam` - VOF方法 + 动网格
- `interIsoFoam` - VOF方法 + 几何重构
- `multiphaseEulerFoam` - 多相欧拉方法
- `twoPhaseEulerFoam` - 两相欧拉方法

#### thermophysical - 热物理模型

- `heRhoThermo` - 能量+密度+热物理
- `hePsiThermo` - 能量+可压缩性
- `rhoThermo` - 密度热物理
- `psiThermo` - 可压缩性热物理

### 使用示例

#### 1. 分析湍流模型

```bash
python scripts/model_analyzer.py --type turbulence --name kEpsilon
```

输出：
```json
{
  "success": true,
  "model_name": "kEpsilon",
  "model_type": "turbulence",
  "category": "RANS",
  "file_path": "turbulenceModels/incompressible/RAS/kEpsilon/kEpsilon.H",
  "equations": ["k方程", "epsilon方程"],
  "parameters": [
    {
      "name": "Cmu",
      "value": 0.09,
      "description": "模型常数"
    },
    {
      "name": "C1",
      "value": 1.44,
      "description": "模型常数"
    },
    {
      "name": "C2",
      "value": 1.92,
      "description": "模型常数"
    },
    {
      "name": "sigmaEps",
      "value": 1.3,
      "description": "epsilon的普朗特数"
    }
  ],
  "config_file": "turbulenceProperties"
}
```

#### 2. 分析多相流模型

```bash
python scripts/model_analyzer.py --type multiphase --name interFoam
```

#### 3. 列出所有湍流模型

```bash
python scripts/model_analyzer.py --list --type turbulence
```

#### 4. 搜索模型

```bash
python scripts/model_analyzer.py --type turbulence --search "*kOmega*"
```

#### 5. 生成扩展建议

```bash
python scripts/model_analyzer.py --type turbulence --name kEpsilon --suggest extend
```

---

## code_modifier.py

代码修改建议生成器。

### 功能

1. 整合各分析器的结果
2. 生成标准化修改建议
3. 提供代码模板
4. 输出完整的修改方案

### 参数详解

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--target` | enum | 目标类型：`class`、`boundary`、`model` | `--target class` |
| `--name` | string | 目标名称 | `--name kEpsilon` |
| `--type` | enum | 模型类型（仅用于model目标） | `--type turbulence` |
| `--action` | enum | 操作类型：`create`、`extend`、`modify`、`use` | `--action extend` |
| `--input` | string | 分析结果文件路径 | `--input analysis.json` |
| `--output` | string | 输出文件路径 | `--output suggestions.json` |

### 使用示例

#### 1. 扩展类

```bash
python scripts/code_modifier.py --target class --name kEpsilon --action extend
```

输出：
```json
{
  "success": true,
  "target": {
    "type": "class",
    "name": "kEpsilon",
    "action": "extend"
  },
  "suggestions": [
    {
      "type": "create_derived_class",
      "description": "创建派生类",
      "template": "// 头文件模板\n...",
      "steps": [
        "创建派生类头文件",
        "继承kEpsilon类",
        "重写虚函数",
        "添加新成员和方法",
        "注册到选择表",
        "编译测试"
      ],
      "required_files": [
        "MyKEpsilon.H",
        "MyKEpsilon.C",
        "Make/files",
        "Make/options"
      ]
    }
  ],
  "general_recommendations": [
    "优先使用extend而非直接修改现有类",
    "修改前备份原始文件",
    "使用版本控制跟踪变更",
    "修改后进行充分测试"
  ]
}
```

#### 2. 创建新边界条件

```bash
python scripts/code_modifier.py --target boundary --name fixedValue --action create
```

#### 3. 修改模型

```bash
python scripts/code_modifier.py --target model --type turbulence --name kEpsilon --action modify
```

#### 4. 从分析结果文件生成建议

```bash
# 先执行分析
python scripts/inheritance_analyzer.py --class kEpsilon --chain --suggest extend > analysis.json

# 再生成建议
python scripts/code_modifier.py --input analysis.json --output suggestions.json
```

---

## 输出格式规范

### 标准输出格式

所有脚本输出均为JSON格式，包含以下标准字段：

```json
{
  "success": true|false,          // 操作是否成功（必需）
  "error": "...",                 // 错误信息（失败时必需）
  "data": {...},                  // 主要数据（成功时）
  "locations": [                  // 代码位置信息（可选）
    {
      "file_path": "...",
      "line_number": 42,
      "content": "..."
    }
  ],
  "modification_suggestions": [...] // 修改建议（可选）
}
```

### JSON输出格式化

使用 `jq` 工具格式化JSON输出：

```bash
# 美化输出
python scripts/inheritance_analyzer.py --class fvMesh --chain | jq .

# 提取特定字段
python scripts/inheritance_analyzer.py --class fvMesh --chain | jq '.base_classes'

# 过滤结果
python scripts/boundary_analyzer.py --list | jq '.boundary_conditions[] | select(.category == "turbulent")'
```

---

## 性能优化

### 搜索优化

1. **使用精确的正则表达式**
   ```bash
   # 好：精确匹配
   python scripts/inheritance_analyzer.py --class "^fvMesh$"
   
   # 差：模糊匹配
   python scripts/inheritance_analyzer.py --search "*Mesh*"
   ```

2. **限制搜索范围**
   - 使用 `--depth` 参数限制派生树深度
   - 使用 `--category` 参数过滤边界条件
   - 使用 `--type` 参数限定模型类型

3. **利用缓存**
   - 类继承分析首次扫描后会缓存结果
   - 同一脚本的多次调用会更快

### 大规模分析

对于大规模代码分析：

```bash
# 1. 先执行小范围测试
python scripts/inheritance_analyzer.py --class fvMesh --chain

# 2. 确认无误后扩大范围
python scripts/inheritance_analyzer.py --search "*FvPatchField*" --list

# 3. 使用输出重定向保存结果
python scripts/inheritance_analyzer.py --search "*" --list > all_classes.json
```

---

## 故障排查

### 常见错误

#### 1. 源码路径不存在

**错误信息**：
```
FileNotFoundError: OpenFOAM source path not found
```

**解决方法**：
```bash
# 方法1：指定路径
python scripts/inheritance_analyzer.py --root /path/to/openfoam/src --class fvMesh

# 方法2：设置环境变量
export FOAM_SRC=/path/to/openfoam/src
python scripts/inheritance_analyzer.py --class fvMesh
```

#### 2. 类/边界条件未找到

**错误信息**：
```json
{
  "success": false,
  "error": "未找到类: MyClass"
}
```

**解决方法**：
- 检查拼写是否正确
- 使用 `--search` 参数模糊搜索
- 查看是否在正确的模型类型下

#### 3. MCP工具不可用

**错误信息**：
```
Warning: MCP tool not available, falling back to local file access
```

**说明**：
- 这是警告而非错误，脚本会自动回退到本地文件访问
- 不影响功能，只是性能可能稍慢

---

## 高级用法

### 批处理分析

```bash
# 批量分析多个类
for class in fvMesh polyMesh turbulenceModel; do
  python scripts/inheritance_analyzer.py --class $class --chain > ${class}_chain.json
done

# 批量分析边界条件
for bc in fixedValue zeroGradient inletOutlet; do
  python scripts/boundary_analyzer.py --name $bc --params > ${bc}_params.json
done
```

### 与其他工具集成

```bash
# 与grep结合
python scripts/inheritance_analyzer.py --class fvMesh --chain | jq '.file_path' | xargs grep -n "virtual"

# 与编译系统集成
python scripts/code_modifier.py --target class --name MySolver --action create --output Make/files
```

---

**最后更新**: 2026-03-10  
**版本**: 2.1.0
