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
        "client_id": "ID de aplicación OAuth",
        "google_secret": "Secreto de Google (si procede)",
        "microsoft_tenant": "Tenant Microsoft",
        "account_hint": "Registra una aplicación en Google Cloud o Microsoft Entra.\nPulsa Ayuda para ver los pasos y los datos que necesitas.",
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
        "client_id": "OAuth application ID",
        "google_secret": "Google client secret (if needed)",
        "microsoft_tenant": "Microsoft tenant",
        "account_hint": "Register an application in Google Cloud or Microsoft Entra.\nSelect Help for the steps and required details.",
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

HELP_URLS = {
    "gmail": "https://developers.google.com/identity/protocols/oauth2/native-app",
    "outlook": "https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app",
    "educacyl": "https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app",
}

HELP = {
    "es": {
        "gmail": (
            "1. En Google Cloud Console, crea o selecciona un proyecto y habilita Gmail API.\n\n"
            "2. Configura la pantalla de consentimiento de Google Auth Platform. Si la aplicación "
            "está en modo de prueba, añade tu dirección como usuario de prueba. La cuenta debe poder "
            "autorizar el permiso gmail.modify, necesario para leer, archivar, marcar como spam y mover a papelera.\n\n"
            "3. En Clientes, crea un cliente OAuth de tipo Aplicación de escritorio y descarga su JSON.\n\n"
            "4. Copia client_id en «ID de aplicación OAuth» y client_secret en «Secreto de Google». "
            "No compartas el JSON ni lo subas a GitHub. El campo Tenant Microsoft no se usa para Gmail.\n\n"
            "5. Pulsa «Conectar cuenta», autoriza en el navegador y vuelve a CoMa. La redirección local "
            "se configura automáticamente; no tienes que introducir una URI."
        ),
        "outlook": (
            "1. En Microsoft Entra admin center, registra una aplicación. Para Outlook/Hotmail personal, "
            "elige un tipo de cuenta que incluya cuentas Microsoft personales.\n\n"
            "2. En Información general, copia «Id. de aplicación (cliente)» al campo «ID de aplicación OAuth».\n\n"
            "3. En Autenticación > Configuración avanzada, activa «Permitir flujos de cliente público». "
            "CoMa usa el código de dispositivo; no necesita secreto de cliente ni URI de redirección.\n\n"
            "4. En Permisos de API > Microsoft Graph, añade los permisos delegados Mail.ReadWrite, "
            "User.Read y offline_access. Concede el consentimiento cuando se solicite.\n\n"
            "5. Deja «Tenant Microsoft» en common para cuentas personales. Pulsa «Conectar cuenta», "
            "abre la dirección mostrada e introduce el código temporal en Microsoft."
        ),
        "educacyl": (
            "1. Confirma que tu buzón Educacyl funciona con Microsoft 365 y que tu organización permite "
            "registrar o autorizar aplicaciones de terceros. Si lo bloquea, solicita ayuda a su administrador.\n\n"
            "2. En Microsoft Entra admin center, registra una aplicación para cuentas de la organización. "
            "Copia «Id. de aplicación (cliente)» en «ID de aplicación OAuth».\n\n"
            "3. En Autenticación > Configuración avanzada, activa «Permitir flujos de cliente público». "
            "No necesitas secreto ni URI de redirección para el código de dispositivo.\n\n"
            "4. Añade en Microsoft Graph los permisos delegados Mail.ReadWrite, User.Read y offline_access. "
            "Puede ser necesario el consentimiento del administrador de Educacyl.\n\n"
            "5. Deja «Tenant Microsoft» en organizations o escribe el «Id. de directorio (inquilino)» "
            "que figure en Información general, si te lo facilita el administrador. Conecta y sigue "
            "el código temporal mostrado. CoMa no puede omitir restricciones de la organización."
        ),
    },
    "en": {
        "gmail": (
            "1. In Google Cloud Console, create or select a project and enable the Gmail API.\n\n"
            "2. Configure the Google Auth Platform consent screen. If the app is in testing mode, "
            "add your address as a test user. The account must be able to authorize gmail.modify, "
            "which CoMa needs to read, archive, mark as spam, and move messages to Trash.\n\n"
            "3. Under Clients, create a Desktop app OAuth client and download its JSON file.\n\n"
            "4. Copy client_id into OAuth application ID and client_secret into Google client secret. "
            "Do not share the JSON or commit it to GitHub. Microsoft tenant is unused for Gmail.\n\n"
            "5. Select Connect account and authorize in your browser. CoMa sets up the local redirect "
            "automatically; you do not need to enter a redirect URI."
        ),
        "outlook": (
            "1. In the Microsoft Entra admin center, register an application. For personal Outlook/Hotmail, "
            "choose an account type that includes personal Microsoft accounts.\n\n"
            "2. Under Overview, copy Application (client) ID into OAuth application ID.\n\n"
            "3. Under Authentication > Advanced settings, enable Allow public client flows. "
            "CoMa uses device code flow, so no client secret or redirect URI is needed.\n\n"
            "4. Under API permissions > Microsoft Graph, add delegated Mail.ReadWrite, User.Read, "
            "and offline_access permissions. Grant consent when prompted.\n\n"
            "5. Leave Microsoft tenant as common for personal accounts. Select Connect account, "
            "open the displayed address, and enter the temporary code at Microsoft."
        ),
        "educacyl": (
            "1. Confirm your Educacyl mailbox uses Microsoft 365 and that your organization permits "
            "third-party app registration or consent. If blocked, contact its administrator.\n\n"
            "2. Register an app for organizational accounts in the Microsoft Entra admin center. "
            "Copy Application (client) ID into OAuth application ID.\n\n"
            "3. Under Authentication > Advanced settings, enable Allow public client flows. "
            "Device code flow needs no client secret or redirect URI.\n\n"
            "4. Add delegated Microsoft Graph permissions Mail.ReadWrite, User.Read, and offline_access. "
            "Educacyl administrator consent may be required.\n\n"
            "5. Leave Microsoft tenant as organizations or enter the Directory (tenant) ID shown in "
            "Overview if the administrator supplies it. Connect and follow the temporary code. "
            "CoMa cannot bypass organizational restrictions."
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
