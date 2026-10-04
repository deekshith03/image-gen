"""Dataset integrity check: labels, splits, hashes, ground-truth derivation, judge prompt version, committed results."""

from adgen.golden.integrity import verify


def main() -> None:
    report = verify()
    for note in report.notes:
        print(f"· {note}")
    for defect in report.defects:
        print(f"✗ {defect}")
    print("ZERO DEFECTS" if not report.defects else f"{len(report.defects)} DEFECT(S)")
    raise SystemExit(1 if report.defects else 0)


if __name__ == "__main__":
    main()
