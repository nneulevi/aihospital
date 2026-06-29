import torch
import os
from tqdm import tqdm
from monai.transforms import LoadImaged

class WeightUtils:
    @staticmethod
    def compute_class_weights(mask_dir, train_files, device=None):
        """
        静态方法：计算二分类类别平衡权重
        直接 WeightUtils.compute_class_weights(...) 调用
        """
        total_pos = 0
        total_neg = 0

        for fname in tqdm(train_files, desc="计算类别平衡权重"):
            path = os.path.join(mask_dir, fname)
            mask = LoadImaged(keys=["label"])({"label": path})["label"]
            mask = (mask > 0).float()

            pos = mask.sum().item()
            neg = (1 - mask).sum().item()

            total_pos += pos
            total_neg += neg

        pos_weight = total_neg / (total_pos + 1e-8)
        print(f"✅ 正样本平衡权重: {pos_weight:.4f}")

        pos_weight_tensor = torch.tensor([pos_weight], dtype=torch.float32)
        if device is not None:
            pos_weight_tensor = pos_weight_tensor.to(device)

        return pos_weight_tensor