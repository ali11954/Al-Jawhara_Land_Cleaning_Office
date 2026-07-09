$env:PYTHONUTF8='1'
$env:PORT='7555'
Set-Location D:\ghith\aljwahrh_land
& "D:\ghith\aljwahrh_land\venv\Scripts\waitress-serve.exe" --host=0.0.0.0 --port=7555 --threads=4 wsgi:application
