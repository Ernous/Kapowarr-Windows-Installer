Unicode True

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"
!include "version.nsh"

Name "Kapowarr"
OutFile "installer_output\Kapowarr-${APP_VERSION}-NSIS-Setup-${ARCH}.exe"
InstallDir "$PROGRAMFILES64\Kapowarr"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "favicon.ico"
!define MUI_UNICON "favicon.ico"
!define MUI_COMPONENTSPAGE_SMALLDESC

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Kapowarr Application (Required)" MainSection
    SectionIn 1 2 3 RO
    SetOutPath "$INSTDIR"
    
    DetailPrint "Installing Kapowarr and Python environment..."
    File /r "build_temp\app_files\*"
    
    File /r "installer_files"
    File "favicon.ico"
    File "LICENSE"

    CreateDirectory "$INSTDIR\logs"
    nsExec::Exec 'icacls "$INSTDIR\logs" /grant *S-1-5-32-545:(OI)(CI)M /T'
    nsExec::Exec 'icacls "$INSTDIR" /grant *S-1-5-32-545:(OI)(CI)M /T'

    DetailPrint "Configuring Python environment..."
    nsExec::ExecToLog 'cmd.exe /c ""$INSTDIR\installer_files\prepare_python.bat" "$INSTDIR" --no-pause"'
    
    WriteUninstaller "$INSTDIR\uninstall.exe"

    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Kapowarr" "DisplayName" "Kapowarr"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Kapowarr" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Kapowarr" "DisplayIcon" "$INSTDIR\favicon.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Kapowarr" "Publisher" "Kapowarr"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Kapowarr" "DisplayVersion" "${APP_VERSION}"
SectionEnd

Section "Windows Service" ServiceSection
    DetailPrint "Setting up Windows Service..."
    nsExec::ExecToLog 'cmd.exe /c ""$INSTDIR\installer_files\setup_service.bat" "$INSTDIR" --no-pause"'
SectionEnd

Section "Tray Application & Autostart" TraySection
    SetOutPath "$INSTDIR"
    File "installer_files\kapowarr_tray.exe"
    WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Run" "Kapowarr" '"$INSTDIR\kapowarr_tray.exe"'
SectionEnd

Section "-Post"
    Call DumpLog
SectionEnd

Function DumpLog
    DetailPrint "Saving installation log to $INSTDIR\logs\installer_full_report.log..."
    Push $0
    Push $1
    Push $2
    Push $3
    
    StrCpy $0 "$INSTDIR\logs\installer_full_report.log"
    FindWindow $1 "#32770" "" $HWNDPARENT
    GetDlgItem $1 $1 1016
    StrCmp $1 0 exit
    
    FileOpen $2 $0 "w"
    StrCpy $3 0
    
    loop:
        SendMessage $1 ${LVM_GETITEMTEXT} $3 $0
        Pop $0
        StrCmp $0 "" done
        FileWrite $2 "$0$\r$\n"
        IntOp $3 $3 + 1
        Goto loop
        
    done:
        FileClose $2
    exit:
        Pop $3
        Pop $2
        Pop $1
        Pop $0
FunctionEnd

Section "-Shortcuts"
    CreateDirectory "$SMPROGRAMS\Kapowarr"
    CreateShortcut "$SMPROGRAMS\Kapowarr\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\favicon.ico"
    CreateShortcut "$SMPROGRAMS\Kapowarr\Kapowarr Web Interface.lnk" "http://localhost:5656" "" "$INSTDIR\favicon.ico"
    
    ${If} ${SectionIsSelected} ${TraySection}
        CreateShortcut "$SMPROGRAMS\Kapowarr\Kapowarr.lnk" "$INSTDIR\kapowarr_tray.exe" "" "$INSTDIR\favicon.ico"
        CreateShortcut "$DESKTOP\Kapowarr.lnk" "$INSTDIR\kapowarr_tray.exe" "" "$INSTDIR\favicon.ico"
    ${EndIf}
SectionEnd

Section "Uninstall"
    DetailPrint "Stopping and removing service..."
    nsExec::ExecToLog 'cmd.exe /c "$INSTDIR\installer_files\full_cleanup.bat" "$INSTDIR"'
    
    DeleteRegValue HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Run" "Kapowarr"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Kapowarr"
    
    Delete "$SMPROGRAMS\Kapowarr\*.*"
    RMDir "$SMPROGRAMS\Kapowarr"
    Delete "$DESKTOP\Kapowarr.lnk"
    
    RMDir /r "$INSTDIR"
SectionEnd

Function .onInit
    InitPluginsDir
    nsExec::Exec 'taskkill /F /IM kapowarr_tray.exe /T'
    nsExec::Exec 'taskkill /F /IM python.exe /T'

    FileOpen $0 "$TEMP\exclude_nsis.txt" w
    FileWrite $0 ".zip$\r$\n"
    FileWrite $0 ".log$\r$\n"
    FileWrite $0 "\python\$\r$\n"
    FileWrite $0 "\installer_files\$\r$\n"
    FileWrite $0 "\installer_output\$\r$\n"
    FileWrite $0 "\logs\$\r$\n"
    FileWrite $0 "\db\$\r$\n"
    FileWrite $0 ".db$\r$\n"
    FileWrite $0 ".sqlite$\r$\n"
    FileWrite $0 "config.json$\r$\n"
    FileWrite $0 "settings.json$\r$\n"
    FileClose $0
FunctionEnd
