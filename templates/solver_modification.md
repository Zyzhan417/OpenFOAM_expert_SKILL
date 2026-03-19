# OpenFOAM 求解器修改模板

## 概述

本文档提供OpenFOAM求解器修改的标准化模板和最佳实践。

## 修改类型

### 1. 创建新求解器

基于现有求解器创建新的求解器。

#### 目录结构

```
mySolver/
├── mySolver.C           # 主程序
├── createFields.H       # 场创建
├── UEqn.H               # 动量方程
├── pEqn.H               # 压力方程
├── Make/
│   ├── files            # 编译文件列表
│   └── options          # 编译选项
└── README.md            # 说明文档
```

#### 主程序模板

```cpp
// mySolver.C

#include "fvCFD.H"
#include "singlePhaseTransportModel.H"
#include "turbulentTransportModel.H"
#include "simpleControl.H"
#include "fvOptions.H"

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

int main(int argc, char *argv[])
{
    #include "setRootCaseLists.H"
    #include "createTime.H"
    #include "createMesh.H"
    #include "createControl.H"
    #include "createFields.H"
    #include "initContinuityErrs.H"

    // * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

    Info<< "\nStarting time loop\n" << endl;

    while (simple.loop())
    {
        Info<< "Time = " << runTime.timeName() << nl << endl;

        // 压力-速度耦合
        #include "UEqn.H"
        #include "pEqn.H"

        laminarTransport.correct();
        turbulence->correct();

        runTime.write();

        Info<< "ExecutionTime = " << runTime.elapsedCpuTime() << " s"
            << "  ClockTime = " << runTime.elapsedClockTime() << " s"
            << nl << endl;
    }

    Info<< "End\n" << endl;

    return 0;
}
```

#### Make/files 模板

```
mySolver.C

EXE = $(FOAM_USER_APPBIN)/mySolver
```

#### Make/options 模板

```
EXE_INC = \
    -I$(LIB_SRC)/finiteVolume/lnInclude \
    -I$(LIB_SRC)/meshTools/lnInclude \
    -I$(LIB_SRC)/sampling/lnInclude \
    -I$(LIB_SRC)/turbulenceModels \
    -I$(LIB_SRC)/transportModels \
    -I$(LIB_SRC)/transportModels/incompressible/singlePhaseTransportModel \
    -I$(LIB_SRC)/transportModels/incompressible

EXE_LIBS = \
    -lfiniteVolume \
    -lmeshTools \
    -lsampling \
    -lincompressibleTransportModels \
    -lincompressibleTurbulenceModel \
    -lincompressibleRASModels \
    -lincompressibleLESModels
```

### 2. 添加新方程

在现有求解器中添加新的输运方程。

#### 方程模板

```cpp
// scalarEqn.H - 标量输运方程

fvScalarMatrix scalarEqn
(
    fvm::ddt(scalarField)
  + fvm::div(phi, scalarField)
  - fvm::laplacian(Dscalar, scalarField)
 ==
    fvOptions(scalarField)
    + sourceTerm
);

scalarEqn.relax();
fvOptions.constrain(scalarEqn);
scalarEqn.solve();
fvOptions.correct(scalarField);
```

#### 场创建模板

```cpp
// createFields.H 中添加

Info<< "Reading scalar field\n" << endl;
volScalarField scalarField
(
    IOobject
    (
        "scalarField",
        runTime.timeName(),
        mesh,
        IOobject::MUST_READ,
        IOobject::AUTO_WRITE
    ),
    mesh
);

// 扩散系数
dimensionedScalar Dscalar
(
    transportProperties.lookup("Dscalar")
);

// 源项（可选）
volScalarField sourceTerm
(
    IOobject
    (
        "sourceTerm",
        runTime.timeName(),
        mesh,
        IOobject::READ_IF_PRESENT,
        IOobject::AUTO_WRITE
    ),
    mesh,
    dimensionedScalar("sourceTerm", dimless/dimTime, 0)
);
```

### 3. 修改求解算法

修改压力-速度耦合算法。

#### SIMPLE算法修改

```cpp
// pEqn.H - 修改后的压力方程

{
    volScalarField rAU("rAU", 1.0/UEqn.A());
    volVectorField HbyA(constrainHbyA(rAU*UEqn.H(), U, p));
    
    // 添加自定义项
    surfaceScalarField phiHbyA("phiHbyA", fvc::flux(HbyA));
    
    // 修正通量
    MRF.makeRelative(phiHbyA);
    
    // 调整参考压力
    adjustPhi(phiHbyA, U, p);

    // 非正交修正循环
    while (simple.correctNonOrthogonal())
    {
        fvScalarMatrix pEqn
        (
            fvm::laplacian(rAU, p)
         == fvc::div(phiHbyA)
            // 添加自定义源项
          + customSource
        );

        pEqn.setReference(pRefCell, pRefValue);
        pEqn.solve();

        if (simple.finalNonOrthogonalIter())
        {
            phi = phiHbyA - pEqn.flux();
        }
    }

    // 显式修正速度
    #include "continuityErrs.H"
    U = HbyA - rAU*fvc::grad(p);
    U.correctBoundaryConditions();
    fvOptions.correct(U);
}
```

## 最佳实践

### 编译前检查

1. 检查所有依赖的头文件是否存在
2. 确认 Make/options 中的库路径正确
3. 验证场变量名称与案例文件一致

### 调试技巧

1. 使用 `Info` 输出中间变量值
2. 检查残差和收敛性
3. 使用 `gdb` 调试

### 性能优化

1. 避免不必要的场复制
2. 使用引用传递大对象
3. 合理设置松弛因子

## 常见问题

### 编译错误

**问题**: 找不到头文件
**解决**: 检查 Make/options 中的 `-I` 路径

**问题**: 未定义引用
**解决**: 检查 Make/options 中的 `-l` 库链接

### 运行错误

**问题**: 场变量未找到
**解决**: 检查案例的 0/ 目录中是否有对应文件

**问题**: 求解器发散
**解决**: 调整松弛因子、时间步长或离散格式

## 参考资料

- OpenFOAM 官方文档
- OpenFOAM Wiki
- tutorials/ 目录中的示例案例
