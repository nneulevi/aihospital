import os
from torch.utils.data import Dataset
from functools import lru_cache  # 🔥 Python 官方缓存

class BrainCTArtifactSegDataset(Dataset):
	def __init__(self, img_dir, mask_dir, file_list, transform=None):
		self.img_dir = img_dir
		self.mask_dir = mask_dir
		self.file_list = file_list
		self.transform = transform

	def __len__(self):
		return len(self.file_list)
	# --------------------------
	# 🔥 核心：Python 官方缓存（只缓存最近 1 条）
	# --------------------------
	@lru_cache(maxsize=1)  # 只保留最近一次读取的结果
	def _load_data(self, fname):
		""" 读取 + 预处理，交给 lru_cache 缓存 """
		img_path = os.path.join(self.img_dir, fname)
		mask_path = os.path.join(self.mask_dir, fname)

		data = {"image": img_path, "label": mask_path}
		if self.transform:
			data = self.transform(data)

		data["label"] = (data["label"] > 0).float()
		return data["image"], data["label"]

	def __getitem__(self, idx):
		fname = self.file_list[idx]
		# 从缓存 / 硬盘 读取
		img, label = self._load_data(fname)
		return img, label