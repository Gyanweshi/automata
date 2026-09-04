[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string]$InputPath,

    [string]$OutputDirectory,

    [ValidateRange(2, 32768)]
    [int]$Width4K = 3840,

    [ValidateRange(2, 32768)]
    [int]$Height4K = 2160,

    [ValidateSet('black', 'white', 'transparent')]
    [string]$PadColor = 'black',

    [switch]$Force
)

$ErrorActionPreference = 'Stop'

if (($Width4K % 2) -ne 0 -or ($Height4K % 2) -ne 0) {
    throw 'Width4K and Height4K must be even numbers.'
}

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
    throw 'ffmpeg is required but was not found on PATH.'
}

$source = Get-Item -LiteralPath $InputPath
$supportedExtensions = @('.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff', '.bmp')
if ($source.Extension.ToLowerInvariant() -notin $supportedExtensions) {
    throw "Unsupported image type '$($source.Extension)'."
}

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $source.DirectoryName ($source.BaseName + '-upscaled')
}
$outputRoot = [System.IO.Path]::GetFullPath($OutputDirectory)
$fourKDirectory = Join-Path $outputRoot '4k-exact'
$eightKDirectory = Join-Path $outputRoot '8k-exact'
$fourKPath = Join-Path $fourKDirectory ($source.BaseName + '-4k.png')
$eightKPath = Join-Path $eightKDirectory ($source.BaseName + '-8k.png')

if (-not $Force -and ((Test-Path -LiteralPath $fourKPath) -or (Test-Path -LiteralPath $eightKPath))) {
    throw "Output already exists under '$outputRoot'. Use -Force to replace it."
}

$width8K = $Width4K * 2
$height8K = $Height4K * 2
$fourKFilter = "scale=${Width4K}:${Height4K}:force_original_aspect_ratio=decrease:flags=lanczos,pad=${Width4K}:${Height4K}:(ow-iw)/2:(oh-ih)/2:color=${PadColor},setsar=1"
$eightKFilter = "scale=${width8K}:${height8K}:flags=lanczos,setsar=1"

if ($PSCmdlet.ShouldProcess($outputRoot, "Create sequential Lanczos 4K and 8K PNGs from '$($source.FullName)'")) {
    New-Item -ItemType Directory -Force -Path $fourKDirectory, $eightKDirectory | Out-Null

    & $ffmpeg.Source -hide_banner -loglevel error -y -i $source.FullName -vf $fourKFilter -frames:v 1 $fourKPath
    if ($LASTEXITCODE -ne 0) { throw 'ffmpeg failed during the 4K Lanczos pass.' }

    # The second pass intentionally uses the 4K result, matching the proven
    # storyboard workflow instead of scaling the low-resolution source directly.
    & $ffmpeg.Source -hide_banner -loglevel error -y -i $fourKPath -vf $eightKFilter -frames:v 1 $eightKPath
    if ($LASTEXITCODE -ne 0) { throw 'ffmpeg failed during the 8K Lanczos pass.' }

    [PSCustomObject]@{
        Source = $source.FullName
        FourK = $fourKPath
        EightK = $eightKPath
        Method = 'Lanczos: source -> 4K -> 8K'
        Canvas4K = "${Width4K}x${Height4K}"
        Canvas8K = "${width8K}x${height8K}"
    }
}
