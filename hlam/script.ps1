# Функция получения системной информации
function Get-SystemInfo {
    $computerInfo = @{
        computer = $env:COMPUTERNAME
        user = $env:USERNAME
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    
    # Материнская плата
    $motherboard = Get-WmiObject Win32_BaseBoard
    $computerInfo.motherboard = @{
        manufacturer = $motherboard.Manufacturer
        product = $motherboard.Product
        serial = $motherboard.SerialNumber
    }
    
    # Процессор
    $cpu = Get-WmiObject Win32_Processor
    $computerInfo.cpu = @{
        name = $cpu.Name.Trim()
        cores = $cpu.NumberOfCores
        threads = $cpu.NumberOfLogicalProcessors
        maxClock = [math]::Round($cpu.MaxClockSpeed / 1000, 2)
    }
    
    # Оперативная память
    $ram = Get-WmiObject Win32_PhysicalMemory
    $totalRam = ($ram | Measure-Object -Property Capacity -Sum).Sum / 1GB
    $computerInfo.ram = @{
        totalGB = [math]::Round($totalRam, 2)
        slots = $ram.Count
        modules = $ram | ForEach-Object {
            @{
                manufacturer = $_.Manufacturer
                capacityGB = [math]::Round($_.Capacity / 1GB, 2)
                speed = $_.Speed
            }
        }
    }
    
    # Хранилище
    $disks = Get-WmiObject Win32_DiskDrive
    $computerInfo.storage = $disks | ForEach-Object {
        @{
            model = $_.Model
            sizeGB = [math]::Round($_.Size / 1GB, 2)
            interface = $_.InterfaceType
            serial = $_.SerialNumber.Trim()
        }
    }
    
    # Видеокарта
    $gpu = Get-WmiObject Win32_VideoController
    $computerInfo.gpu = $gpu | ForEach-Object {
        @{
            name = $_.Name
            ramMB = [math]::Round($_.AdapterRAM / 1MB, 2)
            driver = $_.DriverVersion
        }
    }
    
    # Сертификаты (личное хранилище текущего пользователя)
    $certs = Get-ChildItem -Path Cert:\CurrentUser\My -ErrorAction SilentlyContinue
    $computerInfo.certificates = $certs | ForEach-Object {
        @{
            subject = $_.Subject
            thumbprint = $_.Thumbprint
            issuer = $_.Issuer
            notAfter = $_.NotAfter.ToString('dd-MM-yyyy')
            notBefore = $_.NotBefore.ToString('dd-MM-yyyy')
        }
    }
    
    return $computerInfo
}



# Создаем временную папку
$tempDir = "$env:TEMP\certs_export_$([System.Guid]::NewGuid())"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Получаем все сертификаты из личного хранилища текущего пользователя
$certs = Get-ChildItem -Path Cert:\CurrentUser\My

$files = @()
foreach ($cert in $certs) {
    $thumbprint = $cert.Thumbprint
    $filePath = Join-Path $tempDir "$thumbprint.cer"
    Export-Certificate -Cert $cert -FilePath $filePath -Type CERT | Out-Null
    $files += "-F `"files=@$filePath`""
}

# Отправляем архив на сервер
$uri = "http://10.16.16.33:8000/parcer/cert/$env:COMPUTERNAME/$env:USERNAME"

$filesString = $files -join " "
Invoke-Expression "curl.exe -s $filesString $uri"

Remove-Item $tempDir -Recurse -Force
Write-Host "✅ Отправлено $($certs.Count) сертификатов"



# Собираем информацию
$data = Get-SystemInfo

# Конвертируем в JSON с правильной кодировкой
$jsonBody = $data | ConvertTo-Json -Depth 10

# Отправляем на сервер
try {
    $response = Invoke-RestMethod -Uri "http://10.16.16.33:8000/parcer/pc" `
        -Method Post `
        -Body $jsonBody `
        -ContentType "application/json; charset=utf-8" `
        -TimeoutSec 15
    
    Write-Host "✅ Характеристики отправлены успешно"
} catch {
    Write-Host "❌ Ошибка отправки: $($_.Exception.Message)"
}
