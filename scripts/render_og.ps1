# Render og.html (written by build_map_data.py) to og.png, the 1200x630 social card.
# Usage, from the repo root:  powershell -File scripts/render_og.ps1
# Fonts come from the Data Hub Adobe Fonts kit, so this needs a network connection.
$root = Split-Path -Parent $PSScriptRoot
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$profile = Join-Path $root "_work\chrome-profile"
$out = Join-Path $root "og.png"
$src = "file:///" + ((Join-Path $root "og.html") -replace '\\', '/' -replace ' ', '%20')
& $chrome --headless=new --disable-gpu --hide-scrollbars "--user-data-dir=$profile" `
  --window-size=1200,630 --virtual-time-budget=15000 "--screenshot=$out" $src
Write-Output "og card -> $out"
