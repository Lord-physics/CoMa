"""Small, local Spanish/English catalogue and saved language preference."""

import json
import os
from pathlib import Path

from .storage import data_dir


_language = "es"

STRINGS = {
    "es": {
        "window_title": "CoMa · Bandeja no leída",
        "inbox": "  Bandeja no leída",
        "add_account": "Añadir cuenta",
        "remove_account": "Quitar cuenta",
        "refresh": "Actualizar",
        "update_now": "Actualizar CoMa",
        "release_downloading": "Descargando y verificando la última versión…",
        "update_installing": "Instalando CoMa {version}; la aplicación se cerrará y volverá a abrirse.",
        "update_script_missing": "Falta actualizar.ps1 junto al ejecutable de CoMa.",
        "update_launch_failed": "No se pudo iniciar la instalación de la actualización.",
        "release_connection_failed": "No se pudo consultar la última versión en GitHub.",
        "release_missing": "La última versión de GitHub no contiene CoMa-Windows.zip.",
        "release_invalid": "Los datos del paquete publicado no son válidos.",
        "release_bad_destination": "Selecciona una carpeta existente y un archivo .zip.",
        "release_too_large": "El paquete supera el tamaño máximo permitido.",
        "release_hash_failed": "La descarga no coincide con la huella SHA-256 publicada por GitHub.",
        "release_download_failed": "No se pudo descargar o guardar el paquete.",
        "language": "Idioma:",
        "autostart": "Abrir CoMa al iniciar sesión",
        "no_messages_loaded": "Sin mensajes cargados",
        "possible_spam": "Posible spam: {count}",
        "ready": "Añade una cuenta para empezar.",
        "autostart_title": "Inicio automático",
        "busy": "Espera a que termine la operación actual.",
        "operation_failed": "La operación falló.",
        "syncing": "Sincronizando cuentas…",
        "unread_count": "{count} correos no leídos",
        "sync_done": "Sincronización terminada.",
        "no_unread": "No hay mensajes no leídos o todavía no has añadido ninguna cuenta.",
        "open_web": "Abrir web",
        "not_spam": "No es spam",
        "archive": "Archivar",
        "delete": "Eliminar",
        "spam": "Spam",
        "spam_delete": "Spam y borrar",
        "open_mail": "Abrir correo",
        "browser_failed": "No se pudo abrir el navegador.",
        "action_done": "Acción aplicada en el proveedor.",
        "applying": "Aplicando acción…",
        "correction_saved": "Corrección guardada: no es spam.",
        "provider": "Proveedor",
        "email_address": "Correo electrónico",
        "auto_provider": "Detectar automáticamente",
        "invalid_email": "Introduce una dirección de correo válida.",
        "choose_provider": "Elige el proveedor de esta cuenta.",
        "client_id": "ID de aplicación OAuth",
        "google_secret": "Secreto de Google (si procede)",
        "microsoft_tenant": "Tenant Microsoft",
        "account_hint": "CoMa detecta el proveedor por el correo y abre su acceso oficial.\nPara la primera cuenta de cada proveedor necesitas su ID OAuth; pulsa Ayuda. Después se reutiliza.",
        "help": "Ayuda",
        "connect": "Conectar cuenta",
        "missing_client_id": "Introduce el ID de aplicación OAuth.",
        "invalid_tenant": "Indica un tenant de Microsoft válido.",
        "authorizing": "Iniciando autorización…",
        "account_added": "Cuenta {email} añadida.",
        "accounts": "Cuentas",
        "no_accounts": "No hay cuentas configuradas.",
        "remove_selected": "Quitar cuenta seleccionada",
        "select_summary": "Selecciona un mensaje para ver su resumen.",
        "help_title": "Ayuda · {provider}",
        "open_instructions": "Abrir instrucciones oficiales",
        "official_links": "Enlaces oficiales (pulsa para abrirlos):",
        "close": "Cerrar",
        "lang_changed": "Idioma cambiado.",
        "google_browser": "Completa el acceso de Google en el navegador.",
        "google_auth_failed": "No se completó la autorización de Google.",
        "microsoft_start_failed": "No se pudo iniciar el acceso de Microsoft. Revisa el identificador de aplicación.",
        "microsoft_device": "Abre {url} e introduce: {code}",
        "microsoft_rejected": "Microsoft rechazó el acceso ({error}).",
        "microsoft_expired": "Caducó el código de acceso de Microsoft.",
        "browser_callback": "CoMa: autorización recibida. Puedes cerrar esta pestaña.",
        "http_service": "El servicio devolvió HTTP {code}.",
        "http_mail_connect": "No se pudo conectar con el servicio de correo.",
        "http_auth": "Autenticación rechazada (HTTP {code}).",
        "http_auth_connect": "No se pudo conectar con el servicio de autenticación.",
        "refresh_missing": "El proveedor no entregó acceso renovable. Revisa el consentimiento y vuelve a intentarlo.",
        "account_missing": "La cuenta ya no existe.",
        "learning_failed": "La acción se aplicó al correo, pero no se pudo guardar el aprendizaje local.",
        "sender_unknown": "Remitente desconocido",
        "subject_missing": "(Sin asunto)",
        "summary_missing": "Sin texto para resumir.",
        "gmail_partial": "Marcado como spam, pero no se pudo mover a papelera: {error}",
        "graph_pagination": "Paginación inesperada de Microsoft Graph",
        "microsoft_partial": "Movido a spam, pero no a papelera: {error}",
    },
    "en": {
        "window_title": "CoMa · Unread inbox",
        "inbox": "  Unread inbox",
        "add_account": "Add account",
        "remove_account": "Remove account",
        "refresh": "Refresh",
        "update_now": "Update CoMa",
        "release_downloading": "Downloading and verifying the latest version…",
        "update_installing": "Installing CoMa {version}; the app will close and reopen.",
        "update_script_missing": "actualizar.ps1 is missing next to the CoMa executable.",
        "update_launch_failed": "Could not start the update installation.",
        "release_connection_failed": "Could not check the latest version on GitHub.",
        "release_missing": "The latest GitHub release does not contain CoMa-Windows.zip.",
        "release_invalid": "The published package details are invalid.",
        "release_bad_destination": "Choose an existing folder and a .zip file.",
        "release_too_large": "The package exceeds the maximum allowed size.",
        "release_hash_failed": "The download does not match the SHA-256 digest published by GitHub.",
        "release_download_failed": "Could not download or save the package.",
        "language": "Language:",
        "autostart": "Open CoMa when I sign in",
        "no_messages_loaded": "No messages loaded",
        "possible_spam": "Possible spam: {count}",
        "ready": "Add an account to get started.",
        "autostart_title": "Start automatically",
        "busy": "Wait for the current operation to finish.",
        "operation_failed": "The operation failed.",
        "syncing": "Syncing accounts…",
        "unread_count": "{count} unread messages",
        "sync_done": "Sync finished.",
        "no_unread": "No unread messages, or no accounts have been added yet.",
        "open_web": "Open on web",
        "not_spam": "Not spam",
        "archive": "Archive",
        "delete": "Delete",
        "spam": "Spam",
        "spam_delete": "Spam and delete",
        "open_mail": "Open message",
        "browser_failed": "Could not open the browser.",
        "action_done": "Action applied by the provider.",
        "applying": "Applying action…",
        "correction_saved": "Correction saved: not spam.",
        "provider": "Provider",
        "email_address": "Email address",
        "auto_provider": "Detect automatically",
        "invalid_email": "Enter a valid email address.",
        "choose_provider": "Choose the provider for this account.",
        "client_id": "OAuth application ID",
        "google_secret": "Google client secret (if needed)",
        "microsoft_tenant": "Microsoft tenant",
        "account_hint": "CoMa detects the provider from your email and opens its official sign-in.\nThe first account for each provider needs an OAuth app ID; select Help. CoMa then reuses it.",
        "help": "Help",
        "connect": "Connect account",
        "missing_client_id": "Enter the OAuth application ID.",
        "invalid_tenant": "Enter a valid Microsoft tenant.",
        "authorizing": "Starting authorization…",
        "account_added": "Account {email} added.",
        "accounts": "Accounts",
        "no_accounts": "No accounts configured.",
        "remove_selected": "Remove selected account",
        "select_summary": "Select a message to see its summary.",
        "help_title": "Help · {provider}",
        "open_instructions": "Open official instructions",
        "official_links": "Official links (select to open):",
        "close": "Close",
        "lang_changed": "Language changed.",
        "google_browser": "Complete Google sign-in in your browser.",
        "google_auth_failed": "Google authorization was not completed.",
        "microsoft_start_failed": "Could not start Microsoft sign-in. Check the application ID.",
        "microsoft_device": "Open {url} and enter: {code}",
        "microsoft_rejected": "Microsoft rejected sign-in ({error}).",
        "microsoft_expired": "The Microsoft sign-in code expired.",
        "browser_callback": "CoMa: authorization received. You can close this tab.",
        "http_service": "The service returned HTTP {code}.",
        "http_mail_connect": "Could not connect to the mail service.",
        "http_auth": "Authentication rejected (HTTP {code}).",
        "http_auth_connect": "Could not connect to the authentication service.",
        "refresh_missing": "The provider did not issue a refresh token. Check consent and try again.",
        "account_missing": "The account no longer exists.",
        "learning_failed": "The mail action succeeded, but local learning could not be saved.",
        "sender_unknown": "Unknown sender",
        "subject_missing": "(No subject)",
        "summary_missing": "No text to summarize.",
        "gmail_partial": "Marked as spam, but could not move to Trash: {error}",
        "graph_pagination": "Unexpected Microsoft Graph pagination",
        "microsoft_partial": "Moved to spam, but not to Deleted Items: {error}",
    },
}

