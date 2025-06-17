!include "MUI2.nsh"

Name "Intelligent Biostats"
OutFile "IntelligentBiostats-Setup.exe"
InstallDir "$PROGRAMFILES\Intelligent Biostats"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"
    
    # Copy the executable and all its dependencies
    File /r "dist\IntelligentBiostats\*.*"
    
    # Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\Intelligent Biostats"
    CreateShortcut "$SMPROGRAMS\Intelligent Biostats\Intelligent Biostats.lnk" "$INSTDIR\IntelligentBiostats.exe"
    
    # Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    # Add uninstall information to Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\IntelligentBiostats" \
                     "DisplayName" "Intelligent Biostats"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\IntelligentBiostats" \
                     "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
SectionEnd

Section "Uninstall"
    # Remove installed files
    RMDir /r "$INSTDIR"
    
    # Remove shortcuts
    Delete "$SMPROGRAMS\Intelligent Biostats\Intelligent Biostats.lnk"
    RMDir "$SMPROGRAMS\Intelligent Biostats"
    
    # Remove uninstall information
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\IntelligentBiostats"
SectionEnd 