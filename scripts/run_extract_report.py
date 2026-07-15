import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_agent import extract, classify  # noqa: E402

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset")

FILES = [
    "contract_001.txt",
    "spec_001.txt",
    "invoice_001.txt",
    "invoice_002.txt",
    "act_001.txt",
    "act_002.txt",
    "scan_ocr_001.txt",
]


def main() -> None:
    header = f"{'file':<20}{'amount':<14}{'date':<12}{'inn':<14}{'contractor':<20}{'doc_type':<10}{'conf':<6}"
    print(header)
    print("-" * len(header))
    for name in FILES:
        path = os.path.join(DATASET_DIR, name)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        fields = extract(text)
        doc_type, conf = classify(text)
        print(
            f"{name:<20}"
            f"{str(fields['amount']):<14}"
            f"{str(fields['date']):<12}"
            f"{str(fields['inn']):<14}"
            f"{str(fields['contractor']):<20}"
            f"{doc_type:<10}"
            f"{conf:<6}"
        )


if __name__ == "__main__":
    main()
