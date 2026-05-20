#!/bin/bash
# WSL 调用 Windows Git Credential Manager（路径含空格，供 git -c credential.helper 使用）
exec "/mnt/c/Program Files/Git/mingw64/bin/git-credential-manager.exe" "$@"
