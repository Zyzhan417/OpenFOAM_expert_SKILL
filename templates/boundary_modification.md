# OpenFOAM 边界条件修改模板

## 概述

本文档提供OpenFOAM边界条件创建和修改的标准化模板和最佳实践。

## 边界条件类型

### 基础边界条件类型

| 类型 | 基类 | 说明 |
|------|------|------|
| 固定值 | `fixedValueFvPatchField` | 边界值为常数或场 |
| 零梯度 | `zeroGradientFvPatchField` | 边界梯度为零 |
| 入口出口 | `inletOutletFvPatchField` | 根据流向切换条件 |
| 混合 | `mixedFvPatchField` | 值和梯度的线性组合 |

## 创建新边界条件

### 目录结构

```
myBoundaryCondition/
├── myBoundaryConditionFvPatchField.H    # 头文件
├── myBoundaryConditionFvPatchField.C    # 实现文件
└── Make/
    ├── files
    └── options
```

### 头文件模板

```cpp
//- myBoundaryConditionFvPatchField.H
#ifndef myBoundaryConditionFvPatchField_H
#define myBoundaryConditionFvPatchField_H

#include "fixedValueFvPatchField.H"

namespace Foam
{

class myBoundaryConditionFvPatchField
:
    public fixedValueFvPatchField<Type>
{
    // 私有成员
    scalar param1_;
    scalar param2_;

public:

    //- Runtime type information
    TypeName("myBoundaryCondition");

    // 构造函数

    //- 从patch和内部场构造
    myBoundaryConditionFvPatchField
    (
        const fvPatch& p,
        const DimensionedField<Type, volMesh>& iF
    );

    //- 从patch、内部场和字典构造
    myBoundaryConditionFvPatchField
    (
        const fvPatch& p,
        const DimensionedField<Type, volMesh>& iF,
        const dictionary& dict
    );

    //- 拷贝构造函数
    myBoundaryConditionFvPatchField
    (
        const myBoundaryConditionFvPatchField& ptf,
        const fvPatch& p,
        const DimensionedField<Type, volMesh>& iF,
        const fvPatchFieldMapper& m
    );

    //- 拷贝构造函数
    myBoundaryConditionFvPatchField
    (
        const myBoundaryConditionFvPatchField& ptf
    );

    //- 克隆函数
    virtual tmp<fvPatchField<Type>> clone() const
    {
        return tmp<fvPatchField<Type>>
        (
            new myBoundaryConditionFvPatchField<Type>(*this)
        );
    }

    //- 克隆函数（带内部场）
    virtual tmp<fvPatchField<Type>> clone
    (
        const DimensionedField<Type, volMesh>& iF
    ) const
    {
        return tmp<fvPatchField<Type>>
        (
            new myBoundaryConditionFvPatchField<Type>(*this, iF)
        );
    }

    // 成员函数

    //- 更新系数
    virtual void updateCoeffs();

    //- 写入
    virtual void write(Ostream& os) const;
};

} // End namespace Foam

#endif
```

### 实现文件模板

```cpp
//- myBoundaryConditionFvPatchField.C

#include "myBoundaryConditionFvPatchField.H"
#include "addToRunTimeSelectionTable.H"
#include "fvPatchFieldMapper.H"
#include "volFields.H"
#include "surfaceFields.H"

namespace Foam
{

// 添加到运行时选择表
makePatchTypeField
(
    fvPatchField,
    myBoundaryConditionFvPatchField
);

// 构造函数实现

template<class Type>
myBoundaryConditionFvPatchField<Type>::myBoundaryConditionFvPatchField
(
    const fvPatch& p,
    const DimensionedField<Type, volMesh>& iF
)
:
    fixedValueFvPatchField<Type>(p, iF),
    param1_(0.0),
    param2_(0.0)
{}

template<class Type>
myBoundaryConditionFvPatchField<Type>::myBoundaryConditionFvPatchField
(
    const fvPatch& p,
    const DimensionedField<Type, volMesh>& iF,
    const dictionary& dict
)
:
    fixedValueFvPatchField<Type>(p, iF, dict),
    param1_(dict.lookupOrDefault<scalar>("param1", 0.0)),
    param2_(dict.lookupOrDefault<scalar>("param2", 0.0))
{
    // 读取value（如果存在）
    if (dict.found("value"))
    {
        fvPatchField<Type>::operator=
        (
            Field<Type>("value", dict, p.size())
        );
    }
    else
    {
        // 默认初始化
        fvPatchField<Type>::operator=(Zero);
    }
}

template<class Type>
myBoundaryConditionFvPatchField<Type>::myBoundaryConditionFvPatchField
(
    const myBoundaryConditionFvPatchField& ptf,
    const fvPatch& p,
    const DimensionedField<Type, volMesh>& iF,
    const fvPatchFieldMapper& m
)
:
    fixedValueFvPatchField<Type>(ptf, p, iF, m),
    param1_(ptf.param1_),
    param2_(ptf.param2_)
{}

template<class Type>
myBoundaryConditionFvPatchField<Type>::myBoundaryConditionFvPatchField
(
    const myBoundaryConditionFvPatchField& ptf
)
:
    fixedValueFvPatchField<Type>(ptf),
    param1_(ptf.param1_),
    param2_(ptf.param2_)
{}

// 成员函数实现

template<class Type>
void myBoundaryConditionFvPatchField<Type>::updateCoeffs()
{
    if (this->updated())
    {
        return;
    }

    // 边界条件计算逻辑
    // 示例：基于参数计算边界值
    const fvPatch& patch = this->patch();
    
    Field<Type>& field = *this;
    
    forAll(field, i)
    {
        // 计算边界值
        field[i] = param1_ * param2_;
    }

    fixedValueFvPatchField<Type>::updateCoeffs();
}

template<class Type>
void myBoundaryConditionFvPatchField<Type>::write(Ostream& os) const
{
    fvPatchField<Type>::write(os);
    os.writeEntry<scalar>("param1", param1_);
    os.writeEntry<scalar>("param2", param2_);
    this->writeEntry("value", os);
}

} // End namespace Foam
```

