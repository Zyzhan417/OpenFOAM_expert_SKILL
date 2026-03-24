# fvModel Modification Guide

## Overview

fvModel (formerly fvOptions) is OpenFOAM's framework for adding source terms to field equations. The `coded` fvModel allows users to define custom source terms using C++ code snippets directly in the dictionary file.

**Source Code Location**:
- Implementation: `src/fvModels/general/codedFvModel/codedFvModel.C`
- Header: `src/fvModels/general/codedFvModel/codedFvModel.H`
- Templates: `etc/codeTemplates/dynamicCode/codedFvModelTemplate.*`

---

## coded fvModel Syntax

### Basic Structure

```cpp
sourceName
{
    type            coded;           // Required: fvModel type

    // Required: target field name
    field           U;               // or h, k, epsilon, U.air, etc.

    // Required: cell zone selection (codedFvModel always uses fvCellZone)
    cellZone        all;             // 'all' for entire domain, or zone name

    // Code sections
    codeInclude
    #{
        // Additional #include directives
        #include "mathematicalConstants.H"
    #};

    localCode
    #{
        // Local helper functions/classes
    #};

    codeAddSup
    #{
        // Source term for incompressible equations
        // ∂(ρφ)/∂t + ∇·(ρUφ) - ∇·(Γ∇φ) = S(φ)
    #};

    codeAddRhoSup
    #{
        // Source term for compressible equations (with ρ)
    #};

    codeAddAlphaRhoSup
    #{
        // Source term for multiphase equations (with α and ρ)
    #};
}
```

### Key Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | word | Yes | Must be `coded` |
| `field` | word | Yes | Name of the field to apply source term |
| `cellZone` | word | **Yes** | Cell zone name (`all` for entire domain) |
| `active` | bool | No | Enable/disable (default: yes) |
| `codeInclude` | code | No | Additional #include directives |
| `localCode` | code | No | Local helper functions |
| `codeAddSup` | code | Yes* | Source term for basic equations |
| `codeAddRhoSup` | code | Yes* | Source term for compressible equations |
| `codeAddAlphaRhoSup` | code | Yes* | Source term for multiphase equations |

*At least one of codeAddSup/codeAddRhoSup/codeAddAlphaRhoSup is required.

---

## Available Variables in Code Sections

### Common Objects

| Variable | Type | Description |
|----------|------|-------------|
| `mesh()` | `const fvMesh&` | Mesh reference |
| `mesh().time()` | `const Time&` | Time object |
| `eqn` | `fvMatrix<Type>&` | The equation matrix |
| `eqn.source()` | `Field<Type>&` | Source term field |
| `eqn.psi()` | `const VolField<Type>&` | The field being solved |

### For codeAddRhoSup

| Variable | Type | Description |
|----------|------|-------------|
| `rho` | `const volScalarField&` | Density field |

### For codeAddAlphaRhoSup

| Variable | Type | Description |
|----------|------|-------------|
| `alpha` | `const volScalarField&` | Volume fraction field |
| `rho` | `const volScalarField&` | Density field |

---

## Usage Examples

### Example 1: Simple Heat Source

```cpp
// constant/fvModels or system/fvOptions
heatSource
{
    type            coded;
    cellZone        all;
    field           h;

    codeAddSup
    #{
        const scalarField& V = mesh().V();
        scalarField& heSource = eqn.source();

        // Uniform heat source: 1000 W/m³
        heSource += 1000.0 * V;
    #};
}
```

### Example 2: Time-Varying Gravity (Vibration)

```cpp
vibration
{
    type            coded;
    cellZone        all;
    field           U;

    codeInclude
    #{
        #include "mathematicalConstants.H"
    #};

    codeAddSup
    #{
        using namespace Foam::constant::mathematical;

        // Vibration parameters
        const scalar f = 36.0;       // Frequency [Hz]
        const scalar A = 0.008;      // Amplitude [m]
        const scalar omega = 2*pi*f;
        const scalar a_max = A*sqr(omega);  // Max acceleration

        const scalar t = mesh().time().value();
        scalar a = a_max*sin(omega*t);

        // Add acceleration as source term
        const scalarField& V = mesh().V();
        vectorField& Usource = eqn.source();
        Usource += vector(0, -a, 0) * V;  // Vertical vibration
    #};
}
```

### Example 3: Darcy-Forchheimer Porous Media

