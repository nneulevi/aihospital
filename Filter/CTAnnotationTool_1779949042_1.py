import sys
import os
import SimpleITK as sitk
import numpy as np
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import vtk
# VTK与Qt界面融合的核心组件
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# ===================== 异步进度条弹窗 =====================
# 功能：处理数据时弹出加载进度条，防止界面卡死
class ProgressDialog(QDialog):
    def __init__(self, title="处理中...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(450, 120)
        self.setModal(True)  # 模态弹窗，操作时无法点击主界面

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        # 提示文字
        self.label = QLabel("初始化处理...")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

    # 更新进度条值和提示文字
    def set_progress(self, value, text=""):
        self.progress.setValue(value)
        if text:
            self.label.setText(text)

# ===================== 工作线程（异步执行） =====================
# 功能：将耗时操作（加载CT、生成掩码）放到子线程，避免UI卡死
class Worker(QThread):
    # 自定义信号
    progress = Signal(int, str)    # 进度更新信号
    finished = Signal()            # 完成信号
    error = Signal(str)            # 错误信号
    success_msg = Signal(str)       # 成功提示信号

    def __init__(self, func, *args, parent=None):
        super().__init__(parent)
        self.func = func    # 要执行的耗时函数
        self.args = args    # 函数参数

    def run(self):
        # 线程启动后自动执行
        try:
            self.func(self.report_progress, *self.args)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    # 向外发送进度更新
    def report_progress(self, value, text=""):
        self.progress.emit(value, text)

# ===================== 主界面 =====================
# 主窗口：CT金属伪影标注 + 三平面视图 + VTK 3D重建
class ArtifactAnnotationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CT金属伪影掩码标注系统 - 支持DICOM/MHD + VTK 3D视图")
        self.resize(1600, 900)

        # 全局变量：CT图像、掩码、numpy数组
        self.ct_image = None       # SimpleITK图像对象
        self.artifact_mask = None  # 伪影掩码图像
        self.volume_np = None      # CT体数据numpy数组 (z,y,x)
        self.mask_np = None        # 掩码numpy数组

        # 三个视图当前切片索引
        self.slice_axial = 0       # 轴位
        self.slice_coronal = 0     # 冠状
        self.slice_sagittal = 0    # 矢状

        # 初始化UI和VTK 3D窗口
        self.init_ui()
        self.init_vtk_3d_view()

    # -------------------------------------------------------------------------
    # 初始化整个界面布局：左侧控制面板 + 右侧三平面视图 + VTK 3D视图
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # ========== 左侧控制面板 ==========
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        control_widget.setFixedWidth(340)

        # 加载按钮组
        self.btn_load = QPushButton("加载 DICOM 序列文件夹")
        self.btn_load.clicked.connect(self.load_dicom_async)
        control_layout.addWidget(self.btn_load)

        self.btn_load_mhd = QPushButton("加载 MHD/RAW 三维影像")
        self.btn_load_mhd.clicked.connect(self.load_mhd_async)
        control_layout.addWidget(self.btn_load_mhd)

        self.btn_load_single = QPushButton("加载 单张图像(DCM/PNG)")
        self.btn_load_single.clicked.connect(self.load_single_async)
        control_layout.addWidget(self.btn_load_single)

        # 阈值下限滑动条
        control_layout.addWidget(QLabel("阈值下限｜二值化阈值滤波"))
        self.th_low = QSlider(Qt.Horizontal)
        self.th_low.setRange(300, 1500)
        self.th_low.setValue(600)
        self.th_low_label = QLabel("600")
        control_layout.addWidget(self.th_low)
        control_layout.addWidget(self.th_low_label)

        # 阈值上限滑动条
        control_layout.addWidget(QLabel("阈值上限｜二值化阈值滤波"))
        self.th_high = QSlider(Qt.Horizontal)
        self.th_high.setRange(2000, 4000)
        self.th_high.setValue(2800)
        self.th_high_label = QLabel("2800")
        control_layout.addWidget(self.th_high)
        control_layout.addWidget(self.th_high_label)

        # 梯度阈值
        control_layout.addWidget(QLabel("梯度阈值｜梯度幅值滤波"))
        self.grad_th = QSlider(Qt.Horizontal)
        self.grad_th.setRange(50, 500)
        self.grad_th.setValue(100)
        self.grad_th_label = QLabel("100")
        control_layout.addWidget(self.grad_th)
        control_layout.addWidget(self.grad_th_label)

        # 形态学开运算半径
        control_layout.addWidget(QLabel("开运算半径｜形态学开运算"))
        self.open_r = QSlider(Qt.Horizontal)
        self.open_r.setRange(0, 5)
        self.open_r.setValue(1)
        self.open_r_label = QLabel("1")
        control_layout.addWidget(self.open_r)
        control_layout.addWidget(self.open_r_label)

        # 形态学闭运算半径
        control_layout.addWidget(QLabel("闭运算半径｜形态学闭运算"))
        self.close_r = QSlider(Qt.Horizontal)
        self.close_r.setRange(0, 10)
        self.close_r.setValue(2)
        self.close_r_label = QLabel("2")
        control_layout.addWidget(self.close_r)
        control_layout.addWidget(self.close_r_label)

        # 最小连通域面积过滤
        control_layout.addWidget(QLabel("最小面积｜连通域过滤"))
        self.min_area = QSlider(Qt.Horizontal)
        self.min_area.setRange(10, 500)
        self.min_area.setValue(40)
        self.min_area_label = QLabel("40")
        control_layout.addWidget(self.min_area)
        control_layout.addWidget(self.min_area_label)

        # 执行与保存按钮
        self.btn_run = QPushButton("生成伪影掩码")
        self.btn_run.clicked.connect(self.generate_mask_async)
        control_layout.addWidget(self.btn_run)

        self.btn_save = QPushButton("保存掩码(NIfTI)")
        self.btn_save.clicked.connect(self.save_mask_async)
        control_layout.addWidget(self.btn_save)

        control_layout.addStretch()
        main_layout.addWidget(control_widget)

        # ========== 右侧整体布局 ==========
        right_layout = QVBoxLayout()

        # ====================== 轴位视图 + VTK 3D 视图 横向并排 ======================
        axial_vtk_layout = QHBoxLayout()

        # 轴位视图
        axial_layout = QVBoxLayout()
        axial_title_layout = QHBoxLayout()
        axial_title_layout.addWidget(QLabel("【轴位 Axial】"))
        axial_title_layout.addStretch()
        self.axial_slice_label = QLabel("切片：0 / 0")
        self.axial_slice_label.setStyleSheet("""
            QLabel { color: #0066CC; font-weight: bold; font-size: 12pt; background-color: #F0F8FF; padding: 4px 8px; border-radius: 4px; }
        """)
        axial_title_layout.addWidget(self.axial_slice_label)
        axial_layout.addLayout(axial_title_layout)

        self.axial_label = QLabel()
        self.axial_label.setStyleSheet("background-color:#111;min-height:280px")
        self.axial_label.setAlignment(Qt.AlignCenter)
        self.slider_axial = QSlider(Qt.Horizontal)
        self.slider_axial.valueChanged.connect(lambda v: self.on_slice_change("axial", v))
        axial_layout.addWidget(self.axial_label)
        axial_layout.addWidget(self.slider_axial)
        axial_vtk_layout.addLayout(axial_layout)

        # VTK 3D 视图（放在轴位右边）
        vtk_box = QVBoxLayout()
        vtk_box.addWidget(QLabel("【VTK 3D CT 重建】"))
        self.vtk_widget = QWidget()
        self.vtk_widget.setStyleSheet("background-color:#000;")
        self.vtk_widget.setMinimumWidth(350)
        vtk_box.addWidget(self.vtk_widget)
        axial_vtk_layout.addLayout(vtk_box)

        right_layout.addLayout(axial_vtk_layout)

        # ========== 冠状 + 矢状 视图并排 ==========
        cor_sag_layout = QHBoxLayout()

        # 冠状视图
        coronal_layout = QVBoxLayout()
        coronal_title_layout = QHBoxLayout()
        coronal_title_layout.addWidget(QLabel("【冠状 Coronal】"))
        coronal_title_layout.addStretch()
        self.coronal_slice_label = QLabel("切片：0 / 0")
        self.coronal_slice_label.setStyleSheet("""
            QLabel { color: #0066CC; font-weight: bold; font-size: 12pt; background-color: #F0F8FF; padding: 4px 8px; border-radius: 4px; }
        """)
        coronal_title_layout.addWidget(self.coronal_slice_label)
        coronal_layout.addLayout(coronal_title_layout)

        self.coronal_label = QLabel()
        self.coronal_label.setStyleSheet("background-color:#111;min-height:280px")
        self.coronal_label.setAlignment(Qt.AlignCenter)
        self.slider_coronal = QSlider(Qt.Horizontal)
        self.slider_coronal.valueChanged.connect(lambda v: self.on_slice_change("coronal", v))
        coronal_layout.addWidget(self.coronal_label)
        coronal_layout.addWidget(self.slider_coronal)
        cor_sag_layout.addLayout(coronal_layout)

        # 矢状视图
        sagittal_layout = QVBoxLayout()
        sagittal_title_layout = QHBoxLayout()
        sagittal_title_layout.addWidget(QLabel("【矢状 Sagittal】"))
        sagittal_title_layout.addStretch()
        self.sagittal_slice_label = QLabel("切片：0 / 0")
        self.sagittal_slice_label.setStyleSheet("""
            QLabel { color: #0066CC; font-weight: bold; font-size: 12pt; background-color: #F0F8FF; padding: 4px 8px; border-radius: 4px; }
        """)
        sagittal_title_layout.addWidget(self.sagittal_slice_label)
        sagittal_layout.addLayout(sagittal_title_layout)

        self.sagittal_label = QLabel()
        self.sagittal_label.setStyleSheet("background-color:#111;min-height:280px")
        self.sagittal_label.setAlignment(Qt.AlignCenter)
        self.slider_sagittal = QSlider(Qt.Horizontal)
        self.slider_sagittal.valueChanged.connect(lambda v: self.on_slice_change("sagittal", v))
        sagittal_layout.addWidget(self.sagittal_label)
        sagittal_layout.addWidget(self.slider_sagittal)
        cor_sag_layout.addLayout(sagittal_layout)

        right_layout.addLayout(cor_sag_layout)
        main_layout.addLayout(right_layout)

        # 绑定所有滑动条事件
        self.connect_all_sliders()

    # -------------------------------------------------------------------------
    # VTK 3D 视图初始化
    # 创建VTK渲染器、窗口、交互器，嵌入Qt界面
    def init_vtk_3d_view(self):
        self.vtk_view = QVTKRenderWindowInteractor(self.vtk_widget)
        self.vtk_renderer = vtk.vtkRenderer()                  # VTK渲染器（场景）
        self.vtk_renderer.SetBackground(0.1, 0.1, 0.1)         # 背景深灰色
        self.vtk_view.GetRenderWindow().AddRenderer(self.vtk_renderer)
        self.iren = self.vtk_view.GetRenderWindow().GetInteractor()
        self.iren.Initialize()  # 初始化交互

        # 把VTK窗口塞进Qt组件
        layout = QVBoxLayout(self.vtk_widget)
        layout.addWidget(self.vtk_view)
        layout.setContentsMargins(0,0,0,0)

    # -------------------------------------------------------------------------
    # 3D CT 体渲染（VTK 核心）
    # 将CT体数据转为三维立体视图
    def render_3d_ct(self):
        if self.ct_image is None:
            return

        from vtkmodules.util import numpy_support
        self.vtk_renderer.RemoveAllViewProps()  # 清空旧模型

        vol = self.volume_np.astype(np.short)
        depth, height, width = vol.shape

        # numpy 转 VTK 图像数据
        vtk_data = numpy_support.numpy_to_vtk(
            vol.ravel(), deep=True, array_type=vtk.VTK_SHORT
        )

        vtk_image = vtk.vtkImageData()
        vtk_image.SetDimensions(width, height, depth)
        vtk_image.GetPointData().SetScalars(vtk_data)

        # 体渲染Mapper
        mapper = vtk.vtkSmartVolumeMapper()
        mapper.SetInputData(vtk_image)

        # 颜色传输函数：不同CT值对应不同颜色
        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(-500, 0.0, 0.0, 0.0)
        color.AddRGBPoint(0, 0.2, 0.2, 0.2)
        color.AddRGBPoint(200, 1.0, 0.8, 0.6)
        color.AddRGBPoint(1000, 1.0, 1.0, 1.0)

        # 不透明度函数：控制组织显示透明度
        opacity = vtk.vtkPiecewiseFunction()
        opacity.AddPoint(-500, 0.00)
        opacity.AddPoint(0, 0.00)
        opacity.AddPoint(200, 0.05)
        opacity.AddPoint(1000, 0.15)

        # 体积属性
        prop = vtk.vtkVolumeProperty()
        prop.SetColor(color)
        prop.SetScalarOpacity(opacity)
        prop.ShadeOn()  # 开启阴影，立体感更强
        prop.SetInterpolationTypeToLinear()

        # 创建体积对象并加入场景
        volume = vtk.vtkVolume()
        volume.SetMapper(mapper)
        volume.SetProperty(prop)

        self.vtk_renderer.AddVolume(volume)
        self.vtk_renderer.ResetCamera()       # 自动调整相机视角
        self.vtk_view.GetRenderWindow().Render()

    # -------------------------------------------------------------------------
    # 绑定所有滑动条事件 + 防抖更新（300ms延迟）
    def connect_all_sliders(self):
        self.th_low.valueChanged.connect(lambda v: self.th_low_label.setText(str(v)))
        self.th_high.valueChanged.connect(lambda v: self.th_high_label.setText(str(v)))
        self.grad_th.valueChanged.connect(lambda v: self.grad_th_label.setText(str(v)))
        self.open_r.valueChanged.connect(lambda v: self.open_r_label.setText(str(v)))
        self.close_r.valueChanged.connect(lambda v: self.close_r_label.setText(str(v)))
        self.min_area.valueChanged.connect(lambda v: self.min_area_label.setText(str(v)))

        # 定时器：滑动停止300ms后再自动生成掩码，防止卡顿
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.generate_mask_async)

        self.th_low.valueChanged.connect(lambda: self.update_timer.start(300))
        self.th_high.valueChanged.connect(lambda: self.update_timer.start(300))
        self.grad_th.valueChanged.connect(lambda: self.update_timer.start(300))
        self.open_r.valueChanged.connect(lambda: self.update_timer.start(300))
        self.close_r.valueChanged.connect(lambda: self.update_timer.start(300))
        self.min_area.valueChanged.connect(lambda: self.update_timer.start(300))

    # -------------------------------------------------------------------------
    # 统一异步任务启动封装：显示进度条 + 启动线程
    def run_async(self, title, func, *args):
        self.dialog = ProgressDialog(title, self)
        self.worker = Worker(func, *args)
        self.worker.progress.connect(self.dialog.set_progress)
        self.worker.finished.connect(self.dialog.close)
        self.worker.finished.connect(self.on_task_done)
        self.worker.error.connect(lambda e: (self.dialog.close(), QMessageBox.critical(self, "错误", e)))
        self.worker.success_msg.connect(self.on_success_msg)
        self.dialog.show()
        self.worker.start()

    # 任务完成后刷新界面 + 3D重建
    def on_task_done(self):
        self.refresh_all_views()
        self.update_all_slice_labels()
        self.render_3d_ct()

    # 成功提示
    def on_success_msg(self, msg):
        QMessageBox.information(self, "成功", msg)

    # -------------------------------------------------------------------------
    # 加载 MHD 文件（异步）
    def load_mhd_async(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 MHD 文件", "", "MHD Image (*.mhd *.MHD)")
        if not path: return
        self.run_async("加载 MHD 中...", self._load_mhd_task, path)

    def _load_mhd_task(self, report, path):
        report(20, "读取MHD文件...")
        img = sitk.ReadImage(path)
        report(60, "解析三维数据...")
        vol = sitk.GetArrayFromImage(img)
        self.ct_image = img
        self.volume_np = vol
        self.mask_np = None
        self.artifact_mask = None
        self.init_slice_range()
        report(100, "完成")

    # -------------------------------------------------------------------------
    # 加载 DICOM 序列（异步）
    def load_dicom_async(self):
        folder = QFileDialog.getExistingDirectory(self, "选择 DICOM 序列文件夹")
        if not folder: return
        self.run_async("加载 DICOM 中...", self._load_dicom_task, folder)

    def _load_dicom_task(self, report, folder):
        report(10, "扫描序列文件...")
        reader = sitk.ImageSeriesReader()
        fns = reader.GetGDCMSeriesFileNames(folder)
        reader.SetFileNames(fns)
        report(40, "读取图像...")
        img = reader.Execute()
        report(70, "构建三维体...")
        vol = sitk.GetArrayFromImage(img)
        self.ct_image = img
        self.volume_np = vol
        self.mask_np = None
        self.artifact_mask = None
        self.init_slice_range()
        report(100, "完成")

    # -------------------------------------------------------------------------
    # 加载单张图像（异步）
    def load_single_async(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图像", "", "所有图像 (*.dcm *.png *.jpg *.nii *.mhd)")
        if not path: return
        self.run_async("加载单张图像...", self._load_single_task, path)

    def _load_single_task(self, report, path):
        img = sitk.ReadImage(path)
        vol = sitk.GetArrayFromImage(img)
        if vol.ndim == 2:
            vol = vol[None]
            img = sitk.GetImageFromArray(vol)
        self.ct_image = img
        self.volume_np = vol
        self.mask_np = None
        self.artifact_mask = None
        self.init_slice_range()
        report(100)

    # -------------------------------------------------------------------------
    # 生成伪影掩码（异步，核心算法）
    def generate_mask_async(self):
        if self.ct_image is None: return
        self.run_async("生成伪影掩码...", self._generate_mask_task)

    # 真正执行掩码生成的任务函数
    def _generate_mask_task(self, report):
        img = self.ct_image
        tl = self.th_low.value()
        th = self.th_high.value()
        gg = self.grad_th.value()
        ro = self.open_r.value()
        rc = self.close_r.value()
        ma = self.min_area.value()

        report(10, "二值化阈值处理...")
        mask = sitk.BinaryThreshold(img, tl, th, 1, 0)  # 阈值分割

        report(25, "计算梯度幅值...")
        g = sitk.GradientMagnitude(sitk.Cast(img, sitk.sitkFloat32))
        gmask = sitk.BinaryThreshold(g, gg, 99999, 1, 0)

        comb = sitk.And(mask, gmask)  # 与运算：保留高灰度+高梯度区域

        report(40, "形态学开运算...")
        comb = sitk.BinaryMorphologicalOpening(comb, [ro, ro, ro])

        report(55, "形态学闭运算...")
        comb = sitk.BinaryMorphologicalClosing(comb, [rc, rc, rc])

        report(70, "连通域分析...")
        cc = sitk.ConnectedComponent(comb)
        stats = sitk.LabelShapeStatisticsImageFilter()
        stats.Execute(cc)

        report(85, "生成最终掩码...")
        final = sitk.Image(img.GetSize(), sitk.sitkUInt8)
        final.CopyInformation(img)
        for lbl in stats.GetLabels():
            if stats.GetNumberOfPixels(lbl) >= ma:
                final += sitk.BinaryThreshold(cc, lbl, lbl, 1, 0)

        self.artifact_mask = final
        self.mask_np = sitk.GetArrayFromImage(final)
        report(100, "处理完成")

    # -------------------------------------------------------------------------
    # 保存掩码（异步）
    def save_mask_async(self):
        if self.artifact_mask is None:
            QMessageBox.warning(self, "提示", "先生成掩码！")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存掩码", "artifact_mask.nii.gz", "NIfTI 掩码 (*.nii.gz *.nii)")
        if not path: return
        if os.path.exists(path):
            yes = QMessageBox.question(self, "文件已存在", f"{path}\n已存在，是否覆盖？")
            if yes != QMessageBox.Yes:
                return
        self.run_async("保存掩码中...", self._save_mask_task, path)

    def _save_mask_task(self, report, path):
        sitk.WriteImage(self.artifact_mask, path)
        report(100, "保存完成")
        self.worker.success_msg.emit(f"掩码已保存到：\n{path}")

    # -------------------------------------------------------------------------
    # 更新切片序号显示
    def update_all_slice_labels(self):
        if self.volume_np is None: return
        d, h, w = self.volume_np.shape
        self.axial_slice_label.setText(f"切片：{self.slice_axial} / {d-1}")
        self.coronal_slice_label.setText(f"切片：{self.slice_coronal} / {h-1}")
        self.sagittal_slice_label.setText(f"切片：{self.slice_sagittal} / {w-1}")

    # 初始化切片范围，默认显示中间层
    def init_slice_range(self):
        d, h, w = self.volume_np.shape
        self.slider_axial.setRange(0, d-1)
        self.slider_coronal.setRange(0, h-1)
        self.slider_sagittal.setRange(0, w-1)
        sa, sc, ss = d//2, h//2, w//2
        self.slice_axial, self.slice_coronal, self.slice_sagittal = sa, sc, ss
        self.slider_axial.setValue(sa)
        self.slider_coronal.setValue(sc)
        self.slider_sagittal.setValue(ss)
        self.update_all_slice_labels()

    # -------------------------------------------------------------------------
    # ✅ 核心：三平面同步滑动逻辑
    # 滑动任意一个视图，另外两个自动同步
    def on_slice_change(self, vt, v):
        if self.volume_np is None:
            return

        # 获取当前体数据尺寸 (z,y,x)
        d, h, w = self.volume_np.shape

        # 轴位滑动 → 同步冠状、矢状
        if vt == "axial":
            self.slice_axial = v
            self.slice_coronal = int((v / d) * h)
            self.slice_sagittal = int((v / d) * w)

        # 冠状滑动 → 同步轴位、矢状
        elif vt == "coronal":
            self.slice_coronal = v
            self.slice_axial = int((v / h) * d)
            self.slice_sagittal = int((v / h) * w)

        # 矢状滑动 → 同步轴位、冠状
        elif vt == "sagittal":
            self.slice_sagittal = v
            self.slice_axial = int((v / w) * d)
            self.slice_coronal = int((v / w) * h)

        # 防止索引越界
        self.slice_axial = np.clip(self.slice_axial, 0, d-1)
        self.slice_coronal = np.clip(self.slice_coronal, 0, h-1)
        self.slice_sagittal = np.clip(self.slice_sagittal, 0, w-1)

        # 暂时阻塞信号，避免循环触发
        self.slider_axial.blockSignals(True)
        self.slider_axial.setValue(self.slice_axial)
        self.slider_axial.blockSignals(False)

        self.slider_coronal.blockSignals(True)
        self.slider_coronal.setValue(self.slice_coronal)
        self.slider_coronal.blockSignals(False)

        self.slider_sagittal.blockSignals(True)
        self.slider_sagittal.setValue(self.slice_sagittal)
        self.slider_sagittal.blockSignals(False)

        # 刷新所有视图
        self.refresh_all_views()
        self.update_all_slice_labels()

    # -------------------------------------------------------------------------
    # 绘制单张切片：CT + 掩码红色叠加
    def draw_slice(self, im, mk):
        im = np.clip(im, -500, 1500)  # CT窗宽窗位截断
        im = ((im - im.min()) / (im.max() - im.min() + 1e-8) * 255).astype(np.uint8)
        c = np.stack([im, im, im], axis=-1)  # 转RGB
        if mk is not None and mk.shape == im.shape:
            c[mk > 0] = [255, 80, 80]  # 掩码区域标红
        return c

    # numpy数组转Qt图片
    def to_qpix(self, arr):
        h, w, ch = arr.shape
        qim = QImage(arr.data, w, h, 3*w, QImage.Format_RGB888)
        return QPixmap.fromImage(qim).scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    # -------------------------------------------------------------------------
    # 更新三个视图显示
    def update_view_axial(self):
        if self.volume_np is None: return
        im = self.volume_np[self.slice_axial]
        mk = self.mask_np[self.slice_axial] if self.mask_np is not None else None
        self.axial_label.setPixmap(self.to_qpix(self.draw_slice(im, mk)))

    def update_view_coronal(self):
        if self.volume_np is None: return
        im = self.volume_np[:, self.slice_coronal, :]
        mk = self.mask_np[:, self.slice_coronal, :] if self.mask_np is not None else None
        self.coronal_label.setPixmap(self.to_qpix(self.draw_slice(im, mk)))

    def update_view_sagittal(self):
        if self.volume_np is None: return
        im = self.volume_np[:, :, self.slice_sagittal]
        mk = self.mask_np[:, :, self.slice_sagittal] if self.mask_np is not None else None
        self.sagittal_label.setPixmap(self.to_qpix(self.draw_slice(im, mk)))

    def refresh_all_views(self):
        self.update_view_axial()
        self.update_view_coronal()
        self.update_view_sagittal()

# -------------------------------------------------------------------------
# 主程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ArtifactAnnotationWindow()
    win.show()
    sys.exit(app.exec())