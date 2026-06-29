import torch

# ========================
# 🔥 模型评估指标工具类
# 包含：Dice、IoU、Recall (二分类分割专用)
# ========================
class MetricUtils:
    @staticmethod
    def calculate_metrics(pred_logits, target, threshold=0.35):
        """
        静态方法：计算分割任务核心指标
        :param pred_logits: 模型原始输出（未经过sigmoid）
        :param target: 真实标签
        :param threshold: 二值化阈值
        :return: dice, iou, recall
        """
        # 1. 预测值经过sigmoid + 阈值二值化
        pred = (torch.sigmoid(pred_logits) > threshold).float()

        # 2. 展平为1维，方便计算交集、并集
        pred = pred.contiguous().view(-1)
        target = target.contiguous().view(-1)

        # 3. 计算交集、预测和、标签和
        intersection = (pred * target).sum().item()
        sum_pred = pred.sum().item()
        sum_target = target.sum().item()

        # 4. 计算各项指标（加平滑项防止除0）
        dice = (2 * intersection + 1e-6) / (sum_pred + sum_target + 1e-6)
        iou = (intersection + 1e-6) / (sum_pred + sum_target - intersection + 1e-6)
        recall = (intersection + 1e-6) / (sum_target + 1e-6)

        return dice, iou, recall