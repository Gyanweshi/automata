[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateScript({ Test-Path -LiteralPath $_ })]
    [string]$InputPath,

    [Parameter(Mandatory, Position = 1)]
    [string]$OutputDirectory,

    [ValidateRange(2, 32768)]
    [int]$Width = 3840,

    [ValidateRange(2, 32768)]
    [int]$Height = 2160,

    [ValidateSet('static', 'pan-left', 'pan-right', 'pan-up', 'pan-down', 'zoom-in', 'zoom-out')]
    [string]$Motion = 'static',

    [ValidateRange(1, 60)]
    [int]$DurationSeconds = 5,

    [ValidateRange(1, 60)]
    [int]$Fps = 30,

    [ValidateRange(0.0, 1.0)]
    [double]$ZoomAmount = 0.08,

    [ValidateRange(0.0, 1.0)]
    [double]$CenterX = 0.5,

    [ValidateRange(0.0, 1.0)]
    [double]$CenterY = 0.5,

    [ValidateRange(0, 51)]
    [int]$Crf = 15,

    [string]$Preset = 'medium',

    [switch]$Assemble,

    [switch]$AllowUpsample,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
$ffprobe = Get-Command ffprobe -ErrorAction SilentlyContinue
if (-not $ffmpeg -or -not $ffprobe) {
    throw 'ffmpeg and ffprobe are required but were not found on PATH.'
}

if (($Width % 2) -ne 0 -or ($Height % 2) -ne 0) {
    throw 'Width and Height must be even numbers.'
}

$invariant = [System.Globalization.CultureInfo]::InvariantCulture
$zoomStr = $ZoomAmount.ToString($invariant)
$cxFrac = $CenterX.ToString($invariant)
$cyFrac = $CenterY.ToString($invariant)

$supportedExtensions = @('.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff', '.bmp')
$item = Get-Item -LiteralPath $InputPath
if ($item.PSIsContainer) {
    $sources = Get-ChildItem -LiteralPath $item.FullName -File |
        Where-Object { $_.Extension.ToLowerInvariant() -in $supportedExtensions } |
        Sort-Object Name
} else {
    if ($item.Extension.ToLowerInvariant() -notin $supportedExtensions) {
        throw "Unsupported image type '$($item.Extension)'."
    }
    $sources = @($item)
}
if (-not $sources) {
    throw "No supported images found at '$InputPath'."
}

$outputRoot = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

$codec = @('-c:v', 'libx264', '-preset', $Preset, '-crf', $Crf, '-pix_fmt', 'yuv420p', '-movflags', '+faststart')

# Motions other than 'static' hold the crop at (1+ZoomAmount) so there is room to pan/zoom
# within the frame. The source must already be at least that many pixels, or ffmpeg would
# be inventing detail rather than resampling it — same "no invented pixels" rule the
# upscale helper documents.
$requiredZoom = if ($Motion -eq 'static') { 1.0 } else { 1.0 + $ZoomAmount }
$requiredWidth = [math]::Ceiling($Width * $requiredZoom)
$requiredHeight = [math]::Ceiling($Height * $requiredZoom)

function Get-ImageSize([string]$Path) {
    $raw = & $ffprobe.Source -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x $Path
    if ($LASTEXITCODE -ne 0 -or -not $raw) { throw "ffprobe could not read dimensions for '$Path'." }
    $parts = $raw.Trim() -split 'x'
    [PSCustomObject]@{ Width = [int]$parts[0]; Height = [int]$parts[1] }
}

$generated = @()

