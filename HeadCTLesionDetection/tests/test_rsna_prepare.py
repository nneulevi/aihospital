from __future__ import annotations

from pathlib import Path

from HeadCTLesionDetection.models.hemorrhage.prepare_rsna_dataset import (
    deterministic_split,
    load_rsna_labels,
    parse_rsna_label_id,
)


def test_parse_rsna_label_id() -> None:
    assert parse_rsna_label_id("ID_abc123_any") == ("ID_abc123", "any")
    assert parse_rsna_label_id("ID_abc123_subdural") == ("ID_abc123", "subdural")


def test_load_rsna_labels_groups_subtypes(tmp_path: Path) -> None:
    labels_csv = tmp_path / "stage_2_train.csv"
    labels_csv.write_text(
        "\n".join(
            [
                "ID,Label",
                "ID_case001_any,1",
                "ID_case001_epidural,0",
                "ID_case001_intraparenchymal,1",
                "ID_case001_intraventricular,0",
                "ID_case001_subarachnoid,0",
                "ID_case001_subdural,0",
                "ID_case002_any,0",
                "ID_case002_epidural,0",
                "ID_case002_intraparenchymal,0",
                "ID_case002_intraventricular,0",
                "ID_case002_subarachnoid,0",
                "ID_case002_subdural,0",
            ]
        ),
        encoding="utf-8",
    )

    records = load_rsna_labels(labels_csv)

    assert len(records) == 2
    assert records[0].image_id == "ID_case001"
    assert records[0].hemorrhage == 1
    assert records[0].labels["intraparenchymal"] == 1
    assert records[1].image_id == "ID_case002"
    assert records[1].hemorrhage == 0


def test_deterministic_split_is_stable() -> None:
    first = deterministic_split("ID_case001", val_fraction=0.1, test_fraction=0.1, seed=2026)
    second = deterministic_split("ID_case001", val_fraction=0.1, test_fraction=0.1, seed=2026)
    assert first == second
    assert first in {"train", "val", "test"}
