# OpenFOAM 物理模型修改模板

## 概述

本文档提供OpenFOAM物理模型（湍流、多相流、热物理）创建和修改的标准化模板。

## 模型类型

### 湍流模型

| 类型 | 基类 | 典型模型 |
|------|------|----------|
| RANS | `RASModel` | k-ε, k-ω, SST |
| LES | `LESModel` | Smagorinsky, dynamicLagrangian |

### 多相流模型

| 类型 | 基类 | 说明 |
|------|------|------|
| VOF | `interPhaseProperties` | 界面追踪 |
| Eulerian | `phaseSystem` | 多相欧拉 |

### 热物理模型

| 类型 | 基类 | 说明 |
|------|------|------|
| 可压缩 | `rhoThermo` | 密度基 |
| 焓基 | `heThermo` | 焓基热物理 |

## 创建湍流模型

### 目录结构

```
myTurbulenceModel/
├── myTurbulenceModel.H    # 头文件
├── myTurbulenceModel.C    # 实现文件
└── Make/
    ├── files
    └── options
```

### 头文件模板

```cpp
//- myTurbulenceModel.H
#ifndef myTurbulenceModel_H
#define myTurbulenceModel_H

#include "RASModel.H"
#include "eddyViscosity.H"

namespace Foam
{

template<class BasicTurbulenceModel>
class myTurbulenceModel
:
    public eddyViscosity<RASModel<BasicTurbulenceModel>>
{
protected:

    // 模型常数
    dimensionedScalar Cmu_;
    dimensionedScalar C1_;
    dimensionedScalar C2_;
    dimensionedScalar sigmaEps_;
    
    // 场变量
    volScalarField k_;
    volScalarField epsilon_;

    // 私有成员函数
    tmp<volScalarField> DkEff(const volScalarField& nut) const;
    tmp<volScalarField> DepsilonEff(const volScalarField& nut) const;

public:

    //- Runtime type information
    TypeName("myTurbulenceModel");

    // 构造函数
    myTurbulenceModel
    (
        const alphaField& alpha,
        const rhoField& rho,
        const volVectorField& U,
        const surfaceScalarField& alphaRhoPhi,
        const surfaceScalarField& phi,
        const transportModel& transport,
        const word& propertiesName = turbulenceModel::propertiesName,
        const word& type = typeName
    );

    virtual ~myTurbulenceModel() = default;

    // 成员函数

    //- 读取模型参数
    virtual bool read();

    //- 返回湍流粘度
    virtual tmp<volScalarField> nut() const;

    //- 正确计算
    virtual void correct();
};

} // End namespace Foam

#endif
```

### 实现文件模板

```cpp
//- myTurbulenceModel.C

#include "myTurbulenceModel.H"
#include "fvOptions.H"
#include "bound.H"
#include "wallFvPatch.H"

namespace Foam
{

// 添加到运行时选择表
addToRunTimeSelectionTable
(
    RASModel,
    myTurbulenceModel,
    dictionary
);

// 构造函数
template<class BasicTurbulenceModel>
myTurbulenceModel<BasicTurbulenceModel>::myTurbulenceModel
(
    const alphaField& alpha,
    const rhoField& rho,
    const volVectorField& U,
    const surfaceScalarField& alphaRhoPhi,
    const surfaceScalarField& phi,
    const transportModel& transport,
    const word& propertiesName,
    const word& type
)
:
    eddyViscosity<RASModel<BasicTurbulenceModel>>
    (
        type,
        alpha,
        rho,
        U,
        alphaRhoPhi,
        phi,
        transport,
        propertiesName
    ),
    Cmu_("Cmu", dimless, 0.09),
    C1_("C1", dimless, 1.44),
    C2_("C2", dimless, 1.92),
    sigmaEps_("sigmaEps", dimless, 1.3),
    k_
    (
        IOobject
        (
            "k",
            this->runTime_.timeName(),
            this->mesh_,
            IOobject::MUST_READ,
            IOobject::AUTO_WRITE
        ),
        this->mesh_
    ),
    epsilon_
    (
        IOobject
        (
            "epsilon",
            this->runTime_.timeName(),
            this->mesh_,
            IOobject::MUST_READ,
            IOobject::AUTO_WRITE
        ),
        this->mesh_
    )
{
    // 读取模型系数
    this->read();
    
    // 边界条件修正
    bound(k_, this->kMin_);
    bound(epsilon_, this->epsilonMin_);
}

// 读取参数
template<class BasicTurbulenceModel>
bool myTurbulenceModel<BasicTurbulenceModel>::read()
{
    if (eddyViscosity<RASModel<BasicTurbulenceModel>>::read())
    {
        // 从字典读取模型常数
        Cmu_.readIfPresent(this->coeffDict());
        C1_.readIfPresent(this->coeffDict());
        C2_.readIfPresent(this->coeffDict());
        sigmaEps_.readIfPresent(this->coeffDict());

        return true;
    }
    
    return false;
}

// 湍流粘度
template<class BasicTurbulenceModel>
tmp<volScalarField> myTurbulenceModel<BasicTurbulenceModel>::nut() const
{
    return Cmu_*sqr(k_)/epsilon_;
}

// 正确计算
template<class BasicTurbulenceModel>
void myTurbulenceModel<BasicTurbulenceModel>::correct()
{
    if (!this->turbulence_)
    {
        return;
    }

    // 调用父类的correct
    eddyViscosity<RASModel<BasicTurbulenceModel>>::correct();

    // 计算应变率
    const volScalarField& nut = this->nut_;
    const volScalarField::Internal G
    (
        this->GName(),
        nut*(dev(twoSymm(fvc::grad(this->U_))) && fvc::grad(this->U_))
    );

    // k方程
    tmp<fvScalarMatrix> kEqn
    (
        fvm::ddt(alpha, rho, k_)
      + fvm::div(alphaRhoPhi, k_)
      - fvm::laplacian(alpha*rho*DkEff(nut), k_)
     ==
        alpha*rho*G
      - fvm::Sp(alpha*rho*epsilon_/k_, k_)
      + fvOptions(alpha, rho, k_)
    );

    kEqn.ref().relax();
    fvOptions.constrain(kEqn.ref());
    kEqn.ref().solve();
    fvOptions.correct(k_);
    bound(k_, this->kMin_);

    // epsilon方程
    tmp<fvScalarMatrix> epsEqn
    (
        fvm::ddt(alpha, rho, epsilon_)
      + fvm::div(alphaRhoPhi, epsilon_)
      - fvm::laplacian(alpha*rho*DepsilonEff(nut), epsilon_)
     ==
        alpha*rho*C1_*G*epsilon_/k_
      - fvm::Sp(alpha*rho*C2_*epsilon_/k_, epsilon_)
      + fvOptions(alpha, rho, epsilon_)
    );

    epsEqn.ref().relax();
    fvOptions.constrain(epsEqn.ref());
    epsEqn.ref().solve();
    fvOptions.correct(epsilon_);
    bound(epsilon_, this->epsilonMin_);

    // 更新湍流粘度
    this->nut_ = Cmu_*sqr(k_)/epsilon_;
    this->nut_.correctBoundaryConditions();
}

} // End namespace Foam
```

