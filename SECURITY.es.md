[![English](https://img.shields.io/badge/Language-English-39D3C5?style=for-the-badge)](SECURITY.md)

# Seguridad

USBGuard Control es un cliente independiente de USBGuard. No certifica dispositivos, detecta malware ni sustituye USBGuard. Los atributos USB pueden falsificarse. Autorizar un dispositivo permite que sus interfaces interactúen con el equipo.

El proceso gráfico se ejecuta sin root. No modifica directamente reglas ni instala excepciones generales de Polkit. El motor upstream conserva la autorización y la persistencia. Los controles de servicios usan D-Bus de systemd y su política Polkit existente, únicamente para `usbguard.service` y `usbguard-dbus.service`, tras una confirmación explícita. Abrir la aplicación o consultar estados no inicia USBGuard.

Los cambios de servicio y arranque requieren varias operaciones y no son atómicos. Una cancelación o un error pueden dejar cambios parciales; la interfaz vuelve a consultar el estado y no informa éxito sin verificar el resultado. No elimina máscaras administrativas, no genera reglas iniciales ni reemplaza unidades. Detener el daemon no garantiza desbloquear dispositivos; iniciarlo aplica las reglas existentes y puede afectar periféricos sin una regla adecuada.

Las decisiones requieren confirmación y una nueva consulta de identidad. La API de USBGuard no ofrece comparación y aplicación atómicas; existe una ventana entre ambas operaciones. Se restringe bloquear dispositivos de entrada, adaptadores Bluetooth USB y hubs desde esta versión.

Desde la versión 0.3, el observador guarda un historial SQLite local (archivo 0600), con retención de 7/30/90 días y hasta 10000 registros; la vista muestra hasta 2000. Los respaldos de reglas se guardan antes de cada edición y pueden contener identificadores personales. El modo demostración no crea historial persistente. Las exportaciones ofrecen ocultar los detalles de eventos; los respaldos conservan la política completa cargada y no son anónimos. No hay telemetría ni conexión de red automática. Los enlaces externos se abren únicamente desde botones explícitos. Las exportaciones pueden contener nombres de dispositivos.

Antes de informar un problema, elimina números de serie, hashes y datos personales de los registros. El repositorio aún no tiene un canal privado de reporte configurado. No publiques detalles explotables ni secretos en incidencias públicas; coordina un canal con el mantenedor [Jan Herrera](https://github.com/Lupo-SysAdmin) antes de compartirlos.

## Gestión guiada de reglas (0.3)

Solo se editan reglas concretas con VID:PID, huella e interfaces conocidas, excluyendo HID, Bluetooth y concentradores. La política y el propietario D-Bus se releen antes de escribir. Esto no constituye una transacción atómica: otros administradores pueden modificar la política entre operaciones. Un error después de una escritura se informa como cambio parcial y conserva el respaldo; no se declara éxito sin releer el resultado.

La recuperación agrega al final como permanentes las reglas específicas faltantes, omitiendo reglas protegidas/avanzadas. No reemplaza toda la política ni restaura configuración del daemon, permisos o unidades systemd. Las reglas anteriores conservan prioridad. El listado D-Bus no informa la persistencia de cada regla: se presenta como política cargada, no como prueba de que todas sus entradas estén guardadas en disco.

El inicio de sesión crea únicamente la entrada XDG del usuario para esta aplicación. La instancia única usa un socket local de acceso de usuario y un bloqueo de proceso. Cerrar el observador no modifica servicios ni reglas. La integración iPhone solo ejecuta `idevicepair validate`, sin emparejar ni instalar paquetes; su salida detallada no se exporta.

## Editor de texto 0.5

El editor normaliza únicamente reglas específicas con identidad fijada (VID:PID, serie, huella e interfaces). No admite condiciones, comodines ni varias reglas. Se comprueban las coincidencias de la regla anterior y de la propuesta y se revalida antes de escribir. El predicado se consulta al daemon sin mutación; las escrituras mantienen autenticación, respaldo obligatorio y detección de cambios parciales. No se promete una transacción atómica.
