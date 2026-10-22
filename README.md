# sb-audit

Audits Windows boot posture, including Secure Boot, TPM, and firmware mode. Explains what's blocking what.

Read-only. It will NEVER change firmware or disk state.

This tool helps diagnose what is preventing a system from meeting Secure Boot and TPM requirements. It doesn't bypass, disable, or circumvent them.

## Why

I worked with a relative who couldn't launch Call of Duty. The anticheat wanted Secure Boot and
TPM 2.0; and his machine had neither enabled. He didn't know what either of those
were, and the error message didn't give him any clues at all.

Most tools that already exist tell you *whether* Secure Boot is on. None of them
tell you *why you can't turn it on yet*, which is the part that actually blocks
someone.

This tool addresses this by reporting the state and directing a fix.

## Usage

Requires Windows and administrator rights.
Requires python.

```
python -m sb_audit
```

## Sample output

A machine that boots the old way:

```
BOOT PATH  (do these in order)
  [ ] 1. Firmware is in UEFI mode   <- start here
  [-] 2. Secure Boot keys enrolled
        Locked until the firmware is in UEFI mode.
  [-] 3. Secure Boot enabled
        Locked until the keys above are enrolled.

  What to do: Your PC is booting the old way. Convert the disk with mbr2gpt,
  then switch the firmware from Legacy/CSM to UEFI.

OTHER REQUIREMENTS  (any order)
  [x] TPM chip present
  [ ] TPM enabled
        Enable the TPM (fTPM/PTT) in the firmware menu.
  [x] TPM is version 2.0

4 item(s) need attention. Start with the boot path above.
```

`[x]` pass, `[ ]` fail, `[-]` locked behind an earlier step, `[?]` couldn't
be determined.

## Why administrator rights are required

Without elevation the tool reports confident, plausible,
completely wrong results.

Same machine, five minutes apart. Unelevated:

```
{'firmwareType': 'Uefi', 'secureBoot': 'unsupported', 'setupMode': None,
 'tpmPresent': False, 'tpmEnabled': False, 'tpmSpecVersion': None}
```

Elevated:

```
{'firmwareType': 'Uefi', 'secureBoot': True, 'setupMode': 0,
 'tpmPresent': True, 'tpmEnabled': True, 'tpmSpecVersion': 2.0}
```

The first output says there's no TPM and Secure Boot is unsupported. My machine
has a working TPM 2.0 with Secure Boot enabled.

So the tool refuses to run without elevation rather than degrade.

It does **not** self-elevate. A script that spontaneously raises a UAC prompt is
a habit I'm not comfortable with, especially for an auditing tool.

## Where to install it

Install this somewhere only administrators can write, under `Program Files`,
or a checkout whose permissions you control.

The tool runs `boot_posture.ps1` from its own install directory, with admin rights. Therefore, a non-admin could run their own
code if they can edit the script.

To further protect against this, the tool calls Powershell by absolute
System32 path, so a `powershell.exe` added in the working
directory cannot win the search order.

## Architecture

PowerShell extracts, Python interprets.

```
boot_posture.ps1   reads the machine, unwraps .NET containers, emits flat JSON
sb_audit/
  elevation.py     privilege check
  snapshot.py      runs the script, parses JSON, normalises the TPM version
  walker.py        turns a snapshot into findings
  render.py        turns findings into text
  __main__.py      entry point
```

While PowerShell can only be mainly exercised in a Windows box (and in that boot state),
Python can be utilized anywhere, allowing testing to be done on fake snapshots.

## Design decisions

**Audit only.** Every setting here: Secure Boot, TPM, boot mode, lives in UEFI and can't be changed from the OS.
The one step that is scriptable, `mbr2gpt`, can be potentially destructive enough that it shouldn't
be performed by an audit tool.

**A sequence + checklist**, with the boot path being ordered, each step preceding
the next. TPM requirements are separate and don't wait on it. Separating these helps
make the output more actionable.
