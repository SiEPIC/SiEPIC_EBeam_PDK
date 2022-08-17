@echo off

REM This batch file is an installer for SiEPIC EBeam PDK in KLayout\tech\siepic_ebeam_pdk
REM This file assumes that 
REM - The SiEPIC_EBeam_PDK repository is installed (cloned) in (you)/Documents/GitHub
REM - That the KLAYOUT configuration file is (you)/klayout
REM - That the Lumerical INTERCONNECT Custom library folder is in one of:
REM   - (you)/AppData/Roaming/Lumerical/Custom
REM   - (you)/AppData/Roaming/Custom
REM Note that AppData is a hidden windows directory
REM Reset the INTERCONNECT "Custom" library directory and re-run this script if you still can't see the library in INTERCONNECT

:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
    IF "%PROCESSOR_ARCHITECTURE%" EQU "amd64" (
>nul 2>&1 "%SYSTEMROOT%\SysWOW64\cacls.exe" "%SYSTEMROOT%\SysWOW64\config\system"
) ELSE (
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
)

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params= %*
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params:"=""%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
:-------------------------------------- 

mkdir "%userprofile%"\KLayout\tech

mklink /d "%userprofile%"\KLayout\tech\SiEPIC_EBeam_PDK "%userprofile%"\Documents\GitHub\SiEPIC_EBeam_PDK\klayout\siepic_ebeam_pdk\
(call)

mklink /d "%userprofile%"\AppData\Roaming\Custom\SiEPIC_EBeam_PDK "%userprofile%"\Documents\GitHub\SiEPIC_EBeam_PDK\lumerical_CML\siepic_ebeam_pdk\

if %errorlevel% NEQ 0 (
    mklink /d "%userprofile%"\AppData\Roaming\Lumerical\Custom\SiEPIC_EBeam_PDK "%userprofile%"\Documents\GitHub\SiEPIC_EBeam_PDK\lumerical_CML\siepic_ebeam_pdk\
)

set /p Text= Hit Enter to continue...