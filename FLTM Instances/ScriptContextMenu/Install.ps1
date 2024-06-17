# Cambiar la política de ejecución para permitir la ejecución de scripts
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Definir las rutas
$dataAnalysisFolder = "C:\DataAnalysis"
$dbFolder = "$dataAnalysisFolder\db"
$ps1FileName = "ProcessAltitudes.ps1"

# Nuevas rutas para Documentacion y Registro
$documentacionFolderPath = "C:\Documentacion"
$registroFolderPath = "C:\Registro"

# URL para la versión específica de HtmlAgilityPack
$htmlAgilityPackUrl = "https://www.nuget.org/api/v2/package/HtmlAgilityPack/1.11.36"

# Rutas actualizadas
$nugetFilePath = "$dataAnalysisFolder\HtmlAgilityPack.nupkg"
$htmlAgilityPackDllPath = "$dataAnalysisFolder\HtmlAgilityPack.dll"
$ps1FilePath = "$dataAnalysisFolder\$ps1FileName"
$regFilePath = "$registroFolderPath\AddContextMenuOption.reg"
$unregFilePath = "$registroFolderPath\UninstallContextMenu.reg"

# Crear las carpetas necesarias
New-Item -ItemType Directory -Force -Path $dataAnalysisFolder -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $dbFolder -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $documentacionFolderPath -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $registroFolderPath -ErrorAction SilentlyContinue

# Descargar HtmlAgilityPack
Write-Host "Descargando HtmlAgilityPack..."
Invoke-WebRequest -Uri $htmlAgilityPackUrl -OutFile $nugetFilePath

# Extraer HtmlAgilityPack.dll
Write-Host "Extrayendo HtmlAgilityPack.dll..."
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($nugetFilePath, $dataAnalysisFolder)
Copy-Item -Path "$dataAnalysisFolder\lib\netstandard2.0\HtmlAgilityPack.dll" -Destination $htmlAgilityPackDllPath -Force

# Limpiar archivos innecesarios
Remove-Item -Path "$dataAnalysisFolder\lib" -Recurse -Force
Remove-Item -Path "$dataAnalysisFolder\_rels" -Recurse -Force
Remove-Item -Path "$dataAnalysisFolder\package" -Recurse -Force
Remove-Item -Path "$dataAnalysisFolder\[Content_Types].xml" -Force
Remove-Item -Path $nugetFilePath -Force

# Copiar los archivos y carpetas a la ruta correcta
Copy-Item -Path ".\$ps1FileName" -Destination $ps1FilePath -Force
Copy-Item -Path "Documentacion\*" -Destination $documentacionFolderPath -Recurse -Force
Copy-Item -Path "Registro\*" -Destination $registroFolderPath -Recurse -Force

# Ejecutar el archivo de registro para agregar la opción al menú contextual
Start-Process regedit.exe -ArgumentList "/s $regFilePath" -Wait

Write-Host "Configuración completada. Los archivos y carpetas se han copiado y las opciones de menú contextual se han registrado."

# Mantener la ventana abierta
Read-Host "Presiona Enter para cerrar la ventana"
