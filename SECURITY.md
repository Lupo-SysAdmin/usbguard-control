# Seguridad

USBGuard Control es un cliente en versión candidata. No certifica dispositivos, detecta malware ni sustituye USBGuard. Los atributos USB pueden falsificarse. Autorizar un dispositivo permite que sus interfaces interactúen con el equipo.

El proceso gráfico se ejecuta sin root. No modifica directamente reglas ni instala excepciones generales de Polkit. El motor upstream conserva la autorización y la persistencia. Los controles de servicios usan D-Bus de systemd y su política Polkit existente, únicamente para `usbguard.service` y `usbguard-dbus.service`, tras una confirmación explícita. Abrir la aplicación o consultar estados no inicia USBGuard.

Los cambios de servicio y arranque requieren varias operaciones y no son atómicos. Una cancelación o un error pueden dejar cambios parciales; la interfaz vuelve a consultar el estado y no informa éxito sin verificar el resultado. No elimina máscaras administrativas, no genera reglas iniciales ni reemplaza unidades. Detener el daemon no garantiza desbloquear dispositivos; iniciarlo aplica las reglas existentes y puede afectar periféricos sin una regla adecuada.

Las decisiones requieren confirmación y una nueva consulta de identidad. La API de USBGuard no ofrece comparación y aplicación atómicas; existe una ventana entre ambas operaciones. Se restringe bloquear dispositivos de entrada, adaptadores Bluetooth USB y hubs desde esta versión.

El historial solo reside en memoria hasta que el usuario lo exporta. No hay telemetría ni conexión de red automática. Los enlaces externos se abren únicamente desde botones explícitos. Las exportaciones pueden contener nombres de dispositivos.

Antes de informar un problema, elimina números de serie, hashes y datos personales de los registros. El repositorio aún no tiene un canal privado de reporte configurado. No publiques detalles explotables ni secretos en incidencias públicas; coordina un canal con el mantenedor [Jan Herrera](https://github.com/Lupo-SysAdmin) antes de compartirlos.
