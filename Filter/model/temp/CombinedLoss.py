import torch
import torch.nn as nn


# ========================
# Dice Loss
# ========================
class DiceLoss(nn.Module):
	def __init__(self, smooth=1e-6):
		super().__init__()
		self.smooth = smooth

	def forward(self, pred, target):
		pred = torch.sigmoid(pred)
		pred = pred.contiguous().view(-1)
		target = target.contiguous().view(-1)

		intersection = (pred * target).sum()
		union = pred.sum() + target.sum()
		return 1 - (2. * intersection + self.smooth) / (union + self.smooth)


# ========================
# 组合损失：返回 总loss + dice + bce
# ========================
class CombinedLoss(nn.Module):
	def __init__(self, pos_weight=None):
		super().__init__()
		self.dice = DiceLoss()

		# 🔥 核心修复：权重封顶在 30，绝对不能用 700！
		if pos_weight is not None:
			pos_weight = torch.clamp(pos_weight, max=1.0)  # 封顶
			self.bce = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
		else:
			self.bce = nn.BCEWithLogitsLoss()

	def forward(self, pred, target):
		loss_dice = self.dice(pred, target)
		loss_bce = self.bce(pred, target)

		# 🔥 小目标必须 Dice 主导！
		loss_total = 0.7 * loss_dice + 0.3 * loss_bce
		return loss_total, loss_dice.detach(), loss_bce.detach()


# ========================
# 工厂函数（统一调用）
# ========================
def get_loss_function(pos_weight=None):
	return CombinedLoss(pos_weight=pos_weight)