# Validación y límites de la versión 0.1.0

## Resultado local — 8 de noviembre de 2026

- **26 pruebas aprobadas** con `sh scripts/check.sh` en Kali 2026.3, Python 3.14.8 y PySide6 6.10.3.
- Capturas renderizadas desde QML en español latinoamericano e inglés estadounidense; revisión visual de la ventana normal, compacta y los diálogos.
- Lanzador `.desktop` validado y `.deb` construido sin privilegios.
- Demostración abierta desde el contenido extraído del `.deb` usando Python aislado; paquete no instalado en el sistema.
- Distribuciones fuente y wheel construidas; sumas en `dist/SHA256SUMS`.
- Tres advertencias de obsolescencia provienen de PyGObject/asyncio en Python 3.14; no hubo fallos de prueba ni advertencias QML en el flujo probado.

Estos resultados no implican validación del daemon real, hardware, instalación APT completa ni ejecución remota de GitHub Actions.

## Automatizable sin hardware

- Analizar snapshots con nombres entre comillas e interfaces compuestas.
- Restringir bloqueo de HID, hubs e interfaces desconocidas.
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
- [ ] Verificar GNOME Shell 50.4/Wayland, KDE Plasma y Xfce/X11 en sesiones reales.
- [ ] Validar escalado 100 %, 150 % y 200 %, foco, lector de pantalla y contraste.
- [ ] Revisar los dos idiomas con lector de pantalla y diálogos nativos del escritorio.
- [ ] Preparar reglas, recuperación y autenticación con USBGuard 1.1.4 real.
- [ ] Conectar y retirar USB prescindibles, sin bloquear periféricos de acceso.
- [ ] Verificar permitir temporal, permitir persistente, reinicio y posterior revocación.
- [ ] Denegar/cancelar Polkit, retirar el dispositivo con el diálogo abierto y reiniciar el daemon.
- [ ] Verificar convivencia con la protección USB de GNOME y cambios externos de políticas.
- [ ] Confirmar notificaciones agrupadas y recuperación tras interrupciones del bus.
- [ ] Probar nombres Unicode/escapados de hardware real.
- [ ] Revisar captura, README, licencias, fuente correspondiente y sumas antes de subir artefactos.

## Alcance

La ventana muestra actividad de la sesión, no un historial persistente de auditoría. No contiene editor de reglas, pausa global, revocación gráfica ni configuración automática de privilegios. El modo demo no prueba el daemon. La protección de HID de esta interfaz no puede impedir que otra herramienta modifique el mismo dispositivo.
