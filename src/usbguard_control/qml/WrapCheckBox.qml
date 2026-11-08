// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls
CheckBox {
    id: check
    implicitWidth: 260
    font.pixelSize: 14
    contentItem: UiText {
        text: check.text
        font: check.font
        leftPadding: check.indicator.width + check.spacing
        wrapMode: Text.Wrap
        elide: Text.ElideNone
        opacity: check.enabled ? 1 : 0.55
    }
}
