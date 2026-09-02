# sb-audit

Audits Windows boot posture, including Secure Boot, TPM, and firmware mode. Explains what's blocking what.

Read-only. It will NEVER change firmware or disk state.

This tool helps diagnose what is preventing a system from meeting Secure Boot and TPM requirements. It doesn't bypass, disable, or circumvent them.

## Why

I worked with a relative who couldn't launch Call of Duty. The anticheat wanted Secure Boot and
TPM 2.0; and his machine had neither enabled. He didn't know what either of those
were, and the error message didn't give him any clues at all. I had to go to the
machine to work out what was wrong. It was fun, but it drew my attention to a gap between tooling
and non-technical users.

Most tools that already exist tell you *whether* Secure Boot is on. None of them
tell you *why you can't turn it on yet*, which is the part that actually blocks
someone. Secure Boot has pre-requisites like UEFI and GPT, that these tools don't
mention. Telling someone "enable Secure Boot" while they haven't met these requirements
sends them across reboots trying to find options in the BIOS that don't exist.

This tool addresses this by reporting the state and directing the fix.

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
has a working TPM 2.0 with Secure Boot enabled. `Get-ComputerInfo` reads fine
without elevation; `Confirm-SecureBootUEFI`, `Get-SecureBootUEFI` and `Get-Tpm`
do not, and a `[bool]` cast over an unreadable property was turning
"I can't read this" into "it's definitively absent".

So the tool refuses to run without elevation rather than degrade. I would prefer no
answer over misleading ones.

It does **not** self-elevate. A script that spontaneously raises a UAC prompt is
a habit I'm not comfortable with, especially for an auditing tool. It detects, instructs,
and exits.

## Where to install it

Install this somewhere only administrators can write, under `Program Files`,
or a checkout whose permissions you control. Not Downloads, not a per-user temp
directory, not anywhere a standard user can drop a file.

The reason is the same trust concept as elevation. The tool runs `boot_posture.ps1` from 
its own install directory, with admin rights it just confirmed it has. 
If a non-admin can edit that script, they could potentially have
their own code run as admin the next time someone audits the machine. 
Same logic for the `powershell.exe` path: the tool calls it by absolute
System32 path rather than by name, so a `powershell.exe` added in the working
directory can't win the search order. Both are the one assumption this tool
makes explicit, the script and the shell it runs are trusted, so put them
where only trusted accounts can touch them.

`-ExecutionPolicy Bypass` is part of the same picture and isn't a hole:
execution policy was never a security boundary (Microsoft says as much), and the
script's integrity is already guaranteed by the install-location requirement
above.

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

The split is important because of where the testing lives. PowerShell can only be
exercised on a Windows box in whatever state that box happens to be
in. Python logic is a pure function over a dict, so it can be run against
testing snapshots: legacy firmware, Setup Mode, a missing TPM, a TPM 1.2 which are
states my machine would never produce. Keeping the PowerShell layer as thin as
possible keeps the untestable surface as small as possible.

The dividing line: PowerShell *unwraps* (`.Bytes[0]` → `0`), Python *interprets*
(`0` → keys are enrolled). Anything requiring knowledge of what a value means is
Python's job.

## Design decisions

**Audit only.** Every setting here: Secure Boot, TPM, boot mode, lives
behind a reboot in a vendor menu and can't be changed from the OS. The one fix
that *is* scriptable, `mbr2gpt`, is destructive-adjacent enough that it shouldn't
be owned by a diagnostic tool. So the blast radius is zero intentionally.

**A sequence and a checklist, not one list.** The boot path is ordered, each
step gates the next. TPM requirements are separate and don't wait on it. Flattening
them into a single list loses that distinction that makes the output actionable.

The checklist isn't entirely flat. TPM requirements form their
own small chain plus one independent check:

    TPM present
        ↓
    TPM enabled

    TPM version 2.0  - standalone, checked whenever it's detectable

Version stands apart, coming from a different source (`Win32_Tpm`) than the presence and
enabled flags (`Get-Tpm`), so it can often be read even when the TPM is
disabled. When it can't, it reports unknown rather than guessing.

**Four states, not two.** `pass` / `fail` / `locked` / `unknown`. `locked` is the
dependency chain visible. `unknown` exists because the tool would otherwise
have to guess, and I'll take a gap over a wrong answer.
