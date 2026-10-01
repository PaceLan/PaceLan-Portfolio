#define ProductName "PacePilot"
#define ProductVersion "1.0.0"
#define ProductExe "PacePilot.exe"
#ifndef ProductDist
#define ProductDist "..\dist\PacePilot"
#endif

[Setup]
AppId={{A50DBE0F-3627-4A5F-9C35-D1505CF034CB}
AppName={#ProductName}
AppVersion={#ProductVersion}
AppPublisher=PacePilot
DefaultDirName={localappdata}\PacePilot
DefaultGroupName={#ProductName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Uninstallable=yes
OutputDir=..\release
OutputBaseFilename=PacePilot-{#ProductVersion}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
VersionInfoVersion=1.0.0.0

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "{#ProductDist}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#ProductName}"; Filename: "{app}\{#ProductExe}"
Name: "{autodesktop}\{#ProductName}"; Filename: "{app}\{#ProductExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ProductExe}"; Description: "Launch {#ProductName}"; Flags: postinstall nowait skipifsilent
