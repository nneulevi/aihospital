import os
import torch
from torch.utils.data import DataLoader, WeightedRandomSampler
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# MONAI
from monai.transforms import LoadImaged

from BrainArtifacts.datasets.DataPreprocessor import DataPreprocessor
# 自定义模块
from datasets.BrainCTArtifactSegDataset import BrainCTArtifactSegDataset
from utils.WeightUtils import WeightUtils
from trainer.SegTrainer import SegTrainer
#from model.UNet3D import UNet3D
#from model.DepthwiseUNet3D import UNet3D
from model.ResidualUNet3D import UNet3D

# ========================
# 全局配置
# ========================
IMG_DIR = "./images"
MASK_DIR = "./masks"
BATCH_SIZE = 1
EPOCHS = 50
LR = 1e-3
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ========================
# 🔥 主入口：创建分割数据加载器（含均衡采样）
# ========================
def create_seg_dataloaders(img_dir, mask_dir, batch_size=1, num_workers=0):
    # 1. 读取所有文件
    all_files = sorted([f for f in os.listdir(img_dir) if f.endswith(".nii.gz")])
    print(f"✅ 总样本数：{len(all_files)}")

    # 2. 划分训练/验证
    train_files, val_files = train_test_split(all_files, test_size=0.2, random_state=42)

    # 获取数据集
    preData = DataPreprocessor(datapath=img_dir)
    # 3. 数据增强
    trainTransform = preData.get_train_transform()
    valTransform = preData.get_val_transform()


    # 4. 创建数据集
    train_ds = BrainCTArtifactSegDataset(img_dir, mask_dir, train_files, trainTransform)
    val_ds = BrainCTArtifactSegDataset(img_dir, mask_dir, val_files, valTransform)

    # 5. 困难样本均衡采样（含病灶加权）
    weights = []
    for f in train_files:
        mask_path = os.path.join(mask_dir, f)
        mask = LoadImaged(keys=["label"])({"label": mask_path})["label"]
        pos = (mask > 0).sum().item()
        w = 5.0 if pos > 0 else 1.0
        weights.append(w)

    sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)

    # 6. 创建加载器
    train_loader = DataLoader(
        train_ds, batch_size=batch_size, sampler=sampler, num_workers=num_workers
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )

    # 7. 静态调用计算类别权重
    pos_weight = WeightUtils.compute_class_weights(mask_dir, train_files, device=DEVICE)

    return train_loader, val_loader, pos_weight

# ========================
# 🔥 主训练流程
# ========================
def main():
    print("=" * 50)
    print("3D UNet 脑部CT伪影分割训练")
    print(f"设备：{DEVICE}")
    print("=" * 50)
    ctPath = r'D:\pythonObj\dLink_medical_ai\BrainArtifacts\datasets\CT'
    maskPath = r'D:\pythonObj\dLink_medical_ai\BrainArtifacts\datasets\mask'

    train_loader, val_loader, pos_weight = create_seg_dataloaders(ctPath, maskPath, 1, 0)

    # 2. 初始化模型
    model = UNet3D()

    # 3. 初始化训练器
    trainer = SegTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        device=DEVICE,
        pos_weight=pos_weight,
        lr=LR
    )
    trainer.run()

# ========================
# 主入口执行
# ========================
if __name__ == "__main__":
    main()