# Build Leonardo-formatted v4 docx files (EN + KO_bilingual)
# Output: 4 files (2 docx × 2 locations)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
$DocsDir = Join-Path $ProjectRoot 'docs'
$DesktopDir = "$env:USERPROFILE\OneDrive\바탕 화면"

. (Join-Path $ScriptDir 'v4_revisions.ps1')
. (Join-Path $ScriptDir 'v4_leonardo_overlay.ps1')

$en_path = Join-Path $ScriptDir 'v3_en_text.txt'
$ko_path = Join-Path $ScriptDir 'v3_ko_text.txt'

$EnLines = Get-Content $en_path -Encoding UTF8
$KoLines = Get-Content $ko_path -Encoding UTF8

Write-Output "Loaded $($EnLines.Count) EN lines, $($KoLines.Count) KO lines"

function Decode-Entities([string]$s) {
    if ($null -eq $s) { return '' }
    return $s -replace '&apos;', "'" -replace '&quot;', '"' -replace '&amp;', '&' -replace '&lt;', '<' -replace '&gt;', '>'
}

function Html-Escape([string]$s) {
    if ($null -eq $s) { return '' }
    return $s -replace '&', '&amp;' -replace '<', '&lt;' -replace '>', '&gt;' -replace '"', '&quot;'
}

# --- Build block list (Leonardo-formatted) ---
$Blocks = New-Object System.Collections.ArrayList

# Title (line 1) — keep as-is
$titleEn = Decode-Entities $EnLines[0]
$titleKo = Decode-Entities $KoLines[0]
[void]$Blocks.Add(@{type='h1'; en=$titleEn; ko=$titleKo})

# Author info — single line in Leonardo format (replaces lines 2-4)
[void]$Blocks.Add(@{type='author'; en=$LeoAuthorLine.en; ko=$LeoAuthorLine.ko})

# Process lines 6 onwards (skip blank line 5 and old multi-line author info 2-4)
for ($i = 6; $i -le $EnLines.Count; $i++) {
    $en = Decode-Entities $EnLines[$i-1]
    $ko = Decode-Entities $KoLines[$i-1]

    if ([string]::IsNullOrWhiteSpace($en)) { continue }

    # Replace abstract (line 7)
    if ($i -eq 7) {
        [void]$Blocks.Add(@{type='p'; en=$LeoAbstract.en; ko=$LeoAbstract.ko})
        continue
    }

    # Replace keywords (line 9)
    if ($i -eq 9) {
        [void]$Blocks.Add(@{type='kw'; en=$LeoKeywords.en; ko=$LeoKeywords.ko})
        continue
    }

    # Apply revisions
    if ($Revisions.ContainsKey($i)) {
        foreach ($rev in $Revisions[$i]) {
            $revType = if ($rev.en -match '^Figure \d+\.|^Fig\. \d+\.') { 'fig' } else { 'p' }
            [void]$Blocks.Add(@{type=$revType; en=$rev.en; ko=$rev.ko})
        }
        continue
    }

    # Heading? Apply Leonardo text override + marker
    if ($Headings.ContainsKey($i)) {
        $type = $Headings[$i]
        # Override heading text if specified
        if ($LeoHeadingText.ContainsKey($i)) {
            $en = $LeoHeadingText[$i].en
            $ko = $LeoHeadingText[$i].ko
        }
        [void]$Blocks.Add(@{type=$type; en=$en; ko=$ko})
        continue
    }

    # Figure caption
    if ($en -match '^Figure \d+\.') {
        [void]$Blocks.Add(@{type='fig'; en=$en; ko=$ko})
        continue
    }

    # Body paragraph
    [void]$Blocks.Add(@{type='p'; en=$en; ko=$ko})
}

# Append Biographical Information (Leonardo requirement)
[void]$Blocks.Add(@{type='biohead'; en='Biographical Information'; ko='약력'})
[void]$Blocks.Add(@{type='p'; en=$LeoBio.en; ko=$LeoBio.ko})

Write-Output "Built $($Blocks.Count) blocks"

