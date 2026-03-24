# OpenFOAM 代码修改工作流程

本文档提供完整的代码修改工作流程和实际案例，指导如何扩展和修改 OpenFOAM 代码。

## 修改策略总览

### 三种主要策略

| 策略 | 适用场景 | 风险等级 | 推荐度 |
|------|---------|---------|--------|
| **extend** (扩展) | 添加新功能、新模型、新边界条件 | 低 | ⭐⭐⭐⭐⭐ |
| **create** (创建) | 创建独立的求解器、工具 | 低 | ⭐⭐⭐⭐ |
| **modify** (修改) | 直接修改现有代码 | 高 | ⭐⭐ |

### 推荐原则

1. **优先使用继承和组合** - 通过扩展而非修改现有类
2. **遵循 OpenFOAM 设计模式** - 运行时选择机制、工厂模式
3. **保持向后兼容** - 修改不应破坏现有功能
4. **添加充分测试** - 每个修改都应有对应的测试用例

---

## 场景一：扩展湍流模型

### 目标

基于现有的 kEpsilon 模型，创建一个改进版本 MyKEpsilon。

### 完整工作流

#### Step 1: 分析现有模型

```bash
# 1.1 查看继承链
python scripts/inheritance_analyzer.py --class kEpsilon --chain

# 1.2 查看派生树（了解现有扩展）
python scripts/inheritance_analyzer.py --class kEpsilon --tree --depth 2

# 1.3 分析设计模式
python scripts/inheritance_analyzer.py --class kEpsilon --patterns

# 1.4 查看模型参数
python scripts/model_analyzer.py --type turbulence --name kEpsilon
```

**预期输出要点**：
- 基类：`RASModel`
- 文件位置：`turbulenceModels/incompressible/RAS/kEpsilon/`
- 关键虚函数：`correct()`, `k()`, `epsilon()`
- 设计模式：Strategy + Factory

#### Step 2: 生成扩展建议

```bash
python scripts/model_analyzer.py --type turbulence --name kEpsilon --suggest extend
```

**输出示例**：
```json
{
  "success": true,
  "suggestions": {
    "approach": "create_derived_class",
    "base_class": "kEpsilon",
    "required_methods": [
      "correct()",
      "k() const",
      "epsilon() const"
    ],
    "files_to_create": [
      "MyKEpsilon.H",
      "MyKEpsilon.C"
    ],
    "registration": "addToRunTimeSelectionTable"
  }
}
```

#### Step 3: 创建文件结构

```bash
# 创建目录
mkdir -p myTurbulence/MyKEpsilon

# 创建文件
touch myTurbulence/MyKEpsilon/MyKEpsilon.H
touch myTurbulence/MyKEpsilon/MyKEpsilon.C
touch myTurbulence/Make/files
touch myTurbulence/Make/options
```

#### Step 4: 实现头文件

**MyKEpsilon.H**：
```cpp
#ifndef MyKEpsilon_H
#define MyKEpsilon_H

#include "kEpsilon.H"

namespace Foam
{
namespace RASModels
{

class MyKEpsilon
:
    public kEpsilon
{
    // 私有成员
    volScalarField k_;
    volScalarField epsilon_;
    
    // 新增成员
    volScalarField customField_;
    
public:
    TypeName("MyKEpsilon");

    // 构造函数
    MyKEpsilon
    (
        const geometricOneField& alpha,
        const geometricOneField& rho,
        const volVectorField& U,
        const surfaceScalarField& alphaRhoPhi,
        const surfaceScalarField& phi,
        const transportModel& transport,
        const word& propertiesName = turbulenceModel::propertiesName,
        const word& type = typeName
    );

    // 析构函数
    virtual ~MyKEpsilon() = default;

    // 成员函数
    virtual tmp<volScalarField> k() const { return k_; }
    virtual tmp<volScalarField> epsilon() const { return epsilon_; }
    
    virtual void correct();
};

} // namespace RASModels
} // namespace Foam

#endif
```

#### Step 5: 实现源文件

