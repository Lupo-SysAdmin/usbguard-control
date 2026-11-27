[![English](https://img.shields.io/badge/Language-English-39D3C5?style=for-the-badge)](COMPATIBILITY.md)

# Compatibilidad de 0.5.0 / Compatibility

Comprobada el **21 de noviembre de 2026**. Una prueba automatizada en contenedor no equivale a una sesión de escritorio con autenticación y hardware.

| Sistema | Resultado y alcance |
|---|---|
| Kali 2026.3 / Xfce / X11 | Paquete instalado, interfaz real, editor con Polkit y reconexión de USB virtuales |
| Parrot 7.4 / KDE / Wayland | Paquete instalado, interfaz real, editor con Polkit y reconexión de USB virtuales |
| Debian trixie | 117 pruebas en CI, capturas QML y construcción del `.deb` |
| Ubuntu 26.04 | 117 pruebas como usuario normal, QML ES/EN y dependencias nativas; instalación, integridad y apertura del `.deb` en modo demostración |
| Fedora 45 | 117 pruebas como usuario normal y QML ES/EN con dependencias nativas; ejecución desde código fuente |
| Arch Linux rolling | 117 pruebas como usuario normal y QML ES/EN con dependencias nativas; ejecución desde código fuente |

Las tres últimas filas se ejecutaron en imágenes oficiales de distribución dentro de máquinas de GitHub Actions. La [ejecución inicial de la matriz](https://github.com/Lupo-SysAdmin/usbguard-control/actions/runs/44949137231) y el [workflow permanente](https://github.com/Lupo-SysAdmin/usbguard-control/actions/workflows/ci.yml) conservan los resultados. Los artefactos de CI incluyen inventario, informe JUnit, registro de pruebas y capturas; están sujetos a la retención de GitHub.

| Entorno de CI | Python | PySide6 / Qt | PyGObject | USBGuard instalado |
|---|---|---|---|---|
| Ubuntu 26.04 | 3.14.4 | 6.10.2 | 3.56.2 | 1.1.4 |
| Fedora 45 | 3.15.2 | 6.11.2 | 3.58.1 | 1.1.4 |
| Arch rolling | 3.14.10 | 6.12.0 | 3.58.1 | 1.1.4 |

El inventario verifica la presencia de GIO, las unidades `usbguard.service` y `usbguard-dbus.service`, y las acciones Polkit utilizadas. No inicia esos servicios: la suite utiliza un bus aislado y un servicio de prueba. Por tanto, **no se han validado diálogos Polkit, reinicio, bandeja, SELinux ni USB reales en Ubuntu/Fedora/Arch**. Hubo tres avisos de obsolescencia de PyGObject/asyncio en Fedora/Arch y cuatro en Ubuntu; ninguna prueba falló.

## Instalación y límites

- El instalador distribuido es `.deb`. No es un paquete para Fedora ni Arch, y no se ha publicado RPM, PKGBUILD o paquete AUR.
- El código/wheel requiere **Python ≥ 3.11, PySide6 ≥ 6.6 y < 7, PyGObject/GIO**, y para funciones del sistema, USBGuard con puente D-Bus, systemd y Polkit. Los módulos y nombres de paquetes cambian por distribución.
- El inicio automático de esta GUI requiere la disposición del paquete instalado (`/usr/share/usbguard-control` y `/usr/bin/usbguard-control`); una ejecución desde código o una instalación wheel aislada no habilita esa opción.
- La instalación/configuración inicial de USBGuard es independiente. No se deben copiar las instrucciones APT de Kali a Fedora o Arch.
- No se garantiza el `.deb` en versiones antiguas de Ubuntu ni compatibilidad con todas las derivadas, arquitecturas o distribuciones sin systemd. Que dos sistemas compartan un escritorio no certifica su empaquetado ni sus permisos.
- La prueba de GNOME/Wayland pertenece a 0.3.0; el host continúa instalado con 0.2.0. Consulta [validación de 0.5.0](VALIDATION-0.5.es.md) para la separación de evidencias.

Referencias de paquetes: [PySide6 en Ubuntu 26.04](https://packages.ubuntu.com/resolute/python3-pyside6.qtquickcontrols2), [PySide6 en Fedora](https://packages.fedoraproject.org/pkgs/python-pyside6/python3-pyside6/), [puente D-Bus en Fedora](https://packages.fedoraproject.org/pkgs/usbguard/usbguard-dbus/), [PySide6 en Arch](https://archlinux.org/packages/extra/x86_64/pyside6/) y [archivos de USBGuard en Arch](https://archlinux.org/packages/extra/x86_64/usbguard/files/).

## English

Version 0.5.0 passed **117 tests per distribution** on Ubuntu 26.04, Fedora 45 and Arch rolling using native dependencies in GitHub Actions containers as a regular user. ES/EN offscreen QML rendering also passed. Ubuntu additionally installed, verified and launched the Debian package in demo mode. Fedora/Arch coverage is from source; no RPM or pacman/AUR package is distributed.

The inventory checks installed USBGuard/systemd/Polkit integration files, not running services. These jobs do not validate live desktop authentication, reboot, tray behavior, SELinux or physical USB. Native Polkit and kernel USB gadget testing belong to Kali/Xfce and Parrot/KDE. Source/wheel use requires system dependencies and does not enable the packaged-layout-only GUI autostart. Other releases, architectures and non-systemd distributions are not universally certified.
