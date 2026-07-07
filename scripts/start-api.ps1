Set-Location $PSScriptRoot\..
python -m uvicorn road_hawk.api:app --host 127.0.0.1 --port 8000 --reload