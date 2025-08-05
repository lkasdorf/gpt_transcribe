; -------------------------------------------------------------
; GPT Transcribe – Installer (optimierte Version)
; -------------------------------------------------------------
#define MyAppName     "GPT Transcribe"
#define MyAppVersion  "v0.2-beta"
#define MyAppPublisher "Leon Kasdorf"
#define MyAppExeName  "gpt_transcribe.exe"

[Setup]
; eindeutige GUID – doppelte Klammern = {{}}
AppId={{EC8F017A-D72C-47EE-92FD-E1FC4310873C}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

; 64-Bit-Installationsmodus forcieren (x64 & Win 11 ARM)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

DisableProgramGroupPage=yes
LicenseFile=LICENSE
; Hinweis: Passe den Pfad an, falls deine LICENSE woanders liegt.
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename=gpt_transcribe_install
SolidCompression=yes
WizardStyle=modern
SetupIconFile=logo\logo.ico             
; <- falls nötig anpassen
OutputDir=dist

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
      GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Haupt-Executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; ffmpeg-Binaries gebündelt in Unterordner „ffmpeg“
Source: "packages\ffmpeg\*.exe"; DestDir: "{app}\ffmpeg"; \
        Flags: ignoreversion recursesubdirs createallsubdirs

; -------------------------------------------------------------
[Environment]
; Installationspfad der ffmpeg-Binaries systemweit an PATH anhängen
; Flags:  system = HKLM,  setenv = sofort wirksam,  uninsdeletevalue = sauber entfernen
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

; Kein eigener [Code]-Abschnitt mehr nötig – PATH-Handling läuft über [Environment]
