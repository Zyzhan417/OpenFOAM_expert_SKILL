# 求解器代码分析指南

## 求解器分析概述

OpenFOAM 求解器的代码分析需要理解以下核心要素：

1. **求解器类型**: 稳态/瞬态、可压缩/不可压缩、单相/多相
2. **主循环结构**: 时间推进或迭代循环
3. **求解方程**: 动量、压力、能量、标量输运
4. **离散格式**: 时间、空间离散方法
5. **算法**: SIMPLE、PISO、PIMPLE 等

## 分析流程

### Step 1: 识别求解器类型

从求解器目录名和文件结构推断：

| 目录关键词 | 求解器类型 |
|-----------|-----------|
| `simpleFoam` | 稳态不可压缩, SIMPLE 算法 |
| `pisoFoam` | 瞬态不可压缩, PISO 算法 |
| `pimpleFoam` | 瞬态, PIMPLE 算法 |
| `interFoam` | VOF 多相流 |
| `buoyantFoam` | 浮力驱动流动 |
| `rhoPimpleFoam` | 可压缩瞬态 |
| `chtMultiRegionFoam` | 共轭传热 |

### Step 2: 定位主循环

**搜索模式**:

```regex
# 瞬态求解器
while (runTime.loop())    # 或 runTime.run()

# 稳态求解器
while (simple.loop())     # SIMPLE 迭代

# PIMPLE 求解器
while (runTime.loop())
{
    while (pimple.loop())  # 内层迭代
}
```

**典型结构**:

```cpp
// 瞬态求解器典型结构
int main(int argc, char *argv[])
{
    #include "setRootCase.H"
    #include "createTime.H"
    #include "createMesh.H"
    #include "createFields.H"

    while (runTime.loop())  // 主时间循环
    {
        #include "UEqn.H"   // 动量方程
        #include "pEqn.H"   // 压力方程

        runTime.write();    // 写入结果
    }

    return 0;
}
```

### Step 3: 分析求解方程

**动量方程 (UEqn.H)**:

```cpp
// 典型动量方程结构
fvVectorMatrix UEqn
(
    fvm::ddt(U)              // 时间导数
  + fvm::div(phi, U)         // 对流项
  - fvm::laplacian(nu, U)    // 扩散项
 ==
    fvOptions(U)             // 源项
);

UEqn.relax();               // 松弛
fvOptions.constrain(UEqn);
solve(UEqn == -fvc::grad(p));  // 求解
fvOptions.correct(U);
```

**压力方程 (pEqn.H)**:

```cpp
// SIMPLE 算法压力方程
{
    volScalarField rAU(1.0/UEqn.A());
    volVectorField HbyA(constrainHbyA(rAU*UEqn.H(), U, p));

    fvScalarMatrix pEqn
    (
        fvm::laplacian(rAU, p) == fvc::div(HbyA)
    );

    pEqn.solve();
    U = HbyA - rAU*fvc::grad(p);
    U.correctBoundaryConditions();
}
```

### Step 4: 分析离散格式

**读取 fvSchemes 文件**:

```cpp
// system/fvSchemes 典型内容
ddtSchemes
{
    default         Euler;          // 时间: Euler 隐式
}

gradSchemes
{
    default         Gauss linear;   // 梯度: Gauss 线性
}

divSchemes
{
    div(phi,U)      Gauss upwind;   // 对流: 迎风
}

laplacianSchemes
{
    default         Gauss linear corrected;  // 拉普拉斯
}
```

**常见离散格式**:

| 格式类型 | 可选方案 | 特点 |
|---------|---------|------|
| 时间 | Euler, backward, CrankNicolson | 稳定性/精度权衡 |
| 对流 | upwind, linearUpwind, QUICK | 扩散性/精度权衡 |
| 梯度 | Gauss linear, leastSquares | 精度权衡 |
| 拉普拉斯 | corrected, uncorrected | 正交性要求 |

### Step 5: 分析求解器设置

**读取 fvSolution 文件**:

```cpp
// system/fvSolution 典型内容
solvers
{
    p
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       1e-06;
        relTol          0.1;
    }
    U
    {
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-05;
        relTol          0.1;
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 0;
    pRefCell        0;
    pRefValue       0;
}
```

**线性求解器选择**:

| 求解器 | 适用场景 |
|--------|---------|
| PCG (预条件共轭梯度) | 对称正定矩阵 (压力) |
| PBiCGStab | 非对称矩阵 (速度) |
| GAMG | 大规模问题 |

