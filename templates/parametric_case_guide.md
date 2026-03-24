# OpenFOAM 参数化 Case 与时变边界条件指南

## 概述

本文档总结 MCVD (Modified Chemical Vapor Deposition) OpenFOAM case 的参数化方法和时变边界条件的正确实现方式。

---

## 一、参数化方法

### 1.1 核心思想

通过一个中央 `Param` 文件集中管理所有常用参数，使用 `#include` 和 `#calc` 实现参数间的自动推导计算。

### 1.2 Param 文件结构

```cpp
// Param 文件模板
FoamFile
{
    format      ascii;
    class       dictionary;
    object      Param;
}

// ============ 分段切换时间 ============
tSwitch                 40;     // 阶段切换时间点 [s]

// ============ 火焰温度 ============
flameTemp               1873;   // [K]

// ============ 组分体积流量 ============ 单位sccm
// Phase 1: 0~40s
M_SiCl4_0_p1            190;    // 第一阶段SiCl4混气流量
X_SiCl4_p1              1.0;    // 第一阶段SiCl4体积分数
M_SiCl4_p1              #calc "$M_SiCl4_0_p1*$X_SiCl4_p1"; // 实际SiCl4流量

M_GeCl4_0_p1            0;      // 第一阶段GeCl4混气流量
X_GeCl4_p1              1.0;
M_GeCl4_p1              #calc "$M_GeCl4_0_p1*$X_GeCl4_p1";

M_POCl3_0_p1            100;    // 第一阶段POCl3混气流量
X_POCl3_p1              1.0;
M_POCl3_p1              #calc "$M_POCl3_0_p1*$X_POCl3_p1";

// O2包含载气流量: 1000 + 各组分稀释气
M_O2_p1                 #calc "1000.0 + $M_SiCl4_0_p1 * (1.0 - $X_SiCl4_p1) + $M_GeCl4_0_p1 * (1.0 - $X_GeCl4_p1) + $M_POCl3_0_p1 * (1.0 - $X_POCl3_p1)";
M_He_p1                 300.0;  // He流量
M_gas_p1                #calc "$M_O2_p1 + $M_SiCl4_p1 + $M_GeCl4_p1 + $M_POCl3_p1 + $M_He_p1";

// Phase 2: 40~80s
M_SiCl4_0_p2            0;      // 第二阶段SiCl4混气流量
X_SiCl4_p2              1.0;
M_SiCl4_p2              #calc "$M_SiCl4_0_p2*$X_SiCl4_p2";

M_GeCl4_0_p2            100;    // 第二阶段GeCl4混气流量
X_GeCl4_p2              1.0;
M_GeCl4_p2              #calc "$M_GeCl4_0_p2*$X_GeCl4_p2";

M_POCl3_0_p2            100;
X_POCl3_p2              1.0;
M_POCl3_p2              #calc "$M_POCl3_0_p2*$X_POCl3_p2";

M_O2_p2                 #calc "1000.0 + $M_SiCl4_0_p2 * (1.0 - $X_SiCl4_p2) + $M_GeCl4_0_p2 * (1.0 - $X_GeCl4_p2) + $M_POCl3_0_p2 * (1.0 - $X_POCl3_p2)";
M_He_p2                 300.0;
M_gas_p2                #calc "$M_O2_p2 + $M_SiCl4_p2 + $M_GeCl4_p2 + $M_POCl3_p2 + $M_He_p2";

// ============ 组分浓度参数 (摩尔分数) ============
// Phase 1
x_O2_p1                 #calc "($M_O2_p1)*1.0 / $M_gas_p1";
x_SiCl4_p1              #calc "($M_SiCl4_p1)*1.0 / $M_gas_p1";
x_GeCl4_p1              #calc "($M_GeCl4_p1)*1.0 / $M_gas_p1";
x_POCl3_p1              #calc "($M_POCl3_p1)*1.0 / $M_gas_p1";
x_He_p1                 #calc "1.0001 - $x_O2_p1 - $x_SiCl4_p1 - $x_GeCl4_p1 - $x_POCl3_p1";

// Phase 2
x_O2_p2                 #calc "($M_O2_p2)*1.0 / $M_gas_p2";
x_SiCl4_p2              #calc "($M_SiCl4_p2)*1.0 / $M_gas_p2";
x_GeCl4_p2              #calc "($M_GeCl4_p2)*1.0 / $M_gas_p2";
x_POCl3_p2              #calc "($M_POCl3_p2)*1.0 / $M_gas_p2";
x_He_p2                 #calc "1.0001 - $x_O2_p2 - $x_SiCl4_p2 - $x_GeCl4_p2 - $x_POCl3_p2";

// ============ 速度场参数 ============
// velocityZ = M_gas[sccm] / 60[s/min] / 1e6[cm3/m3] / Area[m2] * T_in[K] / T_ref[K]
// Phase 1 入口速度
velocityZ_p1            #calc "$M_gas_p1 / 60.0 / 1000000.0 / (3.1415*0.019*0.019 / 4.0)*300.0 / 273.0";

// Phase 2 入口速度
velocityZ_p2            #calc "$M_gas_p2 / 60.0 / 1000000.0 / (3.1415*0.019*0.019 / 4.0)*300.0 / 273.0";

// WALLS 旋转角速度 [rad/s]
wallOmega               3.1415;

// ============ 计算时长 ============
CalcTime                80;
```

