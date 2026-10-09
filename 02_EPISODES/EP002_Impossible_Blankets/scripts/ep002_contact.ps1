Add-Type -AssemblyName System.Drawing
$epPreview = 'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets\previews'
$names = @('Opening','Slime','Glass','Cloth','Honey','Sand','Water','Lava','Final','Outro')
$canvas = New-Object System.Drawing.Bitmap 1260,948
$graphics = [System.Drawing.Graphics]::FromImage($canvas)
$graphics.Clear([System.Drawing.Color]::FromArgb(20,32,39))
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$font = New-Object System.Drawing.Font 'Arial',13,([System.Drawing.FontStyle]::Bold)
for ($i=0; $i -lt $names.Count; $i++) {
    $im = [System.Drawing.Image]::FromFile((Join-Path $epPreview ('EP002_'+$names[$i]+'_v002.png')))
    $x = ($i % 5)*252+3
    $y = [math]::Floor($i/5)*474+29
    $graphics.DrawImage($im,[int]$x,[int]$y,246,438)
    $graphics.DrawString($names[$i].ToUpper(),$font,[System.Drawing.Brushes]::White,[single]($x+7),[single]($y-23))
    $im.Dispose()
}
$canvas.Save((Join-Path $epPreview 'EP002_Review_ContactSheet_v002.jpg'),[System.Drawing.Imaging.ImageFormat]::Jpeg)
$graphics.Dispose(); $canvas.Dispose(); $font.Dispose()
