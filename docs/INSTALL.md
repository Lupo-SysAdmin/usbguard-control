# Instalación y prueba en Kali

Objetivo inicial: Kali 2026.3. La revisión candidata observada el 8 de noviembre de 2026 es `usbguard 1.1.4+ds-10`; consulta siempre `apt policy usbguard` en tu equipo. El paquete incluye `usbguard-dbus` y su unidad systemd; no existe la necesidad de instalar otro paquete llamado `usbguard-dbus` en esta revisión.

También se ensayaron instalación/desinstalación en Kali 2026.1/Xfce y Parrot 7.4/KDE. Parrot distribuye `1.1.3+ds-3`: se probaron su API, conexión gráfica y arranque; no se sustituyeron sus paquetes con los de Kali. Consulta la [matriz de validación](VALIDATION.md) para distinguir el alcance de cada prueba. Para el escalado, reserva al menos 900×620 píxeles lógicos de área útil: al 200 % son 1800×1240 píxeles físicos, además de los paneles del escritorio.

## 1. Probar solo la interfaz

Instala las dependencias gráficas, sin instalar todavía el daemon:

```bash
sudo apt update
sudo apt install python3 python3-gi \
  python3-pyside6.qtcore python3-pyside6.qtgui \
  python3-pyside6.qtqml python3-pyside6.qtquick \
  qml6-module-qtquick qml6-module-qtquick-window \
  qml6-module-qtquick-layouts qml6-module-qtquick-controls \
  qml6-module-qtquick-dialogs qml6-module-qtquick-templates \
  qml6-module-qtqml-workerscript
PYTHONPATH=src python3 -m usbguard_control --demo
```

Para pruebas automatizadas: `sudo apt install python3-pytest dbus-daemon desktop-file-utils`.

O construye e instala el paquete de la interfaz:

```bash
python3 scripts/build_deb.py
sudo apt install ./dist/usbguard-control_0.2.0-1_all.deb
usbguard-control --demo
```

USBGuard figura como `Suggests`, no como dependencia que se instale automáticamente. El `.deb` no contiene scripts postinst, servicios ni cambios Polkit. El menú de aplicaciones ofrece una acción “Abrir demostración”.

No mezcles `sudo pip` con paquetes del sistema. Para desarrollo en un entorno virtual, usa `python3 -m venv --system-site-packages .venv` para conservar acceso a PyGObject instalado por APT. `pip install -e . --no-deps` puede registrar el comando si las dependencias ya están instaladas.

## 2. Preparar USBGuard en una instalación nueva

Realiza esta etapa en una VM con instantánea o con un acceso de recuperación que no dependa de los USB que vas a filtrar. Conecta únicamente dispositivos de confianza. No uses esta secuencia para sobrescribir una configuración que ya administras.

El `postinst` del paquete oficial puede generar una política y arrancar servicios. Para una **primera instalación**, el instalador incluido instala la interfaz y USBGuard y deja ambos servicios enmascarados hasta revisar las reglas:

```bash
sudo sh scripts/install_kali.sh
```

Se detiene si USBGuard ya está instalado o encuentra unidades administrativas preexistentes. Para hacer los mismos pasos manualmente, bloquea el arranque durante la preparación:

```bash
sudo systemctl mask usbguard.service usbguard-dbus.service
sudo apt install usbguard
```

Comprueba con `systemctl is-active usbguard.service usbguard-dbus.service` que no estén ejecutándose. Las máscaras persisten después de reiniciar hasta que las retires explícitamente. No actives el servicio mientras la política siga pendiente.

Respalda el directorio existente antes de editarlo. Genera una política candidata en un archivo privado:

```bash
umask 077
policy_candidate=$(mktemp)
sudo usbguard generate-policy > "$policy_candidate"
less "$policy_candidate"
```

Revisa que estén contemplados teclado, ratón, hubs y dispositivos internos necesarios. La política generada confía en lo conectado en ese momento; no determina si los dispositivos son benignos. Confirma `RuleFile` y `RuleFolder` en `/etc/usbguard/usbguard-daemon.conf` y revisa reglas preexistentes en ambos lugares.

Solo después de revisar y respaldar, instala la candidata:

```bash
sudo install -m 0600 -o root -g root "$policy_candidate" /etc/usbguard/rules.conf
rm -- "$policy_candidate"
sudo systemctl unmask usbguard.service usbguard-dbus.service
sudo systemctl start usbguard.service usbguard-dbus.service
```

Prueba los dispositivos y un USB prescindible. Comprueba `systemctl is-enabled usbguard.service usbguard-dbus.service`: el paquete puede haberlos habilitado durante la instalación. Conserva el arranque automático solo después de la validación. No otorgues acceso general al grupo `users` ni añadas reglas Polkit que permitan todas las acciones.

## 3. Conectar la interfaz

```bash
usbguard-control
```

Desde el código fuente: `PYTHONPATH=src python3 -m usbguard_control`.

Ejecuta como usuario normal en una sesión local activa con agente Polkit. Las acciones administrativas pueden mostrar la autenticación del escritorio. La aplicación no solicita ni guarda contraseñas.

“Permitir ahora” no guarda una regla: al reconectar o reiniciar se reevalúa la política. “Permitir siempre” pide a USBGuard guardar una regla; fallará si su almacenamiento de reglas no es escribible o no está configurado. “Bloquear ahora” tampoco elimina reglas persistentes. Para revocar una regla guardada, revisa `sudo usbguard list-rules` y administra la regla correcta con las herramientas oficiales; el editor gráfico está pendiente.