HELP_LINKS = {
    "gmail": (
        ("1. Consola de Google Cloud", "1. Google Cloud Console", "https://console.cloud.google.com/"),
        ("2. Activar Gmail API", "2. Enable Gmail API", "https://console.cloud.google.com/apis/library/gmail.googleapis.com"),
        ("3. Audiencia y usuarios de prueba", "3. Audience and test users", "https://support.google.com/cloud/answer/15549945"),
        ("4. Cliente OAuth de escritorio", "4. Desktop OAuth client", "https://developers.google.com/identity/protocols/oauth2/native-app"),
        ("5. Permisos de Gmail API", "5. Gmail API scopes", "https://developers.google.com/workspace/gmail/api/auth/scopes"),
        ("6. Verificación para publicar", "6. Verification for public release", "https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification"),
    ),
    "outlook": (
        ("1. Centro Microsoft Entra", "1. Microsoft Entra admin center", "https://entra.microsoft.com/"),
        ("2. Registrar una aplicación", "2. Register an application", "https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app"),
        ("3. Tipos de cuenta admitidos", "3. Supported account types", "https://learn.microsoft.com/en-us/entra/identity-platform/single-and-multi-tenant-apps"),
        ("4. Cliente público de escritorio", "4. Public desktop client", "https://learn.microsoft.com/en-us/entra/identity-platform/scenario-desktop-app-registration"),
        ("5. Permisos de Microsoft Graph", "5. Microsoft Graph permissions", "https://learn.microsoft.com/en-us/graph/permissions-reference"),
        ("6. Acceso con código de dispositivo", "6. Device code sign-in", "https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code"),
    ),
    "educacyl": (
        ("1. Ayuda oficial de correo Educacyl", "1. Official Educacyl mail help", "https://www.educa.jcyl.es/es/informacion/informacion-usuarios/correo-electronico-manuales-configuracion"),
        ("2. Registrar una aplicación Entra", "2. Register an Entra application", "https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app"),
        ("3. Cliente público de escritorio", "3. Public desktop client", "https://learn.microsoft.com/en-us/entra/identity-platform/scenario-desktop-app-registration"),
        ("4. Permisos de Microsoft Graph", "4. Microsoft Graph permissions", "https://learn.microsoft.com/en-us/graph/permissions-reference"),
        ("5. Consentimiento del administrador", "5. Administrator consent", "https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/user-admin-consent-overview"),
        ("6. Acceso con código de dispositivo", "6. Device code sign-in", "https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code"),
    ),
}

