import json
import subprocess
from pathlib import Path
from typing import Optional

PS_SCRIPT = Path(__file__).parent.parent / "boot_posture.ps1"

class SnapshotError(Exception):
    """Raised when the extraction layer can't produce a usable snapshot."""


def normalize_tpm_version(raw: Optional[str]) -> Optional[float]:
    """Extract the TPM spec version from Win32_Tpm's SpecVersion string.

    Real observed input: "2.0, 0, 1.38" -- spec version, then revision
    metadata we don't care about.

    Returns None when the version can't be determined, for any reason.
    """
    if not raw:
        return None
    first = raw.split(",")[0].strip()
    try:
        return float(first)
    except ValueError:
        return None


def read_snapshot() -> dict:
    """Run the PowerShell extraction script and return the parsed snapshot."""
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", str(PS_SCRIPT),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise SnapshotError("PowerShell not found — is this Windows?") from exc
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
