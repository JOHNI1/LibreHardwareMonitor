If WScript.Arguments.length = 0 Then
    Set objShell = CreateObject("Shell.Application")
    objShell.ShellExecute "wscript.exe", Chr(34) & WScript.ScriptFullName & Chr(34) & " uac", "", "runas", 1
Else
    Set WshShell = CreateObject("WScript.Shell")
    WshShell.Run Chr(34) & "C:\Program Files (x86)\LibreHardwareMonitor\avrtemp.bat" & Chr(34), 0, True
End If