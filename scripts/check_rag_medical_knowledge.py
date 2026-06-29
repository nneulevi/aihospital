from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from HeadCTOrchestrator.rag.retriever import retrieve_context


CHECKS = [
    (
        "middle cerebral artery hyperdense sign early ischemic stroke gray white differentiation CT",
        "early_ischemic_stroke_ct_v1",
    ),
    (
        "depressed skull fracture bone window pneumocephalus traumatic head CT",
        "skull_fracture_trauma_ct_v1",
    ),
    (
        "hydrocephalus fourth ventricle compression midline shift mass effect head CT",
        "hydrocephalus_mass_effect_ct_v1",
    ),
    (
        "postoperative titanium plate metal artifact head CT limitation",
        "postoperative_artifact_ct_v1",
    ),
]


def main() -> int:
    results = []
    for query, expected_source in CHECKS:
        retrieved = retrieve_context(query, filter_tags=None)
        sources = [source.get("source_id") for source in retrieved.get("sources", [])]
        results.append(
            {
                "query": query,
                "expected_source": expected_source,
                "status": retrieved.get("status"),
                "sources": sources[:6],
                "matched": expected_source in sources,
                "recall_count": retrieved.get("recall_count"),
            }
        )
    print(json.dumps({"status": "success", "results": results}, ensure_ascii=True, indent=2))
    return 0 if all(item["matched"] for item in results) else 1


if __name__ == "__main__":
    sys.exit(main())
