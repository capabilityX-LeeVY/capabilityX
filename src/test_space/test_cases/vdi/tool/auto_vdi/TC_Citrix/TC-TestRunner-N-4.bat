@echo off
for /f "usebackq delims=" %%V in ("C:\dev\auto_vdi\n-4_GA_version.txt") do (
   call TestRunner-WRS-LastestV.bat %%V
)