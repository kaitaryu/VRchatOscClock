dim fso
set fso = createObject("Scripting.FileSystemObject")
Set ws = CreateObject("Wscript.Shell")

ws.run "cmd /c" & fso.getParentFolderName(WScript.ScriptFullName) & "\\move.bat", vbhide