# --- HTML generation (Leonardo style with <N> markers as plain text) ---
function Build-Html($bilingual) {
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('<!DOCTYPE html>')
    [void]$sb.AppendLine('<html><head>')
    [void]$sb.AppendLine('<meta charset="UTF-8">')
    [void]$sb.AppendLine('<style>')
    [void]$sb.AppendLine('  body { font-family: "Times New Roman", serif; font-size: 12pt; line-height: 1.5; }')
    [void]$sb.AppendLine('  .title { font-size: 14pt; font-weight: bold; text-align: center; margin: 0 0 12pt 0; }')
    [void]$sb.AppendLine('  .author { font-size: 11pt; text-align: center; margin: 0 0 18pt 0; }')
    [void]$sb.AppendLine('  .marker { font-weight: bold; }')
    [void]$sb.AppendLine('  h1 { font-size: 12pt; font-weight: bold; margin: 18pt 0 6pt 0; }')
    [void]$sb.AppendLine('  h2 { font-size: 12pt; font-weight: bold; font-style: italic; margin: 12pt 0 6pt 0; }')
    [void]$sb.AppendLine('  h3 { font-size: 12pt; font-style: italic; margin: 8pt 0 4pt 0; }')
    [void]$sb.AppendLine('  p { margin: 0 0 8pt 0; text-align: justify; text-indent: 0; }')
    [void]$sb.AppendLine('  p.kw { font-style: italic; margin: 6pt 0 12pt 0; }')
    [void]$sb.AppendLine('  p.fig { font-style: italic; font-size: 10pt; text-align: left; margin: 12pt 0; }')
    [void]$sb.AppendLine('  p.ko { color: #444; }')
    [void]$sb.AppendLine('  p.bio { margin: 6pt 0; }')
    [void]$sb.AppendLine('</style>')
    [void]$sb.AppendLine('</head><body>')

    foreach ($block in $Blocks) {
        $type = $block.type
        $en = Html-Escape $block.en
        $ko = Html-Escape $block.ko
        $hasKo = $bilingual -and -not [string]::IsNullOrWhiteSpace($block.ko) -and $block.ko -ne $block.en

        switch ($type) {
            'h1' {
                # Title
                $titleHtml = if ($hasKo) { "$en<br><span style='font-size:11pt; font-weight:normal;'>$ko</span>" } else { $en }
                [void]$sb.AppendLine("<p class='title'>$titleHtml</p>")
            }
            'author' {
                [void]$sb.AppendLine("<p class='author'>$en</p>")
                if ($hasKo) {
                    [void]$sb.AppendLine("<p class='author ko'>$ko</p>")
                }
            }
            'h2' {
                # Top-level section: <1>Heading
                $hText = if ($hasKo) { "$en  /  $ko" } else { $en }
                [void]$sb.AppendLine("<h1><span class='marker'>&lt;1&gt;</span>$hText</h1>")
            }
            'h3' {
                # Subsection: <2>Heading
                $hText = if ($hasKo) { "$en  /  $ko" } else { $en }
                [void]$sb.AppendLine("<h2><span class='marker'>&lt;2&gt;</span>$hText</h2>")
            }
            'h4' {
                # Sub-subsection: <3>Heading
                $hText = if ($hasKo) { "$en  /  $ko" } else { $en }
                [void]$sb.AppendLine("<h3><span class='marker'>&lt;3&gt;</span>$hText</h3>")
            }
            'lbl' {
                # Keywords label — Leonardo doesn't usually have this; treat as bold p
                [void]$sb.AppendLine("<p><strong>$en</strong></p>")
            }
            'kw' {
                [void]$sb.AppendLine("<p class='kw'>Keywords: $en</p>")
                if ($hasKo) {
                    [void]$sb.AppendLine("<p class='kw ko'>키워드: $ko</p>")
                }
            }
            'fig' {
                # Insert image before caption based on figure number
                $imgFile = $null
                if ($block.en -match '^Figure 1\.|^Fig\. 1\.') { $imgFile = 'gymnopedie_1.png' }
                elseif ($block.en -match '^Figure 2\.|^Fig\. 2\.') { $imgFile = 'gnossienne_1.png' }
                elseif ($block.en -match '^Figure 3\.|^Fig\. 3\.') { $imgFile = 'vexations.png' }

                if ($imgFile) {
                    $imgPath = Join-Path (Join-Path (Split-Path $ScriptDir -Parent) 'site\images') $imgFile
                    if (Test-Path $imgPath) {
                        $bytes = [IO.File]::ReadAllBytes($imgPath)
                        $b64 = [Convert]::ToBase64String($bytes)
                        [void]$sb.AppendLine("<p style='text-align:center; margin: 20pt 0 6pt 0;'><img src='data:image/png;base64,$b64' style='max-width: 4.5in; height: auto; border: 1px solid #888;' alt='$($block.en)' /></p>")
                    }
                }

                [void]$sb.AppendLine("<p class='fig'>$en</p>")
                if ($hasKo) {
                    [void]$sb.AppendLine("<p class='fig ko'>$ko</p>")
                }
            }
            'biohead' {
                # Biographical Information (no marker per Leonardo style)
                $hText = if ($hasKo) { "$en  /  $ko" } else { $en }
                [void]$sb.AppendLine("<h1>$hText</h1>")
            }
            default {
                [void]$sb.AppendLine("<p>$en</p>")
                if ($hasKo) {
                    [void]$sb.AppendLine("<p class='ko'>$ko</p>")
                }
            }
        }
    }

    [void]$sb.AppendLine('</body></html>')
    return $sb.ToString()
}

# Generate HTML files
$TempDir = $env:TEMP
$EnHtml = Join-Path $TempDir 'satie_v4_leo_en.htm'
$KoHtml = Join-Path $TempDir 'satie_v4_leo_ko.htm'

$utf8WithBom = New-Object System.Text.UTF8Encoding $true

Write-Output "Generating EN Leonardo HTML..."
[System.IO.File]::WriteAllText($EnHtml, (Build-Html $false), $utf8WithBom)
Write-Output "  $EnHtml ($((Get-Item $EnHtml).Length) bytes)"

Write-Output "Generating KO Leonardo HTML..."
[System.IO.File]::WriteAllText($KoHtml, (Build-Html $true), $utf8WithBom)
Write-Output "  $KoHtml ($((Get-Item $KoHtml).Length) bytes)"

# --- Copy to .htm and .doc (Word handles HTML-as-doc) in 2 locations ---
$EnFileBase = 'Sonorous_Brushstrokes_v4_Leonardo_EN'
$KoFileBase = 'Sonorous_Brushstrokes_v4_Leonardo_KO_bilingual'

# Write to project docs/ only. Hardlinks propagate to Leonardo 최종제출용/.
Copy-Item $EnHtml (Join-Path $DocsDir "$EnFileBase.htm") -Force
Copy-Item $EnHtml (Join-Path $DocsDir "$EnFileBase.doc") -Force
Copy-Item $KoHtml (Join-Path $DocsDir "$KoFileBase.htm") -Force
Copy-Item $KoHtml (Join-Path $DocsDir "$KoFileBase.doc") -Force
Write-Output "Saved 4 files to: $DocsDir"
Write-Output "(Hardlinks should propagate to Desktop\Leonardo\최종제출용\)"

Write-Output ""
Write-Output "=== Done ==="
