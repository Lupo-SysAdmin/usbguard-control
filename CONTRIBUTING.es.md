[![English](https://img.shields.io/badge/Language-English-39D3C5?style=for-the-badge)](CONTRIBUTING.md)

# Contribuir

Ejecuta `sh scripts/check.sh` con las dependencias de docs/INSTALL.md. Trabaja con `--demo` y el bus privado de pruebas; los tests nunca deben cambiar autorización USB real.

Mantén la separación QML/controlador/transporte. No añadas ejecución de shell, una GUI como root ni políticas que permitan todas las acciones. Cada nueva operación real debe manejar denegación, desconexión y fallos de persistencia.

Documenta las pruebas de sesión y hardware por separado de los mocks. Conserva los avisos existentes y añade los de contribuciones nuevas cuando corresponda. Las contribuciones se distribuyen bajo GPL-3.0-or-later.

## Idiomas de la documentación

El README predeterminado y la documentación principal se escriben en inglés estadounidense. Mantén las versiones en español latinoamericano en archivos `.es.md` y conserva los botones de idioma. Actualiza ambos idiomas cuando cambien el comportamiento o el alcance de validación. `README.en.md` sigue siendo una copia inglesa de compatibilidad de `README.md`.
