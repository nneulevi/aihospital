$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

python -m PyInstaller `
  --noconfirm `
  --console `
  --name MetalArtifactMaskToolDesktop `
  --workpath build_desktop `
  --distpath dist_desktop `
  --specpath build_desktop `
  --collect-all vtkmodules `
  --hidden-import vtkmodules.qt.QVTKRenderWindowInteractor `
  --hidden-import PySide6.QtXml `
  --hidden-import SimpleITK `
  metal_artifact_mask_desktop.py

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "Build finished: dist_desktop/MetalArtifactMaskToolDesktop/MetalArtifactMaskToolDesktop.exe"
