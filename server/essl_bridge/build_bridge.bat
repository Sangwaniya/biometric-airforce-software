@echo off
set CSC_PATH=C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe

echo Copying eSSL Interop.zkemkeeper.dll from SDK...
copy /Y "..\..\Biometric\AI -device SDK\AI -device SDK\AI Device UserInfo - with photos Copy\AI Device UserInfo - with photos Copy\bin\Release\Interop.zkemkeeper.dll" ".\Interop.zkemkeeper.dll"

echo Compiling eSSLBridge.exe...
%CSC_PATH% /target:exe /platform:x86 /r:Interop.zkemkeeper.dll /out:eSSLBridge.exe eSSLBridge.cs

if exist eSSLBridge.exe (
    echo [SUCCESS] eSSLBridge.exe successfully built!
) else (
    echo [ERROR] Build failed.
)