**MyKEpsilon.C**：
```cpp
#include "MyKEpsilon.H"
#include "fvOptions.H"
#include "bound.H"

// 注册到运行时选择表
makeRASModel(MyKEpsilon);

namespace Foam
{
namespace RASModels
{

// 构造函数
MyKEpsilon::MyKEpsilon
(
    const geometricOneField& alpha,
    const geometricOneField& rho,
    const volVectorField& U,
    const surfaceScalarField& alphaRhoPhi,
    const surfaceScalarField& phi,
    const transportModel& transport,
    const word& propertiesName,
    const word& type
)
:
    kEpsilon(alpha, rho, U, alphaRhoPhi, phi, transport, propertiesName, type),
    customField_
    (
        IOobject
        (
            "customField",
            this->runTime_.timeName(),
            this->mesh_,
            IOobject::NO_READ,
            IOobject::AUTO_WRITE
        ),
        this->mesh_,
        dimensionedScalar("customField", dimless, 0.0)
    )
{
    Info << "Creating MyKEpsilon turbulence model" << endl;
}

// correct 函数
void MyKEpsilon::correct()
{
    // 调用基类的 correct
    kEpsilon::correct();
    
    // 添加自定义修正
    if (!this->turbulence_)
    {
        return;
    }
    
    // 自定义逻辑
    // ...
    
    Info << "MyKEpsilon::correct() executed" << endl;
}

} // namespace RASModels
} // namespace Foam
```

#### Step 6: 配置编译

**Make/files**：
```
MyKEpsilon.C
LIB = $(FOAM_USER_LIBBIN)/libMyTurbulence
```

**Make/options**：
```
EXE_INC = \
    -I$(LIB_SRC)/turbulenceModels/incompressible/turbulenceModel \
    -I$(LIB_SRC)/turbulenceModels/incompressible/RAS/RASModel \
    -I$(LIB_SRC)/finiteVolume/lnInclude \
    -I$(LIB_SRC)/meshTools/lnInclude

LIB_LIBS = \
    -lincompressibleTurbulenceModel \
    -lincompressibleRASModels \
    -lfiniteVolume \
    -lmeshTools
```

#### Step 7: 编译测试

```bash
# 编译
cd myTurbulence
wmake

# 验证编译
ls $FOAM_USER_LIBBIN/libMyTurbulence.so
```

#### Step 8: 使用新模型

**constant/turbulenceProperties**：
```
simulationType  RAS;

RAS
{
    RASModel    MyKEpsilon;  // 使用自定义模型
    turbulence  on;
    printCoeffs on;
}
```

**运行案例**：
```bash
# 运行求解器
simpleFoam

# 检查日志
# 应看到 "Creating MyKEpsilon turbulence model"
```

---

## 场景二：创建新的边界条件

### 目标

创建一个随时间变化的边界条件 TimeVaryingFixedValue。

### 完整工作流

#### Step 1: 分析基类

```bash
# 1.1 查看基础边界条件
python scripts/boundary_analyzer.py --name fixedValue --params

# 1.2 查看基类信息
python scripts/boundary_analyzer.py --name fixedValue --base

# 1.3 查看示例
python scripts/boundary_analyzer.py --name inletOutlet --examples
```

#### Step 2: 生成创建建议

```bash
python scripts/boundary_analyzer.py --name fixedValue --suggest create
```

**输出要点**：
- 基类：`fixedValueFvPatchField<Type>`
- 必需参数：`value`
- 需重写方法：`updateCoeffs()`, `write()`

#### Step 3: 创建文件结构

```bash
mkdir -p myBoundaryConditions/TimeVaryingFixedValue
touch myBoundaryConditions/TimeVaryingFixedValue/TimeVaryingFixedValueFvPatchField.H
touch myBoundaryConditions/TimeVaryingFixedValue/TimeVaryingFixedValueFvPatchFields.H
touch myBoundaryConditions/Make/files
touch myBoundaryConditions/Make/options
```

#### Step 4: 实现边界条件