### 1.3 参数引用链

```
输入参数 (M_xxx_0_p1/p2) 
    → 实际流量 (M_xxx_p1/p2) [#calc]
        → 总流量 (M_gas_p1/p2) [#calc]
            → 摩尔分数 (x_xxx_p1/p2) [#calc]
                → 边界条件 ($x_xxx_p1/p2)
            → 入口速度 (velocityZ_p1/p2) [#calc]
                → 速度边界 ($velocityZ_p1/p2)
```

### 1.4 在边界条件文件中引用参数

```cpp
// 0/SiCl4.gas
FoamFile
{
    format      ascii;
    class       volScalarField;
    object      SiCl4.gas;
}

// 包含参数文件 - 必须在 FoamFile 之后
#include "$FOAM_CASE/Param"

dimensions      [];

// 初始场使用 Phase 1 的值
internalField   uniform $x_SiCl4_p1;

boundaryField
{
    #includeEtc "caseDicts/setConstraintTypes"

    INLET
    {
        type            codedFixedValue;  // 时变边界
        value           uniform 0;
        name            SiCl4Inlet;

        code
        #{
            scalar t = this->db().time().value();
            scalar x_Si = 0.0;
            if (t < $tSwitch)
            {
                x_Si = $x_SiCl4_p1;
            }
            else
            {
                x_Si = $x_SiCl4_p2;
            }
            operator==(x_Si);  // 标量场直接用标量值
        #};
    }
    // ... 其他边界
}
```

---

## 二、时变边界条件 (codedFixedValue)

### 2.1 适用场景

当需要在运行期间动态改变边界值时使用，例如：
- 分阶段改变前驱体流量
- 随时间变化的热源移动
- 周期性边界条件

### 2.2 标量场时变边界

```cpp
// 0/GeCl4.gas - 标量场示例
INLET
{
    type            codedFixedValue;
    value           uniform 0;      // 初始值
    name            GeCl4Inlet;     // 生成的边界条件类名

    code
    #{
        // 获取当前时间
        scalar t = this->db().time().value();
        
        // 根据时间选择参数
        scalar x_Ge = 0.0;
        if (t < $tSwitch)           // 引用 Param 中的切换时间
        {
            x_Ge = $x_GeCl4_p1;     // Phase 1
        }
        else
        {
            x_Ge = $x_GeCl4_p2;     // Phase 2
        }
        
        // 设置边界值 - 标量场直接用标量
        operator==(x_Ge);
    #};
}
```

### 2.3 向量场时变边界

```cpp
// 0/U.gas - 向量场示例
INLET
{
    type            codedFixedValue;
    value           uniform (0 0 0);
    name            UgasInlet;

    code
    #{
        scalar t = this->db().time().value();
        scalar vz = 0.0;
        
        if (t < $tSwitch)
        {
            vz = $velocityZ_p1;
        }
        else
        {
            vz = $velocityZ_p2;
        }
        
        // 向量场使用 vector(x, y, z) 构造函数
        operator==(vector(0, 0, vz));
    #};
}
```