```cpp
porousZone
{
    type            coded;
    cellZone        porousZone;
    field           U;

    codeAddSup
    #{
        // Darcy-Forchheimer: S = -(μ/K)·U - C₂·½ρ|U|U
        const scalar mu = 1.8e-5;   // Dynamic viscosity
        const scalar K = 1e-7;      // Permeability
        const scalar C2 = 1000;     // Forchheimer coefficient

        const volVectorField& U = eqn.psi();
        const scalarField& V = mesh().V();

        vectorField& USource = eqn.source();
        forAll(U, celli)
        {
            scalar magU = mag(U[celli]);
            USource[celli] -= (mu/K + C2*magU) * U[celli] * V[celli];
        }
    #};
}
```

### Example 4: Multiphase Momentum Source

```cpp
phaseSource
{
    type            coded;
    cellZone        all;
    field           U.particles;

    codeAddAlphaRhoSup
    #{
        // Access phase information
        const volScalarField& alpha = alpha.particles;
        const volScalarField& rho = rho.particles;

        // Add custom force
        const scalarField& V = mesh().V();
        vectorField& Usource = eqn.source();

        forAll(V, celli)
        {
            Usource[celli] += alpha[celli]*rho[celli]*vector(0, -9.81, 0)*V[celli];
        }
    #};
}
```

---

## Common Pitfalls

### 1. cellZone Not Specified

**Problem**: `FOAM FATAL IO ERROR: cellZone not specified`

**Cause**: `codedFvModel` template always constructs `fvCellZone zone_(mesh, coeffs(dict))`, which requires `cellZone` keyword.

**Solution**: Always specify `cellZone all;` (for entire domain) or a specific cell zone name.

### 2. Field Not Found Error

**Problem**: `coded` fvModel requires the target field to exist when the model is constructed.

**Solution**: Ensure `field` name matches an existing volField (e.g., `U`, `h`, `k`, `U.air`).

### 3. Type Mismatch

**Problem**: Source term type doesn't match field type.

**Solution**: 
- For vector fields (U): `vectorField& source = eqn.source();`
- For scalar fields (h, k): `scalarField& source = eqn.source();`

### 4. #codeStream vs coded fvModel

**Problem**: Using `#codeStream` inside other fvModel types (e.g., `vectorSemiImplicitSource`) for time-varying values.

**Cause**: `#codeStream` generates a standalone `extern "C"` function with signature `void func(Ostream& os, const dictionary& dict)`. There is no `this` pointer, no `mesh()` access, and it only executes **once** during dictionary parsing (not per-timestep).

**Solution**: Use `type coded;` fvModel instead for time-varying source terms. It has full access to `mesh()`, `mesh().time()`, and `eqn.source()`, and executes every timestep.

### 5. Compilation Errors

**Problem**: Code in code sections must be valid C++.

**Solution**: Check syntax and ensure all variables are properly declared.

---

## Advanced Usage

### Accessing Other Fields

```cpp
codeAddSup
#{
    // Lookup other fields from the mesh
    const volScalarField& T = mesh().lookupObject<volScalarField>("T");
    const volVectorField& U = mesh().lookupObject<volVectorField>("U");

    // Use in source term calculation
    scalarField& source = eqn.source();
    forAll(source, celli)
    {
        source[celli] += T[celli] * mag(U[celli]);
    }
#};
```

### Using Mathematical Functions

```cpp
codeInclude
#{
    #include "mathematicalConstants.H"
    #include "randomGenerator.H"
#};

codeAddSup
#{
    using namespace Foam::constant::mathematical;

    const scalar pi = pi;              // 3.14159...
    const scalar e = e;                // 2.71828...

    scalar randomValue = rndGen.scalar01();
    scalar sinValue = sin(2*pi*mesh().time().value());
#};
```

---

## References

1. OpenFOAM Source Code:
   - `src/fvModels/general/codedFvModel/codedFvModel.H`
   - `src/fvModels/general/codedFvModel/codedFvModel.C`
   - `etc/codeTemplates/dynamicCode/codedFvModelTemplate.*`

2. OpenFOAM User Guide: fvModels chapter

3. Example Cases:
   - `$FOAM_TUTORIALS/lagrangian/simpleReactingParcels/`
   - `$FOAM_TUTORIALS/multiphase/multiphaseEulerFoam/`
