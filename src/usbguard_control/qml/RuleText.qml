// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls.Basic
TextArea {
    id: area
    padding: 10; readOnly: true; selectByMouse: true
    color: control.workspace.colors["#e7edf7"]
    selectedTextColor: "#ffffff"; selectionColor: "#2d69ce"
    font.family: "DejaVu Sans Mono"; font.pixelSize: 11
    wrapMode: TextEdit.Wrap; textFormat: TextEdit.PlainText
    background: Rectangle { radius: 8; color: control.workspace.colors["#151e2b"]; border.color: area.activeFocus ? control.workspace.colors["#79adf5"] : control.workspace.colors["#2c3a4e"] }
}
