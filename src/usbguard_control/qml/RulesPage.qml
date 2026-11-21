// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs

ColumnLayout {
    id: rulesPage
    property var desk: control.workspace
    spacing: 10
    RowLayout {
        UiText { text: qsTr("Reglas y confianza"); font.pixelSize: 19; font.bold: true; Layout.fillWidth: true }
        ActionButton { text: qsTr("Ver respaldos"); onClicked: desk.openBackups() }
        ActionButton { text: qsTr("Respaldar"); enabled: control.connected && !control.busy && !desk.rulesError; onClicked: backupDialog.open() }
        ActionButton { text: qsTr("Recuperar reglas"); enabled: control.connected && !control.busy && !desk.rulesError; onClicked: restoreDialog.open() }
    }
    UiText { Layout.fillWidth: true; text: qsTr("Reglas cargadas en orden de evaluación, incluidos dispositivos desconectados. D-Bus no indica cuáles son temporales."); wrapMode: Text.Wrap; elide: Text.ElideNone; color: control.workspace.colors["#a3b9d6"]; font.pixelSize: 12 }
    UiText { visible: !!desk.rulesError; text: desk.rulesError; Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; color: control.workspace.colors["#f5bba0"] }
    InputField {
        objectName: "ruleSearch"; Layout.fillWidth: true; placeholderText: qsTr("Buscar reglas por nombre, identificador o contenido…")
        Accessible.name: placeholderText; selectByMouse: true; onTextChanged: desk.searchRules(text)
    }
    RowLayout {
        Layout.fillWidth: true; Layout.fillHeight: true; spacing: 12
        ListView {
            objectName: "ruleList"; Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 6
            model: desk.rules; ScrollBar.vertical: ScrollBar {}
            delegate: ItemDelegate {
                id: ruleRow
                required property var modelData
                required property int index
                width: ListView.view.width; height: 76; focusPolicy: Qt.StrongFocus
                Accessible.name: modelData.order + ". " + modelData.name + ": " + modelData.targetLabel
                onClicked: desk.selectRule(modelData.id)
                onActiveFocusChanged: if (activeFocus) ListView.view.positionViewAtIndex(index, ListView.Contain)
                background: Rectangle { color: ruleRow.modelData.id === desk.selectedRule.id ? control.workspace.colors["#223b58"] : control.workspace.colors["#182231"]; radius: 8; border.color: ruleRow.activeFocus ? control.workspace.colors["#a6caff"] : control.workspace.colors["#334155"] }
                contentItem: ColumnLayout {
                    UiText { Layout.fillWidth: true; text: ruleRow.modelData.order + ". " + ruleRow.modelData.name; font.bold: true }
                    UiText { Layout.fillWidth: true; text: "#" + ruleRow.modelData.id + " · " + ruleRow.modelData.targetLabel + (ruleRow.modelData.editable ? "" : " · " + qsTr("Protegida / avanzada")); color: control.workspace.colors["#a3b9d6"]; font.pixelSize: 11 }
                    UiText { visible: ruleRow.modelData.duplicate; text: qsTr("Regla duplicada"); color: control.workspace.colors["#efd09a"]; font.pixelSize: 11 }
                }
            }
            Label { anchors.centerIn: parent; visible: !desk.rules.length; text: qsTr("No hay reglas con este filtro."); wrapMode: Text.Wrap; width: parent.width - 20; horizontalAlignment: Text.AlignHCenter }
        }
        Rectangle {
            Layout.preferredWidth: 330; Layout.fillHeight: true; color: control.workspace.colors["#182231"]; radius: 10; border.color: control.workspace.colors["#334155"]
            ScrollView {
                anchors.fill: parent; anchors.margins: 14; contentWidth: availableWidth; clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ColumnLayout {
                    width: parent.width; spacing: 12
                    UiText { Layout.fillWidth: true; text: desk.selectedRule.name || qsTr("Selecciona una regla"); font.pixelSize: 17; font.bold: true; wrapMode: Text.Wrap; elide: Text.ElideNone }
                    RuleText { Layout.fillWidth: true; visible: desk.selectedRule.id !== undefined; text: desk.selectedRule.raw || ""; readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap; textFormat: TextEdit.PlainText; Accessible.name: qsTr("Contenido de la regla") }
                    UiText { Layout.fillWidth: true; visible: desk.selectedRule.id !== undefined && !desk.selectedRule.editable; text: qsTr("Las reglas de entrada, Bluetooth, concentradores o sintaxis avanzada se muestran para consulta. Su modificación requiere revisión administrativa."); wrapMode: Text.Wrap; elide: Text.ElideNone; color: control.workspace.colors["#efd09a"]; font.pixelSize: 12 }
                    ChoiceBox { id: ruleTarget; objectName: "ruleTarget"; Layout.fillWidth: true; model: [qsTr("Permitir"), qsTr("Bloquear")]; enabled: !!desk.selectedRule.editable; Accessible.name: qsTr("Nueva decisión de la regla") }
                    ActionButton { objectName: "editRuleButton"; Layout.fillWidth: true; text: qsTr("Vista previa del cambio"); enabled: control.connected && !control.busy && !!desk.selectedRule.editable; onClicked: desk.prepareRule("edit", ruleTarget.currentIndex === 0 ? "allow" : "block") }
                    ActionButton { objectName: "removeRuleButton"; Layout.fillWidth: true; text: qsTr("Retirar regla"); tone: "danger"; enabled: control.connected && !control.busy && !!desk.selectedRule.editable; onClicked: desk.prepareRule("remove", "") }
                    UiText { Layout.fillWidth: true; text: qsTr("Retirar una regla no bloquea inmediatamente el dispositivo ni elimina otras reglas que puedan autorizarlo."); wrapMode: Text.Wrap; elide: Text.ElideNone; color: control.workspace.colors["#a3b9d6"]; font.pixelSize: 12 }
                    InputField { id: ruleAlias; Layout.fillWidth: true; visible: !!desk.selectedRule.canRename; text: desk.selectedRule.alias || ""; placeholderText: qsTr("Nombre personalizado (opcional)"); Accessible.name: placeholderText; maximumLength: 80; onAccepted: desk.renameRule(text) }
                    ActionButton { Layout.fillWidth: true; visible: !!desk.selectedRule.canRename; text: qsTr("Guardar nombre"); onClicked: desk.renameRule(ruleAlias.text) }
                }
            }
        }
    }
    Dialog {
        id: policyConfirm; objectName: "policyConfirmDialog"; parent: Overlay.overlay; anchors.centerIn: parent
        width: Math.min(640, parent.width - 40); height: Math.min(590, parent.height - 40); modal: true; padding: 18
        title: qsTr("Revisar cambio de reglas")
        closePolicy: Popup.CloseOnEscape
        contentItem: ScrollView {
            clip: true; contentWidth: availableWidth
            ColumnLayout {
                width: parent.width; spacing: 12
                UiText { Layout.fillWidth: true; text: qsTr("Se guardará un respaldo local antes de modificar la política. Puede solicitarse autenticación del sistema."); wrapMode: Text.Wrap; elide: Text.ElideNone }
                UiText { Layout.fillWidth: true; text: desk.confirmation.operation === "restore" ? qsTr("Recuperación selectiva: se agregan al final como permanentes las reglas específicas faltantes. No se reemplaza la política completa; las reglas anteriores pueden tener prioridad.") : qsTr("El cambio afecta futuras evaluaciones. Los dispositivos conectados conservarán su estado actual."); wrapMode: Text.Wrap; elide: Text.ElideNone; color: control.workspace.colors["#efd09a"] }
                UiText { visible: desk.confirmation.operation === "restore"; text: qsTr("Reglas a recuperar: ") + (desk.confirmation.count || 0) + qsTr(" · Protegidas o avanzadas omitidas: ") + (desk.confirmation.skipped || 0); Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone }
                UiText { Layout.fillWidth: true; text: qsTr("Dispositivos conectados coincidentes: ") + ((desk.confirmation.affected || []).join(", ") || qsTr("Ninguno")); wrapMode: Text.Wrap; elide: Text.ElideNone }
                RuleText { Layout.fillWidth: true; visible: !!desk.confirmation.before; text: desk.confirmation.before || ""; readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap; textFormat: TextEdit.PlainText; Accessible.name: qsTr("Regla actual") }
                RuleText { Layout.fillWidth: true; visible: !!desk.confirmation.after; text: desk.confirmation.after || ""; readOnly: true; selectByMouse: true; wrapMode: TextEdit.Wrap; textFormat: TextEdit.PlainText; Accessible.name: qsTr("Regla resultante") }
                UiText { visible: control.demo; text: qsTr("Esta acción es simulada."); color: control.workspace.colors["#efd09a"] }
            }
        }
        footer: DialogButtonBox {
            ActionButton { text: qsTr("Cancelar"); onClicked: desk.cancelRule() }
            ActionButton { objectName: "confirmRuleButton"; text: qsTr("Confirmar cambio"); tone: "danger"; enabled: control.connected && !control.busy; onClicked: desk.confirmRule() }
        }
        onRejected: desk.cancelRule()
    }
    Connections { target: desk; function onConfirmationChanged() { if (desk.confirmation.operation) policyConfirm.open(); else policyConfirm.close() } }
    FileDialog { id: backupDialog; title: qsTr("Guardar respaldo de reglas"); fileMode: FileDialog.SaveFile; nameFilters: ["JSON (*.json)"]; defaultSuffix: "json"; onAccepted: desk.exportBackup(selectedFile.toString()) }
    FileDialog { id: restoreDialog; title: qsTr("Abrir respaldo para recuperar reglas"); fileMode: FileDialog.OpenFile; nameFilters: ["JSON (*.json)"]; onAccepted: desk.loadBackup(selectedFile.toString()) }
}
