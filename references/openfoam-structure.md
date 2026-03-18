# OpenFOAM 源码结构知识

## 源码目录结构

### 核心目录 (src/)

```
src/
├── OpenFOAM/                    # 核心基础库
│   ├── db/                     # 数据库管理 (registry, time)
│   ├── fields/                 # 场数据结构 (Field, GeometricField)
│   ├── meshes/                 # 网格结构 (polyMesh, fvMesh)
│   ├── primitives/             # 基础数据类型 (scalar, vector, tensor)
│   └── global/                 # 全局函数和常量
│
├── finiteVolume/               # 有限体积法核心
│   ├── fvMesh/                 # 有限体积网格
│   ├── fields/                 # 场的有限体积实现
│   │   ├── fvPatchFields/      # 边界条件
│   │   └── fvsPatchFields/     # 表面场边界条件
│   ├── interpolation/          # 插值方法
│   └── convectionSchemes/      # 对流格式
│
├── turbulenceModels/           # 湍流模型
│   ├── incompressible/         # 不可压缩湍流
│   │   ├── RAS/               # RANS 模型 (k-ε, k-ω, SST)
│   │   └── LES/               # 大涡模拟
│   └── compressible/           # 可压缩湍流
│
├── thermophysicalModels/       # 热物理模型
│   ├── basic/                  # 基础热物理
│   ├── reactionThermo/         # 反应热力学
│   └── specie/                 # 组分模型
│
├── transportModels/            # 输运模型
│   ├── incompressible/         # 不可压缩输运
│   └── compressible/           # 可压缩输运
│
├── multiphaseInterFoam/        # 多相流模型
│   ├── interFoam/              # VOF 方法
│   └── interDyMFoam/           # 动网格 VOF
│
└── populationBalance/          # 粒子群平衡模型
    ├── coalescenceModels/      # 聚并模型
    ├── breakupModels/          # 破碎模型
    └── nucleationModels/       # 成核模型
```

### 应用程序目录 (applications/)

```
applications/
├── solvers/                    # 求解器
│   ├── incompressible/         # 不可压缩流动
│   │   ├── simpleFoam/        # 稳态 SIMPLE
│   │   ├── pisoFoam/          # 瞬态 PISO
│   │   └── icoFoam/           # 层流不可压缩
│   ├── compressible/           # 可压缩流动
│   ├── multiphase/             # 多相流
│   │   ├── interFoam/         # VOF 两相流
│   │   └── multiphaseEulerFoam/ # 多相欧拉
│   ├── combustion/             # 燃烧
│   └── heatTransfer/           # 传热
│
└── utilities/                  # 工具程序
    ├── mesh/                   # 网格处理
    ├── postProcessing/         # 后处理
    └── parallelProcessing/     # 并行处理
```

### 教程目录 (tutorials/)

```
tutorials/
├── incompressible/             # 不可压缩流动教程
├── multiphase/                 # 多相流教程
├── heatTransfer/               # 传热教程
└── combustion/                 # 燃烧教程
```

## 核心类层次结构

### 网格层次

```
object
└── regIOobject                 # 注册对象基类
    └── polyMesh                # 多面体网格
        └── fvMesh              # 有限体积网格
            └── fvMeshStitcher  # 网格缝合器
```

### 场层次

```
Field<T>                        # 场基类 (模板)
└── GeometricField<T, PatchField, GeoMesh>
    ├── volField               # 体场 (volScalarField, volVectorField)
    └── surfaceField           # 表面场 (surfaceScalarField)
```

### 边界条件层次

```
fvPatchField<T>                 # 边界条件基类
├── fixedValueFvPatchField     # 固定值
├── zeroGradientFvPatchField   # 零梯度
├── inletOutletFvPatchField    # 入口出口
├── mixedFvPatchField          # 混合边界
└── [Derived Conditions...]    # 派生边界条件
```

### 求解器层次

```
solver
├── solverCore                  # 求解器核心
├── SIMPLE                      # SIMPLE 算法
├── PISO                        # PISO 算法
└── PIMPLE                      # PIMPLE (SIMPLE + PISO)
```

### 湍流模型层次

```
turbulenceModel                 # 湍流模型基类
├── RASModel                    # RANS 模型基类
│   ├── kEpsilon               # k-ε 模型
│   ├── kOmega                 # k-ω 模型
│   └── kOmegaSST              # SST k-ω 模型
└── LESModel                    # LES 模型基类
    ├── Smagorinsky            # Smagorinsky 亚网格模型
    └── dynamicLagrangian      # 动态 Lagrangian 模型
```

## 命名约定

### 文件命名

| 后缀 | 含义 |
|------|------|
| `.H` | 头文件 (类声明) |
| `.C` | 源文件 (类实现) |
| `I.H` | 内联函数实现 |
| `IO.C` | 输入输出函数 |

### 类命名

| 前缀 | 含义 |
|------|------|
| `fv` | 有限体积 (fvMesh, fvPatch) |
| `vol` | 体场 (volScalarField) |
| `surface` | 表面场 (surfaceScalarField) |
| `RAS` | RANS 模型 |
| `LES` | LES 模型 |

### 变量命名

| 命名 | 含义 |
|------|------|
| `U` | 速度场 |
| `p` | 压力场 |
| `T` | 温度场 |
| `k` | 湍动能 |
| `epsilon` | 耗散率 |
| `omega` | 比耗散率 |
| `alpha` | 相分数 |

## 配置文件结构

### 系统文件 (system/)

```
system/
├── controlDict                 # 时间控制
│   ├── startTime/endTime       # 起止时间
│   ├── deltaT                  # 时间步长
│   ├── writeControl/Interval   # 写入控制
│   └── functions               # 函数对象
│
├── fvSchemes                   # 离散格式
│   ├── ddtSchemes              # 时间离散
│   ├── gradSchemes             # 梯度格式
│   ├── divSchemes              # 散度格式
│   └── laplacianSchemes        # 拉普拉斯格式
│
└── fvSolution                  # 求解器设置
    ├── solvers                 # 线性求解器
    ├── SIMPLE/PISO             # 算法参数
    └── relaxationFactors       # 松弛因子
```

### 常数文件 (constant/)

```
constant/
├── polyMesh/                   # 网格数据
│   ├── points                  # 点坐标
│   ├── faces                   # 面定义
│   ├── owner                   # 面所属单元
│   └── neighbour               # 面相邻单元
│
├── transportProperties         # 输运属性
├── turbulenceProperties        # 湍流属性
└── thermophysicalProperties    # 热物理属性
```

## 关键宏和模板

### 运行时选择机制

```cpp
// 声明运行时选择表
addToRunTimeSelectionTable(BaseClass, DerivedClass, dictionary);

// 使用选择表
autoPtr<BaseClass> obj = BaseClass::New(subDict, mesh);
```

### 常用宏

| 宏 | 用途 |
|---|------|
| `Foam::` | 命名空间前缀 |
| `Info` | 信息输出 (类似 cout) |
| `Warning` | 警告输出 |
| `FatalError` | 致命错误 |
| `dimensionedScalar` | 有量纲标量 |
| `dimensionedVector` | 有量纲向量 |
