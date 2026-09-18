@echo off
set CSC_PATH=C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe

echo Copying Interop.zkemkeeper.dll from SDK...
copy /Y "..\..\Biometric\AI -device SDK\AI -device SDK\AI Device UserInfo - with photos Copy\AI Device UserInfo - with photos Copy\bin\Release\Interop.zkemkeeper.dll" ".\Interop.zkemkeeper.dll"

echo Compiling BiomaxBridge.exe...
%CSC_PATH% /target:exe /platform:x86 /r:Interop.zkemkeeper.dll /out:BiomaxBridge.exe BiomaxBridge.cs

if exist BiomaxBridge.exe (
    echo [SUCCESS] BiomaxBridge.exe successfully built!
) else (
    echo [ERROR] Build failed.
)
