del *.pyc /s /q
del m*.htm /s /q
del Log.txt /s /q
del *.cfg /s /q /a -h
taskkill /f /im python.exe
taskkill /f /im pythonw.exe
taskkill /f /im firefox.exe
pause