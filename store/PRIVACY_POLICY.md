# Folder Automation Engine — Privacy Policy Draft

Status: engineering-verified draft for owner/legal review. It is not yet hosted or approved for publication.

## Scope

Folder Automation Engine is a Windows desktop application that previews, copies or moves local files according to rules supplied by the user. It can optionally monitor a user-selected folder while the application is running.

## Data the app accesses

The app accesses only locations selected or configured by the user. It may read:

- folder paths and file names;
- file size, modification time and other file-system metadata;
- file contents required to copy or move a matching file;
- user-created configuration JSON files that the user explicitly selects.

File names, paths or document contents may be personal information depending on what the user chooses to process. The app does not require an account, contact list, location, microphone, camera or advertising identifier.

## Local storage

The app stores the selected UI language in a small versioned `preferences.json` file:

- unpackaged build: `%LOCALAPPDATA%\FolderAutomationEngine\preferences.json`;
- installed MSIX: under the package LocalState directory, normally `%LOCALAPPDATA%\Packages\<actual package family name>\LocalState\FolderAutomationEngine\preferences.json`.

The actual installed package family name must be taken from Windows/Partner Center; the repository candidate is not a promise of the final path.

For each configured root folder, processing history is stored at `<selected root>\.state\processed.sqlite3`. Configuration JSON is written only when the user selects a new save location. Input and output files remain in the folders selected by the user.

## External communication and disclosure

The implemented product workflow does not make external network requests, upload files, use telemetry or analytics, display advertising, or transmit credentials. The app contains no OAuth or cloud-account sign-in.

If the user selects a cloud-synchronized folder, network drive or other externally managed location, that provider or administrator may process the files independently of this app. The user is responsible for the settings and privacy terms of that environment.

The app does not disclose data to the publisher or to third parties through its own code.

## Retention and deletion

Data is kept locally until the user removes it or the applicable Windows/app-data cleanup removes it. To delete app-created data, the user can:

1. close the app and stop watching;
2. delete any configuration JSON files the user saved;
3. delete `<selected root>\.state\processed.sqlite3` if processing history is no longer needed;
4. delete the `FolderAutomationEngine\preferences.json` file from the applicable LocalState or `%LOCALAPPDATA%` location;
5. delete copied output files if they are no longer needed.

Moving a file intentionally removes it from the configured input folder after the destination is safely published. Uninstall behavior and MSIX LocalState retention must be confirmed on the final installed package before publication.

## User controls and safeguards

The user selects every root, source, destination and rule. A successful no-write Dry Run and explicit confirmation are required before live one-time processing. Existing destination files are not overwritten. Changing the rules or observed inputs invalidates the prior preview. Watching is optional and can be stopped by the user; closing the app signals watching to stop and waits for active work to reach a safe boundary.

## Contact and Store field

Publisher contact, effective date, support address and public policy destination remain owner decisions. Microsoft documentation states that Partner Center may accept policy text directly, but current Store policy can require a valid privacy-policy URL when an app accesses personal information. Confirm the live submission form and legal requirements before upload.

Official references reviewed 2026-10-25:

- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/support-info
- https://learn.microsoft.com/en-us/windows/apps/publish/store-policies
