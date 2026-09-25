param(
    [string] $InputPath = "$PSScriptRoot\assets\sim-controls-manager.png",
    [string] $OutputPath = "$PSScriptRoot\assets\sim-controls-manager.ico"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$sourcePath = (Resolve-Path -LiteralPath $InputPath).Path
$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $outputFullPath
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$sizes = @(16, 20, 24, 32, 40, 48, 64, 128, 256)
$pngImages = [System.Collections.Generic.List[byte[]]]::new()
$source = [System.Drawing.Image]::FromFile($sourcePath)

try {
    foreach ($size in $sizes) {
        $bitmap = [System.Drawing.Bitmap]::new(
            $size,
            $size,
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $stream = [System.IO.MemoryStream]::new()

        try {
            $graphics.Clear([System.Drawing.Color]::Transparent)
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
            $graphics.DrawImage($source, 0, 0, $size, $size)
            $bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
            $pngImages.Add($stream.ToArray())
        }
        finally {
            $stream.Dispose()
            $graphics.Dispose()
            $bitmap.Dispose()
        }
    }
}
finally {
    $source.Dispose()
}

$fileStream = [System.IO.File]::Open(
    $outputFullPath,
    [System.IO.FileMode]::Create,
    [System.IO.FileAccess]::Write
)
$writer = [System.IO.BinaryWriter]::new($fileStream)

try {
    # ICONDIR header: reserved, image type, image count.
    $writer.Write([uint16] 0)
    $writer.Write([uint16] 1)
    $writer.Write([uint16] $sizes.Count)

    $dataOffset = 6 + (16 * $sizes.Count)
    for ($index = 0; $index -lt $sizes.Count; $index++) {
        $size = $sizes[$index]
        $imageBytes = $pngImages[$index]

        # An ICO encodes a 256-pixel dimension as zero.
        $dimension = if ($size -eq 256) { 0 } else { $size }
        $writer.Write([byte] $dimension)
        $writer.Write([byte] $dimension)
        $writer.Write([byte] 0) # palette colors
        $writer.Write([byte] 0) # reserved
        $writer.Write([uint16] 1) # color planes
        $writer.Write([uint16] 32) # bits per pixel
        $writer.Write([uint32] $imageBytes.Length)
        $writer.Write([uint32] $dataOffset)
        $dataOffset += $imageBytes.Length
    }

    foreach ($imageBytes in $pngImages) {
        $writer.Write($imageBytes)
    }
}
finally {
    $writer.Dispose()
    $fileStream.Dispose()
}

Write-Host "Created: $outputFullPath"
