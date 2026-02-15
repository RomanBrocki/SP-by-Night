$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSCommandPath)

$port = 8010
Start-Process "http://localhost:$port/06_MAPA_SP/mapa_sp_dominios.html"
python -m http.server $port

