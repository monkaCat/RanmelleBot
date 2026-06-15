Set shell = CreateObject("WScript.Shell")
Set shellApp = CreateObject("Shell.Application")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
appScript = fso.BuildPath(scriptDir, "MeowMeowBot_Lightweight.pyw")
shell.CurrentDirectory = scriptDir

Function ExistsOnPath(exeName)
    ExistsOnPath = (shell.Run("%ComSpec% /c where " & exeName & " >nul 2>nul", 0, True) = 0)
End Function

Function PythonwFromPy()
    tempFile = shell.ExpandEnvironmentStrings("%TEMP%") & "\meowmeowbot_lightweight_pythonw.txt"
    cmd = "%ComSpec% /c py -3 -c " & Chr(34) & _
        "import sys, pathlib; print(str(pathlib.Path(sys.executable).with_name('pythonw.exe')))" & _
        Chr(34) & " > " & Chr(34) & tempFile & Chr(34)
    If shell.Run(cmd, 0, True) = 0 Then
        If fso.FileExists(tempFile) Then
            Set file = fso.OpenTextFile(tempFile, 1)
            PythonwFromPy = Trim(file.ReadAll)
            file.Close
            If fso.FileExists(PythonwFromPy) Then Exit Function
        End If
    End If
    PythonwFromPy = ""
End Function

If ExistsOnPath("py.exe") Then
    pythonwPath = PythonwFromPy()
    If pythonwPath <> "" Then
        shellApp.ShellExecute pythonwPath, Chr(34) & appScript & Chr(34), scriptDir, "runas", 0
        WScript.Quit 0
    End If
End If

If ExistsOnPath("pyw.exe") Then
    shellApp.ShellExecute "pyw.exe", "-3 " & Chr(34) & appScript & Chr(34), scriptDir, "runas", 0
    WScript.Quit 0
End If

If ExistsOnPath("pythonw.exe") Then
    shellApp.ShellExecute "pythonw.exe", Chr(34) & appScript & Chr(34), scriptDir, "runas", 0
    WScript.Quit 0
End If

MsgBox "Could not start MeowMeowBot Lightweight as admin without a console. Make sure Python is installed and py.exe, pyw.exe, or pythonw.exe is available.", vbExclamation, "MeowMeowBot Lightweight"
