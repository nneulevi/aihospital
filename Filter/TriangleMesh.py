import vtk
import numpy as np

# ==========================================
# 第一步：只有点云！没有模型！
# ==========================================
points = vtk.vtkPoints()

# 生成 200 个散乱点（模拟扫描数据）
np.random.seed(0)
for _ in range(200):
    x = np.random.uniform(-5, 5)
    y = np.random.uniform(-5, 5)
    z = np.sin(x) * np.cos(y)   # 地形高度
    points.InsertNextPoint(x, y, z)

# 把点打包成 VTK 格式
poly = vtk.vtkPolyData()
poly.SetPoints(points)

# ==========================================
# 第二步：表面重建（核心！生成三角面片）
# ==========================================
reconstruct = vtk.vtkDelaunay2D()  # 三角化重建算法
reconstruct.SetInputData(poly)
reconstruct.Update()

# ==========================================
# 第三步：显示重建出来的曲面
# ==========================================
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(reconstruct.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetColor(0.2, 0.8, 0.2)

renderer = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(renderer)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

renderer.AddActor(actor)
renderer.SetBackground(0.1, 0.1, 0.1)
renWin.SetSize(800, 600)
renWin.SetWindowName("真正的表面重建（点 → 三角面片）")

iren.Initialize()
renWin.Render()
iren.Start()