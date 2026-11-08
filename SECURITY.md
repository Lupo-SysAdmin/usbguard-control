# Seguridad

USBGuard Control es un cliente alpha. No certifica dispositivos, detecta malware ni sustituye USBGuard. Los atributos USB pueden falsificarse. Autorizar un dispositivo permite que sus interfaces interactúen con el equipo.

El proceso gráfico se ejecuta sin root. No inicia servicios, no modifica directamente reglas ni instala excepciones generales de Polkit. El motor upstream conserva la autorización y la persistencia.

Las decisiones requieren confirmación y una nueva consulta de identidad. La API de USBGuard no ofrece comparación y aplicación atómicas; existe una ventana entre ambas operaciones. Se restringe bloquear dispositivos de entrada, adaptadores Bluetooth USB y hubs desde esta versión.

El historial solo reside en memoria hasta que el usuario lo exporta. No hay telemetría ni conexión de red automática. Los enlaces externos se abren únicamente desde botones explícitos. Las exportaciones pueden contener nombres de dispositivos.

Antes de informar un problema, elimina números de serie, hashes y datos personales de los registros. El repositorio aún no tiene un canal privado de reporte configurado. No publiques detalles explotables ni secretos en incidencias públicas; coordina un canal con el mantenedor [Jan Herrera](https://github.com/Lupo-SysAdmin) antes de compartirlos.
