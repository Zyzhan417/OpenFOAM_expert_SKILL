# 检索模式模板库

## 类定义搜索

### 基础类定义

```regex
# 搜索类声明
pattern: "class\s+\w+"
file_types: ".H"
scope: "source"

# 搜索带继承的类定义
pattern: "class\s+\w+\s*:\s*(public|protected|private)\s+\w+"
file_types: ".H"
scope: "source"

# 搜索特定基类的派生类
pattern: "class\s+\w+\s*:\s*public\s+BaseClassName"
file_types: ".H"
scope: "source"
```

### 模板类定义

```regex
# 搜索模板类
pattern: "template\s*<[^>]*>\s*class\s+\w+"
file_types: ".H"
scope: "source"

# 搜索特化模板
pattern: "template\s*<>\s*class\s+\w+"
file_types: ".H"
scope: "source"
```

## 函数搜索

### 函数声明

```regex
# 搜索成员函数声明
pattern: "\w+\s+\w+\s*\([^)]*\)\s*(const)?\s*;"
file_types: ".H"
scope: "source"

# 搜索虚函数
pattern: "virtual\s+\w+\s+\w+\s*\([^)]*\)"
file_types: ".H"
scope: "source"

# 搜索静态函数
pattern: "static\s+\w+\s+\w+\s*\([^)]*\)"
file_types: ".H"
scope: "source"
```

### 函数实现

```regex
# 搜索类外函数定义
pattern: "\w+\s+\w+::\w+\s*\([^)]*\)"
file_types: ".C"
scope: "source"

# 搜索特定类的成员函数实现
pattern: "ClassName::\w+\s*\([^)]*\)"
file_types: ".C"
scope: "source"

# 搜索构造函数
pattern: "\w+::\w+\s*\([^)]*\)\s*:"
file_types: ".C"
scope: "source"
```

### 关键算法函数

```regex
# 求解函数
pattern: "(void|autoPtr<\w+>)\s+(solve|correct|calculate|update)\s*\("
file_types: ".C"
scope: "source"

# 插值函数
pattern: "\w+\s+interpolate\s*\([^)]*\)"
file_types: ".C,.H"
scope: "source"

# 计算函数
pattern: "(Foam::)?\w+\s+(calc|compute|evaluate)\s*\("
file_types: ".C"
scope: "source"
```

## 边界条件搜索

### 边界条件类

```regex
# 搜索边界条件基类
pattern: "class\s+\w+FvPatchField"
file_types: ".H"
scope: "source"

# 搜索边界条件注册
pattern: "addToRunTimeSelectionTable.*FvPatchField"
file_types: ".C"
scope: "source"

# 搜索特定边界条件
pattern: "(fixedValue|zeroGradient|inletOutlet|mixed|pressureInletOutlet)FvPatchField"
file_types: ".H,.C"
scope: "source"
```

### 边界条件实现

```regex
# 搜索边界条件更新函数
pattern: "void\s+\w+FvPatchField.*::updateCoeffs\s*\("
file_types: ".C"
scope: "source"

# 搜索边界条件评估
pattern: "void\s+\w+FvPatchField.*::evaluate\s*\("
file_types: ".C"
scope: "source"
```

## 模型搜索

### 湍流模型

```regex
# 搜索湍流模型类
pattern: "class\s+\w+.*:\s*public\s+(RAS|LES)Model"
file_types: ".H"
scope: "source"

# 搜索 k-ε 模型
pattern: "kEpsilon|kEpsilonModel"
file_types: ".H,.C"
scope: "source"

# 搜索 SST 模型
pattern: "kOmegaSST|kOmegaSSTModel"
file_types: ".H,.C"
scope: "source"
```

### 多相流模型

```regex
# 搜索 VOF 模型
pattern: "(interFoam|VOF|volumeOfFluid)"
file_types: ".H,.C"
scope: "source"

# 搜索多相欧拉模型
pattern: "multiphaseEuler|multiphaseSystem"
file_types: ".H,.C"
scope: "source"

# 搜索相分数方程
pattern: "alpha.*eqn|alphaEqn"
file_types: ".C"
scope: "source"
```

### 热物理模型

```regex
# 搜索热物理模型
pattern: "thermophysicalModel|thermoModel"
file_types: ".H,.C"
scope: "source"

# 搜索反应模型
pattern: "reaction|Reaction\s*<"
file_types: ".H,.C"
scope: "source"
```

## 求解器搜索

### 主循环

