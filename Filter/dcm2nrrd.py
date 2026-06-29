import SimpleITK as sitk

def dicom2nrrd(dicom_dir, output_nrrd):
    # 读取 DICOM
    reader = sitk.ImageSeriesReader()
    series_ids = reader.GetGDCMSeriesIDs(dicom_dir)
    dicom_names = reader.GetGDCMSeriesFileNames(dicom_dir, series_ids[0])
    reader.SetFileNames(dicom_names)
    img = reader.Execute()

    # 打印信息（方便你核对CT是否正确）
    print("图像大小:", img.GetSize())       # (512,512,100)
    print("体素间距:", img.GetSpacing())    # 层厚
    print("数据类型:", img.GetPixelIDTypeAsString())

    # 保存 NRRD（支持压缩，更小）
    sitk.WriteImage(img, output_nrrd, True)
    print(f"保存成功: {output_nrrd}")

# 使用
dicom2nrrd(r"../../Three/data/CT PLAIN THIN", r"data/out/brain_ct.nrrd")