# Build v4 docx files (EN + KO_bilingual) — HTML route for speed
# 1. Generate two .htm files
# 2. Word opens .htm and saves as .docx (one round-trip per file)
# 3. Copy resulting docx to two locations each

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
$DocsDir = Join-Path $ProjectRoot 'docs'
$DesktopDir = "$env:USERPROFILE\OneDrive\바탕 화면"

. (Join-Path $ScriptDir 'v4_revisions.ps1')

# --- Step 1: Read v3 extracted texts ---
$en_path = Join-Path $ScriptDir 'v3_en_text.txt'
$ko_path = Join-Path $ScriptDir 'v3_ko_text.txt'

$EnLines = Get-Content $en_path -Encoding UTF8
$KoLines = Get-Content $ko_path -Encoding UTF8

Write-Output "Loaded $($EnLines.Count) EN lines, $($KoLines.Count) KO lines"

function Decode-Entities([string]$s) {
    if ($null -eq $s) { return '' }
    return $s `
        -replace '&apos;', "'" `
        -replace '&quot;', '"' `
        -replace '&amp;', '&' `
        -replace '&lt;', '<' `
        -replace '&gt;', '>'
}

function Html-Escape([string]$s) {
    if ($null -eq $s) { return '' }
    return $s `
        -replace '&', '&amp;' `
        -replace '<', '&lt;' `
        -replace '>', '&gt;' `
        -replace '"', '&quot;'
}

# --- Step 2: Build block list ---
$Blocks = New-Object System.Collections.ArrayList

for ($i = 1; $i -le $EnLines.Count; $i++) {
    $en = Decode-Entities $EnLines[$i-1]
    $ko = Decode-Entities $KoLines[$i-1]

    if ($i -eq 5 -or [string]::IsNullOrWhiteSpace($en)) { continue }

    if ($Revisions.ContainsKey($i)) {
        foreach ($rev in $Revisions[$i]) {
            [void]$Blocks.Add(@{type='p'; en=$rev.en; ko=$rev.ko})
        }
        continue
    }

    $type = 'p'
    if ($MetaLines -contains $i) { $type = 'meta' }
    elseif ($Headings.ContainsKey($i)) { $type = $Headings[$i] }
    elseif ($en -match '^Figure \d+\.') { $type = 'fig' }

    [void]$Blocks.Add(@{type=$type; en=$en; ko=$ko})
}

Write-Output "Built $($Blocks.Count) blocks"

# --- Step 3: Generate HTML ---
function Build-Html($bilingual) {
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('<!DOCTYPE html>')
    [void]$sb.AppendLine('<html><head>')
    [void]$sb.AppendLine('<meta charset="UTF-8">')
    [void]$sb.AppendLine('<style>')
    [void]$sb.AppendLine('  body { font-family: "Calibri", sans-serif; font-size: 11pt; line-height: 1.5; }')
    [void]$sb.AppendLine('  h1 { font-size: 18pt; text-align: center; margin: 24pt 0 12pt 0; }')
    [void]$sb.AppendLine('  h2 { font-size: 14pt; margin: 18pt 0 6pt 0; }')
    [void]$sb.AppendLine('  h3 { font-size: 12pt; margin: 12pt 0 6pt 0; font-style: italic; }')
    [void]$sb.AppendLine('  h4 { font-size: 11pt; margin: 8pt 0 4pt 0; font-style: italic; }')
    [void]$sb.AppendLine('  p { margin: 0 0 8pt 0; text-align: justify; }')
    [void]$sb.AppendLine('  p.meta { font-style: italic; text-align: center; margin: 0; }')
    [void]$sb.AppendLine('  p.lbl { font-weight: bold; margin: 8pt 0 0 0; }')
    [void]$sb.AppendLine('  p.fig { font-style: italic; font-size: 10pt; text-align: center; }')
    [void]$sb.AppendLine('  p.ko { color: #444; }')
    [void]$sb.AppendLine('</style>')
    [void]$sb.AppendLine('</head><body>')

    foreach ($block in $Blocks) {
        $type = $block.type
        $en = Html-Escape $block.en
        $ko = Html-Escape $block.ko

        switch ($type) {
            'h1' {
                $hText = if ($bilingual -and -not [string]::IsNullOrWhiteSpace($block.ko) -and $block.ko -ne $block.en) { "$en<br><span style='font-size:14pt; font-weight:normal;'>$ko</span>" } else { $en }
                [void]$sb.AppendLine("<h1>$hText</h1>")
            }
            'h2' {
                $hText = if ($bilingual -and -not [string]::IsNullOrWhiteSpace($block.ko) -and $block.ko -ne $block.en) { "$en  /  $ko" } else { $en }
                [void]$sb.AppendLine("<h2>$hText</h2>")
            }
            'h3' {
                $hText = if ($bilingual -and -not [string]::IsNullOrWhiteSpace($block.ko) -and $block.ko -ne $block.en) { "$en  /  $ko" } else { $en }
                [void]$sb.AppendLine("<h3>$hText</h3>")
            }
            'h4' {
                $hText = if ($bilingual -and -not [string]::IsNullOrWhiteSpace($block.ko) -and $block.ko -ne $block.en) { "$en  /  $ko" } else { $en }
                [void]$sb.AppendLine("<h4>$hText</h4>")
            }
            'meta' {
                [void]$sb.AppendLine("<p class='meta'>$en</p>")
            }
            'lbl' {
                $hText = if ($bilingual -and -not [string]::IsNullOrWhiteSpace($block.ko) -and $block.ko -ne $block.en) { "$en  /  $ko" } else { $en }
                [void]$sb.AppendLine("<p class='lbl'>$hText</p>")
            }
            'fig' {
                [void]$sb.AppendLine("<p class='fig'>$en</p>")
                if ($bilingual -and -not [string]::IsNullOrWhiteSpace($block.ko)) {
                    [void]$sb.AppendLine("<p class='fig ko'>$ko</p>")
                }
            }
            default {
                [void]$sb.AppendLine("<p>$en</p>")
                if ($bilingual -and -not [string]::IsNullOrWhiteSpace($block.ko)) {
                    [void]$sb.AppendLine("<p class='ko'>$ko</p>")
                }
            }
        }
    }

    [void]$sb.AppendLine('</body></html>')
    return $sb.ToString()
}

# Generate HTML temp files
$TempDir = $env:TEMP
$EnHtml = Join-Path $TempDir 'satie_v4_en.htm'
$KoHtml = Join-Path $TempDir 'satie_v4_ko.htm'

Write-Output "Generating EN HTML..."
$utf8WithBom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText($EnHtml, (Build-Html $false), $utf8WithBom)
Write-Output "  $EnHtml ($((Get-Item $EnHtml).Length) bytes)"

Write-Output "Generating KO bilingual HTML..."
[System.IO.File]::WriteAllText($KoHtml, (Build-Html $true), $utf8WithBom)
Write-Output "  $KoHtml ($((Get-Item $KoHtml).Length) bytes)"

# --- Step 4: Word COM converts HTML to docx ---
Write-Output ""
Write-Output "Starting Word COM..."

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0  # wdAlertsNone

try {
    $EnFile = 'Sonorous_Brushstrokes_v4_EN.docx'
    $KoFile = 'Sonorous_Brushstrokes_v4_KO_bilingual.docx'

    $EnPath = Join-Path $DocsDir $EnFile
    $KoPath = Join-Path $DocsDir $KoFile
    $EnDesktop = Join-Path $DesktopDir $EnFile
    $KoDesktop = Join-Path $DesktopDir $KoFile

    # Build EN docx
    Write-Output "Converting EN HTML → docx..."
    $doc = $word.Documents.Open($EnHtml, $false, $true)  # confirmConversions=$false, readOnly=$true
    $doc.SaveAs2($EnPath, 16)  # 16 = wdFormatDocumentDefault
    $doc.Close($false)
    Copy-Item $EnPath $EnDesktop -Force
    Write-Output "  Saved: $EnPath"
    Write-Output "  Saved: $EnDesktop"

    # Build KO bilingual docx
    Write-Output "Converting KO bilingual HTML → docx..."
    $doc = $word.Documents.Open($KoHtml, $false, $true)
    $doc.SaveAs2($KoPath, 16)
    $doc.Close($false)
    Copy-Item $KoPath $KoDesktop -Force
    Write-Output "  Saved: $KoPath"
    Write-Output "  Saved: $KoDesktop"
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-Output ""
Write-Output "=== Done ==="
