import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_agent import check_subject  # noqa: E402

PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "subjects_test.txt"
)


def main() -> None:
    print(f"{'expected':<10}{'matches':<10}{'conf':<7}{'subject / reason'}")
    print("-" * 100)
    for line in open(PATH, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        expected, _, subject = line.partition("|")
        expected, subject = expected.strip(), subject.strip()
        matches, confidence, reason = check_subject(subject)
        print(f"{expected:<10}{str(matches):<10}{confidence:<7}{subject}")
        print(f"{'':<10}{'':<10}{'':<7}-> {reason}")


if __name__ == "__main__":
    main()
