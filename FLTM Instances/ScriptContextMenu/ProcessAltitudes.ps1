
param([string]$path)
if (-not $path) {
    Write-Host "No se proporcionó ninguna ruta o archivo."
    exit
}
# Definir las rutas
$scriptFolder = "C:\DataAnalysis"
$dbFolder = "C:\DataAnalysis\db"
$domDataFile = "$dbFolder\altitude_company.csv"
$fltmcFileName = "fltmc_instances.txt"
# Crear la carpeta db si no existe
if (-not (Test-Path -Path $dbFolder)) {
    New-Item -ItemType Directory -Force -Path $dbFolder
}
# Verificar si el archivo DOM existe y tiene menos de 7 días
$fileExists = Test-Path -Path $domDataFile
$fileIsRecent = $fileExists -and ((Get-Date) - (Get-Item $domDataFile).LastWriteTime).Days -lt 7
if (-not $fileIsRecent) {
    # Definir la URL de la página web
    $url = "https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/allocated-altitudes"
    
    # Validar la URL
    try {
        $response = Invoke-WebRequest -Uri $url -ErrorAction Stop
    }
    catch {
        Write-Host "Error al acceder a la URL: $_"
        exit
    }
    
    # Utilizar HtmlAgilityPack para procesar el contenido HTML
    try {
        Add-Type -Path "C:\DataAnalysis\HtmlAgilityPack.dll"
        $htmlDoc = New-Object HtmlAgilityPack.HtmlDocument
        $htmlDoc.LoadHtml($response.Content)
        
        # Crear un array para almacenar los resultados
        $results = @()
        
        # Navegar por cada fila de la tabla y extraer las altitudes y las compañías
        $rows = $htmlDoc.DocumentNode.SelectNodes("//tr")
        foreach ($row in $rows) {
            $cells = $row.SelectNodes("td")
            if ($cells.Count -ge 3) {
                $altitude = $cells[1].InnerText
                $company = $cells[2].InnerText
                if ($altitude -and $company) {
                    $results += [PSCustomObject]@{
                        Altitude = $altitude
                        Company  = $company
                    }
                }
            }
        }
        
        # Exportar los resultados a un archivo CSV en la carpeta db
        try {
            $results | Export-Csv -Path $domDataFile -NoTypeInformation -Delimiter ","
        }
        catch {
            Write-Host "Error al exportar datos a CSV: $_"
            exit
        }
    }
    catch {
        Write-Host "Error al procesar el contenido HTML: $_"
        exit
    }
}
# Determinar si el path es un directorio
if (Test-Path $path -PathType Container) {
    # Buscar el archivo específico "fltmc_instances.txt" dentro del directorio
    $fltmcFile = Get-ChildItem -Path $path -Filter $fltmcFileName -File
    if ($null -eq $fltmcFile) {
        Write-Host "No se encontró el archivo $fltmcFileName en el directorio proporcionado."
        exit
    }
    
    # Crear una carpeta con la fecha y hora actual en el directorio proporcionado
    $folderName = Join-Path -Path $path -ChildPath ("FLTMC_" + (Get-Date -Format "yyyyMMddHHmmss"))
    New-Item -ItemType Directory -Force -Path $folderName
}
else {
    Write-Host "El path proporcionado no es un directorio."
    exit
}
# Procesar el archivo encontrado
try {
    # Leer el contenido del archivo de texto
    $fileContent = Get-Content -Path $fltmcFile.FullName | Select-Object -Skip 1 | ForEach-Object {
        $properties = $_ -split '\s+', 7
        if ($properties[1] -match '^\D') {
            [PSCustomObject]@{
                Filter       = $properties[0]
                VolumeName   = $properties[1]
                Altitude     = $properties[2]
                InstanceName = $properties[3]
                Frame        = $properties[4]
                SprtFtrs     = $properties[5]
                VStatus      = $properties[6]
            }
        }
        else {
            [PSCustomObject]@{
                Filter       = $properties[0]
                VolumeName   = 'Desconocido'
                Altitude     = $properties[1]
                InstanceName = $properties[2]
                Frame        = $properties[3]
                SprtFtrs     = $properties[4]
                VStatus      = $properties[5]
            }
        }
    }
    
    # Exportar los objetos a un archivo CSV en la carpeta creada
    $csvFileName = Join-Path -Path $folderName -ChildPath ([System.IO.Path]::GetFileNameWithoutExtension($fltmcFile.Name) + ".csv")
    $fileContent | Export-Csv -Path $csvFileName -NoTypeInformation -Delimiter ","
}
catch {
    Write-Host "Error al procesar el archivo $($fltmcFile.FullName): $_"
}
# Leer el archivo CSV generado por el comando fltmc instances
try {
    $fltmcData = Get-ChildItem -Path $folderName -Filter "*.csv" | ForEach-Object {
        Import-Csv -Path $_.FullName
    }
}
catch {
    Write-Host "Error al leer los archivos CSV generados: $_"
    exit
}
# Filtrar los valores únicos de la columna 'Altitude'
$uniqueAltitudes = $fltmcData | Select-Object -Unique Altitude
# Crear un hashtable para un acceso rápido a las compañías por altitud
try {
    $webData = Import-Csv -Path $domDataFile
}
catch {
    Write-Host "Error al leer el archivo CSV generado desde la página web: $_"
    exit
}
$webLookup = @{}
foreach ($entry in $webData) {
    $webLookup[$entry.Altitude] = $entry.Company
}
# Comparar los valores únicos de 'Altitude' con el archivo web y guardar los resultados
$results = foreach ($altitude in $uniqueAltitudes.Altitude) {
    $company = if ($webLookup.ContainsKey($altitude)) { $webLookup[$altitude] } else { "Desconocido" }
    [PSCustomObject]@{
        Altitude = $altitude
        Company  = $company
    }
}
# Mostrar los resultados por pantalla
$results | Format-Table -AutoSize
# Exportar los resultados a un archivo CSV en la carpeta creada
$csvFilePath = "$folderName\checked_altitudes.csv"
try {
    $results | Export-Csv -Path $csvFilePath -NoTypeInformation -Delimiter ","
}
catch {
    Write-Host "Error al exportar los resultados a CSV: $_"
    exit
}
# Exportar los resultados a un archivo TXT en la carpeta creada
$txtFilePath = "$folderName\checked_altitudes.txt"
try {
    $results | Out-File -FilePath $txtFilePath
}
catch {
    Write-Host "Error al exportar los resultados a TXT: $_"
    exit
}
# Imprimir un mensaje de éxito
Write-Host "Los resultados se han guardado en $csvFilePath y $txtFilePath"
