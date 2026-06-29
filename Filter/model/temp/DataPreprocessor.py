from monai.transforms import (
	Compose, LoadImaged, EnsureChannelFirstd, ScaleIntensityd,
	Orientationd, Spacingd, ToTensord,
	RandFlipd, RandRotate90d, RandZoomd, RandAffined,
	SpatialPadd, CenterSpatialCropD
)
import os
from tqdm import tqdm

from monai.transforms import Compose, LoadImaged, EnsureChannelFirstd


# ==============================================
# 🔥 封装好的【数据预处理类】全能版
# 包含：增强、缓存、尺寸统一、坐标系统一、体素间距统一
# ==============================================
class DataPreprocessor:
	def __init__(self, datapath = '', pixdim=(2.0, 2.0, 2.5)):
		# 统一输出尺寸 (D, H, W)
		#self.target_shape = self.get_max_shape(datapath)
		# 自动获取最大形状
		max_shape = self.get_max_shape(datapath)

		# 🔥 核心：最大尺寸整体缩小1/4（向下取整）
		self.target_shape = (
			max_shape[0] // 4,
			max_shape[1] // 4,
			max_shape[2] // 4
		)
		print(f"✅ 最终统一尺寸（缩小一半）: {self.target_shape}")
		# 统一体素间距
		self.pixdim = pixdim

	def get_max_shape(self, root_dir, suffix=".nii.gz"):
		"""
		自动扫描数据集根目录下的所有 NIfTI 图像，返回全局最大 (D, H, W)
		:param root_dir: 图像文件夹根目录
		:param suffix: 文件后缀
		:return: max_shape = (max_D, max_H, max_W)
		"""
		# 读取所有文件
		files = sorted([f for f in os.listdir(root_dir) if f.endswith(suffix)])

		# 加载器（只读取数据，不做其他处理）
		loader = Compose([
			LoadImaged(keys=["image"]),
			EnsureChannelFirstd(keys=["image"])
		])

		max_d = max_h = max_w = 0

		# 遍历计算最大尺寸
		print(f"\n📏 正在扫描数据集：{root_dir}")
		for fname in tqdm(files, desc="计算最大形状"):
			path = os.path.join(root_dir, fname)
			data = loader({"image": path})
			_, w, h, d = data["image"].shape

			max_d = max(max_d, d)
			max_h = max(max_h, h)
			max_w = max(max_w, w)

		max_shape = (max_w, max_h, max_d)
		print(f"✅ 数据集最大尺寸 (W, H, D) → {max_shape}")
		return max_shape

	# --------------------------
	# 训练集变换：增强 + 预处理
	# --------------------------
	def get_train_transform(self):
		return Compose([
			LoadImaged(keys=["image", "label"]),
			EnsureChannelFirstd(keys=["image", "label"]),
			ScaleIntensityd(keys=["image"]),
			Orientationd(keys=["image", "label"], axcodes="RAS"),
			Spacingd(keys=["image", "label"], pixdim=self.pixdim, mode=("bilinear", "nearest")),
			# 尺寸统一：深度填补 + 中心裁剪
			SpatialPadd(keys=["image", "label"], spatial_size=self.target_shape),
			CenterSpatialCropD(keys=["image", "label"], roi_size=self.target_shape),

			# 🔥 数据增强（训练专用）
			RandFlipd(keys=["image", "label"], spatial_axis=[0, 1, 2], prob=0.5),
			RandRotate90d(keys=["image", "label"], spatial_axes=(0, 1), prob=0.5),
			RandZoomd(keys=["image", "label"], min_zoom=0.9, max_zoom=1.1, prob=0.5),
			RandAffined(keys=["image", "label"], rotate_range=(-10, 10), shear_range=(-5, 5), translate_range=5,
						prob=0.3),

			ToTensord(keys=["image", "label"]),
		])

	# --------------------------
	# 验证集变换：无增强
	# --------------------------
	def get_val_transform(self):
		return Compose([
			LoadImaged(keys=["image", "label"]),
			EnsureChannelFirstd(keys=["image", "label"]),
			ScaleIntensityd(keys=["image"]),
			Orientationd(keys=["image", "label"], axcodes="RAS"),
			Spacingd(keys=["image", "label"], pixdim=self.pixdim, mode=("bilinear", "nearest")),

			# 尺寸统一
			SpatialPadd(keys=["image", "label"], spatial_size=self.target_shape),
			CenterSpatialCropD(keys=["image", "label"], roi_size=self.target_shape),

			ToTensord(keys=["image", "label"]),
		])

	# --------------------------
	# 测试集 / 推理专用：只处理 image（重要！）
	# --------------------------
	def get_test_transform(self):
		return Compose([
			LoadImaged(keys=["image"]),
			EnsureChannelFirstd(keys=["image"]),
			ScaleIntensityd(keys=["image"]),
			Orientationd(keys=["image"], axcodes="RAS", labels=None),
			Spacingd(keys=["image"], pixdim=self.pixdim, mode="bilinear"),
			SpatialPadd(keys=["image"], spatial_size=self.target_shape),
			CenterSpatialCropD(keys=["image"], roi_size=self.target_shape),

			# 🔥 关键修复：加上 track_meta=True
			ToTensord(keys=["image"], track_meta=True),
		])