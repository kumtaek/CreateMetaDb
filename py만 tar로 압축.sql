for /r %i in (*.py) do @echo %i >> list.txt

Get-ChildItem -Recurse -Filter *.py | Select-Object -Expand FullName > list.txt

tar -czvf pys.tar.gz -T list.txt

certutil -encode pys.tar.gz pys.log
