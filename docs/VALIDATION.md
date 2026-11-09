# Validación y límites de la versión 0.2.0

## Resultado local — 8 de noviembre de 2026

- **62 pruebas automatizadas aprobadas** con la suite de `scripts/check.sh` en Kali 2026.3, Python 3.14.8 y PySide6 6.10.3; incluyen regresiones de Bluetooth, avisos obsoletos, teclado, nombres accesibles y contraste del botón principal.
- Regresión de refresco: consultas idénticas sin cambios visuales, indicador manual conservado, clics de dispositivo/servicio/actualización durante la consulta, cambios reales, desconexión y recuperación ante errores.
- Medición de dos ciclos automáticos contra USBGuard real, en una instancia invisible: intervalo de cinco segundos, opacidad de botones al 100 %, datos seleccionados iguales y ninguna notificación visual redundante. No se cambiaron reglas ni servicios.
- Controles de servicios verificados contra un systemd simulado en un bus privado: firmas reales, autenticación interactiva, orden de inicio/parada, persistencia opcional, cancelación/denegación, cambios externos, jobs fallidos y fallos parciales.
- Configuración renderizada en ES/EN a 1040×780 y 900×620; comprobación de ancho y alto del texto de las casillas, y del flujo detener/iniciar con la conexión simulada cerrada.
- Capturas renderizadas desde QML en español latinoamericano e inglés estadounidense; revisión visual de la ventana normal, compacta y los diálogos.
- Lanzador `.desktop` validado y `.deb` construido sin privilegios.
- Demostración abierta desde el contenido extraído del `.deb` usando Python aislado; paquete no instalado en el sistema.
- Distribuciones fuente y wheel construidas; sumas en `dist/SHA256SUMS`.
- Tres advertencias de obsolescencia provienen de PyGObject/asyncio en Python 3.14; no hubo fallos de prueba ni advertencias QML en el flujo probado.

Las pruebas aisladas no sustituyen la validación física descrita a continuación. GitHub Actions todavía no se ha ejecutado remotamente.

### Primera instalación en el equipo de desarrollo

El 8 de noviembre de 2026 se instaló la interfaz `0.1.0-1` mediante APT junto con USBGuard `1.1.4+ds-10`, con autenticación Polkit. Se añadieron cuatro paquetes, sin actualizaciones ni eliminaciones. Primero se mantuvieron los servicios `inactive/masked` para preparar las reglas. La interfaz se abrió como usuario normal en GNOME Shell 50.4/Wayland.

Con aprobación explícita del usuario, se delegó la gestión USB de GNOME a USBGuard (`usb-protection=false`; valor anterior `true`, nivel `lockscreen`). Se respaldó la configuración fuera del repositorio y se instalaron reglas específicas para los dispositivos internos. No se añadieron excepciones Polkit. Se corrigieron mediante un drop-in las condiciones de recuperación mal ubicadas en la unidad del paquete. Los servicios terminaron `active/enabled`.

Resultados observados por la API real y confirmados por el usuario:

| Prueba | Resultado |
|---|---|
| iPhone nuevo, sin regla | Bloqueado |
| «Permitir ahora» desde la interfaz | Permitido |
| Reconectar después del permiso temporal | Bloqueado nuevamente |
| Receptor del mouse, regla permanente específica | Permitido automáticamente al reconectar |
| iPhone, regla permanente solicitada después de la prueba temporal | Permitido automáticamente al reconectar |
| Adaptador Bluetooth interno | Permaneció autorizado; su bloqueo se restringe ahora en la GUI |
| Política efectiva | Nuevos dispositivos: evaluar reglas; sin coincidencia: bloquear |
| Reglas generales de GNOME | No se encontró la regla de autorización general de GNOME |

El teclado mencionado funciona por Bluetooth y no se enumeró como teclado USB por su cable; no se presenta como una prueba de teclado USB. No se reinició el equipo físico. Los reinicios, recuperación e instalación/desinstalación se probaron después en VMs, como se describe abajo. No se publican números de serie, hashes ni reglas del hardware personal en el repositorio.

### Acceso a documentos del iPhone

Tras probar la autorización permanente, Archivos mostró `Unhandled Lockdown error (-21)` al abrir los documentos del teléfono. La comprobación real confirmó el dispositivo y sus interfaces autorizados, con USBGuard y usbmuxd activos. Se instalaron `libimobiledevice-utils` y su dependencia `libtatsu0`, sin actualizar ni retirar paquetes existentes.