foreach ($source in $sources) {
    $size = Get-ImageSize $source.FullName
    if (-not $AllowUpsample -and ($size.Width -lt $requiredWidth -or $size.Height -lt $requiredHeight)) {
        throw "Source '$($source.Name)' is $($size.Width)x$($size.Height), below the ${requiredWidth}x${requiredHeight} " +
              "needed for -Motion $Motion at -ZoomAmount $ZoomAmount without inventing pixels. " +
              'Run scripts/upscale-storyboard-image.ps1 first, or pass -AllowUpsample to proceed anyway.'
    }

    $outputFile = Join-Path $outputRoot ("$($source.BaseName)-$Motion-${DurationSeconds}s.mp4")
    if ((Test-Path -LiteralPath $outputFile) -and -not $Force) {
        Write-Warning "Skipping existing '$outputFile' (use -Force to overwrite)."
        $generated += $outputFile
        continue
    }

    $frames = $DurationSeconds * $Fps
    $cx = "iw*$cxFrac-(iw/zoom/2)"
    $cy = "ih*$cyFrac-(ih/zoom/2)"

    switch ($Motion) {
        'static' {
            $filter = "scale=${Width}:${Height}:force_original_aspect_ratio=increase," +
                      "crop=${Width}:${Height}:(iw-ow)*${cxFrac}:(ih-oh)*${cyFrac},format=yuv420p"
            $ffmpegArgs = @('-hide_banner', '-loglevel', 'error', '-y', '-loop', '1', '-i', $source.FullName,
                             '-vf', $filter, '-t', $DurationSeconds, '-r', $Fps) + $codec + @($outputFile)
        }
        'zoom-in' {
            $z = "1+$zoomStr*on/($frames-1)"
            $filter = "zoompan=z='$z':x='$cx':y='$cy':d=${frames}:s=${Width}x${Height},fps=$Fps,format=yuv420p"
            $ffmpegArgs = @('-hide_banner', '-loglevel', 'error', '-y', '-loop', '1', '-i', $source.FullName,
                             '-vf', $filter, '-frames:v', $frames) + $codec + @($outputFile)
        }
        'zoom-out' {
            $z = "(1+$zoomStr)-$zoomStr*on/($frames-1)"
            $filter = "zoompan=z='$z':x='$cx':y='$cy':d=${frames}:s=${Width}x${Height},fps=$Fps,format=yuv420p"
            $ffmpegArgs = @('-hide_banner', '-loglevel', 'error', '-y', '-loop', '1', '-i', $source.FullName,
                             '-vf', $filter, '-frames:v', $frames) + $codec + @($outputFile)
        }
        default {
            $z = "1+$zoomStr"
            switch ($Motion) {
                'pan-left'  { $x = "(iw-iw/zoom)*(1-on/($frames-1))"; $y = $cy }
                'pan-right' { $x = "(iw-iw/zoom)*(on/($frames-1))";   $y = $cy }
                'pan-up'    { $x = $cx; $y = "(ih-ih/zoom)*(1-on/($frames-1))" }
                'pan-down'  { $x = $cx; $y = "(ih-ih/zoom)*(on/($frames-1))" }
            }
            $filter = "zoompan=z='$z':x='$x':y='$y':d=${frames}:s=${Width}x${Height},fps=$Fps,format=yuv420p"
            $ffmpegArgs = @('-hide_banner', '-loglevel', 'error', '-y', '-loop', '1', '-i', $source.FullName,
                             '-vf', $filter, '-frames:v', $frames) + $codec + @($outputFile)
        }
    }

    if ($PSCmdlet.ShouldProcess($outputFile, "Render $Motion clip from '$($source.Name)'")) {
        & $ffmpeg.Source @ffmpegArgs
        if ($LASTEXITCODE -ne 0) { throw "ffmpeg failed rendering '$($source.Name)'." }
        $generated += $outputFile
    }
}

if ($Assemble -and $generated.Count -gt 1) {
    $listFile = Join-Path $outputRoot 'sequence.txt'
    $generated | ForEach-Object { "file '$([System.IO.Path]::GetFileName($_))'" } |
        Set-Content -LiteralPath $listFile -Encoding ascii
    $assembled = Join-Path $outputRoot "assembled-$Motion.mp4"
    & $ffmpeg.Source -hide_banner -loglevel error -y -f concat -safe 0 -i $listFile -c copy -movflags +faststart $assembled
    if ($LASTEXITCODE -ne 0) { throw 'ffmpeg failed to assemble the sequence.' }
    $generated += $assembled
}

$generated | ForEach-Object { [PSCustomObject]@{ Output = $_ } }
