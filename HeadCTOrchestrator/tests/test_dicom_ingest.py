from __future__ import annotations

from pathlib import Path

import pytest

from HeadCTOrchestrator.dicom_ingest import is_supported_ct_upload, normalize_saved_upload


def test_supported_ct_upload_extensions() -> None:
    assert is_supported_ct_upload("case.nii")
    assert is_supported_ct_upload("case.nii.gz")
    assert is_supported_ct_upload("slice.dcm")
    assert is_supported_ct_upload("slice.dicom")
    assert is_supported_ct_upload("rsna_series.zip")
    assert not is_supported_ct_upload("notes.txt")


def test_normalize_single_dicom_to_nifti(tmp_path: Path) -> None:
    sitk = pytest.importorskip("SimpleITK")

    dicom_path = tmp_path / "slice.dcm"
    image = sitk.Image([16, 16], sitk.sitkInt16)
    image = image + 42
    image.SetSpacing((0.7, 0.7))
    image.SetMetaData("0008|0060", "CT")
    image.SetMetaData("0010|0010", "ANON")
    image.SetMetaData("0010|0020", "ANON-001")
    image.SetMetaData("0020|000d", "1.2.826.0.1.3680043.10.1000.1")
    image.SetMetaData("0020|000e", "1.2.826.0.1.3680043.10.1000.2")
    image.SetMetaData("0020|0013", "1")

    writer = sitk.ImageFileWriter()
    writer.SetImageIO("GDCMImageIO")
    writer.SetFileName(str(dicom_path))
    writer.Execute(image)

    output_dir = tmp_path / "task"
    normalized = normalize_saved_upload("slice.dcm", dicom_path, output_dir, "application/dicom")

    assert normalized.original_format == "dicom_file"
    assert normalized.input_filename == "input.nii.gz"
    assert normalized.input_path.exists()
    assert normalized.metadata["source_format"] == "dicom_file"
    assert normalized.metadata["normalization"] == "dicom_file_to_nifti"

    converted = sitk.ReadImage(str(normalized.input_path))
    assert list(converted.GetSize()) == [16, 16, 1]
