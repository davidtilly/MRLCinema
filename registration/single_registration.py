
import SimpleITK as sitk

def command_iteration(method):
    """ Callback invoked when the optimization has an iteration """
    if method.GetOptimizerIteration() == 0:
        print("Estimated Scales: ", method.GetOptimizerScales())
    print(
        f"{method.GetOptimizerIteration():3} "
        + f"= {method.GetMetricValue():7.5f} "
        + f": {method.GetOptimizerPosition()}"
    )

def deformable_registration(fixed:sitk.Image, moving:sitk.Image, initial_transform=None) -> sitk.Image:
    """
    Register the moving image to the fixed image using the SimpleITK library.
    """
    fixed_f = sitk.sitk.Cast(fixed, sitk.sitkFloat32)
    moving_f = sitk.ReadImage(moving_f, sitk.sitkFloat32)   

    if initial_transform == None:
        transformDomainMeshSize = [8] * moving.GetDimension()
        initial_transform = sitk.BSplineTransformInitializer(fixed, transformDomainMeshSize)
    
    R = sitk.ImageRegistrationMethod()

    R.SetMetricAsMeanSquares()

    R.SetOptimizerAsRegularStepGradientDescent(
        learningRate=2.0,
        minStep=1e-4,
        numberOfIterations=500,
        gradientMagnitudeTolerance=1e-8,
    )
    R.SetOptimizerScalesFromIndexShift()

    R.SetInitialTransform(initial_transform)
    R.SetInterpolator(sitk.sitkLinear)

    R.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(R))
    outTx = R.Execute(fixed_f, moving_f)

    print("-------")
    print(outTx)
    print(f"Optimizer stop condition: {R.GetOptimizerStopConditionDescription()}")
    print(f" Iteration: {R.GetOptimizerIteration()}")
    print(f" Metric value: {R.GetMetricValue()}")

    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(fixed_f)
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetDefaultPixelValue(100)
    resampler.SetTransform(outTx)

    moving_t = resampler.Execute(moving_f)

    simg1 = sitk.Cast(sitk.RescaleIntensity(fixed_f), sitk.sitkUInt8)
    simg2 = sitk.Cast(sitk.RescaleIntensity(moving_t), sitk.sitkUInt8)
    cimg = sitk.Compose(simg1, simg2, simg1 // 2.0 + simg2 // 2.0)
    return cimg, outTx
