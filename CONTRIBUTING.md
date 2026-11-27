[![Español](https://img.shields.io/badge/Language-Espa%C3%B1ol-39D3C5?style=for-the-badge)](CONTRIBUTING.es.md)

<a id="contribuir"></a>

# Contribute

Run `sh scripts/check.sh` with the dependencies from docs/INSTALL.md. Works with `--demo` and the private test bus; Tests should never change actual USB authorization.

Maintain QML/controller/transport separation. Don't add shell execution, a GUI as root, or policies that allow all actions. Every new real operation must handle denial, disconnection, and persistence failures.

Document session and hardware tests separately from mocks. Retain existing notices and add notices of new contributions where appropriate. Contributions are distributed under GPL-3.0-or-later.

## Documentation languages

Write the default README and project documentation in American English. Maintain Latin American Spanish counterparts in `.es.md` files and keep both language buttons working. Update both languages when behavior or validation scope changes. `README.en.md` remains an English compatibility copy of `README.md`.
