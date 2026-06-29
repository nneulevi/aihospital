import vtk

# --------------------------
# 1. 读取 NRRD 格式 CT 数据
# --------------------------
reader = vtk.vtkNrrdReader()
reader.SetFileName("brain_ct.nrrd")  # 你的CT文件路径
reader.Update()

# --------------------------
# 2. 体绘制（Volume Rendering）
# --------------------------
volume_mapper = vtk.vtkSmartVolumeMapper()
volume_mapper.SetInputConnection(reader.GetOutputPort())

# CT 窗宽窗位（脑部）
color = vtk.vtkColorTransferFunction()
color.AddRGBPoint(-300, 0.0, 0.0, 0.0)
color.AddRGBPoint(100, 1.0, 1.0, 1.0)
color.AddRGBPoint(400, 1.0, 0.5, 0.5)
color.AddRGBPoint(1000, 1.0, 1.0, 1.0)

opacity = vtk.vtkPiecewiseFunction()
opacity.AddPoint(-300, 0.0)
opacity.AddPoint(100, 0.1)
opacity.AddPoint(400, 0.3)
opacity.AddPoint(1000, 0.5)

volume_property = vtk.vtkVolumeProperty()
volume_property.SetColor(color)
volume_property.SetScalarOpacity(opacity)
volume_property.ShadeOn()  # 阴影光照
volume_property.SetInterpolationTypeToLinear()

# --------------------------
# 3. 创建 3D 体对象
# --------------------------
volume = vtk.vtkVolume()
volume.SetMapper(volume_mapper)
volume.SetProperty(volume_property)

# --------------------------
# 4. 渲染窗口 + 交互
# --------------------------
renderer = vtk.vtkRenderer()
renderer.SetBackground(0.1, 0.1, 0.1)  # 深色背景

ren_win = vtk.vtkRenderWindow()
ren_win.AddRenderer(renderer)
ren_win.SetSize(900, 700)
ren_win.SetWindowName("VTK 3D CT 查看器")

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(ren_win)

# 加入3D影像
renderer.AddVolume(volume)
renderer.ResetCamera()

# --------------------------
# 启动
# --------------------------
iren.Initialize()
ren_win.Render()
iren.Start()