# USBGuard Control 0.5.0 — Validación / Validation

Fecha: **21 de noviembre de 2026**. Desarrollador: **Jan Herrera**.

## Entornos de esta versión

| Entorno | Paquete y sesión | Pruebas nuevas |
|---|---|---|
| Kali 2026.3, Xfce 4.20.4, X11, USBGuard 1.1.4, PySide6 6.11.2 | Actualización 0.3.0 → 0.5.0, usuario normal | Interfaz, editor con Polkit, cambio de alcance, reconexión y recuperación |
| Parrot 7.4, KDE Plasma 6.3.6, Wayland, USBGuard 1.1.3, PySide6 6.8.2.1 | Actualización 0.3.0 → 0.5.0, usuario normal | Interfaz, editor con Polkit, cambio de alcance, reconexión y recuperación |

La VM llamada «Kali 2026.1» ejecuta actualmente Kali 2026.3. No se declara una prueba nueva sobre 2026.1. El host mantiene el paquete 0.2.0: no se sustituyó ni se modificó su política.

## Automatización

- **117 pruebas pasadas** en la suite local, con tres avisos de obsolescencia ya existentes de PyGObject/asyncio. Las pruebas no usan el bus del sistema ni USB físicos.
- Nuevos casos para normalización, escapes UTF-8, atributos de identidad fijos, reglas amplias o inválidas, controles, etiquetas reservadas y cambios que solo alteran el formato.
- Vista previa sin escrituras, coincidencias anteriores y posteriores, cambio de dispositivos sensibles entre vista previa y confirmación, política obsoleta, respaldo obligatorio, posición y cambios parciales.
- Contrato D-Bus aislado para la operación de sustitución.
- Flujo QML completo: error de validación, borrador conservado durante actualización/idioma/tema/cambio de selección, ID capturado, cancelación de la comparación y confirmación. Sin avisos QML a 900 × 620.
- Demostraciones ES/EN, validación del lanzador y construcción del `.deb`. GitHub Actions ejecuta la misma suite en Debian trixie; sus resultados están en [CI](https://github.com/Lupo-SysAdmin/usbguard-control/actions/workflows/ci.yml).

## Pruebas con el paquete y escritorios reales

Además de la suite Debian, **Ubuntu 26.04, Fedora 45 y Arch rolling pasaron 117 pruebas cada una** en GitHub Actions con dependencias nativas y usuario sin privilegios. Ubuntu pasó instalación, integridad y apertura del `.deb` en modo demostración. Estos contenedores no son escritorios ni hardware: consulta el [inventario y alcance de compatibilidad](COMPATIBILITY.md).

- La actualización conservó la política de ambas VMs. Las cuatro páginas renderizaron en ES/EN y claro/oscuro sin errores QML. Se comprobaron cierre al segundo plano, reapertura con instancia única, creación/retirada de la entrada XDG y exportación de respaldo.
- Se utilizaron dispositivos de almacenamiento USB del kernel con `dummy_hcd`/`libcomposite`, imágenes vacías de solo lectura y nombres especiales. No son periféricos físicos.
- El editor rechazó un VID:PID con comodín antes de escribir. El borrador válido añadió una restricción de puerto y una etiqueta. La vista previa mostró un dispositivo coincidente antes y ninguno después, sin cambiar la política.
- El guardado desde la sesión normal solicitó Polkit para añadir la sustitución y retirar la regla anterior. El texto devuelto por USBGuard coincidió con el formato normalizado en ambas versiones del daemon. Se conservaron posición, cantidad de reglas y autorización del dispositivo conectado.
- Al reconectar el USB de prueba, la restricción persistida lo bloqueó. En ambas VMs, retirar esa restricción desde el editor conservó el estado bloqueado actual y volvió a permitirlo al reconectar. Se conservaron respaldos de todas las ediciones.
- Ambas VMs quedaron sin reglas ni gadgets de prueba; los hashes de sus políticas originales coincidieron exactamente y ambos servicios siguieron activos y habilitados. Las entradas de autoarranque creadas por la prueba se retiraron.
- El primer intento de recuperación en Parrot mostró un aviso de cambios parciales durante la autenticación. La comprobación posterior encontró la sustitución completa y la reconexión correcta. Se conservó esa evidencia y se repitió únicamente la recuperación: terminó sin errores con autenticación nativa y reconexión correcta. No se ocultó ni se declaró exitoso el primer resultado de la interfaz.

## Evidencia heredada y límites

Las funciones de historial, diagnóstico, asistente guiado, respaldos y segundo plano provienen de 0.3.0. Sus pruebas de **GNOME/Wayland, desinstalación/reinstalación, reinicio e inicio de sesión automático** se documentan en [VALIDATION-0.3.md](VALIDATION-0.3.md); no se presentan como nuevas pruebas de 0.5.0. Las pruebas físicas de iPhone, teclado y mouse pertenecen a [0.2.0](VALIDATION.md).

El nuevo editor admite únicamente reglas específicas con identidad fija; no toda la gramática de USBGuard. La comparación considera los dispositivos conectados en ese momento. Las operaciones D-Bus de añadir/retirar no son atómicas y una denegación posterior puede dejar cambios parciales. El asistente sigue siendo una guía y los respaldos recuperan reglas selectivamente, sin reemplazar toda la configuración del sistema. Consulta [funciones y límites](FEATURES-0.5.md).

## English

The local suite passed **117 tests**, including bounded rule text validation, read-only before/after previews, stale-policy and sensitive-device checks, mandatory backups, partial-write handling and the full bilingual QML editor flow. Three existing PyGObject/asyncio deprecation warnings remain. Debian CI runs the same checks.

Installed-package upgrade and UI checks ran in real Kali 2026.3/Xfce/X11 and Parrot 7.4/KDE/Wayland sessions. Both daemons accepted the normalized replacement through native Polkit, preserved the connected device authorization and blocked the kernel USB test device on reconnect when its new port constraint did not match. Both VMs also passed authenticated constraint removal, allowed reconnect and exact baseline-policy restoration. The first Parrot recovery attempt reported partial changes during authentication, although the final policy was later found complete. That evidence was retained; a focused repeat passed without errors.

GNOME, remove/reinstall and reboot/sign-in evidence belongs to 0.3.0, and physical peripherals to 0.2.0. The host package remains unchanged. No universal desktop, full-grammar, atomic-edit or automatic system-setup guarantee is implied.
