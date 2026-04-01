@echo off
REM Windows wrapper for skill-creator subprocesses.
REM Call the Claude CLI entrypoint directly and force non-interactive permissions.
node "C:\Users\toqu\AppData\Roaming\npm\node_modules\@anthropic-ai\claude-code\cli.js" %* --permission-mode bypassPermissions
