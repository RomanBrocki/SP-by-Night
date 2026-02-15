$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$port = 8008
$url = "http://127.0.0.1:$port/01_BACKGROUND_NARRADOR/teia_de_conexoes_mapa.html"

Write-Host "Iniciando servidor local em $url"
Write-Host "Para encerrar: feche esta janela ou pressione Ctrl+C"

Start-Process $url
python -m http.server $port