**TimeVaryingFixedValueFvPatchField.H**：
```cpp
#ifndef TimeVaryingFixedValueFvPatchField_H
#define TimeVaryingFixedValueFvPatchField_H

#include "fixedValueFvPatchField.H"
#include "Function1.H"

namespace Foam
{

template<class Type>
class TimeVaryingFixedValueFvPatchField
:
    public fixedValueFvPatchField<Type>
{
    // 时间函数
    autoPtr<Function1<Type>> timeFunction_;

public:
    TypeName("timeVaryingFixedValue");

    // 构造函数
    TimeVaryingFixedValueFvPatchField
    (
        const fvPatch&,
        const DimensionedField<Type, volMesh>&
    );

    TimeVaryingFixedValueFvPatchField
    (
        const fvPatch&,
        const DimensionedField<Type, volMesh>&,
        const dictionary&
    );

    // 其他构造函数...

    // 成员函数
    virtual void updateCoeffs();
    virtual void write(Ostream&) const;
};

} // namespace Foam

#ifdef NoRepository
    #include "TimeVaryingFixedValueFvPatchField.C"
#endif

#endif
```

#### Step 5: 实现源文件

**TimeVaryingFixedValueFvPatchField.C**：
```cpp
#include "TimeVaryingFixedValueFvPatchField.H"
#include "addToRunTimeSelectionTable.H"

namespace Foam
{

// 构造函数实现
template<class Type>
TimeVaryingFixedValueFvPatchField<Type>::TimeVaryingFixedValueFvPatchField
(
    const fvPatch& p,
    const DimensionedField<Type, volMesh>& iF,
    const dictionary& dict
)
:
    fixedValueFvPatchField<Type>(p, iF, dict),
    timeFunction_
    (
        Function1<Type>::New
        (
            "timeFunction",
            dict
        )
    )
{
    this->evaluate();
}

// updateCoeffs - 核心逻辑
template<class Type>
void TimeVaryingFixedValueFvPatchField<Type>::updateCoeffs()
{
    if (this->updated())
    {
        return;
    }

    // 根据当前时间计算边界值
    scalar t = this->db().time().value();
    Type currentValue = timeFunction_->value(t);
    
    // 设置边界值
    this->operator==(currentValue);
    
    fixedValueFvPatchField<Type>::updateCoeffs();
}

// write - 输出配置
template<class Type>
void TimeVaryingFixedValueFvPatchField<Type>::write(Ostream& os) const
{
    fixedValueFvPatchField<Type>::write(os);
    timeFunction_->writeData(os);
}

// 注册
makePatchFieldTypes(TimeVaryingFixedValue);

} // namespace Foam
```

#### Step 6: 配置使用

**0/U**：
```
inlet
{
    type            timeVaryingFixedValue;
    timeFunction    table
    (
        (0   (1 0 0))
        (1   (2 0 0))
        (2   (1 0 0))
    );
}
```

---

## 场景三：修改求解器

### 目标

修改 simpleFoam，添加自定义场输出。

### 完整工作流

#### Step 1: 分析求解器

```bash
# 1.1 查找求解器源码
python scripts/inheritance_analyzer.py --search "*Foam" --list

# 1.2 分析求解器结构
python scripts/model_analyzer.py --type solver --name simpleFoam
```

#### Step 2: 复制求解器

```bash
# 创建自定义求解器目录
mkdir -p mySimpleFoam

# 复制原始求解器
cp -r $FOAM_SOLVERS/incompressible/simpleFoam/* mySimpleFoam/

# 重命名
cd mySimpleFoam
mv simpleFoam.C mySimpleFoam.C
```

#### Step 3: 修改主程序

**mySimpleFoam.C**：
```cpp
#include "fvCFD.H"
#include "singlePhaseTransportModel.H"
#include "turbulentTransportModel.H"
#include "simpleControl.H"
#include "fvOptions.H"

// 主程序
int main(int argc, char *argv[])
{
    #include "setRootCaseLists.H"
    #include "createTime.H"
    #include "createMesh.H"
    #include "createControl.H"
    #include "createFields.H"
    #include "initContinuityErrs.H"

    // 添加自定义场
    volScalarField customField
    (
        IOobject
        (
            "customField",
            runTime.timeName(),
            mesh,
            IOobject::NO_READ,
            IOobject::AUTO_WRITE
        ),
        mesh,
        dimensionedScalar("zero", dimless, 0.0)
    );

    Info<< "\nStarting time loop\n" << endl;

    while (simple.loop())
    {
        Info<< "Time = " << runTime.timeName() << nl << endl;

        // 原有求解步骤
        #include "UEqn.H"
        #include "pEqn.H"

        // 计算自定义场
        customField = mag(U) / max(mag(U)).value();
        
        // 输出
        if (runTime.write())
        {
            customField.write();
        }

        Info<< "ExecutionTime = " << runTime.elapsedCpuTime() << " s"
            << "  ClockTime = " << runTime.elapsedClockTime() << " s"
            << nl << endl;
    }

    Info<< "End\n" << endl;

    return 0;
}
```

