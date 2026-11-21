// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls.Basic
Button {
    id: button
    property string tone: "normal"
    property bool selected: false
    implicitHeight: 36
    implicitWidth: Math.max(80, contentItem.implicitWidth + 28)
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: text
    opacity: enabled ? 1 : 0.38
    background: Rectangle {
        radius: 8
        color: button.down ? control.workspace.colors["#29496d"] : button.tone === "primary" ? control.workspace.colors["#2d69ce"] : button.tone === "danger" ? control.workspace.colors["#36242c"] : button.selected ? control.workspace.colors["#223b58"] : button.hovered ? control.workspace.colors["#283344"] : control.workspace.colors["#1c2634"]
        border.color: button.activeFocus ? control.workspace.colors["#a6caff"] : button.tone === "danger" ? control.workspace.colors["#70404a"] : button.selected ? control.workspace.colors["#4876aa"] : control.workspace.colors["#334155"]
        border.width: button.activeFocus ? 2 : 1
    }
    contentItem: UiText {
        text: button.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.weight: Font.Medium
        color: button.tone === "primary" ? "#ffffff" : button.tone === "danger" ? control.workspace.colors["#ffb3ba"] : control.workspace.colors["#edf3fd"]
    }
}
