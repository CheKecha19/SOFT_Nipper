batch
@echo off
REM Скрипт для Nipper.
REM Дёргает .txt файлы из inputfolder, проверяет на уязвимости и выдаёт отчёты в outputfolder
REM Строки для замены путей: 7, 10-12.
REM Выполняется как из .bat файла, так и из самого CMD.
 
REM Объявляем путь к директории с файлами
set "Path=C:\github\Nipper"
 
REM Перейти в директорию с nipper.exe
cd /d "%Path%"
 
REM Убедиться, что указанные пути верны
set "nipperExecutable=%Path%\nipper.exe"
set "inputFolder=%Path%\configs"
set "outputFolder=%Path%\results"
 
REM Найти все .txt файлы
for %%f in ("%inputFolder%\*.txt") do (
    set "txtFile=%%f"
    set "fileName=%%~nf"
    call :processFile
)
 
pause
exit /b
 
:processFile
setlocal
set "baseName=%fileName:_=_%"
set "outputFileName=%baseName%.html"
set "outputFilePath=%outputFolder%\%outputFileName%"
set "nipperCommand=%nipperExecutable% --input="%txtFile%" --output="%outputFilePath%" --css"
 
REM Вывод информации для отладки
echo Executing command: %nipperCommand%
 
REM Выполнение команды
%COMSPEC% /c %nipperCommand%
 
REM Проверка, создан ли выходной файл
if exist "%outputFilePath%" (
    echo Файл %outputFileName% успешно создан
) else (
    echo Ошибка: файл %outputFileName% не создан
)
 
endlocal
exit /b
