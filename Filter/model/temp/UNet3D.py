import torch
import torch.nn as nn
import torch.nn.functional as F
# ============================
# 🔥 使用 torchsummary 查看模型结构
# ============================
from torchsummary import summary

class DoubleConv3D(nn.Module):
	def __init__(self, in_ch, out_ch):
		super().__init__()
		self.conv = nn.Sequential(
			nn.Conv3d(in_ch, out_ch, 3, padding=1),
			nn.BatchNorm3d(out_ch),
			nn.ReLU(inplace=True),
			nn.Conv3d(out_ch, out_ch, 3, padding=1),
			nn.BatchNorm3d(out_ch),
			nn.ReLU(inplace=True)
		)

	def forward(self, x):
		return self.conv(x)


class Down3D(nn.Module):
	def __init__(self, in_ch, out_ch):
		super().__init__()
		self.pool = nn.MaxPool3d(2)
		self.conv = DoubleConv3D(in_ch, out_ch)

	def forward(self, x):
		return self.conv(self.pool(x))


class Up3D(nn.Module):
	def __init__(self, in_ch, out_ch):
		super().__init__()
		self.up = nn.ConvTranspose3d(in_ch, in_ch // 2, kernel_size=2, stride=2)
		self.conv = DoubleConv3D(in_ch, out_ch)

	def forward(self, x1, x2):
		x1 = self.up(x1)
		diffD = x2.size()[2] - x1.size()[2]
		diffH = x2.size()[3] - x1.size()[3]
		diffW = x2.size()[4] - x1.size()[4]
		x1 = F.pad(x1, [diffW // 2, diffW - diffW // 2, diffH // 2, diffH - diffH // 2, diffD // 2, diffD - diffD // 2])
		x = torch.cat([x2, x1], dim=1)
		return self.conv(x)


class UNet3D(nn.Module):
	def __init__(self):
		super().__init__()
		self.inc = DoubleConv3D(1, 16)
		self.down1 = Down3D(16, 32)
		self.down2 = Down3D(32, 64)
		self.down3 = Down3D(64, 128)
		self.up1 = Up3D(128, 64)
		self.up2 = Up3D(64, 32)
		self.up3 = Up3D(32, 16)
		self.outc = nn.Conv3d(16, 1, kernel_size=1)

	def forward(self, x):
		x1 = self.inc(x)
		x2 = self.down1(x1)
		x3 = self.down2(x2)
		x4 = self.down3(x3)
		x = self.up1(x4, x3)
		x = self.up2(x, x2)
		x = self.up3(x, x1)
		return self.outc(x)

if __name__ == '__main__':
	# 先判断设备
	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
	# 初始化模型
	model = UNet3D().to(device)

	# 1. 打印模型整体结构
	print("="*50)
	print("📦 模型结构")
	print("="*50)
	#print(model)
	# 3D 输入格式：(in_channels, D, H, W)
	# 你可以改成你的数据尺寸，比如 (1, 64, 64, 64)
	summary(model, input_size=(1, 64, 64, 64))

	# 2. 计算并打印总参数量
	total_params = sum(p.numel() for p in model.parameters())
	trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

	print("\n" + "="*50)
	print("📊 参数量统计")
	print("="*50)
	print(f"总参数量      : {total_params:,}")
	print(f"可训练参数量  : {trainable_params:,}")