Con el teléfono desbloqueado, `idevicepair validate` terminó correctamente y GVfs respondió a la consulta de la carpeta raíz de documentos. El usuario confirmó que pudo abrirla de nuevo sin el error. No se modificaron las reglas USB ni se ejecutó un desemparejamiento. Esta comprobación distingue autorización USB de acceso a documentos; no demuestra acceso a todos los archivos ni persistencia del emparejamiento tras reiniciar.

## Automatizable sin hardware

- Analizar snapshots con nombres entre comillas e interfaces compuestas.
- Restringir bloqueo de HID, adaptadores Bluetooth, hubs e interfaces desconocidas.
- Rechazar identidades diferentes, IDs obsoletos y dispositivos desconectados.
- Distinguir persistencia y autorización temporal en la simulación.
- Verificar firmas D-Bus reales, bandera de autenticación interactiva y denegaciones.
- Recibir señales de presencia en un bus privado.
- No asumir una política de bloqueo cuando no puede consultarse.
- Cargar QML y completar búsqueda, confirmación, autorización, reconexión y exportación.
- Cambiar entre español latinoamericano e inglés estadounidense sin reiniciar; verificar traducciones, variables y preferencia guardada.
- Renderizar una captura real del modo demostración.
- Construir e inspeccionar el `.deb` y validar el lanzador de escritorio.

Ejecutar `sh scripts/check.sh`. La prueba D-Bus usa un servicio simulado; no valida las decisiones reales del kernel ni la autenticación de un agente Polkit.

## Pruebas en máquinas virtuales KVM — 8 de noviembre de 2026

Se creó una instantánea de Kali y un respaldo completo verificado del disco y firmware UEFI de Parrot antes de modificar las VMs. La protección del equipo físico permaneció activa. Se emplearon discos USB virtuales vacíos; no se redirigieron el mouse, teclado ni iPhone del host.

| Entorno real | Versiones verificadas | Resultado |
|---|---|---|
| Kali 2026.1, Xfce 4.20.3, X11 | Python 3.13.9; PySide6 6.11.2; USBGuard 1.1.4+ds-10 | Instalación, GUI, autenticación, USB virtual y recuperación aprobados |
| Parrot 7.4, KDE Plasma 6.3.6, Wayland | Python 3.13.5; PySide6 6.8.2.1; USBGuard 1.1.3+ds-3 | Instalación, GUI, API real, arranque, eventos y recuperación de conexión aprobados |

El nombre de la VM Parrot era «Parrot 7.2», pero `/etc/os-release` informa 7.4. La VM Kali conserva su identidad 2026.1; instalar dependencias desde kali-rolling no equivale a validar una instalación limpia de Kali 2026.3.

| Prueba | Evidencia observada |
|---|---|
| `.deb` sin daemon, ambas VMs | La interfaz abre y muestra ausencia del servicio sin instalarlo ni iniciarlo |
| Desinstalar/reinstalar, ambas VMs | Se retiran lanzador, menú y archivos de aplicación; no se modifican reglas ni el daemon |
| Instalador completo | Ambos servicios quedan inactivos/enmascarados antes de revisar las reglas |
| Instalador sobre USBGuard existente | Rechazo explícito; configuración preservada |
| Controles gráficos Xfce con Polkit real | Iniciar/detener con y sin recordar: cuatro combinaciones verificadas como usuario normal |
| Controles gráficos KDE con Polkit real | Iniciar/detener con y sin recordar: cuatro combinaciones verificadas; al terminar ambos servicios quedan activos/habilitados |
| Cancelación Polkit Xfce | Se cancela el diálogo nativo; ambos servicios conservan `active/enabled` |
| Inicio tras reinicio, ambas VMs | Unidades activas/habilitadas después de un nuevo arranque |
| Arranque deshabilitado, Kali | Unidades inactivas/deshabilitadas después de reiniciar |
| Recuperación, Kali | Con el drop-in de condiciones correcto y `usbguard=0`, el daemon no inicia; retirado el parámetro, vuelve a iniciar normalmente |
| USB virtual, Kali | Nuevo bloqueado en el kernel; permiso temporal caduca al reconectar; permiso persistente sobrevive reconexión y cuatro reinicios |
| Revocación, Kali | Se retira únicamente la regla del disco de prueba; reconectar vuelve a producir `authorized=0` |
| Reinicio del daemon, Kali | Una confirmación con propietario D-Bus antiguo se rechaza; la regla persistente permanece |
| Dos clientes simultáneos, Parrot | Ambos ven conexión, autorización externa y desconexión del mismo USB virtual |
| Retirada con confirmación abierta, Parrot | Se rechaza la operación; no se aplica a otro dispositivo ni se conserva una selección obsoleta |
| Interrupción del puente, Parrot | Ambos clientes detectan la pérdida y recuperan conexión al restaurar `usbguard-dbus` |
| Notificaciones, Parrot | El servicio nativo acepta las notificaciones de conexión/desconexión sin errores |
| Refresco silencioso real, Parrot | Dos consultas automáticas iniciales sin cambios de selección ni estado ocupado |
| ES/EN y escala | Ventana 900×620 lógica a 100 %, 150 % y 200 %; KDE se probó con salida virtual 1920×1440 para evitar recorte del compositor |
| Accesibilidad | Nombres/roles/estado de casilla y teclado en Qt; casilla expuesta por AT-SPI desde otro proceso en ambos idiomas |
| Lector Orca 48.1, Parrot | Su registro de salida de voz anuncia el nombre de la casilla y el estado al enfocar/cambiarla en ES/EN; también procesa el diálogo de Configuración |

