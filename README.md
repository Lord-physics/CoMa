# CoMa

[Leer en español](LEEME.md)

CoMa brings unread messages from the Gmail, Outlook/Hotmail, and Educacyl Microsoft 365 inboxes into one Windows window. It summarizes message text locally and flags possible spam based on the user's corrections. Predictions never move or delete messages on their own.

## Install without administrator rights

Download `CoMa-Windows.zip` from the [latest GitHub release](https://github.com/Lord-physics/CoMa/releases/latest), extract it, and run in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-CoMa.ps1
```

CoMa installs in `%LOCALAPPDATA%\Programs\CoMa` and adds a Start menu shortcut. It starts automatically when the current user signs in; you can turn this off in the application. To uninstall, close CoMa and run `Uninstall-CoMa.ps1` from the installation folder. Account data and learning data remain in `%LOCALAPPDATA%\CoMa` so they can be reused after reinstalling.

## Download and install the latest version

Close CoMa, open PowerShell in `%LOCALAPPDATA%\Programs\CoMa`, and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\actualizar.ps1
```

You can also [download `actualizar.ps1` directly](https://github.com/Lord-physics/CoMa/raw/refs/heads/main/actualizar.ps1) if your installed version does not have it yet. The script downloads the latest public release from GitHub, checks its SHA-256 digest, and runs the installer for your Windows user without administrator rights. It keeps your accounts, spam learning, and automatic-start setting. No GitHub login or email credentials are needed for the download.

## Add accounts

Each provider requires an OAuth desktop application registration. CoMa **does not request or store your email password**. Enter the application's client ID under “Añadir cuenta” and complete authorization in your browser. You can add multiple accounts, including several from the same provider. Refresh tokens are encrypted with Windows DPAPI for the current user; message summaries are not stored on disk.

Select **Help** in the Add account window for provider-specific steps to obtain the required IDs, Google client secret, Microsoft tenant, and API permissions. Use the **Language** selector in the main window to switch between English and Spanish; the choice is saved for later sessions.

- **Gmail:** create a Google Cloud project, enable the Gmail API, configure the consent screen, and create a Desktop app OAuth client. Enter the client ID and client secret from the downloaded JSON file. If the app is in testing mode, add your account as a test user. CoMa requests `gmail.modify` to read, archive, mark as spam, and move messages to Trash.
- **Outlook/Hotmail:** register an application in Microsoft Entra that supports personal and organizational accounts. Enable public client flows and grant the delegated `Mail.ReadWrite`, `User.Read`, and `offline_access` permissions. Enter the application ID. CoMa displays a code for signing in at `microsoft.com/devicelogin`.
- **Educacyl:** use an Entra application that supports organizational accounts. The default tenant is `organizations`; you can enter a specific tenant ID if you know it. The organization may block third-party applications or require administrator consent. CoMa cannot bypass that policy.

Actions use the provider's official API. “Eliminar” moves a message to Trash or Deleted Items. “Spam y borrar” records the spam decision, moves the message to spam, and then moves it to Trash or Deleted Items. Outlook and Educacyl require two moves; if the second fails, CoMa reports the error and the message may remain in spam. “Abrir web” opens the provider's message link when available.

The classifier needs examples of both spam and “No es spam” before it starts flagging messages. You can label any message “No es spam”. To correct a false positive, you can also open “Posible spam”, select the message, and press “No es spam”. Only these explicit choices and the spam buttons train the model. CoMa stores word fingerprints and the decision, without storing message text.

## Build

On Windows with Python 3.14 and PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Build-CoMa.ps1
```

The script creates `dist\CoMa-Windows.zip` with `CoMa.exe` and the installer. Python is not required to run the packaged application. To run the local tests: `py -m unittest discover -s tests -v`.

## Known limits

Live access depends on OAuth client IDs, account consent, and Educacyl tenant policies. No credentials are included in the repository. Messages are downloaded again on refresh, so the first scan of a large inbox can take time. CoMa does not execute message HTML or attachments.

Documentation: [Gmail API](https://developers.google.com/workspace/gmail/api/reference/rest), [Google desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app), [Microsoft Graph](https://learn.microsoft.com/en-us/graph/api/user-list-messages?view=graph-rest-1.0), [Microsoft device code flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code).