## 创建热物理模型

### 状态方程模板

```cpp
//- myEquationOfState.H
#ifndef myEquationOfState_H
#define myEquationOfState_H

namespace Foam
{

class myEquationOfState
{
    scalar p_;  // 压力
    scalar T_;  // 温度

public:

    // 构造函数
    myEquationOfState(scalar p, scalar T);

    // 状态方程计算
    scalar rho() const;  // 密度
    scalar psi() const;  // 压缩性
    scalar Z() const;    // 压缩因子
    
    // 热力学性质
    scalar Cp(scalar p, scalar T) const;
    scalar Cv(scalar p, scalar T) const;
    scalar H(scalar p, scalar T) const;
    scalar S(scalar p, scalar T) const;
};

} // End namespace Foam

#endif
```

### 输运性质模板

```cpp
//- myTransport.H

// 粘度计算
template<class Thermo>
inline Foam::scalar Foam::myTransport<Thermo>::mu
(
    scalar p,
    scalar T
) const
{
    // Sutherland定律
    return As_*::sqrt(T)/(1.0 + Ts_/T);
}

// 导热系数计算
template<class Thermo>
inline Foam::scalar Foam::myTransport<Thermo>::kappa
(
    scalar p,
    scalar T
) const
{
    // 基于Prandtl数
    return this->mu(p, T)*Cp(p, T)/Pr_;
}
```

## 配置文件模板

### 湍流模型配置

```cpp
// constant/turbulenceProperties

simulationType  RAS;

RAS
{
    // 使用自定义模型
    RASModel        myTurbulenceModel;

    // 模型参数（覆盖默认值）
    turbulence      on;
    printCoeffs     on;

    // 自定义系数
    Cmu             0.09;
    C1              1.44;
    C2              1.92;
    sigmaEps        1.3;
}
```

### 热物理模型配置

```cpp
// constant/thermophysicalProperties

thermoType
{
    type            hePsiThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState perfectGas;
    specie          specie;
    energy          sensibleEnthalpy;
}

mixture
{
    specie
    {
        molWeight   28.9;
    }
    thermodynamics
    {
        Cp          1005;
        Hf          0;
    }
    transport
    {
        mu          1.8e-05;
        Pr          0.7;
    }
}
```

### 多相流配置

```cpp
// constant/transportProperties

phases (water air);

water
{
    transportModel  Newtonian;
    nu              [0 2 -1 0 0 0 0] 1e-06;
    rho             [1 -3 0 0 0 0 0] 1000;
}

air
{
    transportModel  Newtonian;
    nu              [0 2 -1 0 0 0 0] 1.48e-05;
    rho             [1 -3 0 0 0 0 0] 1;
}

sigma           [1 0 -2 0 0 0 0] 0.07;
```

## 修改现有模型

### 修改模型系数

1. 在配置文件中指定：

```cpp
// constant/turbulenceProperties
RAS
{
    RASModel    kEpsilon;
    Cmu         0.08;  // 覆盖默认值
    C1          1.50;
}
```

2. 或创建派生类：

```cpp
class modifiedKEpsilon : public kEpsilon
{
    // 重写correct()修改计算逻辑
    virtual void correct();
};
```

### 添加新方程

```cpp
// 在模型中添加新的场变量
volScalarField newField_;

// 在correct()中添加新方程
fvScalarMatrix newEqn
(
    fvm::ddt(newField_)
  + fvm::div(phi, newField_)
  - fvm::laplacian(Dnew_, newField_)
 ==
    source_
);
newEqn.solve();
```

## 最佳实践

### 参数设计

1. 使用有物理意义的参数名
2. 提供合理的默认值
3. 添加参数范围检查

### 数值稳定性

1. 使用 `bound()` 限制场值为正
2. 合理设置松弛因子
3. 监控残差收敛

### 测试验证

1. 与解析解对比
2. 与实验数据对比
3. 与标准案例对比

## 常见问题

### 编译问题

**问题**: 找不到基类
**解决**: 检查 Make/options 中的头文件路径

### 计算发散

**问题**: 湍流变量出现负值
**解决**: 使用 `bound()` 函数限制最小值

**问题**: 模型不稳定
**解决**: 减小松弛因子，调整时间步长

### 结果异常

**问题**: 结果与预期不符
**解决**: 检查边界条件、初始条件和模型参数
