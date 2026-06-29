import json
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np

from metal_artifact_mask_tool import create_demo_volume, load_volume, run_pipeline, save_mask, sitk

try:
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QAction, QImage, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QProgressDialog,
        QPushButton,
        QSlider,
        QSpinBox,
        QSplitter,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - only used when GUI deps are missing.
    raise SystemExit(
        "缺少 PySide6。请先运行：pip install -r requirements.txt"
    ) from exc

try:
    import vtk
    from vtk.util import numpy_support
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
except ImportError as exc:  # pragma: no cover - only used when GUI deps are missing.
    raise SystemExit(
        "缺少 vtk。请先运行：pip install -r requirements.txt"
    ) from exc


StageResult = Tuple[np.ndarray, dict, dict]


@dataclass
class LoadedVolume:
    volume: np.ndarray
    template: object
    source_name: str
    description: str
    is_mask: bool = False


def looks_like_binary_mask(volume: np.ndarray, path: Optional[Path] = None) -> bool:
    name_hint = path is not None and "mask" in path.name.lower()
    if volume.size == 0:
        return False
    finite = volume[np.isfinite(volume)]
    if finite.size == 0:
        return False
    vmin = float(np.min(finite))
    vmax = float(np.max(finite))
    if vmin >= 0.0 and vmax <= 1.0:
        return True
    if name_hint:
        values = np.unique(finite)
        return values.size <= 3 and set(values.astype(np.int64).tolist()).issubset({0, 1})
    return False


class VolumeLoader:
    label = "volume"

    def load(self) -> LoadedVolume:
        raise NotImplementedError


class DemoVolumeLoader(VolumeLoader):
    label = "demo"

    def __init__(self, seed: int):
        self.seed = seed

    def load(self) -> LoadedVolume:
        volume = create_demo_volume(seed=self.seed)
        return LoadedVolume(
            volume=volume.astype(np.float32, copy=False),
            template=None,
            source_name=f"demo_seed_{self.seed}",
            description=f"内置 Demo: shape={volume.shape}",
            is_mask=False,
        )


class FileVolumeLoader(VolumeLoader):
    label = "file"

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> LoadedVolume:
        volume, template = load_volume(self.path)
        if volume.ndim == 2:
            volume = volume[None, :, :]
        if volume.ndim != 3:
            raise ValueError("请输入二维或三维体数据；三维数组形状应为 (z, y, x)。")
        is_mask = looks_like_binary_mask(volume, self.path)
        return LoadedVolume(
            volume=volume.astype(np.float32, copy=False),
            template=template,
            source_name=self.path.stem,
            description=f"{self.path.name}\nshape={tuple(volume.shape)}\ntype={'mask' if is_mask else 'ct'}",
            is_mask=is_mask,
        )


class DicomSeriesLoader(VolumeLoader):
    label = "dicom"

    def __init__(self, folder: Path):
        self.folder = folder

    def load(self) -> LoadedVolume:
        if sitk is None:
            raise RuntimeError("加载 DICOM 序列需要安装 SimpleITK。")
        reader = sitk.ImageSeriesReader()
        series_ids = reader.GetGDCMSeriesIDs(str(self.folder))
        if not series_ids:
            raise RuntimeError("该文件夹中没有找到可读取的 DICOM 序列。")

        series_id = series_ids[0]
        file_names = reader.GetGDCMSeriesFileNames(str(self.folder), series_id)
        if not file_names:
            raise RuntimeError("DICOM 序列为空。")

        reader.SetFileNames(file_names)
        image = reader.Execute()
        volume = sitk.GetArrayFromImage(image).astype(np.float32, copy=False)
        return LoadedVolume(
            volume=volume,
            template=image,
            source_name=self.folder.name or "dicom_series",
            description=f"DICOM: {self.folder}\nseries={series_id}\nshape={tuple(volume.shape)}",
            is_mask=False,
        )


class LoadWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, loader: VolumeLoader):
        super().__init__()
        self.loader = loader

    def run(self) -> None:
        try:
            self.finished_ok.emit(self.loader.load())
        except Exception:
            self.failed.emit(traceback.format_exc())


def normalize_slice(image: np.ndarray, window_low: float, window_high: float) -> np.ndarray:
    image = image.astype(np.float32, copy=False)
    if window_high <= window_low:
        lo = float(np.min(image))
        hi = float(np.max(image))
    else:
        lo, hi = window_low, window_high
    if hi - lo < 1e-6:
        return np.zeros(image.shape, dtype=np.uint8)
    clipped = np.clip(image, lo, hi)
    return ((clipped - lo) * 255.0 / (hi - lo)).astype(np.uint8)


def make_overlay(
    volume_slice: np.ndarray,
    mask_slice: Optional[np.ndarray],
    window_low: float,
    window_high: float,
) -> QPixmap:
    gray = normalize_slice(volume_slice, window_low, window_high)
    rgb = np.repeat(gray[:, :, None], 3, axis=2)
    if mask_slice is not None:
        mask = mask_slice.astype(bool)
        rgb[mask, 0] = 255
        rgb[mask, 1] = (rgb[mask, 1] * 0.25).astype(np.uint8)
        rgb[mask, 2] = (rgb[mask, 2] * 0.25).astype(np.uint8)

    h, w, _ = rgb.shape
    image = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(image)


def get_oriented_slice(volume: np.ndarray, orientation: str, index: int) -> np.ndarray:
    if orientation == "axial":
        return volume[index, :, :]
    if orientation == "coronal":
        return volume[:, index, :]
    if orientation == "sagittal":
        return volume[:, :, index]
    raise ValueError(f"unknown orientation: {orientation}")


def orientation_size(volume: np.ndarray, orientation: str) -> int:
    if orientation == "axial":
        return int(volume.shape[0])
    if orientation == "coronal":
        return int(volume.shape[1])
    if orientation == "sagittal":
        return int(volume.shape[2])
    raise ValueError(f"unknown orientation: {orientation}")


class PipelineWorker(QThread):
    finished_ok = Signal(object, object, object)
    failed = Signal(str)

    def __init__(
        self,
        volume: np.ndarray,
        threshold_low: float,
        threshold_high: float,
        gradient_threshold: float,
        opening_radius: int,
        closing_radius: int,
        min_component_size: int,
    ):
        super().__init__()
        self.volume = volume
        self.threshold_low = threshold_low
        self.threshold_high = threshold_high
        self.gradient_threshold = gradient_threshold
        self.opening_radius = opening_radius
        self.closing_radius = closing_radius
        self.min_component_size = min_component_size

    def run(self) -> None:
        try:
            mask, stats, stages = run_pipeline(
                volume=self.volume,
                threshold_low=self.threshold_low,
                threshold_high=self.threshold_high,
                gradient_threshold=self.gradient_threshold,
                opening_radius=self.opening_radius,
                closing_radius=self.closing_radius,
                min_component_size=self.min_component_size,
            )
            self.finished_ok.emit(mask, stats, stages)
        except Exception:
            self.failed.emit(traceback.format_exc())