### Make/files

```
myBoundaryConditionFvPatchField.C

LIB = $(FOAM_USER_LIBBIN)/libmyBoundaryConditions
```

### Make/options

```
EXE_INC = \
    -I$(LIB_SRC)/finiteVolume/lnInclude \
    -I$(LIB_SRC)/meshTools/lnInclude

LIB_LIBS = \
    -lfiniteVolume \
    -lmeshTools
```

## 使用配置模板

### 基本配置

```cpp
// 0/U 文件中

myPatch
{
    type            myBoundaryCondition;
    param1          1.0;
    param2          2.0;
    value           uniform (0 0 0);
}
```

### 与其他场耦合

```cpp
myPatch
{
    type            myBoundaryCondition;
    param1          1.0;
    
    // 引用其他场
    refField        "T";    // 引用温度场
    
    // 表达式（需配合 exprField 功能）
    expression      "T * 0.5";
}
```

## 常见边界条件模式

### 时变边界条件

```cpp
//- 更新系数时获取当前时间
template<class Type>
void timeVaryingBC<Type>::updateCoeffs()
{
    if (this->updated())
    {
        return;
    }

    const scalar t = this->db().time().value();
    
    // 基于时间计算边界值
    this->operator==(amplitude_ * sin(omega_ * t));
    
    fvPatchField<Type>::updateCoeffs();
}
```

### 空间变化边界条件

```cpp
//- 基于位置计算边界值
template<class Type>
void spatiallyVaryingBC<Type>::updateCoeffs()
{
    if (this->updated())
    {
        return;
    }

    const vectorField& Cf = this->patch().Cf();
    
    Field<Type>& field = *this;
    
    forAll(field, i)
    {
        scalar x = Cf[i].x();
        scalar y = Cf[i].y();
        
        // 基于位置计算
        field[i] = profile(x, y);
    }
    
    fvPatchField<Type>::updateCoeffs();
}
```

### 耦合边界条件

```cpp
//- 与其他场耦合
template<class Type>
void coupledBC<Type>::updateCoeffs()
{
    if (this->updated())
    {
        return;
    }

    // 获取耦合场
    const volScalarField& T = 
        this->db().objectRegistry::lookupObject<volScalarField>("T");
    
    const fvPatchScalarField& Tp = 
        T.boundaryField()[this->patch().index()];
    
    // 基于耦合场计算
    this->operator==(functionOf(Tp));
    
    fvPatchField<Type>::updateCoeffs();
}
```

## 最佳实践

### 参数设计

1. 使用 `lookupOrDefault` 为参数提供默认值
2. 添加参数范围检查
3. 在 `write()` 中保存所有参数

### 性能优化

1. 在 `updateCoeffs()` 开头检查 `updated()`
2. 避免不必要的场复制
3. 使用 `const` 引用访问外部场

### 调试技巧

1. 使用 `Info` 输出调试信息
2. 检查边界值范围
3. 验证梯度计算

## 常见问题

### 编译问题

**问题**: 模板实例化错误
**解决**: 确保 `.C` 文件末尾有正确的实例化代码

### 运行问题

**问题**: 参数未读取
**解决**: 检查字典中的参数名与代码中一致

**问题**: 边界值不更新
**解决**: 确保在 `updateCoeffs()` 中调用父类的 `updateCoeffs()`
