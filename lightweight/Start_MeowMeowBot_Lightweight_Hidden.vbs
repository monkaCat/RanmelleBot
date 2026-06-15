Set shell = CreateObject("Shell.Application")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
target = folder & "\MeowMeowBot_Lightweight.pyw"
shell.ShellExecute "pythonw.exe", Chr(34) & target & Chr(34), folder, "runas", 0