La lectura del daemon debe ejecutarse desde una sesión local activa. Un proceso lanzado administrativamente con `runuser` puede ser considerado inactivo por Polkit aunque tenga `DISPLAY`: se verificó el rechazo y luego el acceso correcto desde los lanzadores reales de Xfce y KDE, sin cambiar políticas de autorización. La prueba de Orca verificó la generación de voz registrada, no una evaluación humana de pronunciación; los términos del lector siguieron el idioma inglés del escritorio.

### Pruebas adicionales de eventos y nombres USB

En Parrot se crearon cuatro dispositivos de almacenamiento USB emulados con `dummy_hcd` y `libcomposite`, imágenes vacías de solo lectura y números de serie exclusivos de prueba. El recorrido fue descriptor USB → kernel → daemon USBGuard → D-Bus → GUI; no se simularon respuestas del backend. No se añadieron reglas permanentes para estos dispositivos. Al terminar se retiraron los cuatro gadgets y `dummy_hcd`; se comprobaron los tres USB virtuales iniciales, reglas intactas y ambos servicios activos/habilitados.

- Cinco ciclos de desconectar/reconectar cuatro dispositivos produjeron **40 eventos de presencia y 10 notificaciones agrupadas**, aceptadas por el servicio del escritorio sin errores. Dos clientes observaron los estados correctos y retiraron las selecciones desconectadas.
- Se verificaron acentos, eñe, caracteres CJK, comillas, barras invertidas, texto con apariencia de HTML y un control bidireccional. Los nombres coinciden con los descriptores; el HTML permanece literal y el control bidireccional se elimina solo de la presentación. La identidad original se conserva para revalidar operaciones.
- La prueba descubrió que el analizador anterior conservaba los escapes `\xHH` de USBGuard como texto. Se corrigió para reconstruir los bytes UTF-8 exactamente una vez, sin interpretar escapes literales de nuevo. Trece casos de regresión cubren entradas válidas y malformadas.

### Recorrido completo de teclado y Orca

Se completaron nueve grupos de comprobaciones en cada idioma con Orca 48.1 y la GUI como usuario normal en KDE: búsqueda, selección/filtros, permiso temporal y cancelación, bloqueo/permiso persistente, error por retirada del dispositivo, actividad, exportación mediante el selector de archivos, configuración/confirmaciones de servicios y Acerca de. Las acciones de esta revisión usan el modo demo; las operaciones reales de servicios y USB se validaron por separado arriba.

El recorrido usa Tab, Espacio, Escape, Ctrl+F y edición del nombre de archivo. Los JSON exportados se comprobaron por contenido e idioma. Los registros de voz contienen nombres de dispositivos, controles, confirmaciones, el error, preferencias y los diálogos en ambos idiomas. No es una certificación de accesibilidad ni una evaluación humana de pronunciación o de cada texto de revisión plana. El selector de archivos y los términos de Orca siguen el idioma del escritorio; en Qt 6.8 su campo de nombre fue anunciado como «text», sin repetir la etiqueta visual.

Orca y el puente AT-SPI de Qt 6.8 emitieron advertencias sobre rutas de objetos accesibles retirados durante cambios de modelo; los recorridos y las comprobaciones de voz terminaron correctamente. Se conserva este límite, sin presentar los registros como libres de advertencias. No hubo advertencias QML en los recorridos finales.

### Correcciones detectadas por estas pruebas

