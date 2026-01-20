Remove-Item deliverables\milestone1.zip -ErrorAction SilentlyContinue
Compress-Archive -Path deliverables\milestone1\* -DestinationPath deliverables\milestone1.zip -Force
Write-Host "Successfully packaged deliverables/milestone1 into milestone1.zip"