Antes de bloquear almacenamiento, desmonta el volumen. Bloquear autorización USB no es una operación de expulsión segura. Esta versión no administra montajes.

### Iniciar, detener y recordar la elección

En **Configuración**, las tarjetas muestran por separado el estado actual y el inicio automático de la protección USB y de su conexión con la interfaz.

- **Iniciar servicio** inicia ambos componentes con las reglas existentes.
- **Detener servicio** detiene ambos componentes sin borrar las reglas. No equivale a desbloquear todos los USB: algunos dispositivos pueden seguir sin autorización.
- **Recordar esta elección al iniciar el sistema**, marcada por defecto, hace que Iniciar habilite ambos servicios al arrancar y que Detener deshabilite su inicio automático. Desmárcala para cambiar solo el estado actual.

El diálogo confirma el alcance antes de solicitar los permisos de systemd mediante Polkit. Puede aparecer más de una solicitud de autenticación. La preferencia vive en systemd y no depende de mantener la interfaz abierta. Otros administradores aún pueden iniciar los servicios o cambiar esta configuración.

Estos controles requieren una instalación ya preparada, systemd y un agente Polkit. No retiran máscaras de la primera instalación ni modifican configuraciones especiales como unidades estáticas o habilitadas únicamente en `/run`. Si una operación falla a mitad, se muestran los estados consultados de nuevo y el error; revisa ambos antes de reintentar. Detener USBGuard no deshabilita otros mecanismos de protección USB, como el de GNOME.

## Diagnóstico y recuperación

```bash
python3 scripts/diagnose.py
systemctl status usbguard.service usbguard-dbus.service
journalctl -u usbguard -u usbguard-dbus -b
```

Si existe servicio pero falta autorización, revisa el agente Polkit y las políticas suministradas por USBGuard. No ejecutes la GUI con sudo para resolverlo. Si GNOME gestiona protección USB, su política puede coexistir o cambiar: inspecciona `gsettings get org.gnome.desktop.privacy usb-protection` y, si existe, `usb-protection-level`; no cambiamos estos valores automáticamente.

En GNOME, el gestor de protección puede añadir una regla que autoriza todos los dispositivos en el modo `lockscreen`. Para administrar una lista explícita con un cliente independiente, coordina ese gestor antes del primer arranque y comprueba las reglas resultantes. Cambiar `usb-protection` a `false` mientras el daemon está activo también puede provocar que GNOME inserte una regla de autorización general. No basta con cambiar la preferencia sin revisar el estado. [Código del gestor de GNOME en Debian](https://browse.dgit.debian.org/gnome-settings-daemon.git/tree/plugins/usb-protection/gsd-usb-protection-manager.c).

Si pierdes el acceso al teclado, utiliza el acceso de recuperación preparado. El README.Debian del paquete examinado documenta los parámetros de arranque `usbguard=0` o `usbguard=false` para impedir que USBGuard se inicie. Verifica estas instrucciones en `/usr/share/doc/usbguard/README.Debian` de tu versión antes de necesitarlas. Detener un servicio no garantiza restaurar instantáneamente todos los dispositivos; puede ser necesaria una reconexión o un reinicio tras reparar la política.

En la unidad `usbguard.service` del paquete `1.1.4+ds-10` examinado, `ConditionKernelCommandLine` y `ConditionPathExists` están bajo `[Service]`; systemd las ignora allí. En la instalación de prueba se añadieron sus equivalentes en `[Unit]` mediante `/etc/systemd/system/usbguard.service.d/10-usbguard-control-conditions.conf`, conservando el archivo del paquete. No confíes en los parámetros de recuperación hasta comprobar que las condiciones se aplican en tu instalación.

La desinstalación de la interfaz con `sudo apt remove usbguard-control` deja el daemon y sus reglas bajo administración independiente.

### iPhone permitido, pero Archivos muestra «Lockdown (-21)»

«Permitido» indica autorización USB; el acceso a los documentos del iPhone requiere además el emparejamiento de iOS y el montaje de GVfs. El código `-21` corresponde a `LOCKDOWN_E_INVALID_HOST_ID`: el teléfono rechaza la identidad del equipo en esa sesión. [Definición en libimobiledevice](https://github.com/libimobiledevice/libimobiledevice/blob/1.4.0/include/libimobiledevice/lockdown.h).

Con el iPhone autorizado en USBGuard, desbloquéalo y mantenlo conectado. Acepta «Confiar en este ordenador» si aparece en el teléfono. Para comprobar el emparejamiento, instala las utilidades opcionales y ejecuta la validación como usuario normal:

```bash
sudo apt install --no-install-recommends libimobiledevice-utils
idevicepair validate
```

Si la validación indica que no está emparejado, ejecuta `idevicepair pair`, confirma la confianza en el iPhone y vuelve a validar. Con varios dispositivos Apple conectados, selecciona el correcto mediante `-u` según `idevicepair --help`. Estas herramientas pueden mostrar el identificador del teléfono: ocúltalo antes de compartir sus salidas.

Después de una validación correcta, cierra el aviso anterior de Archivos y abre de nuevo «Documents on …». No hace falta cambiar una regla USB que ya autoriza el dispositivo. Esta ubicación muestra documentos compartidos por aplicaciones compatibles, no todo el sistema de archivos de iOS. La interfaz USBGuard Control no administra el emparejamiento ni los montajes.

Fuentes: [USBGuard 1.1.4](https://github.com/USBGuard/usbguard/releases/tag/usbguard-1.1.4), [paquetes Kali](https://http.kali.org/pool/main/u/usbguard/) y archivos README.Debian/postinst del paquete `1.1.4+ds-10` inspeccionado sin instalarlo.
