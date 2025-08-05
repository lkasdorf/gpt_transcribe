; -------------------------------------------------------------
; GPT Transcribe – Installer (optimized version)
; -------------------------------------------------------------
#define MyAppName     "GPT Transcribe"
#define MyAppVersion  "v0.2-beta"
#define MyAppPublisher "Leon Kasdorf"
#define MyAppExeName  "gpt_transcribe.exe"

[Setup]
; unique GUID – double braces = {{}}
AppId={{EC8F017A-D72C-47EE-92FD-E1FC4310873C}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

; force 64-bit installation mode (x64 & Win 11 ARM)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

DisableProgramGroupPage=yes
LicenseFile=LICENSE
; Note: adjust the path if your LICENSE resides elsewhere.
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename=gpt_transcribe_install
SolidCompression=yes
WizardStyle=modern
SetupIconFile=logo\logo.ico             
; adjust if necessary
OutputDir=dist

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
      GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; ffmpeg binaries bundled in subfolder "ffmpeg"
Source: "packages\ffmpeg\*.exe"; DestDir: "{app}\ffmpeg"; \
        Flags: ignoreversion recursesubdirs createallsubdirs

; -------------------------------------------------------------
[Environment]
; add ffmpeg binaries folder to system PATH
; Flags:  system = HKLM,  setenv = effective immediately,  uninsdeletevalue = remove cleanly
Name: "Path"; Value: "{app}\ffmpeg"; \
      Flags: system setenv expandsz uninsdeletevalue

; -------------------------------------------------------------
[Icons]
Name: "{autoprograms}\{#MyAppName}";   Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}";    Filename: "{app}\{#MyAppExeName}"; \
      Tasks: desktopicon
Name: "{group}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"; \
      IconFilename: "{app}\logo\logo.ico"

; -------------------------------------------------------------
[Run]
Filename: "{app}\{#MyAppExeName}"; \
          Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
          Flags: nowait postinstall skipifsilent

; no separate [Code] section needed – PATH handling is done in [Environment]