```regex
# 搜索时间循环
pattern: "while\s*\(\s*runTime\.(loop|run)\s*\(\s*\)\s*\)"
file_types: ".C"
scope: "applications"

# 搜索求解器主文件
pattern: "int\s+main\s*\(\s*int\s+argc[^)]*\)"
file_types: ".C"
scope: "applications"
```

### 方程求解

```regex
# 搜索 solve 调用
pattern: "solve\s*\(\s*\w+\s*=="
file_types: ".C"
scope: "applications,source"

# 搜索 fvOptions
pattern: "fvOptions\.(constrain|correct|addSource)"
file_types: ".C"
scope: "applications,source"

# 搜索 PIMPLE 循环
pattern: "while\s*\(\s*pimple\.(loop|correct)\s*\("
file_types: ".C"
scope: "applications,source"
```

## 配置读取搜索

### 字典查找

```regex
# 搜索 lookup 调用
pattern: "\.lookup\s*\(\s*[\"']\w+[\"']\s*\)"
file_types: ".C"
scope: "source"

# 掷取参数并设默认值
pattern: "lookupOrDefault\s*<\w+>\s*\(\s*[\"']\w+[\"']\s*,"
file_types: ".C"
scope: "source"

# 搜索子字典
pattern: "subDict\s*\(\s*[\"']\w+[\"']\s*\)"
file_types: ".C,.H"
scope: "source"
```

## 宏和模板搜索

### 运行时选择表

```regex
# 搜索添加到选择表
pattern: "addToRunTimeSelectionTable\s*\(\s*\w+"
file_types: ".C"
scope: "source"

# 搜索声明选择表
pattern: "declareRunTimeSelectionTable"
file_types: ".H"
scope: "source"

# 搜索 New 函数
pattern: "static\s+autoPtr<\w+>\s+New\s*\("
file_types: ".H"
scope: "source"
```

### 类型定义

```regex
# 搜索 typedef
pattern: "typedef\s+\w+"
file_types: ".H"
scope: "source"

# 搜索 using 声明
pattern: "using\s+\w+\s*="
file_types: ".H"
scope: "source"
```

## 文件类型过滤策略

| 目标 | 文件类型 | 说明 |
|------|---------|------|
| 类定义 | `.H` | 头文件包含声明 |
| 函数实现 | `.C` | 源文件包含实现 |
| 模板实现 | `.H,.I.H` | 模板在头文件中实现 |
| 配置示例 | `.md` | 教程和文档 |

## 搜索范围选择策略

| 场景 | 范围 | 说明 |
|------|------|------|
| 核心类实现 | `source` | 在 src/ 中搜索 |
| 求解器主循环 | `applications` | 在 applications/solvers 中搜索 |
| 配置示例 | `tutorials` | 在 tutorials/ 中搜索 |
| 全面搜索 | `all` | 搜索全部范围 |

## 搜索结果过滤技巧

### 减少结果数量

1. **缩小文件类型**: 只搜索 `.H` 找声明
2. **缩小搜索范围**: 使用精确的 `scope`
3. **更精确的模式**: 添加更多上下文约束

### 提高结果相关性

1. **搜索核心目录**: 如 `finiteVolume/`、`OpenFOAM/`
2. **排除测试代码**: 注意路径中不含 `test/`
3. **优先核心实现**: 基类通常比派生类更相关

## 常见检索场景示例

### 场景: 查找 fixedValue 边界条件的实现

```python
# Step 1: 搜索类定义
search_openfoam_code(
    pattern="class\\s+fixedValueFvPatchField",
    file_types=".H",
    scope="source"
)

# Step 2: 定位到 finiteVolume/fields/fvPatchFields/basic/fixedValue/
# Step 3: 读取实现文件
read_openfoam_file(
    file_path="finiteVolume/fields/fvPatchFields/basic/fixedValue/fixedValueFvPatchField.C"
)
```

### 场景: 追踪 simpleFoam 的主循环

```python
# Step 1: 搜索求解器主文件
search_openfoam_code(
    pattern="int\\s+main\\s*\\(",
    file_types=".C",
    scope="applications"
)

# Step 2: 搜索时间循环
search_openfoam_code(
    pattern="while\\s*\\(\\s*runTime\\.loop",
    file_types=".C",
    scope="applications"
)
```

### 场景: 查找 k-ε 模型的实现

```python
# Step 1: 搜索模型类
search_openfoam_code(
    pattern="class\\s+kEpsilon",
    file_types=".H",
    scope="source"
)

# Step 2: 读取模型实现
read_openfoam_file(
    file_path="turbulenceModels/incompressible/RAS/kEpsilon/kEpsilon.C"
)
```