#### Step 4: 编译和测试

```bash
# 编译
wmake

# 测试运行
mySimpleFoam
```

---

## 场景四：添加新的物理方程

### 目标

在现有求解器中添加标量输运方程。

### 工作流

#### Step 1: 准备场变量

在 `createFields.H` 中添加：
```cpp
// 添加标量场
volScalarField T
(
    IOobject
    (
        "T",
        runTime.timeName(),
        mesh,
        IOobject::MUST_READ,
        IOobject::AUTO_WRITE
    ),
    mesh
);

// 输运性质
dimensionedScalar DT("DT", dimViscosity, laminarTransport);
```

#### Step 2: 创建方程文件

**TEqn.H**：
```cpp
// 标量输运方程
fvScalarMatrix TEqn
(
    fvm::ddt(T)
  + fvm::div(phi, T)
  - fvm::laplacian(DT, T)
 ==
    fvOptions(T)
);

TEqn.relax();
fvOptions.constrain(TEqn);
TEqn.solve();
fvOptions.correct(T);
```

#### Step 3: 集成到主循环

```cpp
while (runTime.loop())
{
    // 原有方程
    #include "UEqn.H"
    #include "pEqn.H"
    
    // 新增标量方程
    #include "TEqn.H"
    
    runTime.write();
}
```

---

## 最佳实践清单

### 开发前

- [ ] 分析现有类的继承关系
- [ ] 了解设计模式和架构
- [ ] 查看类似实现的示例
- [ ] **对照源码模板文件验证字典必填关键字**（.H 中的 Usage 块 + etc/codeTemplates/）
- [ ] **不要将其他类型的模式套用到当前类型**（如 selectionMode 不适用于 coded）
- [ ] 准备测试案例

### 开发中

- [ ] 遵循 OpenFOAM 命名规范
- [ ] 使用运行时选择机制
- [ ] 添加充分的注释和文档
- [ ] 保持代码风格一致

### 开发后

- [ ] 编译测试（wmake）
- [ ] 功能测试（tutorial案例）
- [ ] 性能测试（大规模案例）
- [ ] 文档更新

### 提交前

- [ ] 代码审查
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 文档完整

---

## 故障排查

### 编译错误

#### 错误：找不到头文件

```
fatal error: kEpsilon.H: No such file or directory
```

**解决**：
- 检查 `Make/options` 中的 `EXE_INC` 路径
- 确认依赖库已编译
- 使用 `wmake` 而非直接 `g++`

#### 错误：链接错误

```
undefined reference to `Foam::RASModels::kEpsilon::correct()'
```

**解决**：
- 检查 `Make/options` 中的 `LIB_LIBS`
- 确认基类库已加载
- 检查命名空间

### 运行时错误

#### 错误：找不到模型

```
Unknown RASModel MyKEpsilon
```

**解决**：
- 确认库已编译并添加到 `LD_LIBRARY_PATH`
- 检查 `Make/files` 中的注册宏
- 验证 `TypeName` 拼写

#### 错误：参数错误

```
keyword timeFunction is undefined in dictionary
```

**解决**：
- 检查边界条件配置文件
- 确认必需参数已提供
- 参考文档中的示例配置

---

## 参考资源

### OpenFOAM 官方文档

- [OpenFOAM User Guide](https://openfoam.org/docs/user/)
- [OpenFOAM Programmer's Guide](https://openfoam.org/docs/pg/)
- [OpenFOAM Source Code](https://github.com/OpenFOAM/OpenFOAM-9)

### 内部参考

- `references/openfoam-structure.md` - 源码结构
- `references/solver-analysis-guide.md` - 求解器分析
- `references/search-patterns.md` - 搜索模式库

### 代码模板

- `templates/solver_modification.md` - 求解器模板
- `templates/boundary_modification.md` - 边界条件模板
- `templates/model_modification.md` - 物理模型模板

---

**最后更新**: 2026-03-10  
**版本**: 2.1.0
