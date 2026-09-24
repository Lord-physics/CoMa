# CoMa

CoMa reúne el correo no leído de la bandeja de entrada de Gmail, Outlook/Hotmail y cuentas Educacyl de Microsoft 365 en una ventana de Windows. Resume el texto localmente y señala mensajes que podrían ser spam según las correcciones del usuario. Las predicciones nunca mueven ni borran mensajes por sí solas.

## Instalar sin administrador

Descarga `CoMa-Windows.zip`, extráelo y ejecuta en PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-CoMa.ps1
```

Se instala en `%LOCALAPPDATA%\Programs\CoMa` y crea un acceso directo en el menú Inicio. Queda activado el inicio automático para el usuario actual; puedes desactivarlo en la ventana. Para desinstalar, cierra CoMa y ejecuta `Uninstall-CoMa.ps1` desde la carpeta instalada. Los datos de cuentas y aprendizaje permanecen en `%LOCALAPPDATA%\CoMa` para una reinstalación.

## Añadir cuentas

Cada proveedor exige registrar una aplicación OAuth de escritorio. CoMa **no solicita ni almacena la contraseña del correo**. Introduce en «Añadir cuenta» el ID de esa aplicación y completa el acceso en el navegador. Puedes añadir varias cuentas, incluso varias del mismo proveedor. Los tokens de renovación se cifran con DPAPI para el usuario de Windows; los resúmenes de correo no se guardan en disco.

- **Gmail:** crea un proyecto en Google Cloud, habilita Gmail API, configura la pantalla de consentimiento y crea un cliente OAuth de tipo «Aplicación de escritorio». Introduce el ID y el secreto del JSON descargado. Si la aplicación está en modo de prueba, añade tu cuenta como usuario de prueba. CoMa solicita el permiso `gmail.modify` para leer, archivar, enviar a spam y mover a papelera.
- **Outlook/Hotmail:** registra una aplicación en Microsoft Entra que admita cuentas personales y organizativas. Activa «Permitir flujos de cliente público» y concede permisos delegados `Mail.ReadWrite`, `User.Read` y `offline_access`. Introduce el ID de aplicación. CoMa mostrará un código para iniciar sesión en `microsoft.com/devicelogin`.
- **Educacyl:** usa una aplicación Entra que admita cuentas de organización. El tenant predeterminado es `organizations`; si conoces el ID de tenant específico, puedes indicarlo. La organización puede bloquear aplicaciones de terceros o exigir consentimiento del administrador. CoMa no puede omitir esa política.

Las acciones usan la API oficial del proveedor. «Eliminar» mueve a la papelera. «Spam y borrar» registra la decisión como spam y después mueve el correo a spam y a la papelera. En Outlook y Educacyl se hacen dos movimientos; si falla el segundo, CoMa muestra el error y el correo puede quedar en spam. «Abrir web» usa el enlace del proveedor cuando está disponible.

El clasificador necesita ejemplos de spam y de «No es spam» para comenzar a señalar mensajes. Puedes marcar cualquier mensaje como «No es spam»; para corregir un falso positivo, también puedes abrir «Posible spam», seleccionarlo y pulsar «No es spam». Solo esas decisiones y los botones de spam entrenan el modelo. Se conservan huellas de palabras y la decisión, sin guardar el texto del correo.

## Compilar

En Windows con Python 3.14 y PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Build-CoMa.ps1
```

El script crea `dist\CoMa-Windows.zip`, con `CoMa.exe` y el instalador. La aplicación en ejecución no requiere Python. Para pruebas locales: `py -m unittest discover -s tests -v`.

## Límites conocidos

La conexión real depende de los IDs OAuth, del consentimiento de cada cuenta y de las políticas del tenant Educacyl. No hay credenciales incluidas en el repositorio. Los mensajes se descargan de nuevo al actualizar; el primer análisis de buzones grandes puede tardar. CoMa no ejecuta HTML ni adjuntos de mensajes.

Documentación: [Gmail API](https://developers.google.com/workspace/gmail/api/reference/rest), [OAuth de escritorio de Google](https://developers.google.com/identity/protocols/oauth2/native-app), [Microsoft Graph](https://learn.microsoft.com/en-us/graph/api/user-list-messages?view=graph-rest-1.0), [código de dispositivo de Microsoft](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code).
