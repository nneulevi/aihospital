"""PySide6 desktop GUI for CT metal artifact mask annotation."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Callable, Optional

import numpy as np

try:
    import SimpleITK as sitk
except ImportError as exc:  # pragma: no cover - dependency guard.
    raise SystemExit("SimpleITK is required. Install it with: pip install SimpleITK") from exc

try:
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QImage, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSlider,
        QSpinBox,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - GUI dependency guard.
    raise SystemExit("PySide6 is required. Install it with: pip install PySide6") from exc

try:  # VTK is optional at import time.
    import vtk
    from vtk.util import numpy_support
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
except ImportError:  # pragma: no cover - optional GUI feature.
    vtk = None
    numpy_support = None
    QVTKRenderWindowInteractor = None

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from Detection.CTArtifactInfer import CTArtifactInfer  # noqa: E402


class Worker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[[], object]) -> None:
        super().__init__()
        self.fn = fn

    def run(self) -> None:
        try:
            self.finished_ok.emit(self.fn())
        except Exception:
            self.failed.emit(traceback.format_exc())


def ensure_3d_image(image):
    array = sitk.GetArrayFromImage(image)
    if array.ndim == 2:
        array = array[None, :, :]
        converted = sitk.GetImageFromArray(array)
        return converted
    if array.ndim != 3:
        raise ValueError(f"Expected 2D/3D image, got shape={array.shape}")
    return image


def normalize_slice(image: np.ndarray, low: float = -500.0, high: float = 1500.0) -> np.ndarray:
    image = np.clip(image.astype(np.float32, copy=False), low, high)
    return ((image - low) * 255.0 / max(high - low, 1e-6)).astype(np.uint8)


def draw_slice(volume_slice: np.ndarray, mask_slice: Optional[np.ndarray]) -> QPixmap:
    gray = normalize_slice(volume_slice)
    rgb = np.repeat(gray[:, :, None], 3, axis=2)
    if mask_slice is not None:
        mask = mask_slice.astype(bool)
        rgb[mask, 0] = 255
        rgb[mask, 1] = 80
        rgb[mask, 2] = 80
    h, w, _ = rgb.shape
    qimage = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(qimage)


class ArtifactAnnotationWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CT金属伪影掩码标注系统 - 3D U-Net")
        self.resize(1600, 900)

        self.ct_image = None
        self.artifact_mask = None
        self.volume_np: Optional[np.ndarray] = None
        self.mask_np: Optional[np.ndarray] = None
        self.slice_axial = 0
        self.slice_coronal = 0
        self.slice_sagittal = 0
        self.worker: Optional[Worker] = None

        try:
            self.infer = CTArtifactInfer()
            self.ai_available = True
        except Exception as exc:
            self.infer = None
            self.ai_available = False
            self.ai_error = str(exc)

        self._build_ui()
        self._set_loaded(False)

    def _build_ui(self) -> None:
        root = QSplitter(Qt.Horizontal)
        root.addWidget(self._build_controls())
        root.addWidget(self._build_views())
        root.setSizes([360, 1240])
        self.setCentralWidget(root)

    def _build_controls(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        load_group = QGroupBox("数据")
        load_layout = QVBoxLayout(load_group)
        self.btn_load_file = QPushButton("加载 CT 文件")
        self.btn_load_dicom = QPushButton("加载 DICOM 序列")
        self.btn_load_mask = QPushButton("加载外部 Mask")
        self.btn_save_mask = QPushButton("保存 Mask")
        for btn in [self.btn_load_file, self.btn_load_dicom, self.btn_load_mask, self.btn_save_mask]:
            load_layout.addWidget(btn)
        layout.addWidget(load_group)

        rule_group = QGroupBox("规则法掩码")
        form = QFormLayout(rule_group)
        self.th_low = QSpinBox()
        self.th_low.setRange(300, 1500)
        self.th_low.setValue(600)
        self.th_high = QSpinBox()
        self.th_high.setRange(2000, 5000)
        self.th_high.setValue(2800)
        self.grad_th = QSpinBox()
        self.grad_th.setRange(20, 1000)
        self.grad_th.setValue(100)
        self.open_r = QSpinBox()
        self.open_r.setRange(0, 5)
        self.open_r.setValue(1)
        self.close_r = QSpinBox()
        self.close_r.setRange(0, 10)
        self.close_r.setValue(2)
        self.min_area = QSpinBox()
        self.min_area.setRange(1, 5000)
        self.min_area.setValue(40)
        for label, widget in [
            ("阈值下限", self.th_low),
            ("阈值上限", self.th_high),
            ("梯度阈值", self.grad_th),
            ("开运算半径", self.open_r),
            ("闭运算半径", self.close_r),
            ("最小体素数", self.min_area),
        ]:
            form.addRow(label, widget)
        self.btn_rule_mask = QPushButton("生成规则 Mask")
        form.addRow(self.btn_rule_mask)
        layout.addWidget(rule_group)

        self.btn_ai = QPushButton("AI 自动分割")
        self.btn_ai.setEnabled(self.ai_available)
        layout.addWidget(self.btn_ai)
        if not self.ai_available:
            self.ai_status = QLabel("AI 未启用：未找到训练权重")
            self.ai_status.setWordWrap(True)
            layout.addWidget(self.ai_status)

        slice_group = QGroupBox("切片")
        slice_layout = QFormLayout(slice_group)
        self.slider_axial = QSlider(Qt.Horizontal)
        self.slider_coronal = QSlider(Qt.Horizontal)
        self.slider_sagittal = QSlider(Qt.Horizontal)
        slice_layout.addRow("Axial", self.slider_axial)
        slice_layout.addRow("Coronal", self.slider_coronal)
        slice_layout.addRow("Sagittal", self.slider_sagittal)
        layout.addWidget(slice_group)
        layout.addStretch(1)

        self.btn_load_file.clicked.connect(self.load_file_async)
        self.btn_load_dicom.clicked.connect(self.load_dicom_async)
        self.btn_load_mask.clicked.connect(self.load_mask_async)
        self.btn_save_mask.clicked.connect(self.save_mask)
        self.btn_rule_mask.clicked.connect(self.generate_mask_async)
        self.btn_ai.clicked.connect(self.ai_segment_async)
        self.slider_axial.valueChanged.connect(lambda v: self.on_slice_change("axial", v))
        self.slider_coronal.valueChanged.connect(lambda v: self.on_slice_change("coronal", v))
        self.slider_sagittal.valueChanged.connect(lambda v: self.on_slice_change("sagittal", v))
        return panel

    def _build_views(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        row = QHBoxLayout()
        self.view_axial = QLabel("Axial")
        self.view_coronal = QLabel("Coronal")
        self.view_sagittal = QLabel("Sagittal")
        for label in [self.view_axial, self.view_coronal, self.view_sagittal]:
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumSize(360, 300)
            row.addWidget(label)
        layout.addLayout(row)

        if vtk is not None and QVTKRenderWindowInteractor is not None:
            self.vtk_widget = QVTKRenderWindowInteractor(panel)
            self.vtk_renderer = vtk.vtkRenderer()
            self.vtk_widget.GetRenderWindow().AddRenderer(self.vtk_renderer)
            layout.addWidget(self.vtk_widget)
        else:
            self.vtk_widget = QLabel("VTK 3D 视图不可用：未安装 vtk")
            self.vtk_widget.setAlignment(Qt.AlignCenter)
            self.vtk_renderer = None
            layout.addWidget(self.vtk_widget)
        return panel

    def _set_loaded(self, loaded: bool) -> None:
        for widget in [
            self.btn_load_mask,
            self.btn_save_mask,
            self.btn_rule_mask,
            self.slider_axial,
            self.slider_coronal,
            self.slider_sagittal,
        ]:
            widget.setEnabled(loaded)
        self.btn_ai.setEnabled(loaded and self.ai_available)

    def run_async(self, fn: Callable[[], object], done: Callable[[object], None]) -> None:
        self.worker = Worker(fn)
        self.worker.finished_ok.connect(done)
        self.worker.failed.connect(self.show_error)
        self.worker.start()

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "错误", message)

    def load_file_async(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "加载 CT",
            "",
            "CT 文件 (*.nii *.nii.gz *.mhd *.mha *.nrrd *.dcm *.png *.jpg);;所有文件 (*)",
        )
        if not path:
            return
        self.run_async(lambda: ensure_3d_image(sitk.ReadImage(path)), self.set_ct_image)

    def load_dicom_async(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择 DICOM 序列文件夹")
        if not folder:
            return

        def task():
            reader = sitk.ImageSeriesReader()
            names = reader.GetGDCMSeriesFileNames(folder)
            if not names:
                raise RuntimeError("未找到可读取的 DICOM 序列。")
            reader.SetFileNames(names)
            return reader.Execute()

        self.run_async(task, self.set_ct_image)

    def set_ct_image(self, image) -> None:
        self.ct_image = image
        self.volume_np = sitk.GetArrayFromImage(image).astype(np.float32, copy=False)
        self.artifact_mask = None
        self.mask_np = None
        self.slice_axial = self.volume_np.shape[0] // 2
        self.slice_coronal = self.volume_np.shape[1] // 2
        self.slice_sagittal = self.volume_np.shape[2] // 2
        self.update_slider_ranges()
        self._set_loaded(True)
        self.refresh_all_views()
        self.render_3d_ct()

    def update_slider_ranges(self) -> None:
        assert self.volume_np is not None
        for slider, value, maximum in [
            (self.slider_axial, self.slice_axial, self.volume_np.shape[0] - 1),
            (self.slider_coronal, self.slice_coronal, self.volume_np.shape[1] - 1),
            (self.slider_sagittal, self.slice_sagittal, self.volume_np.shape[2] - 1),
        ]:
            slider.blockSignals(True)
            slider.setRange(0, max(0, int(maximum)))
            slider.setValue(int(value))
            slider.blockSignals(False)

    def load_mask_async(self) -> None:
        if self.ct_image is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "加载 Mask", "", "Mask (*.nii *.nii.gz *.mhd *.mha *.nrrd)")
        if not path:
            return

        def task():
            mask = sitk.ReadImage(path)
            if mask.GetSize() != self.ct_image.GetSize():
                raise ValueError("Mask 尺寸必须与 CT 一致。")
            arr = (sitk.GetArrayFromImage(mask) > 0).astype(np.uint8)
            out = sitk.GetImageFromArray(arr)
            out.CopyInformation(self.ct_image)
            return out

        self.run_async(task, self.set_mask_image)

    def set_mask_image(self, image) -> None:
        self.artifact_mask = image
        self.mask_np = sitk.GetArrayFromImage(image).astype(np.uint8, copy=False)
        self.refresh_all_views()
        self.render_3d_ct()

    def generate_mask_async(self) -> None:
        if self.ct_image is None:
            return
        self.run_async(self.generate_rule_mask, self.set_mask_image)

    def generate_rule_mask(self):
        img = self.ct_image
        tl, th = int(self.th_low.value()), int(self.th_high.value())
        gg = int(self.grad_th.value())
        ro, rc = int(self.open_r.value()), int(self.close_r.value())
        min_size = int(self.min_area.value())
        mask = sitk.BinaryThreshold(img, tl, th, 1, 0)
        grad = sitk.GradientMagnitude(sitk.Cast(img, sitk.sitkFloat32))
        gmask = sitk.BinaryThreshold(grad, gg, 999999, 1, 0)
        comb = sitk.And(mask, gmask)
        if ro > 0:
            comb = sitk.BinaryMorphologicalOpening(comb, [ro, ro, ro])
        if rc > 0:
            comb = sitk.BinaryMorphologicalClosing(comb, [rc, rc, rc])
        cc = sitk.ConnectedComponent(comb)
        stats = sitk.LabelShapeStatisticsImageFilter()
        stats.Execute(cc)
        final_np = np.zeros(sitk.GetArrayFromImage(comb).shape, dtype=np.uint8)
        cc_np = sitk.GetArrayFromImage(cc)
        for label in stats.GetLabels():
            if stats.GetNumberOfPixels(label) >= min_size:
                final_np[cc_np == label] = 1
        final = sitk.GetImageFromArray(final_np)
        final.CopyInformation(img)
        return final

    def ai_segment_async(self) -> None:
        if self.ct_image is None or self.infer is None:
            return
        self.run_async(lambda: self.infer.predict_from_sitk(self.ct_image), self.set_mask_image)

    def save_mask(self) -> None:
        if self.artifact_mask is None:
            QMessageBox.information(self, "提示", "当前没有可保存的 Mask。")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存 Mask", "artifact_mask.nii.gz", "NIfTI (*.nii *.nii.gz)")
        if path:
            sitk.WriteImage(self.artifact_mask, path)

    def on_slice_change(self, view_type: str, value: int) -> None:
        if self.volume_np is None:
            return
        if view_type == "axial":
            self.slice_axial = int(value)
        elif view_type == "coronal":
            self.slice_coronal = int(value)
        elif view_type == "sagittal":
            self.slice_sagittal = int(value)
        self.refresh_all_views()

    def refresh_all_views(self) -> None:
        if self.volume_np is None:
            return
        views = [
            (self.view_axial, self.volume_np[self.slice_axial], None if self.mask_np is None else self.mask_np[self.slice_axial]),
            (
                self.view_coronal,
                self.volume_np[:, self.slice_coronal, :],
                None if self.mask_np is None else self.mask_np[:, self.slice_coronal, :],
            ),
            (
                self.view_sagittal,
                self.volume_np[:, :, self.slice_sagittal],
                None if self.mask_np is None else self.mask_np[:, :, self.slice_sagittal],
            ),
        ]
        for label, image_slice, mask_slice in views:
            pixmap = draw_slice(image_slice, mask_slice)
            label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def render_3d_ct(self) -> None:
        if vtk is None or self.vtk_renderer is None or self.volume_np is None:
            return
        self.vtk_renderer.RemoveAllViewProps()
        image_data = vtk.vtkImageData()
        z, y, x = self.volume_np.shape
        image_data.SetDimensions(x, y, z)
        flat = np.ascontiguousarray(self.volume_np.astype(np.float32)).ravel(order="C")
        vtk_array = numpy_support.numpy_to_vtk(flat, deep=True, array_type=vtk.VTK_FLOAT)
        image_data.GetPointData().SetScalars(vtk_array)
        contour = vtk.vtkMarchingCubes()
        contour.SetInputData(image_data)
        contour.SetValue(0, 200)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(contour.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.85, 0.85, 0.85)
        actor.GetProperty().SetOpacity(0.25)
        self.vtk_renderer.AddActor(actor)
        self.vtk_renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()


def main() -> None:
    app = QApplication(sys.argv)
    window = ArtifactAnnotationWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

