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
        UiText { text: qsTr("Historial de actividad"); font.pixelSize: 19; font.bold: true; Layout.fillWidth: true }
        ActionButton { text: qsTr("Exportar JSON / CSV"); onClicked: historyExport.open() }
        ActionButton { text: qsTr("Borrar historial"); onClicked: clearConfirm.open() }
    }
    UiText { Layout.fillWidth: true; text: desk.persistentHistory ? qsTr("Eventos observados por la aplicación, también entre aperturas. Los periodos sin observación no se reconstruyen. Vista limitada a 2000 eventos.") : qsTr("Historial de esta sesión. No se guarda en disco en demostración o si el almacenamiento no está disponible."); wrapMode: Text.Wrap; elide: Text.ElideNone; color: control.workspace.colors["#a3b9d6"]; font.pixelSize: 12 }
    UiText { Layout.fillWidth: true; visible: !!desk.storageError; text: desk.storageError; color: control.workspace.colors["#f5bba0"]; wrapMode: Text.Wrap; elide: Text.ElideNone }
    RowLayout {
        InputField { id: historySearch; objectName: "historySearch"; Layout.fillWidth: true; placeholderText: qsTr("Buscar dispositivo, acción o mensaje…"); Accessible.name: placeholderText; onTextChanged: desk.searchActivity(text, daySearch.text) }
        InputField { id: daySearch; Layout.preferredWidth: 150; placeholderText: "YYYY-MM-DD"; Accessible.name: qsTr("Filtrar por fecha"); onTextChanged: desk.searchActivity(historySearch.text, text) }
    }
    WrapCheckBox { id: redact; Layout.fillWidth: true; text: qsTr("Ocultar detalles de los eventos al exportar (privacidad)"); checked: true }
    ListView {
        Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 7
        model: desk.activity; ScrollBar.vertical: ScrollBar {}
        delegate: Rectangle {
            required property var modelData
            width: ListView.view.width; height: historyMessage.implicitHeight + 44; color: control.workspace.colors["#182231"]; radius: 8
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 12
                UiText { text: modelData.time + " / " + modelData.category; color: control.workspace.colors["#a3b9d6"]; font.pixelSize: 10; Layout.fillWidth: true }
                UiText { id: historyMessage; text: modelData.message; Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; activeFocusOnTab: true }
            }
        }
    }
    FileDialog { id: historyExport; title: qsTr("Exportar historial filtrado"); fileMode: FileDialog.SaveFile; nameFilters: ["JSON (*.json)", "CSV (*.csv)"]; defaultSuffix: selectedNameFilter.index === 1 ? "csv" : "json"; onAccepted: desk.exportHistory(selectedFile.toString(), redact.checked) }
    Dialog {
        id: clearConfirm; parent: Overlay.overlay; anchors.centerIn: parent; modal: true; width: 430; title: qsTr("Borrar historial local")
        contentItem: UiText { text: qsTr("Se borrarán los eventos guardados por esta aplicación. Las reglas y los registros del servicio se conservan."); wrapMode: Text.Wrap; elide: Text.ElideNone }
        standardButtons: Dialog.Cancel | Dialog.Ok
        onAccepted: desk.clearHistory()
    }
}