class VtkMaskView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.vtk_widget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtk_widget)

        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.06, 0.07, 0.08)
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.interactor.Initialize()
        self.show_placeholder()

    def clear(self) -> None:
        self.renderer.RemoveAllViewProps()

    def show_placeholder(self) -> None:
        self.clear()
        text = vtk.vtkTextActor()
        text.SetInput("加载体数据或运行滤波后显示 3D 视图")
        text.GetTextProperty().SetColor(0.85, 0.9, 0.95)
        text.GetTextProperty().SetFontSize(20)
        text.SetDisplayPosition(28, 32)
        self.renderer.AddViewProp(text)
        self.vtk_widget.GetRenderWindow().Render()

    def update_mask(self, mask: np.ndarray) -> None:
        self.update_scene(volume=None, mask=mask, mode="mask")

    def update_scene(self, volume: Optional[np.ndarray], mask: Optional[np.ndarray], mode: str) -> None:
        self.clear()
        has_volume = volume is not None
        has_mask = mask is not None and int(mask.sum()) > 0

        if mode in {"ct", "overlay"} and has_volume:
            self._add_ct_volume(volume)
        if mode in {"mask", "overlay"} and has_mask:
            self._add_mask_surface(mask)

        if (mode == "ct" and not has_volume) or (mode == "mask" and not has_mask) or (mode == "overlay" and not (has_volume or has_mask)):
            self.show_placeholder()
            return

        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()

    def _add_ct_volume(self, volume: np.ndarray) -> None:
        vol = np.ascontiguousarray(np.clip(volume, -1000, 3000).astype(np.int16))
        depth, height, width = vol.shape

        image_data = vtk.vtkImageData()
        image_data.SetDimensions(width, height, depth)
        image_data.SetSpacing(1.0, 1.0, 1.0)
        image_data.SetOrigin(0.0, 0.0, 0.0)

        vtk_array = numpy_support.numpy_to_vtk(
            num_array=vol.ravel(order="C"),
            deep=True,
            array_type=vtk.VTK_SHORT,
        )
        image_data.GetPointData().SetScalars(vtk_array)

        mapper = vtk.vtkSmartVolumeMapper()
        mapper.SetInputData(image_data)

        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(-800, 0.0, 0.0, 0.0)
        color.AddRGBPoint(80, 0.55, 0.55, 0.55)
        color.AddRGBPoint(300, 0.95, 0.78, 0.58)
        color.AddRGBPoint(1200, 1.0, 1.0, 1.0)

        opacity = vtk.vtkPiecewiseFunction()
        opacity.AddPoint(-800, 0.0)
        opacity.AddPoint(80, 0.0)
        opacity.AddPoint(300, 0.04)
        opacity.AddPoint(1200, 0.18)

        prop = vtk.vtkVolumeProperty()
        prop.SetColor(color)
        prop.SetScalarOpacity(opacity)
        prop.ShadeOn()
        prop.SetInterpolationTypeToLinear()

        vtk_volume = vtk.vtkVolume()
        vtk_volume.SetMapper(mapper)
        vtk_volume.SetProperty(prop)
        self.renderer.AddVolume(vtk_volume)

    def _add_mask_surface(self, mask: np.ndarray) -> None:
        if mask is None or int(mask.sum()) == 0:
            return

        mask = np.ascontiguousarray(mask.astype(np.uint8))
        depth, height, width = mask.shape

        image_data = vtk.vtkImageData()
        image_data.SetDimensions(width, height, depth)
        image_data.SetSpacing(1.0, 1.0, 1.0)
        image_data.SetOrigin(0.0, 0.0, 0.0)

        vtk_array = numpy_support.numpy_to_vtk(
            num_array=mask.ravel(order="C"),
            deep=True,
            array_type=vtk.VTK_UNSIGNED_CHAR,
        )
        vtk_array.SetName("mask")
        image_data.GetPointData().SetScalars(vtk_array)

        marching = vtk.vtkMarchingCubes()
        marching.SetInputData(image_data)
        marching.SetValue(0, 0.5)
        marching.ComputeNormalsOn()

        smoother = vtk.vtkWindowedSincPolyDataFilter()
        smoother.SetInputConnection(marching.GetOutputPort())
        smoother.SetNumberOfIterations(12)
        smoother.BoundarySmoothingOff()
        smoother.FeatureEdgeSmoothingOff()
        smoother.SetFeatureAngle(120.0)
        smoother.SetPassBand(0.08)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(smoother.GetOutputPort())
        mapper.ScalarVisibilityOff()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 0.18, 0.08)
        actor.GetProperty().SetOpacity(0.82)
        actor.GetProperty().SetSpecular(0.25)
        actor.GetProperty().SetSpecularPower(18)

        outline = vtk.vtkOutlineFilter()
        outline.SetInputData(image_data)
        outline_mapper = vtk.vtkPolyDataMapper()
        outline_mapper.SetInputConnection(outline.GetOutputPort())
        outline_actor = vtk.vtkActor()
        outline_actor.SetMapper(outline_mapper)
        outline_actor.GetProperty().SetColor(0.7, 0.78, 0.86)
        outline_actor.GetProperty().SetOpacity(0.55)

        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(width * 0.18, height * 0.18, depth * 0.18)

        self.renderer.AddActor(actor)
        self.renderer.AddActor(outline_actor)
        self.renderer.AddActor(axes)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CT 金属伪影掩码滤波器")
        self.resize(1480, 920)

        self.volume: Optional[np.ndarray] = None
        self.template = None
        self.source_name = "demo"
        self.mask: Optional[np.ndarray] = None
        self.stages = {}
        self.stats = {}
        self.worker: Optional[PipelineWorker] = None
        self.load_worker: Optional[LoadWorker] = None
        self.progress: Optional[QProgressDialog] = None
        self.slice_indices: Dict[str, int] = {"axial": 0, "coronal": 0, "sagittal": 0}

        self._build_actions()
        self._build_ui()
        self.start_load(DemoVolumeLoader(seed=1), "加载 Demo")

    def _build_actions(self) -> None:
        open_action = QAction("打开体数据", self)
        open_action.triggered.connect(self.open_volume)
        open_dicom_action = QAction("打开 DICOM 序列文件夹", self)
        open_dicom_action.triggered.connect(self.open_dicom_folder)
        save_action = QAction("保存掩码", self)
        save_action.triggered.connect(self.save_current_mask)
        demo_action = QAction("载入 Demo", self)
        demo_action.triggered.connect(lambda: self.start_load(DemoVolumeLoader(seed=1), "加载 Demo"))

        menu = self.menuBar().addMenu("文件")
        menu.addAction(open_action)
        menu.addAction(open_dicom_action)
        menu.addAction(save_action)
        menu.addSeparator()
        menu.addAction(demo_action)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        left = QWidget()
        left.setMinimumWidth(320)
        left.setMaximumWidth(390)
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(10)

        load_box = QGroupBox("数据")
        load_layout = QVBoxLayout(load_box)
        self.btn_open = QPushButton("打开 .npy/.nii/.mha/.mhd")
        self.btn_open.clicked.connect(self.open_volume)
        self.btn_open_dicom = QPushButton("打开 DICOM 序列文件夹")
        self.btn_open_dicom.clicked.connect(self.open_dicom_folder)
        self.btn_demo = QPushButton("载入内置 Demo")
        self.btn_demo.clicked.connect(lambda: self.start_load(DemoVolumeLoader(seed=1), "加载 Demo"))
        self.source_label = QLabel("未加载")
        self.source_label.setWordWrap(True)
        load_layout.addWidget(self.btn_open)
        load_layout.addWidget(self.btn_open_dicom)
        load_layout.addWidget(self.btn_demo)
        load_layout.addWidget(self.source_label)
        left_layout.addWidget(load_box)

        param_box = QGroupBox("滤波参数")
        form = QFormLayout(param_box)
        self.threshold_low = self._double_spin(0, 3000, 800, 10)
        self.threshold_high = self._double_spin(1000, 5000, 4000, 10)
        self.gradient_threshold = self._double_spin(0, 1000, 120, 5)
        self.opening_radius = self._spin(0, 5, 1)
        self.closing_radius = self._spin(0, 10, 2)
        self.min_component_size = self._spin(1, 5000, 50)
        form.addRow("阈值下限 HU", self.threshold_low)
        form.addRow("阈值上限 HU", self.threshold_high)
        form.addRow("梯度阈值", self.gradient_threshold)
        form.addRow("开运算半径", self.opening_radius)
        form.addRow("闭运算半径", self.closing_radius)
        form.addRow("最小连通域", self.min_component_size)
        left_layout.addWidget(param_box)

        self.btn_run = QPushButton("运行掩码滤波")
        self.btn_run.clicked.connect(self.run_filter)
        self.btn_save = QPushButton("保存最终掩码")
        self.btn_save.clicked.connect(self.save_current_mask)
        self.auto_preview = QCheckBox("参数变化后自动运行")
        self.auto_preview.setChecked(False)
        for widget in [
            self.threshold_low,
            self.threshold_high,
            self.gradient_threshold,
            self.opening_radius,
            self.closing_radius,
            self.min_component_size,
        ]:
            widget.valueChanged.connect(self.on_parameter_changed)
        left_layout.addWidget(self.btn_run)
        left_layout.addWidget(self.btn_save)
        left_layout.addWidget(self.auto_preview)

        slice_box = QGroupBox("切片浏览")
        slice_layout = QFormLayout(slice_box)
        self.slice_sliders = {}
        self.slice_labels = {}
        for orientation, title in [
            ("axial", "轴位 Z"),
            ("coronal", "冠状 Y"),
            ("sagittal", "矢状 X"),
        ]:
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            label = QLabel("0 / 0")
            slider = QSlider(Qt.Horizontal)
            slider.valueChanged.connect(lambda value, ori=orientation: self.on_slice_changed(ori, value))
            row_layout.addWidget(label)
            row_layout.addWidget(slider)
            self.slice_labels[orientation] = label
            self.slice_sliders[orientation] = slider
            slice_layout.addRow(title, row)
        left_layout.addWidget(slice_box)

        stats_box = QGroupBox("统计")
        stats_layout = QVBoxLayout(stats_box)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMinimumHeight(230)
        stats_layout.addWidget(self.stats_text)
        left_layout.addWidget(stats_box, stretch=1)

        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        top = QHBoxLayout()
        self.plane_views = {
            "axial": self._image_panel("轴位 Axial - 掩码叠加"),
            "coronal": self._image_panel("冠状 Coronal - 掩码叠加"),
            "sagittal": self._image_panel("矢状 Sagittal - 掩码叠加"),
        }
        for panel in self.plane_views.values():
            top.addWidget(panel["frame"])
        right_layout.addLayout(top, stretch=1)

        tabs = QTabWidget()
        stages_tab = QWidget()
        stages_layout = QHBoxLayout(stages_tab)
        self.threshold_view = self._image_panel("二值阈值")
        self.gradient_view = self._image_panel("梯度约束")
        self.closing_view = self._image_panel("闭运算后")
        stages_layout.addWidget(self.threshold_view["frame"])
        stages_layout.addWidget(self.gradient_view["frame"])
        stages_layout.addWidget(self.closing_view["frame"])
        tabs.addTab(stages_tab, "处理阶段")

        vtk_tab = QWidget()
        vtk_layout = QVBoxLayout(vtk_tab)
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("3D 显示模式"))
        self.render_mode = QComboBox()
        self.render_mode.addItem("掩码表面", "mask")
        self.render_mode.addItem("原始 CT 体渲染", "ct")
        self.render_mode.addItem("CT + 掩码叠加", "overlay")
        self.render_mode.currentIndexChanged.connect(self.refresh_3d_view)
        mode_row.addWidget(self.render_mode)
        mode_row.addStretch()
        vtk_layout.addLayout(mode_row)
        self.vtk_view = VtkMaskView()
        vtk_layout.addWidget(self.vtk_view)
        tabs.addTab(vtk_tab, "3D 掩码可视化")
        right_layout.addWidget(tabs, stretch=2)

        splitter.addWidget(right)
        splitter.setSizes([350, 1100])

        self.statusBar().showMessage("就绪")

    def _double_spin(self, minimum: float, maximum: float, value: float, step: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setSingleStep(step)
        spin.setDecimals(1)
        return spin

    def _spin(self, minimum: int, maximum: int, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        return spin

    def _image_panel(self, title: str) -> dict:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        label_title = QLabel(title)
        label_title.setAlignment(Qt.AlignCenter)
        label_title.setStyleSheet("font-weight:600;")
        image = QLabel("暂无图像")
        image.setAlignment(Qt.AlignCenter)
        image.setMinimumHeight(230)
        image.setStyleSheet("background:#101418;color:#cfd8e3;")
        layout.addWidget(label_title)
        layout.addWidget(image, stretch=1)
        return {"frame": frame, "image": image}

    def start_load(self, loader: VolumeLoader, title: str) -> None:
        self.set_controls_enabled(False)
        self.progress = QProgressDialog(f"{title}...", None, 0, 0, self)
        self.progress.setWindowTitle(title)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setMinimumDuration(0)
        self.progress.show()

        self.load_worker = LoadWorker(loader)
        self.load_worker.finished_ok.connect(self.on_volume_loaded)
        self.load_worker.failed.connect(self.on_load_failed)
        self.load_worker.start()

    def open_volume(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "打开 CT 体数据",
            "",
            "Volume (*.npy *.nii *.nii.gz *.mha *.mhd *.dcm *.png *.jpg *.jpeg);;All Files (*)",
        )
        if not path:
            return
        self.start_load(FileVolumeLoader(Path(path)), "加载体数据")

    def open_dicom_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择 DICOM 序列文件夹")
        if not folder:
            return
        self.start_load(DicomSeriesLoader(Path(folder)), "加载 DICOM")

    def on_volume_loaded(self, loaded: LoadedVolume) -> None:
        if self.progress is not None:
            self.progress.close()
            self.progress = None
        self.set_controls_enabled(True)
        self.volume = loaded.volume
        self.template = loaded.template
        self.source_name = loaded.source_name
        self.mask = loaded.volume.astype(np.uint8, copy=False) if loaded.is_mask else None
        self.stages = {"original": self.volume}
        self.stats = {}
        self.source_label.setText(loaded.description)
        self._reset_slice_sliders()
        self.refresh_2d_views()
        if loaded.is_mask:
            self.render_mode.setCurrentIndex(self.render_mode.findData("mask"))
        self.refresh_3d_view()
        if loaded.is_mask:
            self.stats_text.setPlainText("已识别为 0/1 掩码文件，可直接查看 2D 叠加和 3D 掩码表面。")
            self.statusBar().showMessage("掩码文件加载完成")
        else:
            self.stats_text.setPlainText("数据已加载。点击“运行掩码滤波”生成结果。")
            self.statusBar().showMessage("体数据加载完成")

    def on_load_failed(self, message: str) -> None:
        if self.progress is not None:
            self.progress.close()
            self.progress = None
        self.set_controls_enabled(True)
        self.statusBar().showMessage("加载失败")
        QMessageBox.critical(self, "加载失败", message)

    def set_controls_enabled(self, enabled: bool) -> None:
        for widget in [
            self.btn_open,
            self.btn_open_dicom,
            self.btn_demo,
            self.btn_run,
            self.btn_save,
        ]:
            widget.setEnabled(enabled)

    def _reset_slice_sliders(self) -> None:
        if self.volume is None:
            for slider in self.slice_sliders.values():
                slider.setRange(0, 0)
            return
        for orientation, slider in self.slice_sliders.items():
            size = orientation_size(self.volume, orientation)
            middle = max(0, size // 2)
            self.slice_indices[orientation] = middle
            slider.blockSignals(True)
            slider.setRange(0, max(0, size - 1))
            slider.setValue(middle)
            slider.blockSignals(False)
            self.slice_labels[orientation].setText(f"{middle} / {max(0, size - 1)}")

    def run_filter(self) -> None:
        if self.volume is None:
            QMessageBox.information(self, "提示", "请先加载体数据。")
            return

        self.btn_run.setEnabled(False)
        self.progress = QProgressDialog("正在运行滤波流程...", None, 0, 0, self)
        self.progress.setWindowTitle("滤波处理中")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setMinimumDuration(0)
        self.progress.show()
        self.statusBar().showMessage("正在运行滤波流程...")
        self.worker = PipelineWorker(
            volume=self.volume,
            threshold_low=float(self.threshold_low.value()),
            threshold_high=float(self.threshold_high.value()),
            gradient_threshold=float(self.gradient_threshold.value()),
            opening_radius=int(self.opening_radius.value()),
            closing_radius=int(self.closing_radius.value()),
            min_component_size=int(self.min_component_size.value()),
        )
        self.worker.finished_ok.connect(self.on_pipeline_finished)
        self.worker.failed.connect(self.on_pipeline_failed)
        self.worker.start()

    def on_pipeline_finished(self, mask: np.ndarray, stats: dict, stages: dict) -> None:
        if self.progress is not None:
            self.progress.close()
            self.progress = None
        self.mask = mask
        self.stats = stats
        self.stages = stages
        self.btn_run.setEnabled(True)
        self.refresh_2d_views()
        self.refresh_3d_view()
        self.stats_text.setPlainText(json.dumps(stats, ensure_ascii=False, indent=2))
        self.statusBar().showMessage("滤波完成")

    def on_pipeline_failed(self, message: str) -> None:
        if self.progress is not None:
            self.progress.close()
            self.progress = None
        self.btn_run.setEnabled(True)
        self.statusBar().showMessage("滤波失败")
        QMessageBox.critical(self, "滤波失败", message)

    def on_parameter_changed(self) -> None:
        if self.auto_preview.isChecked() and self.volume is not None and (self.worker is None or not self.worker.isRunning()):
            self.run_filter()

    def refresh_2d_views(self) -> None:
        if self.volume is None:
            return
        window_low = float(np.percentile(self.volume, 1))
        window_high = float(np.percentile(self.volume, 99))

        for orientation, panel in self.plane_views.items():
            idx = self.slice_indices[orientation]
            max_idx = orientation_size(self.volume, orientation) - 1
            self.slice_labels[orientation].setText(f"{idx} / {max_idx}")
            original = get_oriented_slice(self.volume, orientation, idx)
            final_mask = get_oriented_slice(self.mask, orientation, idx) if self.mask is not None else None
            self._set_pixmap(panel["image"], make_overlay(original, final_mask, window_low, window_high))

        z = self.slice_indices["axial"]
        axial_original = get_oriented_slice(self.volume, "axial", z)
        for view, stage in [
            (self.threshold_view, "threshold"),
            (self.gradient_view, "gradient"),
            (self.closing_view, "closing"),
        ]:
            stage_data = self.stages.get(stage)
            if stage_data is None:
                self._set_text(view["image"], "运行后显示")
            else:
                self._set_pixmap(view["image"], make_overlay(axial_original, stage_data[z], window_low, window_high))

    def on_slice_changed(self, orientation: str, value: int) -> None:
        self.slice_indices[orientation] = int(value)
        self.refresh_2d_views()

    def refresh_3d_view(self) -> None:
        mode = self.render_mode.currentData() if hasattr(self, "render_mode") else "mask"
        self.vtk_view.update_scene(self.volume, self.mask, mode)

    def _set_text(self, label: QLabel, text: str) -> None:
        label.setPixmap(QPixmap())
        label.setText(text)

    def _set_pixmap(self, label: QLabel, pixmap: QPixmap) -> None:
        label.setText("")
        scaled = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.refresh_2d_views()

    def save_current_mask(self) -> None:
        if self.mask is None:
            QMessageBox.information(self, "提示", "还没有生成最终掩码。")
            return

        default = f"{self.source_name}_metal_mask.npy"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "保存最终掩码",
            default,
            "NumPy (*.npy);;Medical Image (*.nii *.nii.gz *.mha *.mhd);;All Files (*)",
        )
        if not path:
            return
        try:
            save_mask(self.mask, Path(path), self.template)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", str(exc))
            return
        self.statusBar().showMessage(f"已保存：{path}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