HELP = {
    "es": {
        "gmail": (
            "1. Proyecto de Google Cloud. Entra con la cuenta que administrará CoMa y crea un proyecto, "
            "o selecciona uno existente. Si Google exige verificación en dos pasos para entrar en la consola, "
            "complétala allí. La contraseña no se escribe en CoMa.\n\n"
            "2. Gmail API. En el proyecto correcto, abre APIs y servicios > Biblioteca, busca Gmail API y "
            "pulsa Habilitar. Activar la API en otro proyecto no sirve para el cliente OAuth de CoMa.\n\n"
            "3. Pantalla de consentimiento. En Google Auth Platform > Branding indica CoMa, un correo "
            "de asistencia y uno de contacto. En Audience elige External si usarán la aplicación cuentas "
            "ajenas a tu organización. Durante las pruebas, añade cada Gmail que vaya a conectarse a la lista "
            "de usuarios de prueba. Las autorizaciones de prueba pueden caducar a los siete días.\n\n"
            "4. Permiso. En Data Access añade https://www.googleapis.com/auth/gmail.modify. CoMa lo "
            "necesita para leer correos sin marcarlos como leídos y aplicar archivar, spam y papelera. "
            "Google lo clasifica como permiso restringido; una publicación para cualquier usuario puede "
            "necesitar verificación de la aplicación.\n\n"
            "5. Cliente de escritorio. En Google Auth Platform > Clients, pulsa Create client y elige "
            "Desktop app. Descarga el JSON y busca installed.client_id y, si existe, "
            "installed.client_secret. En CoMa pon esos valores en ID de aplicación OAuth y Secreto de Google; "
            "deja Tenant Microsoft sin cambios. No subas el JSON ni tokens a GitHub.\n\n"
            "6. Conexión. Escribe el correo en Añadir cuenta, elige Gmail si no se detectó y pulsa Conectar "
            "cuenta. Completa el consentimiento en la página oficial de Google. CoMa recibe la respuesta "
            "en una dirección local temporal que configura por sí solo. Si aparece access_denied, comprueba "
            "el usuario de prueba, el proyecto y el permiso solicitado."
        ),
        "outlook": (
            "1. Acceso a Entra. Entra en Microsoft Entra admin center con una cuenta que pueda registrar "
            "aplicaciones en un directorio propio. La cuenta de Outlook/Hotmail que conectarás después puede "
            "ser distinta de la cuenta que registra la aplicación. Si no aparece Registros de aplicaciones, "
            "necesitas acceso a un directorio que permita crear registros.\n\n"
            "2. Registro. Ve a Identidad > Aplicaciones > Registros de aplicaciones > Nuevo registro. "
            "Pon CoMa como nombre y elige Cuentas de cualquier directorio organizativo y cuentas Microsoft "
            "personales. Una opción solo organizativa impediría iniciar sesión con Hotmail/Outlook personal.\n\n"
            "3. Identificador. Tras registrar, abre Información general y copia Id. de aplicación (cliente) "
            "en ID de aplicación OAuth de CoMa. No copies Id. de objeto ni Id. de directorio en ese campo. "
            "Para Outlook personal deja Tenant Microsoft en common.\n\n"
            "4. Cliente público. En Autenticación > Configuración avanzada activa Permitir flujos de "
            "cliente público. CoMa usa el código de dispositivo; no necesita secreto de cliente ni URI "
            "de redirección para este flujo.\n\n"
            "5. Permisos. En Permisos de API > Agregar un permiso > Microsoft Graph > Permisos delegados, "
            "comprueba Mail.ReadWrite, User.Read y offline_access. Mail.ReadWrite permite leer y mover "
            "mensajes; CoMa no solicita permiso para enviar correo. El usuario concederá el acceso cuando "
            "Microsoft lo pida, si su cuenta y su organización lo permiten.\n\n"
            "6. Conexión. Escribe el correo en CoMa y pulsa Conectar cuenta. CoMa abre la página de Microsoft "
            "y muestra un código temporal; introdúcelo allí, inicia sesión y acepta los permisos. Si Microsoft "
            "rechaza el acceso, revisa el tipo de cuenta, el ID de aplicación, el flujo público y el consentimiento."
        ),
        "educacyl": (
            "1. Comprueba el buzón. Abre el correo de Educacyl desde su portal oficial y confirma que "
            "la cuenta @educa.jcyl.es puede entrar en Microsoft 365. Si no puedes acceder al correo web, "
            "resuelve primero ese problema con el soporte de Educacyl.\n\n"
            "2. Comprueba la política de la organización. La Junta puede limitar aplicaciones externas o "
            "exigir consentimiento del administrador. CoMa no puede cambiar esa política. Si aparece "
            "necesita aprobación, comunica al soporte o administrador el nombre CoMa, el ID de aplicación "
            "y los permisos delegados que solicita; no envíes contraseñas ni códigos temporales.\n\n"
            "3. Registro de Entra. Si tienes un directorio donde puedes registrar aplicaciones, crea un "
            "registro para cuentas organizativas en Microsoft Entra. Puedes usar un registro que también "
            "admita cuentas personales si su configuración y la política de Educacyl lo permiten. Copia "
            "Id. de aplicación (cliente), no Id. de objeto, en ID de aplicación OAuth de CoMa.\n\n"
            "4. Cliente público. En Autenticación > Configuración avanzada activa Permitir flujos de "
            "cliente público. CoMa utiliza el código de dispositivo; no necesita secreto de cliente ni "
            "URI de redirección para este flujo.\n\n"
            "5. Permisos delegados. En Microsoft Graph configura Mail.ReadWrite, User.Read y "
            "offline_access. Mail.ReadWrite permite leer, archivar, enviar a correo no deseado y mover a "
            "papelera dentro de los límites de la cuenta. Si se bloquea el consentimiento, debe resolverlo "
            "el administrador del directorio de Educacyl.\n\n"
            "6. Tenant y conexión. Deja Tenant Microsoft en organizations para cuentas de trabajo o "
            "educativas, o usa el Id. de directorio (inquilino) que te facilite el administrador. Escribe "
            "tu correo @educa.jcyl.es y pulsa Conectar cuenta. Introduce en la página oficial de Microsoft "
            "el código temporal que muestre CoMa y completa la verificación."
        ),
    },
    "en": {
        "gmail": (
            "1. Google Cloud project. Sign in with the account that will manage CoMa and create a project, "
            "or select an existing one. If Google requires two-step verification to access the console, "
            "complete it there. Your password is never entered in CoMa.\n\n"
            "2. Gmail API. In the correct project, open APIs & Services > Library, find Gmail API and "
            "select Enable. Enabling it in a different project will not help CoMa's OAuth client.\n\n"
            "3. Consent screen. Under Google Auth Platform > Branding enter CoMa, a support email and "
            "a developer contact. Under Audience choose External if accounts outside your organization "
            "will use the app. While testing, add every Gmail address that will connect as a test user. "
            "Testing authorizations may expire after seven days.\n\n"
            "4. Scope. Under Data Access add https://www.googleapis.com/auth/gmail.modify. CoMa needs "
            "it to read without marking messages as read and to archive, mark as spam and move to Trash. "
            "Google classifies it as restricted; a public release may require app verification.\n\n"
            "5. Desktop client. Under Google Auth Platform > Clients choose Create client > Desktop app. "
            "Download the JSON and find installed.client_id and, if present, installed.client_secret. "
            "Enter them in CoMa's OAuth application ID and Google client secret fields; leave Microsoft "
            "tenant unchanged. Do not upload the JSON or tokens to GitHub.\n\n"
            "6. Connect. Enter the address in Add account, choose Gmail if detection failed and select "
            "Connect account. Complete consent on Google's official page. CoMa receives the response "
            "on a temporary local address it configures automatically. For access_denied, check the "
            "test-user list, project and requested scope."
        ),
        "outlook": (
            "1. Entra access. Sign in to the Microsoft Entra admin center with an account allowed to "
            "register apps in a directory you manage. The Outlook/Hotmail account you connect later may "
            "be different from the account registering the app. If App registrations is unavailable, "
            "you need access to a directory that permits registrations.\n\n"
            "2. Registration. Open Identity > Applications > App registrations > New registration. "
            "Name it CoMa and choose Accounts in any organizational directory and personal Microsoft "
            "accounts. An organizational-only choice prevents personal Hotmail/Outlook sign-in.\n\n"
            "3. App ID. Under Overview copy Application (client) ID into CoMa's OAuth application ID. "
            "Do not copy Object ID or Directory (tenant) ID into this field. For a personal Outlook "
            "account leave Microsoft tenant at common.\n\n"
            "4. Public client. Under Authentication > Advanced settings enable Allow public client flows. "
            "CoMa uses device code flow, which needs no client secret or redirect URI.\n\n"
            "5. Permissions. Under API permissions > Add a permission > Microsoft Graph > Delegated "
            "permissions, check Mail.ReadWrite, User.Read and offline_access. Mail.ReadWrite permits "
            "reading and moving messages; CoMa does not request permission to send mail. The user "
            "grants consent when Microsoft asks, if their account and organization allow it.\n\n"
            "6. Connect. Enter the address in CoMa and select Connect account. CoMa opens Microsoft's "
            "page and displays a temporary code; enter it there, sign in and grant permissions. If "
            "access is denied, review the account type, app ID, public flow and consent."
        ),
        "educacyl": (
            "1. Check the mailbox. Open Educacyl mail from its official portal and confirm that the "
            "@educa.jcyl.es account can access Microsoft 365. If webmail itself fails, resolve that "
            "with Educacyl support before configuring CoMa.\n\n"
            "2. Check organization policy. The education authority may restrict external apps or "
            "require administrator consent. CoMa cannot change that policy. If an approval-required "
            "message appears, give support or your administrator CoMa's name, application ID and "
            "requested delegated permissions; never send passwords or temporary codes.\n\n"
            "3. Entra registration. If you have a directory where you may register apps, create one "
            "for organizational accounts in Microsoft Entra. A registration that also supports personal "
            "accounts can work if its settings and Educacyl policy allow it. Copy Application (client) "
            "ID, not Object ID, into CoMa's OAuth application ID.\n\n"
            "4. Public client. Under Authentication > Advanced settings enable Allow public client "
            "flows. CoMa uses device code flow, which needs no client secret or redirect URI.\n\n"
            "5. Delegated permissions. Configure Microsoft Graph Mail.ReadWrite, User.Read and "
            "offline_access. Mail.ReadWrite allows reading, archiving, junking and moving to Deleted "
            "Items within the account's rights. If consent is blocked, the Educacyl directory "
            "administrator must resolve it.\n\n"
            "6. Tenant and connection. Leave Microsoft tenant at organizations for work or school "
            "accounts, or enter the Directory (tenant) ID supplied by your administrator. Enter the "
            "@educa.jcyl.es address and select Connect account. Enter CoMa's temporary code on "
            "Microsoft's official page and complete verification."
        ),
    },
}


def language() -> str:
    return _language


def load_language(path: Path | None = None) -> str:
    global _language
    path = path or data_dir() / "preferences.json"
    try:
        selected = json.loads(path.read_text(encoding="utf-8")).get("language")
    except (OSError, ValueError, TypeError, AttributeError):
        selected = None
    _language = selected if selected in STRINGS else "es"
    return _language


def set_language(selected: str, path: Path | None = None) -> None:
    global _language
    if selected not in STRINGS:
        raise ValueError(selected)
    path = path or data_dir() / "preferences.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"language": selected}), encoding="utf-8")
    os.replace(temporary, path)
    _language = selected


def tr(key: str, **values) -> str:
    return STRINGS[_language][key].format(**values)


def help_text(provider: str) -> str:
    return HELP[_language][provider]


def help_links(provider: str) -> tuple[tuple[str, str], ...]:
    label_index = 0 if _language == "es" else 1
    return tuple((entry[label_index], entry[2]) for entry in HELP_LINKS[provider])
