// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls
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
        color: button.down ? "#29496d" : button.tone === "primary" ? "#397be5" : button.tone === "danger" ? "#36242c" : button.selected ? "#223b58" : button.hovered ? "#283344" : "#1c2634"
        border.color: button.activeFocus ? "#a6caff" : button.tone === "danger" ? "#70404a" : button.selected ? "#4876aa" : "#334155"
        border.width: button.activeFocus ? 2 : 1
    }
    contentItem: UiText {
        text: button.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.weight: Font.Medium
        color: button.tone === "danger" ? "#ffb3ba" : "#edf3fd"
    }
}
