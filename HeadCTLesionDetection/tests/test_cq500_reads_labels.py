from __future__ import annotations

from pathlib import Path

from HeadCTLesionDetection.models.hemorrhage.prepare_cq500_reads_labels import build_labels


def test_build_labels_uses_majority_vote_for_any_hemorrhage(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "\n".join(
            [
                "case_id,image_path,split,status",
                "CQ500CT200,images/CQ500CT200.nii.gz,val,converted",
                "CQ500CT201,images/CQ500CT201.nii.gz,val,converted",
            ]
        ),
        encoding="utf-8",
    )
    reads = tmp_path / "reads.csv"
    reads.write_text(
        "\n".join(
            [
                "name,R1:ICH,R2:ICH,R3:ICH,R1:IPH,R2:IPH,R3:IPH",
                "CQ500-CT-200,1,1,0,1,0,0",
                "CQ500-CT-201,0,0,1,0,0,0",
            ]
        ),
        encoding="utf-8",
    )

    rows = build_labels(manifest, reads)

    assert rows[0]["case_id"] == "CQ500CT200"
    assert rows[0]["hemorrhage"] == 1
    assert rows[0]["intraparenchymal"] == 0
    assert rows[1]["case_id"] == "CQ500CT201"
    assert rows[1]["hemorrhage"] == 0
