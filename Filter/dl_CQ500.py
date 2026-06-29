from torchvtk.datasets import TorchDataset

# 自动下载+解压+转TorchDataset
# 保存到 ~/.torchvtk/CQ500
if __name__ == '__main__':
    ds = TorchDataset.CQ500(
    tvtk_ds_path='./CQ500',
    num_workers=10)
