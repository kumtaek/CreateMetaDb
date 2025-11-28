cd D:\Analyzer\CreateMetaDb
Get-ChildItem -Recurse -Filter *.py | Select-Object -Expand FullName > list.txt
tar -czvf pys.tar.gz -T list.txt
certutil -encode pys.tar.gz pys.log
del ../pys*.*
move pys*.* ../
