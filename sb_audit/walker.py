from dataclasses import dataclass
from enum import Enum
from typing import Optional


class State(Enum):
    PASS = "pass"
    FAIL = "fail"
    LOCKED = "locked"
    UNKNOWN = "unknown"


@dataclass
class Finding:
    name: str
    state: State
    action: Optional[str] = None


def walk_boot_path(snap: dict) -> list[Finding]:
    """Ordered chain: each step gates the next."""
    findings = []

    # Secure Boot being on proves the entire chain beneath it.
    if snap.get("secureBoot") is True:
        return [
            Finding("Firmware is in UEFI mode", State.PASS),
            Finding("Secure Boot keys enrolled", State.PASS),
            Finding("Secure Boot enabled", State.PASS),
        ]

    # Step 1 -- firmware mode
    fw = snap.get("firmwareType")
    if fw == "Uefi":
        step1 = Finding("Firmware is in UEFI mode", State.PASS)
    elif fw == "Legacy":
        step1 = Finding(
            "Firmware is in UEFI mode", State.FAIL,
            "Your PC is booting the old way. Convert the disk with mbr2gpt, "
            "then switch the firmware from Legacy/CSM to UEFI.",
        )
    else:
        step1 = Finding("Firmware is in UEFI mode", State.UNKNOWN,
                        "Could not read the firmware mode.")
    findings.append(step1)

    # Step 2 -- keys enrolled
    if step1.state is not State.PASS:
        findings.append(Finding("Secure Boot keys enrolled", State.LOCKED,
                                "Locked until the firmware is in UEFI mode."))
    else:
        sm = snap.get("setupMode")
        if sm == 0:
            findings.append(Finding("Secure Boot keys enrolled", State.PASS))
        elif sm == 1:
            findings.append(Finding(
                "Secure Boot keys enrolled", State.FAIL,
                "Your PC is in Setup Mode. In the firmware menu, restore or "
                "enroll the default Secure Boot keys.",
            ))
        else:
            findings.append(Finding("Secure Boot keys enrolled", State.UNKNOWN,
                                    "Could not read the Secure Boot key state."))

    # Step 3 -- Secure Boot itself
    if findings[-1].state is not State.PASS:
        findings.append(Finding("Secure Boot enabled", State.LOCKED,
                                "Locked until the keys above are enrolled."))
    else:
        sb = snap.get("secureBoot")
        if sb is False:
            findings.append(Finding("Secure Boot enabled", State.FAIL,
                                    "Turn on Secure Boot in the firmware menu."))
        else:
            findings.append(Finding("Secure Boot enabled", State.UNKNOWN,
                                    "Could not read the Secure Boot state."))

    return findings


def walk_checklist(snap: dict) -> list[Finding]:
    """Standalone requirements -- no ordering between them."""
    findings = []

    present = snap.get("tpmPresent")
    if present is True:
        findings.append(Finding("TPM chip present", State.PASS))
    elif present is False:
        findings.append(Finding("TPM chip present", State.FAIL,
                                "No TPM found. Check for fTPM/PTT in the firmware menu."))
    else:
        findings.append(Finding("TPM chip present", State.UNKNOWN,
                                "Could not read TPM presence."))

    enabled = snap.get("tpmEnabled")
    if enabled is True:
        findings.append(Finding("TPM enabled", State.PASS))
    elif enabled is False:
        findings.append(Finding("TPM enabled", State.FAIL,
                                "Enable the TPM (fTPM/PTT) in the firmware menu."))
    else:
        findings.append(Finding("TPM enabled", State.UNKNOWN,
                                "Could not read whether the TPM is enabled."))

    ver = snap.get("tpmSpecVersion")
    if ver is None:
        findings.append(Finding("TPM is version 2.0", State.UNKNOWN,
                                "Could not read the TPM version."))
    elif ver >= 2.0:
        findings.append(Finding("TPM is version 2.0", State.PASS))
    else:
        findings.append(Finding("TPM is version 2.0", State.FAIL,
                                f"This PC has TPM {ver}. Games needing TPM 2.0 will not run."))

    return findings