# Changelog

## 0.2.0 — 2026-11-08

- Consulta automática silenciosa cada cinco segundos, sin atenuar controles ni volver a notificar detalles que no cambiaron; los clics durante la consulta se procesan en orden.

- Configuración con casillas multilínea, ancho limitado y desplazamiento en ventanas pequeñas.
- Controles explícitos para iniciar y detener USBGuard y su puente D-Bus, con confirmación y autenticación de systemd/Polkit.
- Elección opcional persistente al arrancar; estados de ejecución y arranque consultados por separado.
- Verificación de jobs, detección de cambios externos y errores parciales, sin retirar máscaras ni modificar reglas USB.
- Flujo completo de servicios simulado, traducciones ES/EN y pruebas aisladas de transporte D-Bus.

## 0.1.0 — 2026-11-08

- Primera interfaz Qt Quick en español latinoamericano e inglés estadounidense con autoría de Jan Herrera.
- Selector ES / EN con cambio inmediato y preferencia guardada.
- Demostración aislada, filtros, detalles, confirmaciones y actividad exportable.
- Cliente D-Bus para USBGuard 1.1.4 y pruebas de integración con servicio simulado.
- Restricciones para dispositivos sensibles y revalidación de identidad.
- Restricción adicional para adaptadores Bluetooth que pueden transportar teclado o mouse.
- Los avisos de éxito caducan y se retiran cuando dejan de coincidir con el estado actual; desconectar un dispositivo no selecciona automáticamente otro.
- Documentación bilingüe, GPL-3.0-or-later, paquete Debian y flujo de CI.
- Primera validación física en Kali/GNOME con iPhone y receptor de mouse: autorización temporal, persistencia y reconexiones.
- Estado alpha: reinicio completo, recuperación, otros escritorios y publicación pendientes.
