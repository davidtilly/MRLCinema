
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


def rigid_registration(fixed:sitk.Image, moving:sitk.Image, mask:sitk.Image, initial_transform=None) -> tuple[sitk.Image, sitk.Transform]:
    """
    Register the moving image to the fixed image using the SimpleITK library.
    """
    fixed_f = sitk.Cast(fixed, sitk.sitkFloat32)
    moving_f = sitk.Cast(moving, sitk.sitkFloat32)   

    if initial_transform == None:
        initial_transform = sitk.TranslationTransform(fixed.GetDimension())
    
    R = sitk.ImageRegistrationMethod()

    #R.SetMetricAsMeanSquares()
    R.SetMetricAsCorrelation()
    R.SetMetricFixedMask(mask)
    R.SetMetricMovingMask(mask)

    R.SetOptimizerAsRegularStepGradientDescent(
        learningRate=2.0,
        minStep=1e-4,
        numberOfIterations=500,
        gradientMagnitudeTolerance=1e-8,
    )
    R.SetOptimizerScalesFromIndexShift()

    R.SetInitialTransform(initial_transform)
    R.SetInterpolator(sitk.sitkLinear)

    metric_start = R.MetricEvaluate(fixed_f, moving_f)
    #R.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(R))
    
    outTx = R.Execute(fixed_f, moving_f)

    print("-------")
    print(f"Optimizer stop condition: {R.GetOptimizerStopConditionDescription()}")
    print(f" Iteration: {R.GetOptimizerIteration()}")
    print(f" Metric value start/sopt: {metric_start} / {R.GetMetricValue()}")
    print(f" Transform parameters: {outTx.GetParameters()}")

    moving_t = sitk.Resample(moving, fixed, outTx, sitk.sitkLinear, 0.0, moving.GetPixelID())

    return moving_t, outTx


def deformable_registration(fixed:sitk.Image, moving:sitk.Image, fixed_mask:sitk.Image, initial_transform=None) -> tuple[sitk.Image, sitk.Transform]:
    """
    Register the moving image to the fixed image using the SimpleITK library.
    """
    fixed_f = sitk.Cast(fixed, sitk.sitkFloat32)
    moving_f = sitk.Cast(moving, sitk.sitkFloat32)   

    if initial_transform == None:
        transformDomainMeshSize = [8] * moving.GetDimension()
        initial_transform = sitk.BSplineTransformInitializer(fixed_f, transformDomainMeshSize)
    
    R = sitk.ImageRegistrationMethod()

    R.SetMetricAsMeanSquares()
    R.SetMetricFixedMask(fixed_mask)

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

    #resampler = sitk.ResampleImageFilter()
    #resampler.SetReferenceImage(fixed_f)
    #resampler.SetInterpolator(sitk.sitkLinear)
    #resampler.SetDefaultPixelValue(100)
    #resampler.SetTransform(outTx)
    #moving_t = resampler.Execute(moving_f)
    moving_t = sitk.Resample(moving, fixed, outTx, sitk.sitkLinear, 0.0, moving.GetPixelID())

    #moving_ti = sitk.Cast(sitk.RescaleIntensity(moving_t), sitk.sitkInt64)

    return moving_t, outTx