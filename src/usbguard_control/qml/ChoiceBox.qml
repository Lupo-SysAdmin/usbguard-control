// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls.Basic
ComboBox {
    id: choice
    implicitHeight: 38; implicitWidth: 140
    leftPadding: 12; rightPadding: 28
    contentItem: UiText { text: choice.displayText; verticalAlignment: Text.AlignVCenter }
    indicator: UiText { text: "⌄"; font.pixelSize: 18; x: choice.width - width - 12; y: (choice.height - height) / 2 }
    background: Rectangle { radius: 8; color: control.workspace.colors["#1c2634"]; border.color: choice.activeFocus ? control.workspace.colors["#79adf5"] : control.workspace.colors["#334155"] }
}
