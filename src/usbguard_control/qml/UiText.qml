// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls.Basic
Label {
    color: control.workspace.colors["#e7edf7"]
    font.pixelSize: 13
    textFormat: Text.PlainText
    elide: Text.ElideRight
    Accessible.name: text
}
