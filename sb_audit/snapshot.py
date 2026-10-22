import json
import math
import os
import subprocess
from pathlib import Path
from typing import Optional
from .elevation import is_admin

PS_SCRIPT = Path(__file__).parent.parent / "boot_posture.ps1"

# Fully-qualified path: never resolve "powershell" via the process search order
POWERSHELL = os.path.join(
    os.environ.get("SystemRoot", r"C:\Windows"),
    "System32", "WindowsPowerShell", "v1.0", "powershell.exe",
)


class SnapshotError(Exception):
    """Raised when the extraction can't produce a usable snapshot."""


def normalize_tpm_version(raw: Optional[str]) -> Optional[float]:
    """Extract the TPM spec version from Win32_Tpm's SpecVersion string.

    Returns None when the version can't be determined, for any reason.
    """
    if not raw:
        return None
    first = raw.split(",")[0].strip()
    try:
        value = float(first)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def read_snapshot() -> dict:
    """Run the PowerShell extraction script and return the snapshot"""
    if not is_admin():
        raise SnapshotError(
            "This tool needs administrator rights to read Secure Boot and "
            "TPM state.\nRight-click PowerShell and choose "
            "'Run as administrator', then try again."
        )
    try:
        result = subprocess.run(
            [
                POWERSHELL,
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", str(PS_SCRIPT),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise SnapshotError("PowerShell not found. Is this Windows?") from exc
    except subprocess.TimeoutExpired as exc:
        raise SnapshotError("Extraction timed out after 60s.") from exc

    if result.returncode != 0:
        raise SnapshotError(
            f"Extraction script failed (exit {result.returncode}): "
            f"{result.stderr.strip()}"
        )

    try:
        snapshot = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SnapshotError(
            f"Extraction returned invalid JSON: {result.stdout[:200]!r}"
        ) from exc

    snapshot["tpmSpecVersion"] = normalize_tpm_version(
        snapshot.get("tpmSpecVersionRaw")
    )
    return snapshot