- El lanzador ahora evita generar bytecode de Python; la desinstalación deja limpio el directorio de la aplicación incluso tras intentar ejecutarla como root.
- La importación explícita de `QtQuick.Controls.Basic` conserva el diseño y elimina los bucles de geometría del tema Breeze observados en KDE. [Selección de estilos de Qt](https://doc.qt.io/qt-6.8/qtquickcontrols-styles.html).
- Las filas de dispositivos ahora reciben foco mediante Tab y se desplazan hasta quedar visibles. Los errores conservan su texto durante las consultas automáticas y pueden enfocarse; Qt 6.8 o superior también recibe un anuncio accesible. La actualización manual y la recuperación de conexión limpian el error.
- `QQuickStyle.setStyle("Basic")` se aplica después de crear la aplicación: KDE sobrescribía la preferencia de entorno y mezclaba Breeze en el selector de archivos. Se añadió la dependencia `python3-pyside6.qtquickcontrols2` al paquete, instalación y CI.
- Las casillas personalizadas exponen su nombre accesible. El contraste del texto del botón principal pasó de 3,67:1 a 4,68:1; el test mide los colores del control renderizado. Esto verifica ese par de colores, no certifica toda la aplicación. [Criterio de contraste W3C](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum).

No hubo advertencias QML en los recorridos finales después de corregir KDE; las advertencias AT-SPI se detallan arriba. La VM Parrot emitió advertencias EGL por su adaptador virtual y renderizó correctamente; no se presenta como validación de todas las GPU. La recuperación probada interrumpe el puente USBGuard, no reinicia el bus D-Bus completo del escritorio. Las operaciones systemd de Parrot se probaron también por la API administrativa; la autenticación positiva interactiva de los botones se verificó en Xfce y KDE, como usuario normal y sin excepciones Polkit.

## Cobertura y comprobaciones adicionales

- [x] Instalar y desinstalar el `.deb` en VMs sin USBGuard Control previo (Kali 2026.1 y Parrot 7.4).
- [x] Compatibilidad con Kali 2026.3 (host) y Kali 2026.1 (VM), aceptada como alcance de esta publicación; no se exige otra VM limpia 2026.3.
- [x] Verificar el flujo básico en GNOME Shell 50.4/Wayland con dispositivos reales.
- [x] Verificar KDE Plasma/Wayland y Xfce/X11 en sesiones reales.
- [x] Validar escalado 100 %, 150 % y 200 %, navegación de teclado y contraste del botón principal.
- [x] Verificar nombres, roles y estados accesibles en ES/EN mediante Qt y AT-SPI.
- [x] Probar foco y anuncio de la casilla de arranque con Orca real en ES/EN.
- [x] Recorrer búsqueda, selección, confirmación/cancelación, errores, actividad/exportación, configuración/servicios y Acerca de con teclado y Orca en ES/EN, dentro del alcance descrito abajo.
- [x] Preparar reglas y ejecutar autorizaciones con USBGuard 1.1.4 real y la política Polkit instalada.
- [x] Verificar permiso temporal y persistente mediante reconexiones físicas.
- [x] Verificar arranque completo después de reiniciar, recuperación y posterior revocación en VM.
- [x] Denegar/cancelar Polkit, retirar el dispositivo con el diálogo abierto y reiniciar el daemon.
- [x] Verificar la delegación explícita de GNOME a USBGuard sin regla general de autorización.
- [x] Verificar cambios externos de autorización y dos clientes simultáneos en una sesión.
- [x] Confirmar entrega de notificaciones y recuperación tras interrupciones del puente D-Bus.
- [x] Validación en tres equipos: host Kali y VMs Kali/Parrot. Las sesiones de usuarios distintos quedan fuera del alcance acordado; no se confunden con equipos distintos.
- [x] Verificar ráfagas de conexión/desconexión de múltiples dispositivos y agrupación de notificaciones.
- [x] Verificar nombres Unicode/escapados mediante descriptores USB emulados en el kernel y USBGuard real; no se atribuye a hardware físico con esos nombres.
- [x] Verificar autenticación positiva de los botones de servicio en KDE con las cuatro combinaciones de ejecución/arranque.
- [x] Revisar capturas, README, licencias, fuente correspondiente y sumas antes de subir artefactos.

## Alcance

La ventana muestra actividad de la sesión, no un historial persistente de auditoría. No contiene editor de reglas, autorización global, revocación gráfica ni configuración automática de privilegios. Los controles explícitos de servicio no equivalen a permitir todos los dispositivos. El modo demo no prueba el daemon. La protección de HID de esta interfaz no puede impedir que otra herramienta modifique el mismo dispositivo.

La parada/inicio con autenticación real y los reinicios se verificaron dentro de las VMs. No se reinició ni se detuvo la protección del equipo de desarrollo durante estas pruebas. Las comprobaciones de nombres Unicode/escapados usan descriptores USB emulados que atraviesan el kernel y el daemon reales; no se atribuyen a hardware físico con nombres Unicode.
