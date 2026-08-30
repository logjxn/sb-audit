# boot_posture.ps1
# Extraction only

$snapshot = [ordered]@{}

# - Firmware Type
try {
    $snapshot['firmwareType'] = (Get-ComputerInfo -ErrorAction Stop).BiosFirmwareType.ToString()
} catch {
    $snapshot['firmwareType'] = $null
}

# - Secure Boot
try {
    $snapshot['secureBoot'] = [bool](Confirm-SecureBootUEFI -ErrorAction Stop)
} catch {
    $snapshot['secureBoot'] = 'unsupported'
}

# - Setup Mode
try {
    $snapshot['setupMode'] = [int](Get-SecureBootUEFI -Name SetupMode -ErrorAction Stop).Bytes[0]
} catch {
    $snapshot['setupMode'] = $null
}

# --- TPM presence / enabled ---
try {
    $tpm = Get-Tpm -ErrorAction Stop
    $snapshot['tpmPresent'] = [bool]$tpm.TpmPresent
    $snapshot['tpmEnabled'] = [bool]$tpm.TpmEnabled
} catch {
    $snapshot['tpmPresent'] = $null
    $snapshot['tpmEnabled'] = $null
}

# --- TPM spec version (raw string — Python parses) ---
try {
    $win32Tpm = Get-CimInstance -Namespace 'root\cimv2\Security\MicrosoftTpm' `
                                -ClassName Win32_Tpm -ErrorAction Stop
    $snapshot['tpmSpecVersionRaw'] = $win32Tpm.SpecVersion
} catch {
    $snapshot['tpmSpecVersionRaw'] = $null
}

$snapshot | ConvertTo-Json -Depth 3