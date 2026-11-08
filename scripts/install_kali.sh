#!/bin/sh
# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
# First installation only. Leave enforcement persistently masked until setup.
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "Ejecuta este instalador mediante sudo o pkexec." >&2
    exit 1
fi

if dpkg-query -W -f='${db:Status-Status}' usbguard 2>/dev/null | grep -qx installed; then
    echo "USBGuard ya está instalado. Revisa su configuración antes de continuar." >&2
    exit 1
fi

install_project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
install_package="$install_project_dir/dist/usbguard-control_0.1.0-1_all.deb"
if [ ! -f "$install_package" ]; then
    echo "Primero construye el paquete con python3 scripts/build_deb.py." >&2
    exit 1
fi
if [ "$(dpkg-deb -f "$install_package" Package)" != usbguard-control ]; then
    echo "El archivo no corresponde a USBGuard Control." >&2
    exit 1
fi
if systemctl is-active --quiet usbguard.service || systemctl is-active --quiet usbguard-dbus.service; then
    echo "Hay un servicio USBGuard activo; no se modificó su estado." >&2
    exit 1
fi

# Do not replace an existing administrative unit or mask.
for install_unit in usbguard.service usbguard-dbus.service; do
    if [ -e "/etc/systemd/system/$install_unit" ] || [ -L "/etc/systemd/system/$install_unit" ]; then
        echo "Ya existe /etc/systemd/system/$install_unit; revisión manual necesaria." >&2
        exit 1
    fi
done

systemctl mask usbguard.service usbguard-dbus.service

# The masks are intentionally retained on both success and failure. Do not
# unmask/start until the trusted-device policy has been reviewed.
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$install_package" usbguard

for install_unit in usbguard.service usbguard-dbus.service; do
    if [ "$(readlink "/etc/systemd/system/$install_unit")" != /dev/null ]; then
        echo "No se conservó la máscara de $install_unit. Revisa el servicio." >&2
        exit 1
    fi
    if systemctl is-active --quiet "$install_unit"; then
        echo "Estado inesperado: $install_unit está activo." >&2
        exit 1
    fi
done

echo "Instalación completada. USBGuard permanece detenido y enmascarado."
echo "Conecta teclado y mouse de confianza antes de generar y revisar las reglas."
dpkg-query -W -f='${Package} ${Version}\n' usbguard usbguard-control
