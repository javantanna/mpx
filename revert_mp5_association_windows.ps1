# ================================================
# Revert MP5 File Association + Uninstall (Windows)
# ================================================

Write-Host "🔄 Reverting .mp5 file association and cleaning up..." -ForegroundColor Cyan

# Step 1: Remove file association
Write-Host ""
Write-Host "📌 Step 1: Removing file association" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow

try {
    # Remove file extension entry
    if (Test-Path "HKCU:\Software\Classes\.mp5") {
        Write-Host "🔧 Removing registry entries..." -ForegroundColor Cyan
        Remove-Item -Path "HKCU:\Software\Classes\.mp5" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ .mp5 extension removed" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  .mp5 extension not found, skipping" -ForegroundColor Gray
    }
    
    # Remove file type entry
    if (Test-Path "HKCU:\Software\Classes\VLC.mp5") {
        Remove-Item -Path "HKCU:\Software\Classes\VLC.mp5" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ VLC.mp5 file type removed" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  VLC.mp5 file type not found, skipping" -ForegroundColor Gray
    }
    
    # Refresh explorer
    $code = @'
[DllImport("shell32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
'@
    
    $type = Add-Type -MemberDefinition $code -Name ShellHelper -Namespace Win32 -PassThru -ErrorAction SilentlyContinue
    $type::SHChangeNotify(0x08000000, 0x0000, [IntPtr]::Zero, [IntPtr]::Zero)
    
    Write-Host ""
    Write-Host "🎉 Cleanup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Summary:" -ForegroundColor White
    Write-Host "  ✅ .mp5 file association removed" -ForegroundColor Green
    Write-Host "  ✅ Registry entries cleaned up" -ForegroundColor Green
    Write-Host ""
    Write-Host "Note: Python packages and FFmpeg were NOT removed" -ForegroundColor Yellow
    Write-Host "      (they may be used by other projects)" -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host "   Try running PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}
