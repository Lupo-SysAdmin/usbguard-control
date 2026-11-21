# USBGuard Control 0.3.0 — Validación / Validation

Fecha: **21 de noviembre de 2026**. Desarrollador: **Jan Herrera**.

## Entornos y alcance

| Entorno real | Ejecución | Resultado |
|---|---|---|
| Host Kali 2026.3, GNOME Shell 50.4, Wayland | Código de la versión nueva, usuario normal, configuración/historial de prueba separados | Navegación, ES/EN, claro/oscuro, cierre al segundo plano y reapertura con instancia única |
| VM Kali 2026.3, Xfce 4.20.4, X11, USBGuard 1.1.4, PySide6 6.11.2 | Paquete Debian instalado, sesión activa de usuario | Interfaz, política con Polkit, USB de prueba, persistencia, instalación y arranque de sesión |
| VM Parrot 7.4, KDE Plasma 6.3.6, Wayland, USBGuard 1.1.3, PySide6 6.8.2.1 | Paquete Debian instalado, sesión activa de usuario | Interfaz, política con Polkit, USB de prueba, persistencia, instalación y arranque de sesión |

El nombre de la VM «Kali 2026.1» se conservó, pero `/etc/os-release` informa **2026.3** después de sus actualizaciones. No se presenta como una prueba nueva de 0.3.0 sobre Kali 2026.1. Los resultados físicos y de compatibilidad de 0.2.0 se conservan en [VALIDATION.md](VALIDATION.md).

## Pruebas completadas

- **91 pruebas automatizadas**: demostración y D-Bus aislado; contratos y errores de la API, identidad, reglas sensibles, política obsoleta, respaldo fallido, cambio parcial, recuperación, preferencias, retención, privacidad de exportaciones, instancia única y traducciones. El CI se ejecuta en Debian trixie.
- Recorrido visual de las cuatro páginas en español latinoamericano e inglés estadounidense, con temas claro y oscuro. Sin errores QML en los recorridos. Se revisaron las capturas y los controles desplazables.
- Instalar el paquete sobre 0.2.0 conservó la política. Desinstalar y reinstalar conservó reglas, preferencias e historial y dejó ambos servicios activos. `dpkg --verify usbguard-control` pasó.
- Cada VM utilizó cuatro dispositivos de almacenamiento USB de prueba creados con `dummy_hcd`/`libcomposite`, con imágenes vacías de solo lectura y nombres con Unicode, comillas, barra inversa, texto parecido a HTML y control bidireccional. Se verificó su lectura y saneamiento visual.
- Desde la aplicación de usuario normal, **editar, retirar y recuperar una regla específica** solicitó la autenticación nativa. La contraseña se introdujo en la VM. No se cambiaron las reglas Polkit para conceder acceso sin autenticación.
- La edición permitir→bloquear se guardó en disco, mantuvo la autorización actual y bloqueó al reconectar el dispositivo. Retirar y recuperar desde JSON conservaron el estado conectado; después de recuperar, la reconexión volvió a permitirlo.
- Se crearon respaldos antes de cada escritura. La cancelación de Polkit en Xfce conservó la política y mostró el error de autorización. Una cancelación posterior a la primera etapa de edición también ejercitó el caso de cambio parcial; la interfaz advierte de este límite antes de confirmar.
- Historial y preferencias sobrevivieron al cierre y reapertura. El archivo SQLite tuvo permisos `0600`. Retención, filtro por fecha y ocultación de exportaciones se verifican adicionalmente en la suite automatizada.
- Cerrar al segundo plano y volver a abrir no creó dos observadores. Se verificó en GNOME/Wayland, Xfce/X11 y KDE/Wayland.
- En ambas VMs, tras **reiniciar e iniciar sesión**, la entrada XDG arrancó el paquete con `--background` como usuario normal. Reabrirlo reutilizó el mismo PID. USBGuard y el puente D-Bus continuaron activos.
- Se retiraron las reglas y gadgets de prueba. El contenido de `/etc/usbguard/rules.conf` volvió a coincidir exactamente con su hash anterior. Se retiró la entrada de autoarranque creada para la prueba, conservando la elección previa.

## Límites y observaciones

- No se sustituyó el paquete estable del host ni se modificaron sus servicios o reglas. La prueba GNOME usó el código de la nueva versión; la instalación y el inicio XDG después de reiniciar se probaron en Xfce y KDE.
- Los USB de esta ronda son dispositivos del kernel dentro de las VMs, no una repetición de pruebas físicas con iPhone, teclado o mouse. La integración de archivos del iPhone requiere además desbloqueo, confianza y soporte de montaje.
- Se verificaron bandejas disponibles en estas sesiones. Las acciones de notificaciones y un GNOME sin extensión de bandeja pueden variar con el servidor de notificaciones; la reapertura desde el lanzador permanece disponible.
- No se promete compatibilidad con todos los escritorios/versiones ni una auditoría de seguridad completa. El editor protege reglas de entrada/infraestructura y sintaxis avanzada; consulta [funciones y límites](FEATURES-0.3.md).
- Las escrituras D-Bus no son atómicas. Cancelar una autenticación posterior puede dejar una regla añadida; se informa de cambios parciales y se conserva el respaldo. No se aplica una reversión automática que pueda sobrescribir cambios externos.
- Se observaron avisos no fatales del portal de Xfce y EGL de la VM KDE en el arnés de pruebas. Las ventanas renderizaron y el paquete normal abrió después del inicio de sesión. La suite local conserva tres avisos de obsolescencia de PyGObject/asyncio.

## English

Version 0.3.0 was tested in real GNOME/Wayland, Xfce/X11, and KDE/Wayland sessions. GNOME used the new source with separate test data and did not replace the host package. Installed Debian-package tests ran on Kali 2026.3/Xfce and Parrot 7.4/KDE, including native Polkit rule editing/removal/recovery, kernel USB gadget reconnects, private persistent history, remove/reinstall, and automatic observer startup after reboot and sign-in. Launching again reused the same process. Test gadgets/rules were removed and original policy hashes restored.

The automated suite contains 91 tests and runs in Debian CI. VM USB gadgets are not new physical iPhone/keyboard/mouse certification. The VM still named “Kali 2026.1” now runs Kali 2026.3. Notification behavior and unsupported desktops are not universally certified. Multi-step D-Bus operations can leave partial changes when later authentication is canceled; previews warn of this and backups are retained. Prior physical-device evidence belongs to the separately documented 0.2.0 release.
