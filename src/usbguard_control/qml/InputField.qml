// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls.Basic
TextField {
    id: field
    implicitHeight: 38
    leftPadding: 12; rightPadding: 12
    color: control.workspace.colors["#e7edf7"]
    placeholderTextColor: control.workspace.colors["#8293aa"]
    selectedTextColor: "#ffffff"; selectionColor: "#2d69ce"
    selectByMouse: true; font.pixelSize: 12
    background: Rectangle { radius: 8; color: control.workspace.colors["#151e2b"]; border.color: field.activeFocus ? control.workspace.colors["#79adf5"] : control.workspace.colors["#2c3a4e"] }
}
