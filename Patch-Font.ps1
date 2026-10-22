# SKALD: Against the Black Priory - Readable Font Mod patcher
# Applies a binary patch (xdelta3) to resources.assets. Needs nothing installed:
# Windows PowerShell 5.1 + the bundled bin\xdelta3.exe are enough.
#
#   Patch-Font.bat                       interactive menu
#   Patch-Font.bat -Variant 04b          04b | restore
#   Patch-Font.bat -GameDir "D:\Games\SKALD ..."   if the game is not found automatically

param(
    [string]$GameDir = "",
    [string]$Variant = ""
)
$ErrorActionPreference = "Stop"
$ModDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# SHA-256 of resources.assets in the supported game build (GOG, "Launch 1.0.5", Unity 2020.3.36)
$OrigHash = "900504F3C38A003AED407D92E03180611BBB1BF5C4AEA92390AA23E4DE3FCDEC"
$Variants = [ordered]@{
    "04b" = @{ Label = "04b_03 - small, rounded, easy on the eyes"; Patch = "04b_03.xdelta"; Hash = "C43A5A28C1113AE26775E1ADD4FBA03B52E1E17AECA58D8917C62C0256FC6B94" }
}
$DataName = "SKALD Against the Black Priory_Data"

function Say($t, $c = "Gray") { Write-Host $t -ForegroundColor $c }
function Fail($t) { Say "ERROR: $t" "Red"; Say "Nothing was changed." "Red"; exit 1 }
function Hash($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToUpper() }

function Find-DataDir {
    $cands = @()
    if ($GameDir) { $cands += $GameDir }
    $cands += $ModDir, (Split-Path -Parent $ModDir)
    $cands += "C:\GOG Games\SKALD - Against the Black Priory", "C:\GOG Games\SKALD Against the Black Priory",
              "C:\Program Files (x86)\GOG Galaxy\Games\SKALD - Against the Black Priory",
              "D:\GAMES\SKALD Against the Black Priory"
    foreach ($c in $cands) {
        if (-not $c) { continue }
        if ((Split-Path -Leaf $c) -eq $DataName -and (Test-Path -LiteralPath (Join-Path $c "resources.assets"))) { return $c }
        $d = Join-Path $c $DataName
        if (Test-Path -LiteralPath (Join-Path $d "resources.assets")) { return $d }
    }
    return $null
}

Say ""
Say "SKALD Readable Font Mod" "Cyan"
Say "-----------------------" "Cyan"

$data = Find-DataDir
if (-not $data) {
    Say "Game folder not found automatically."
    $in = Read-Host "Paste the game folder path (the one containing 'SKALD Against the Black Priory.exe')"
    $GameDir = $in.Trim('"').Trim()
    $data = Find-DataDir
    if (-not $data) { Fail "Could not find '$DataName\resources.assets' in: $GameDir" }
}
Say "Game data folder: $data"

if (Get-Process -Name "SKALD Against the Black Priory" -ErrorAction SilentlyContinue) { Fail "The game is running. Close it first." }

$res = Join-Path $data "resources.assets"
$bak = Join-Path $data "resources.assets.original"
$free = (Get-Item $data).PSDrive.Free
if ($free -lt 700MB) { Fail "Not enough free disk space on the game drive (need about 700 MB)." }

Say "Checking game files..."
$cur = Hash $res
$known = @($OrigHash) + @($Variants.Values | ForEach-Object { $_.Hash })
if ($cur -notin $known) {
    Fail "resources.assets is not the supported version (probably a game update, or another mod). This mod only supports the GOG build 'Launch 1.0.5'."
}
if (Test-Path -LiteralPath $bak) {
    if ((Hash $bak) -ne $OrigHash) { Fail "Existing backup 'resources.assets.original' is not the original file. Remove it only if you are sure, then run again." }
} else {
    if ($cur -ne $OrigHash) { Fail "The game is already patched but no backup was found. Restore the original with GOG Galaxy (Manage installation > Verify / Repair)." }
    Say "Creating backup: resources.assets.original (about 200 MB)..."
    Copy-Item -LiteralPath $res -Destination $bak
    if ((Hash $bak) -ne $OrigHash) { Remove-Item -LiteralPath $bak -Force; Fail "Backup verification failed." }
}

if (-not $Variant) {
    Say ""
    Say "What do you want to do?" "Yellow"
    $i = 1; $keys = @($Variants.Keys)
    foreach ($k in $keys) { Say ("  [{0}] {1}" -f $i, $Variants[$k].Label); $i++ }
    Say "  [R] Restore the original game font"
    Say "  [Q] Quit"
    $a = (Read-Host "Your choice").Trim().ToLower()
    if ($a -eq "q" -or $a -eq "") { exit 0 }
    if ($a -eq "r") { $Variant = "restore" }
    elseif ($a -match '^\d+$' -and [int]$a -ge 1 -and [int]$a -le $keys.Count) { $Variant = $keys[[int]$a - 1] }
    else { Fail "Unknown choice." }
}

if ($Variant -eq "restore") {
    Copy-Item -LiteralPath $bak -Destination $res -Force
    if ((Hash $res) -ne $OrigHash) { Fail "Restore verification failed - run GOG Galaxy 'Verify / Repair'." }
    Say "Done. Original font restored." "Green"
    exit 0
}
if (-not $Variants.Contains($Variant)) { Fail "Unknown variant '$Variant'. Use: 04b, restore." }

$v = $Variants[$Variant]
$patch = Join-Path $ModDir ("patches\" + $v.Patch)
$xd = Join-Path $ModDir "bin\xdelta3.exe"
if (-not (Test-Path -LiteralPath $patch)) { Fail "Patch file missing: $patch" }
if (-not (Test-Path -LiteralPath $xd)) { Fail "Tool missing: $xd" }

# xdelta3 cannot open paths longer than 260 characters, so run it inside the game data folder with short names.
Say "Applying patch..."
$tx = Join-Path $data "xd_tmp.exe"; $tp = Join-Path $data "xd_tmp.xdelta"; $out = "resources.assets.new"
Copy-Item -LiteralPath $xd -Destination $tx -Force
Copy-Item -LiteralPath $patch -Destination $tp -Force
Push-Location $data
try {
    & $tx -f -d -s "resources.assets.original" "xd_tmp.xdelta" $out 2>&1 | Out-Null
    $code = $LASTEXITCODE
} finally {
    Pop-Location
    Remove-Item -LiteralPath $tx, $tp -Force -ErrorAction SilentlyContinue
}
$outPath = Join-Path $data $out
if ($code -ne 0 -or -not (Test-Path -LiteralPath $outPath)) { Fail "xdelta3 failed (exit code $code)." }
if ((Hash $outPath) -ne $v.Hash) { Remove-Item -LiteralPath $outPath -Force; Fail "Patched file failed verification." }
Move-Item -LiteralPath $outPath -Destination $res -Force
Say ""
Say "Done! Font applied: $($v.Label)" "Green"
Say "Start the game. To undo: run this again and choose Restore." "Gray"