## 常见求解器分析案例

### 案例 1: simpleFoam 分析

**核心文件**:
```
applications/solvers/incompressible/simpleFoam/
├── simpleFoam.C         # 主程序
├── createFields.H       # 场创建
├── UEqn.H               # 动量方程
├── pEqn.H               # 压力方程
└── converge.H           # 收敛判断
```

**分析要点**:
1. 稳态求解器, 无时间循环
2. `while (simple.loop())` 迭代循环
3. SIMPLE 算法: 先解动量, 再解压力
4. 压力修正后更新速度

### 案例 2: interFoam 分析

**核心文件**:
```
applications/solvers/multiphase/interFoam/
├── interFoam.C          # 主程序
├── alphaEqn.H           # 相分数方程
├── alphaEqnSubCycle.H   # 相方程子循环
├── pEqn.H               # 压力方程
└── UEqn.H               # 动量方程
```

**分析要点**:
1. VOF 方法追踪界面
2. 相分数方程单独求解
3. MULES 算法保证有界性
4. 表面张力作为源项

### 案例 3: multiphaseEulerFoam 分析

**核心文件**:
```
applications/solvers/multiphase/multiphaseEulerFoam/
├── multiphaseEulerFoam.C    # 主程序
├── createFields.H           # 场创建
├── pUf/                     # 压力-速度耦合
└── phaseSystems/            # 相系统
```

**分析要点**:
1. 多相欧拉方法
2. 每相独立动量方程
3. 相间交换模型
4. 粒子群平衡 (可选)

## 调用关系追踪

### 方法 1: 从主循环出发

```
main()
  └─► runTime.loop()
       └─► UEqn.H
            └─► solve(UEqn)
                 └─► fvMatrix::solve()
                      └─► lduMatrix::solver::solve()
       └─► pEqn.H
            └─► solve(pEqn)
                 └─► ... (同上)
```

### 方法 2: 从类继承出发

```
fvMesh
  └─► polyMesh (基类)
       └─► objectRegistry
            └─► regIOobject
                 └─► IOobject
```

### 方法 3: 从模型选择出发

```
turbulenceModel::New()
  └─► RASModel::New()
       └─► kEpsilon (具体模型)
            ├─► RASModel (基类)
            └─► turbulenceModel (基类)
```

## 代码修改指南

### 修改求解器

1. **添加新方程**: 在主循环中添加新的 Eqn.H 文件
2. **修改离散格式**: 编辑 fvSchemes
3. **调整求解参数**: 编辑 fvSolution
4. **添加源项**: 使用 fvOptions

### 修改边界条件

1. **继承现有条件**: 从合适的基类派生
2. **实现 updateCoeffs()**: 核心更新逻辑
3. **注册到选择表**: addToRunTimeSelectionTable

### 修改物理模型

1. **定位模型基类**: 如 RASModel, LESModel
2. **实现派生类**: 重写必要虚函数
3. **注册模型**: 添加到运行时选择表

## 输出模板

### 求解器分析报告

```markdown
## 求解器: [名称]

### 基本信息
- 类型: [稳态/瞬态]
- 算法: [SIMPLE/PISO/PIMPLE]
- 物理模型: [不可压缩/可压缩/多相/...]

### 主循环位置
- 文件: [路径:行号]
- 结构: [时间循环/迭代循环]

### 求解方程
| 方程 | 变量 | 离散格式 | 求解器 |
|------|------|---------|--------|
| 动量 | U | [格式] | [求解器] |
| 压力 | p | [格式] | [求解器] |

### 关键调用链
[树状结构展示函数调用关系]

### 配置要点
[关键参数及其推荐值]
```

## 高级分析技巧

### 使用 grep 和正则表达式

```bash
# 查找所有方程文件
find $FOAM_APP/solvers -name "*Eqn.H"

# 搜索求解器中的 solve 调用
grep -rn "solve\s*(" $FOAM_APP/solvers

# 搜索特定离散格式
grep -rn "Gauss upwind" $FOAM_TUTORIALS
```

### 使用 Doxygen 文档

OpenFOAM 提供在线 Doxygen 文档:
- 类继承关系
- 成员函数列表
- 源码链接

### 使用 ParaView 后处理

1. 导出 VTK 文件: `foamToVTK`
2. 在 ParaView 中分析
3. 结合源码理解数据流
