# Validación y límites de la versión 0.2.0

## Resultado local — 8 de noviembre de 2026

- **44 pruebas automatizadas aprobadas** con la suite de `scripts/check.sh` en Kali 2026.3, Python 3.14.8 y PySide6 6.10.3; incluyen regresiones de Bluetooth y avisos obsoletos tras desconectar un dispositivo.
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

El teclado mencionado funciona por Bluetooth y no se enumeró como teclado USB por su cable; no se presenta como una prueba de teclado USB. No se reinició el equipo, no se probó una recuperación de emergencia y no se considera completada una instalación/desinstalación en una VM limpia. No se publican números de serie, hashes ni reglas reales en el repositorio.

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

## Antes de publicar una release estable

- [ ] Instalar y desinstalar el `.deb` en una VM Kali 2026.3 limpia.
- [x] Verificar el flujo básico en GNOME Shell 50.4/Wayland con dispositivos reales.
- [ ] Verificar KDE Plasma y Xfce/X11 en sesiones reales.
- [ ] Validar escalado 100 %, 150 % y 200 %, foco, lector de pantalla y contraste.
- [ ] Revisar los dos idiomas con lector de pantalla y diálogos nativos del escritorio.
- [x] Preparar reglas y ejecutar autorizaciones con USBGuard 1.1.4 real y la política Polkit instalada.
- [x] Verificar permiso temporal y persistente mediante reconexiones físicas.
- [ ] Verificar arranque completo después de reiniciar, recuperación y posterior revocación.
- [ ] Denegar/cancelar Polkit, retirar el dispositivo con el diálogo abierto y reiniciar el daemon.
- [x] Verificar la delegación explícita de GNOME a USBGuard sin regla general de autorización.
- [ ] Verificar otros cambios externos de políticas y sesiones simultáneas.
- [ ] Confirmar notificaciones agrupadas y recuperación tras interrupciones del bus.
- [ ] Probar nombres Unicode/escapados de hardware real.
- [ ] Revisar captura, README, licencias, fuente correspondiente y sumas antes de subir artefactos.

## Alcance

La ventana muestra actividad de la sesión, no un historial persistente de auditoría. No contiene editor de reglas, autorización global, revocación gráfica ni configuración automática de privilegios. Los controles explícitos de servicio no equivalen a permitir todos los dispositivos. El modo demo no prueba el daemon. La protección de HID de esta interfaz no puede impedir que otra herramienta modifique el mismo dispositivo.

Para 0.2.0 se consultaron las unidades systemd reales sin modificar su estado: ambas activas y habilitadas. La parada/inicio con autenticación real desde los nuevos botones y el arranque tras un reinicio siguen pendientes de prueba física; las pruebas automatizadas no detienen la protección del equipo de desarrollo.
