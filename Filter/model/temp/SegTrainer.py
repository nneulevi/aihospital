import torch
import torch.optim as optim
from tqdm import tqdm

from BrainArtifacts.loss.CombinedLoss import CombinedLoss
from BrainArtifacts.utils import MetricUtils

torch.backends.cudnn.benchmark = True


class SegTrainer:
	def __init__(self, model, train_loader, val_loader, device, pos_weight=None, lr=1e-3):
		self.model = model.to(device)
		self.train_loader = train_loader
		self.val_loader = val_loader
		self.device = device

		self.criterion = CombinedLoss(pos_weight=pos_weight)
		self.optimizer = optim.AdamW(model.parameters(), lr=lr)
		self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=50)
		self.best_dice = 0.0

	def train_one_epoch(self):
		self.model.train()
		total_loss = 0.0

		# ========== 新加：统计训练损失 ==========
		total_dice_loss = 0.0
		total_bce_loss = 0.0

		for img, mask in tqdm(self.train_loader, desc="Train"):
			img = img.to(self.device)
			mask = mask.to(self.device).float()

			self.optimizer.zero_grad()
			pred = self.model(img)
			loss, loss_dice, loss_bce = self.criterion(pred, mask)

			loss.backward()
			self.optimizer.step()

			total_loss += loss.item()
			# ========== 新加：累计 dice & bce ==========
			total_dice_loss += loss_dice.item()
			total_bce_loss += loss_bce.item()

		# 返回 平均总loss、平均dice、平均bce
		avg_loss = total_loss / len(self.train_loader)
		avg_dice = total_dice_loss / len(self.train_loader)
		avg_bce = total_bce_loss / len(self.train_loader)

		return avg_loss, avg_dice, avg_bce  # 🔥 这里返回三个！

	def val_one_epoch(self):
		self.model.eval()
		total_dice = 0.0
		total_iou = 0.0
		total_recall = 0.0

		with torch.no_grad():
			for img, mask in tqdm(self.val_loader, desc="Val"):
				img = img.to(self.device)
				mask = mask.to(self.device).float()
				pred = self.model(img)
				d, i, r = MetricUtils.MetricUtils.calculate_metrics(pred, mask)
				total_dice += d
				total_iou += i
				total_recall += r

		return (
			total_dice / len(self.val_loader),
			total_iou / len(self.val_loader),
			total_recall / len(self.val_loader)
		)

	def run(self, epochs=50):
		for epoch in range(epochs):
			print(f"\n==== Epoch {epoch + 1}/{epochs} ====")

			# 🔥 改这里：接收 train loss + dice loss + bce loss
			train_loss, train_dice_loss, train_bce_loss = self.train_one_epoch()

			val_dice, val_iou, val_recall = self.val_one_epoch()

			# 🔥 打印训练 Dice 损失
			print(
				f"Loss: {train_loss:.4f} | "
				f"Train Dice Loss: {train_dice_loss:.4f} | "  # <-- 你要的！
				f"Train BCE Loss: {train_bce_loss:.4f} | "
				f"Val Dice: {val_dice:.4f} | "
				f"Val IoU: {val_iou:.4f} | "
				f"Val Recall: {val_recall:.4f}"
			)

			if val_dice > self.best_dice:
				self.best_dice = val_dice
				torch.save(self.model.state_dict(), "best_3dunet.pth")
				print(f"✅ 最佳模型已保存！Dice: {val_dice:.4f}")

			self.scheduler.step()

		print(f"\n训练完成！最佳 Dice: {self.best_dice:.4f}")