### 2.4 空间变化边界（移动热源示例）

```cpp
// 0/T.gas - WALLS 边界：移动热源
WALLS
{
    type        codedFixedValue;
    value       uniform 300;
    name        MovingTorch;

    code
    #{
        // 获取面中心坐标
        const vectorField& Cf = patch().Cf();
        
        // 获取当前场引用（标量场）
        scalarField& Tfield = *this;
        
        // 当前时间和参数
        const scalar t = this->db().time().value();
        const scalar velTorch = 0.001667;        // 焊枪速度 [m/s]
        const scalar TempMax = $flameTemp;       // 从 Param 读取
        const scalar sigma = 0.0306;             // 高斯分布标准差 [m]
        const scalar xposi = 0.0;                // 起始位置 [m]
        
        // 计算当前焊枪位置
        scalar x_torch = xposi + t * velTorch;
        
        // 遍历所有面，计算温度
        forAll(Cf, faceI)
        {
            const scalar z = Cf[faceI][2];       // z坐标
            const scalar dx = z - x_torch;
            
            // 高斯分布温度场
            Tfield[faceI] = 300 + (TempMax - 300) * exp(-0.5 * (dx*dx)/(sigma*sigma));
        }
    #};
}
```

---

## 三、常见错误与正确写法

### 3.1 标量场错误

| 错误写法 | 正确写法 | 说明 |
|----------|----------|------|
| `operator==(uniformValue(x));` | `operator==(x);` | 标量场直接用标量值 |
| `operator==(uniform x);` | `operator==(x);` | uniform 是字典关键字，不是 C++ 函数 |

### 3.2 向量场错误

| 错误写法 | 正确写法 | 说明 |
|----------|----------|------|
| `operator==(uniform (0 0 vz));` | `operator==(vector(0, 0, vz));` | 使用 vector 构造函数 |
| `operator==((0 0 vz));` | `operator==(vector(0, 0, vz));` | 需要显式构造 vector |

### 3.3 参数引用错误

| 错误写法 | 正确写法 | 说明 |
|----------|----------|------|
| `$M_SiCl4_0` | `$M_SiCl4_0_p1` | 阶段参数要带后缀 |
| `#calc "$x_O2"` | `#calc "($M_O2)*1.0 / $M_gas"` | #calc 中直接使用参数名，不要加 $ |

---

## 四、文件修改清单

实现分阶段注入需要修改以下文件：

1. **Param** - 添加分段时间和两套参数
2. **0/SiCl4.gas** - INLET 改为 codedFixedValue
3. **0/GeCl4.gas** - INLET 改为 codedFixedValue
4. **0/POCl3.gas** - INLET 改为 codedFixedValue
5. **0/O2.gas** - INLET 改为 codedFixedValue（摩尔分数会变化）
6. **0/He.gas** - INLET 改为 codedFixedValue（摩尔分数会变化）
7. **0/U.gas** - INLET 改为 codedFixedValue（总流量变化导致速度变化）

---

## 五、使用流程

1. **修改 Param 文件**：设置两阶段的流量值（sccm）
2. **检查切换时间**：确认 `tSwitch` 值与各边界条件中的 `if (t < ...)` 一致
3. **运行 case**：`./Allrun`
4. **调试**：如编译失败，检查 `dynamicCode` 目录中的生成代码

---

## 六、关键经验总结

1. **参数集中管理**：所有可调节参数放在 Param 文件，通过 `#include` 引用
2. **自动推导**：使用 `#calc` 在预处理阶段计算派生值
3. **阶段命名规范**：使用 `_p1`、`_p2` 后缀区分不同阶段
4. **时变边界语法**：
   - 标量：`operator==(scalarValue);`
   - 向量：`operator==(vector(x, y, z));`
5. **参考温度场实现**：`0/T.gas` 中的 MovingTorch 是 codedFixedValue 的标准写法

---

*Created from MCVD case experience - 2026-03-24*
