// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs
ColumnLayout {
    property var desk: control.workspace
    spacing: 10
    RowLayout {
        UiText { text: qsTr("Diagnóstico y primeros pasos"); font.pixelSize: 19; font.bold: true; Layout.fillWidth: true }
        ActionButton { text: qsTr("Asistente inicial"); onClicked: setupWizard.open() }
        ActionButton { text: qsTr("Exportar diagnóstico"); onClicked: diagnosticExport.open() }
    }
    ScrollView {
        Layout.fillWidth: true; Layout.fillHeight: true; clip: true; contentWidth: availableWidth
        ColumnLayout {
            width: parent.width; spacing: 12
            Repeater {
                model: desk.diagnostics
                Rectangle {
                    required property var modelData
                    Layout.fillWidth: true; implicitHeight: diagnosticText.implicitHeight + 28; color: control.workspace.colors["#182231"]; radius: 8
                    ColumnLayout {
                        id: diagnosticText; anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 14
                        UiText { text: modelData.title; font.bold: true; Layout.fillWidth: true }
                        UiText { text: modelData.detail; Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; color: control.workspace.colors["#a3b9d6"] }
                    }
                }
            }
            RowLayout {
                ActionButton { text: qsTr("Comprobar iPhone"); enabled: !control.busy; onClicked: desk.checkPhone() }
                ActionButton { text: qsTr("Revisar servicios"); onClicked: desk.openSettings() }
                ActionButton { text: qsTr("Actualizar diagnóstico"); enabled: !control.busy; onClicked: control.refresh() }
            }
            UiText { Layout.fillWidth: true; text: qsTr("Las comprobaciones no instalan paquetes, no emparejan el teléfono y no cambian reglas."); wrapMode: Text.Wrap; elide: Text.ElideNone; color: control.workspace.colors["#a3b9d6"] }
        }
    }
    FileDialog { id: diagnosticExport; title: qsTr("Exportar diagnóstico"); fileMode: FileDialog.SaveFile; nameFilters: ["JSON (*.json)"]; defaultSuffix: "json"; onAccepted: desk.exportDiagnostics(selectedFile.toString()) }
    Dialog {
        id: setupWizard; objectName: "setupWizard"; parent: Overlay.overlay; anchors.centerIn: parent; modal: true
        width: Math.min(640, parent.width - 40); height: Math.min(570, parent.height - 40); title: qsTr("Preparar la protección USB")
        contentItem: ScrollView {
            contentWidth: availableWidth; clip: true
            ColumnLayout {
                width: parent.width; spacing: 14
                UiText { Layout.fillWidth: true; text: qsTr("1. Identifica tus periféricos de confianza. Conecta teclado y mouse; deja desconectados los dispositivos que no quieras autorizar."); wrapMode: Text.Wrap; elide: Text.ElideNone }
                WrapCheckBox { id: inputReviewed; Layout.fillWidth: true; text: qsTr("He identificado mis dispositivos de entrada y un acceso de recuperación.") }
                UiText { Layout.fillWidth: true; text: qsTr("2. Revisa la política inicial y conserva un respaldo. Si USBGuard aún no está configurado, sigue la guía de instalación antes de iniciar el servicio."); wrapMode: Text.Wrap; elide: Text.ElideNone }
                ActionButton { text: qsTr("Abrir guía de instalación"); onClicked: Qt.openUrlExternally("https://github.com/Lupo-SysAdmin/usbguard-control/blob/main/docs/INSTALL.md") }
                WrapCheckBox { id: policyReviewed; Layout.fillWidth: true; text: qsTr("He revisado las reglas y conservado un respaldo fuera de la aplicación.") }
                UiText { Layout.fillWidth: true; text: qsTr("3. Inicia los servicios desde Configuración. Las máscaras administrativas requieren revisión manual. Este asistente no las retira."); wrapMode: Text.Wrap; elide: Text.ElideNone }
                ActionButton { text: qsTr("Continuar a Configuración"); enabled: inputReviewed.checked && policyReviewed.checked; onClicked: { setupWizard.close(); desk.openSettings() } }
                UiText { Layout.fillWidth: true; text: qsTr("4. Comprueba una reconexión con un dispositivo prescindible. Verifica los permisos temporales y permanentes antes de depender de la configuración."); wrapMode: Text.Wrap; elide: Text.ElideNone }
            }
        }
        standardButtons: Dialog.Close
    }
}
