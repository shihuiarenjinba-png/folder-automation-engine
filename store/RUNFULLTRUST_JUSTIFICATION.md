# Folder Automation Engine — runFullTrust justification draft

The package contains a packaged Win32 desktop application. `runFullTrust` is required so the desktop executable can operate on folders explicitly selected by the user, perform local copy or move operations, keep local processing state, and run the optional in-process folder watcher while the application is open.

The app does not use this capability to execute arbitrary commands, request administrator elevation, or modify Windows security settings.
