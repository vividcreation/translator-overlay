' デスクトップにショートカットを作成するスクリプト
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 現在のフォルダを取得
strCurrentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' デスクトップのパスを取得
strDesktop = WshShell.SpecialFolders("Desktop")

' ショートカットを作成
Set oShortcut = WshShell.CreateShortcut(strDesktop & "\翻訳オーバーレイ.lnk")
oShortcut.TargetPath = strCurrentDir & "\翻訳オーバーレイ.bat"
oShortcut.WorkingDirectory = strCurrentDir
oShortcut.Description = "リアルタイム翻訳オーバーレイアプリ"
oShortcut.WindowStyle = 7  ' 最小化して実行
oShortcut.Save

MsgBox "デスクトップにショートカットを作成しました！", vbInformation, "完了"



