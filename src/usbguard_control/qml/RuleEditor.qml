// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Dialog {
    id: editor
    objectName: "ruleEditorDialog"
    parent: Overlay.overlay; anchors.centerIn: parent
    width: Math.min(760, parent.width - 40); height: Math.min(640, parent.height - 40)
    modal: true; padding: 18; closePolicy: Popup.CloseOnEscape
    title: qsTr("Editor avanzado · regla específica")
    property int ruleId: -1
    property string original: ""
    function editSelected() {
        ruleId = control.workspace.selectedRule.id
        original = control.workspace.selectedRule.raw
        draft.text = original
        control.workspace.resetRuleEditor()
        open()
        draft.forceActiveFocus()
    }
    contentItem: ColumnLayout {
        spacing: 12
        UiText {
            Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone
            text: qsTr("Edita permitir/bloquear, nombre USB, puerto, huella del padre, tipo de conexión o etiqueta. Conserva VID:PID, serie, huella e interfaces. Las reglas globales, las condiciones y los dispositivos de entrada siguen protegidos.")
        }
        UiText {
            Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; font.pixelSize: 12
            color: control.workspace.colors["#a3b9d6"]
            text: qsTr("El atributo name debe coincidir con el nombre USB real; para un alias usa Guardar nombre. Escribe una sola regla en una línea. Validar no guarda cambios.")
        }
        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            contentWidth: availableWidth; ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            RuleText {
                id: draft; objectName: "ruleDraft"; width: parent.width
                readOnly: control.busy; Accessible.name: qsTr("Borrador de la regla")
            }
        }
        UiText {
            objectName: "ruleDraftError"; Layout.fillWidth: true
            visible: !!control.workspace.editorError
            text: control.workspace.editorError
            wrapMode: Text.Wrap; elide: Text.ElideNone; color: control.workspace.colors["#ffb3ba"]
        }
        UiText {
            Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; font.pixelSize: 12
            text: qsTr("La vista previa mostrará la regla normalizada y las coincidencias actuales antes y después. Al confirmar se guardará un respaldo y se conservará la posición de la regla.")
            color: control.workspace.colors["#a3b9d6"]
        }
    }
    footer: DialogButtonBox {
        ActionButton { text: qsTr("Cancelar"); enabled: !control.busy; onClicked: editor.close() }
        ActionButton { text: qsTr("Restablecer borrador"); enabled: !control.busy; onClicked: { draft.text = editor.original; control.workspace.resetRuleEditor() } }
        ActionButton {
            objectName: "previewRuleTextButton"; text: qsTr("Validar y comparar"); tone: "primary"
            enabled: control.connected && !control.busy && draft.text !== editor.original
            onClicked: control.workspace.previewRuleText(editor.ruleId, draft.text)
        }
    }
}
