Option Explicit
On Error Resume Next

Dim pythonPath, runnerPath, routine, shell, fileSystem, command, exitCode
If WScript.Arguments.Count <> 3 Then
    WScript.Quit 2
End If

pythonPath = WScript.Arguments(0)
runnerPath = WScript.Arguments(1)
routine = LCase(WScript.Arguments(2))
If routine <> "weekly" And routine <> "monthly" Then
    WScript.Quit 2
End If

Set fileSystem = CreateObject("Scripting.FileSystemObject")
If Not fileSystem.FileExists(pythonPath) Or Not fileSystem.FileExists(runnerPath) Then
    WScript.Quit 3
End If

command = """" & pythonPath & """"
If LCase(fileSystem.GetFileName(pythonPath)) = "py.exe" Then
    command = command & " -3"
End If
command = command & " """ & runnerPath & """ " & routine

Set shell = CreateObject("WScript.Shell")
exitCode = shell.Run(command, 0, True)
If Err.Number <> 0 Then
    WScript.Quit 1
End If

WScript.Quit exitCode
