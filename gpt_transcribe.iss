[Setup]
AppName=gpt_transcribe
AppVersion=1.0
DefaultDirName={autopf}\\gpt_transcribe
DefaultGroupName=gpt_transcribe
OutputBaseFilename=gpt_transcribe_setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\gpt_transcribe.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\gpt_transcribe"; Filename: "{app}\\gpt_transcribe.exe"
Name: "{group}\\Uninstall gpt_transcribe"; Filename: "{uninstallexe}"
