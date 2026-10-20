"""Generate deterministic synthetic PDF inputs for the Golden Demo."""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.pdfgen import canvas


DOCUMENTS = {
    "golden-pid.pdf": (
        "P&ID DESIGN BASIS",
        "Equipment tag XV-101 is an emergency isolation valve.",
        "The specified fail position for XV-101 is Fail Closed (FC).",
        "The stated design pressure for line 10-P-101 is 12 bar.",
        "The emergency shutdown delay is 3 seconds.",
        "All extracted information is advisory until Human engineering review.",
    ),
    "golden-control-narrative.pdf": (
        "CONTROL NARRATIVE",
        "Equipment tag XV-101 is an emergency isolation valve.",
        "The specified fail position for XV-101 is Fail Open (FO).",
        "The stated design pressure for line 10-P-101 is 15 bar.",
        "The emergency shutdown delay is 5 seconds.",
        "This intentional discrepancy requires Human engineering disposition.",
    ),
}


def generate(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for filename, lines in DOCUMENTS.items():
        target = destination / filename
        pdf = canvas.Canvas(str(target), pagesize=(612, 792), invariant=1)
        text = pdf.beginText(54, 738)
        text.setFont("Helvetica", 11)
        for line in lines:
            text.textLine(line)
        pdf.drawText(text)
        pdf.showPage()
        pdf.save()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    resolved = args.destination.resolve()
    if not str(resolved).startswith(("/tmp/", "/private/tmp/")):
        raise RuntimeError("Golden Demo documents must be generated below /tmp")
    generate(resolved)


if __name__ == "__main__":
    main()
