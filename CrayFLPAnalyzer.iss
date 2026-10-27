; Inno Setup 6 - instalación por usuario (sin administrador). NO compilado en el entorno de desarrollo.
#ifndef AppVersion
  #define AppVersion "0.2.0"
#endif
[Setup]
AppId={{B6B5C0D2-6A55-4C3C-9C57-C5A7A1F0A0E1}
AppName=Cray FLP Analyzer
AppVersion={#AppVersion}
AppPublisher=Cray LDR - La Zeta Music
DefaultDirName={autopf}\Cray FLP Analyzer
DefaultGroupName=Cray FLP Analyzer
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=CrayFLPAnalyzer-Setup
Compression=lzma2
SolidCompression=yes
UninstallDisplayName=Cray FLP Analyzer {#AppVersion}
UninstallDisplayIcon={app}\CrayFLPAnalyzer.exe
WizardStyle=modern
[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; Flags: unchecked
[Files]
Source: "..\dist\CrayFLPAnalyzer\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
[Icons]
Name: "{group}\Cray FLP Analyzer"; Filename: "{app}\CrayFLPAnalyzer.exe"
Name: "{autodesktop}\Cray FLP Analyzer"; Filename: "{app}\CrayFLPAnalyzer.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\CrayFLPAnalyzer.exe"; Description: "Iniciar Cray FLP Analyzer"; Flags: nowait postinstall skipifsilent
; Sin [UninstallDelete] sobre %APPDATA%\CrayFLPAnalyzer ni sobre Documentos: el desinstalador no toca proyectos, informes ni ajustes.
