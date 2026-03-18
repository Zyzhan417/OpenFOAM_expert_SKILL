    axisTemperaturePressureCSV
    {
        type            coded;
        libs            ("libutilityFunctionObjects.so");

        name            axisTemperaturePressureCSV;

        codeInclude
        #{
            #include "volFields.H"
            #include "OFstream.H"
            #include "OSspecific.H"
            #include "interpolation.H"
            #include "interpolationCellPoint.H"
        #};

        codeWrite
        #{
            // 配置参数
            const scalar zMin = -0.6;      // z最小值 [m]
            const scalar zMax = 1.6;       // z最大值 [m]
            const label nPoints = 200;     // 采样点数量
            const scalar axisX = 0.0;      // 轴线x坐标 [m]
            const scalar axisY = 0.0;      // 轴线y坐标 [m]

            // 查找温度、压力、速度和组分场
            bool TFound = mesh().foundObject<volScalarField>("T.gas");
            bool pFound = mesh().foundObject<volScalarField>("p");
            bool UFound = mesh().foundObject<volVectorField>("U.gas");
            bool O2Found = mesh().foundObject<volScalarField>("O2.gas");
            bool SiCl4Found = mesh().foundObject<volScalarField>("SiCl4.gas");
            bool GeCl4Found = mesh().foundObject<volScalarField>("GeCl4.gas");

            if (TFound && pFound && UFound)
            {
                const volScalarField& T = mesh().lookupObject<volScalarField>("T.gas");
                const volScalarField& p = mesh().lookupObject<volScalarField>("p");
                const volVectorField& U = mesh().lookupObject<volVectorField>("U.gas");

                // 获取组分场
                const volScalarField* O2_ptr = nullptr;
                const volScalarField* SiCl4_ptr = nullptr;
                const volScalarField* GeCl4_ptr = nullptr;

                if (O2Found)
                    O2_ptr = &mesh().lookupObject<volScalarField>("O2.gas");

                if (SiCl4Found)
                    SiCl4_ptr = &mesh().lookupObject<volScalarField>("SiCl4.gas");

                if (GeCl4Found)
                    GeCl4_ptr = &mesh().lookupObject<volScalarField>("GeCl4.gas");

                // 创建插值器（使用cell-point插值，更精确）
                autoPtr<interpolation<scalar>> TInterp
                (
                    interpolation<scalar>::New(T, "cellPoint")
                );
                autoPtr<interpolation<scalar>> pInterp
                (
                    interpolation<scalar>::New(p, "cellPoint")
                );
                autoPtr<interpolation<vector>> UInterp
                (
                    interpolation<vector>::New(U, "cellPoint")
                );

                autoPtr<interpolation<scalar>> O2Interp;
                autoPtr<interpolation<scalar>> SiCl4Interp;
                autoPtr<interpolation<scalar>> GeCl4Interp;

                if (O2Found)
                    O2Interp.reset(new interpolation<scalar>(*O2_ptr, "cellPoint"));
                if (SiCl4Found)
                    SiCl4Interp.reset(new interpolation<scalar>(*SiCl4_ptr, "cellPoint"));
                if (GeCl4Found)
                    GeCl4Interp.reset(new interpolation<scalar>(*GeCl4_ptr, "cellPoint"));

                // 创建输出目录
                fileName dir
                (
                    mesh().time().globalPath()/
                    "postProcessing"/
                    name()/
                    mesh().time().timeName(mesh().time().value())
                );

                mkDir(dir);

                // 打开CSV文件
                OFstream os(dir/"axis_T_p_U_species.csv");

                // 写入CSV表头
                os << "# Axis Temperature, Pressure, Velocity and Species Distribution" << endl;
                os << "# Sampling along line: x=" << axisX << " m, y=" << axisY << " m" << endl;
                os << "# z range: " << zMin << " to " << zMax << " m" << endl;
                os << "# Number of points: " << nPoints << endl;
                os << "# Time: " << mesh().time().value() << " s" << endl;
                os << "z_position[m],Temperature[K],Pressure[Pa],U_axial[m/s],U_radial[m/s],U_tangential[m/s],O2_mass_frac";
                if (SiCl4Found)
                    os << ",SiCl4_mass_frac";
                if (GeCl4Found)
                    os << ",GeCl4_mass_frac";
                os << endl;

                // 采样统计
                label nValidPoints = 0;
                scalar Tmin = Foam::GREAT;
                scalar Tmax = -Foam::GREAT;
                scalar pmin = Foam::GREAT;
                scalar pmax = -Foam::GREAT;

                Info << "Sampling axis data:" << endl;
                Info << "  Sampling line: x=" << axisX << ", y=" << axisY << " m" << endl;
                Info << "  z range: " << zMin << " to " << zMax << " m" << endl;
                Info << "  Number of points: " << nPoints << endl;

                // 在指定直线上等距采样
                scalar dz = (zMax - zMin) / scalar(nPoints - 1);

                for (label i = 0; i < nPoints; i++)
                {
                    scalar z = zMin + scalar(i) * dz;

                    // 采样点位置
                    point samplePoint(axisX, axisY, z);

                    // 检查采样点是否在网格内
                    if (mesh().findCell(samplePoint) >= 0)
                    {
                        // 在网格内，进行插值
                        scalar T_val = TInterp->interpolate(samplePoint, i);
                        scalar p_val = pInterp->interpolate(samplePoint, i);
                        vector U_vec = UInterp->interpolate(samplePoint, i);

                        // 速度分量分解
                        scalar U_axial = U_vec.z();           // z方向（轴向）
                        scalar U_radial = Foam::sqrt(U_vec.x()*U_vec.x() + U_vec.y()*U_vec.y());  // 径向
                        scalar U_tangential = 0.0;            // 2D楔形网格，切向速度为0

                        // 组分质量分数
                        scalar O2_val = O2Found ? O2Interp->interpolate(samplePoint, i) : 0.0;
                        scalar SiCl4_val = SiCl4Found ? SiCl4Interp->interpolate(samplePoint, i) : 0.0;
                        scalar GeCl4_val = GeCl4Found ? GeCl4Interp->interpolate(samplePoint, i) : 0.0;

                        // 写入数据
                        os << z << ","
                           << T_val << ","
                           << p_val << ","
                           << U_axial << ","
                           << U_radial << ","
                           << U_tangential << ","
                           << O2_val;

                        if (SiCl4Found)
                            os << "," << SiCl4_val;

                        if (GeCl4Found)
                            os << "," << GeCl4_val;

                        os << endl;

                        // 更新统计
                        Tmin = Foam::min(Tmin, T_val);
                        Tmax = Foam::max(Tmax, T_val);
                        pmin = Foam::min(pmin, p_val);
                        pmax = Foam::max(pmax, p_val);
                        nValidPoints++;
                    }
                    else
                    {
                        // 采样点在网格外，写入NaN
                        os << z << ",NaN,NaN,NaN,NaN,NaN";
                        if (SiCl4Found)
                            os << ",NaN";
                        if (GeCl4Found)
                            os << ",NaN";
                        os << endl;

                        WarningIn("axisTemperaturePressureCSV::codeWrite()")
                            << "Sample point at z=" << z << " m is outside the mesh"
                            << endl;
                    }
                }

                // 输出统计信息
                Info << "Axis temperature, pressure, velocity and species distribution written to "
                     << dir/"axis_T_p_U_species.csv" << endl;
                Info << "  Valid points: " << nValidPoints << " / " << nPoints << endl;
                if (nValidPoints > 0)
                {
                    Info << "  Temperature range: " << Tmin << " - " << Tmax << " K" << endl;
                    Info << "  Pressure range: " << pmin << " - " << pmax << " Pa" << endl;
                }
                Info << endl;
            }
            else
            {
                Info << "T.gas, p or U.gas field not found for axis CSV output!" << endl;
            }
        #};

        executeControl  writeTime;
        writeControl    writeTime;
    }
