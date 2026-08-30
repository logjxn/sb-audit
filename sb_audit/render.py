from .walker import Finding, State

GLYPH = {
    State.PASS: "[x]",
    State.FAIL: "[ ]",
    State.LOCKED: "[-]",
    State.UNKNOWN: "[?]",
}


def _first_actionable(findings: list[Finding]) -> Finding | None:
    """The first step the user can actually do something about."""
    for f in findings:
        if f.state in (State.FAIL, State.UNKNOWN):
            return f
    return None


def render(boot_path: list[Finding], checklist: list[Finding]) -> str:
    lines = []
    current = _first_actionable(boot_path)

    lines.append("BOOT PATH  (do these in order)")
    for i, f in enumerate(boot_path, 1):
        marker = "   <- start here" if f is current else ""
        lines.append(f"  {GLYPH[f.state]} {i}. {f.name}{marker}")
        if f.state is State.LOCKED and f.action:
            lines.append(f"        {f.action}")
    if current and current.action:
        lines.append("")
        lines.append(f"  What to do: {current.action}")

    lines.append("")
    lines.append("OTHER REQUIREMENTS  (any order)")
    for f in checklist:
        lines.append(f"  {GLYPH[f.state]} {f.name}")
        if f.state in (State.FAIL, State.LOCKED) and f.action:
            lines.append(f"        {f.action}")

    unresolved = [f for f in boot_path + checklist if f.state is not State.PASS]
    lines.append("")
    if not unresolved:
        lines.append("All checks passed. This PC meets the boot requirements.")
    else:
        lines.append(f"{len(unresolved)} item(s) need attention. Start with the boot path above.")

    return "\n".join(lines)