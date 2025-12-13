# ================================================
# MPX File Association Setup (Windows)
# ================================================

Write-Host "🔗 Setting up .mpx file association for VLC..." -ForegroundColor Cyan

# Find VLC installation
$vlcPaths = @(
    "${env:ProgramFiles}\VideoLAN\VLC\vlc.exe",
    "${env:ProgramFiles(x86)}\VideoLAN\VLC\vlc.exe",
    "$env:LOCALAPPDATA\Programs\VideoLAN\VLC\vlc.exe"
)

$vlcPath = $null
foreach ($path in $vlcPaths) {
    if (Test-Path $path) {
        $vlcPath = $path
        break
    }
}

if (-not $vlcPath) {
    Write-Host "❌ VLC not found. Please install VLC Media Player first." -ForegroundColor Red
    Write-Host "   Download from: https://www.videolan.org/vlc/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ VLC found at: $vlcPath" -ForegroundColor Green

# Create registry entries for .mpx file association
Write-Host "🔧 Creating registry entries..." -ForegroundColor Cyan

try {
    # Create file extension entry
    New-Item -Path "HKCU:\Software\Classes\.mpx" -Force | Out-Null
    Set-ItemProperty -Path "HKCU:\Software\Classes\.mpx" -Name "(Default)" -Value "VLC.mpx"
    
    # Create file type entry
    New-Item -Path "HKCU:\Software\Classes\VLC.mpx" -Force | Out-Null
    Set-ItemProperty -Path "HKCU:\Software\Classes\VLC.mpx" -Name "(Default)" -Value "MPX Video File"
    
    # Set default icon
    New-Item -Path "HKCU:\Software\Classes\VLC.mpx\DefaultIcon" -Force | Out-Null
    Set-ItemProperty -Path "HKCU:\Software\Classes\VLC.mpx\DefaultIcon" -Name "(Default)" -Value "`"$vlcPath`",0"
    
    # Set open command
    New-Item -Path "HKCU:\Software\Classes\VLC.mpx\shell\open\command" -Force | Out-Null
    Set-ItemProperty -Path "HKCU:\Software\Classes\VLC.mpx\shell\open\command" -Name "(Default)" -Value "`"$vlcPath`" --started-from-file `"%1`""
    
    # Refresh explorer
    $code = @'
[DllImport("shell32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
'@
    
    $type = Add-Type -MemberDefinition $code -Name ShellHelper -Namespace Win32 -PassThru
    $type::SHChangeNotify(0x08000000, 0x0000, [IntPtr]::Zero, [IntPtr]::Zero)
    
    Write-Host ""
    Write-Host "🎉 Setup complete!" -ForegroundColor Green
    Write-Host "   .mpx files will now open in VLC Media Player" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Test it:" -ForegroundColor Yellow
    Write-Host "   1. Double-click any .mpx file" -ForegroundColor White
    Write-Host "   2. Or run: Start-Process your_video.mpx" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host "   Try running PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}
