// SPDX-FileCopyrightText: 2026 Jan Herrera
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: window
    objectName: "mainWindow"
    width: 1040; height: 780
    minimumWidth: 900; minimumHeight: 620
    visible: true
    title: "USBGuard Control" + (control.demo ? qsTr(" · Demostración") : "")
    color: "#101722"
    font.family: "DejaVu Sans"
    palette.window: "#101722"; palette.windowText: "#e7edf7"
    palette.base: "#151e2b"; palette.text: "#e7edf7"
    palette.button: "#223044"; palette.buttonText: "#e7edf7"
    palette.highlight: "#2d69ce"; palette.highlightedText: "#ffffff"
    property int page: 0
    readonly property bool compact: height < 720
    property string activeFilter: "all"
    property var picked: control.selected

    Shortcut { sequence: "Ctrl+R"; onActivated: control.refresh() }
    Shortcut { sequence: "Ctrl+F"; onActivated: { window.page = 0; searchField.forceActiveFocus() } }
    Shortcut { sequence: "Ctrl+Q"; onActivated: window.close() }

    ColumnLayout {
        anchors.fill: parent; anchors.margins: window.compact ? 18 : 22
        spacing: window.compact ? 10 : 14
        RowLayout {
            spacing: 13
            Image { source: "../assets/shield.svg"; Layout.preferredWidth: 46; Layout.preferredHeight: 46 }
            ColumnLayout {
                spacing: 3
                UiText { text: "USBGuard Control"; font.pixelSize: 23; font.weight: Font.DemiBold }
                UiText { text: qsTr("El control de tus conexiones, en tus manos."); color: "#94a4bb"; font.pixelSize: 12 }
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                visible: control.demo
                Layout.preferredWidth: 110; Layout.preferredHeight: 26
                radius: 6; color: "#2c2b23"; border.color: "#655b37"
                UiText { anchors.centerIn: parent; text: qsTr("DEMOSTRACIÓN"); color: "#e4cc8a"; font.pixelSize: 10; font.weight: Font.Bold }
            }
            ActionButton { text: qsTr("Acerca de"); onClicked: about.open() }
        }

        RowLayout {
            spacing: 8
            ActionButton { text: qsTr("Dispositivos"); selected: window.page === 0; onClicked: window.page = 0 }
            ActionButton { text: qsTr("Actividad"); selected: window.page === 1; onClicked: window.page = 1 }
            Item { Layout.fillWidth: true }
            RowLayout {
                spacing: 4
                ActionButton {
                    objectName: "spanishButton"; text: "ES"; implicitWidth: 42
                    selected: language.locale === "es-419"
                    onClicked: language.setLocale("es-419")
                    Accessible.name: "Español (Latinoamérica)"
                    ToolTip.text: "Español (Latinoamérica)"; ToolTip.visible: hovered
                }
                ActionButton {
                    objectName: "englishButton"; text: "EN"; implicitWidth: 42
                    selected: language.locale === "en-US"
                    onClicked: language.setLocale("en-US")
                    Accessible.name: "English (United States)"
                    ToolTip.text: "English (United States)"; ToolTip.visible: hovered
                }
            }
            ActionButton { objectName: "settingsButton"; text: qsTr("Configuración"); onClicked: settings.open() }
        }

        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: window.compact ? 70 : 82
            color: control.connected ? "#142a2a" : "#28242a"
            border.color: control.connected ? "#284945" : "#58404a"; radius: 12
            RowLayout {
                anchors.fill: parent; anchors.margins: 19; spacing: 15
                Rectangle {
                    Layout.preferredWidth: 40; Layout.preferredHeight: 40; radius: 20
                    color: control.connected ? "#23473d" : "#45303a"
                    UiText { anchors.centerIn: parent; text: control.connected ? "✓" : "!"; color: control.connected ? "#7bdcb0" : "#ffb3ba"; font.pixelSize: 23 }
                }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 7
                    UiText { text: control.demo ? qsTr("Entorno de demostración") : control.connected ? qsTr("Servicio disponible") : qsTr("Sin conexión con USBGuard"); font.pixelSize: 17; font.weight: Font.DemiBold }
                    UiText { Layout.fillWidth: true; text: control.demo ? qsTr("Datos simulados. Ningún dispositivo real se modifica.") : control.policy; color: "#a4bdb8"; font.pixelSize: 12 }
                }
                ColumnLayout {
                    spacing: 3
                    UiText { text: control.allowedCount; font.pixelSize: 24; color: "#8ee2b9"; Layout.alignment: Qt.AlignHCenter }
                    UiText { text: qsTr("permitidos"); font.pixelSize: 11; color: "#a5bab6" }
                }
                Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 34; color: "#38504c"; Layout.leftMargin: 10; Layout.rightMargin: 10 }
                ColumnLayout {
                    spacing: 3
                    UiText { text: control.blockedCount; font.pixelSize: 24; color: "#f0b7a5"; Layout.alignment: Qt.AlignHCenter }
                    UiText { text: qsTr("sin autorizar"); font.pixelSize: 11; color: "#a5bab6" }
                }
            }
        }

        Rectangle {
            visible: control.error !== "" || control.notice !== ""
            Layout.fillWidth: true
            Layout.preferredHeight: bannerText.implicitHeight + 20
            radius: 8; color: control.error ? "#37242e" : "#1b3047"
            UiText {
                id: bannerText; anchors.fill: parent; anchors.margins: 10
                text: control.error || control.notice; wrapMode: Text.WordWrap; elide: Text.ElideNone
                color: control.error ? "#ffc1c6" : "#b9d8ff"; font.pixelSize: 12
            }
        }

        ColumnLayout {
            visible: window.page === 0
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 12
            RowLayout {
                UiText { text: qsTr("Dispositivos USB"); font.pixelSize: 17; font.weight: Font.DemiBold }
                UiText { text: "  /  " + control.devices.length; color: "#8496af" }
                Item { Layout.fillWidth: true }
                ActionButton { visible: control.demo; text: qsTr("Simular conexión"); enabled: !control.busy; onClicked: control.simulate() }
                ActionButton { text: control.busy ? qsTr("Consultando…") : qsTr("↻  Actualizar"); enabled: !control.busy; onClicked: control.refresh(); ToolTip.text: "Ctrl+R"; ToolTip.visible: hovered }
            }
            RowLayout {
                spacing: 8
                TextField {
                    id: searchField; objectName: "searchField"
                    Layout.fillWidth: true; Layout.preferredHeight: 35
                    placeholderText: qsTr("Buscar nombre, tipo o VID:PID…")
                    placeholderTextColor: "#8293aa"; color: "#e7edf7"; font.pixelSize: 12
                    leftPadding: 12; selectByMouse: true
                    background: Rectangle { radius: 8; color: "#151e2b"; border.color: searchField.activeFocus ? "#79adf5" : "#2c3a4e" }
                    onTextChanged: control.search(text)
                    Accessible.name: qsTr("Buscar dispositivos")
                }
                Repeater {
                    model: [{label: qsTr("Todos"), value: "all"}, {label: qsTr("Permitidos"), value: "allow"}, {label: qsTr("Bloqueados"), value: "block"}]
                    ActionButton { required property var modelData; text: modelData.label; selected: window.activeFilter === modelData.value; onClicked: { window.activeFilter = modelData.value; control.filter(modelData.value) } }
                }
            }
            RowLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; spacing: 12
                Rectangle {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    color: "#151e2b"; radius: 10; border.color: "#2c394b"
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 8; spacing: 4
                        RowLayout {
                            Layout.fillWidth: true; Layout.margins: 9
                            UiText { text: qsTr("DISPOSITIVO"); color: "#8496af"; font.pixelSize: 10; font.letterSpacing: 1; Layout.fillWidth: true }
                            UiText { text: qsTr("ESTADO"); color: "#8496af"; font.pixelSize: 10; font.letterSpacing: 1; Layout.preferredWidth: 100 }
                        }
                        ListView {
                            id: deviceList; objectName: "deviceList"
                            Layout.fillWidth: true; Layout.fillHeight: true
                            clip: true; spacing: 5
                            model: control.devices
                            ScrollBar.vertical: ScrollBar {}
                            delegate: ItemDelegate {
                                id: deviceRow
                                required property var modelData
                                width: ListView.view.width; height: 54
                                hoverEnabled: true
                                Accessible.name: modelData.name + ", " + modelData.status + ", " + modelData.kind
                                onClicked: control.select(modelData.id)
                                background: Rectangle {
                                    radius: 8
                                    color: window.picked.id === deviceRow.modelData.id ? "#213650" : deviceRow.hovered ? "#1d2b3d" : "transparent"
                                    border.color: deviceRow.activeFocus ? "#a6caff" : window.picked.id === deviceRow.modelData.id ? "#456d9c" : "transparent"
                                }
                                contentItem: RowLayout {
                                    spacing: 12
                                    Rectangle {
                                        Layout.preferredWidth: 33; Layout.preferredHeight: 33; radius: 8; color: "#263447"
                                        UiText { anchors.centerIn: parent; text: deviceRow.modelData.infrastructure ? "⌘" : deviceRow.modelData.kind === qsTr("Almacenamiento") ? "▤" : "⋮"; color: "#a9c9f1"; font.pixelSize: 21 }
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true; spacing: 4
                                        UiText { Layout.fillWidth: true; text: deviceRow.modelData.name; font.pixelSize: 12; font.weight: Font.Medium }
                                        UiText { Layout.fillWidth: true; text: deviceRow.modelData.kind; font.pixelSize: 10; color: "#94a6bf" }
                                    }
                                    UiText { Layout.preferredWidth: 100; text: (deviceRow.modelData.target === "allow" ? "✓  " : "⊘  ") + deviceRow.modelData.status; color: deviceRow.modelData.target === "allow" ? "#8eddb5" : "#efb09e"; font.pixelSize: 11 }
                                }
                            }
                            UiText { anchors.centerIn: parent; width: parent.width - 40; horizontalAlignment: Text.AlignHCenter; visible: deviceList.count === 0; text: control.connected ? qsTr("No hay dispositivos con este filtro.") : qsTr("Conecta con USBGuard para ver tus dispositivos."); wrapMode: Text.WordWrap; elide: Text.ElideNone; color: "#95a6bd" }
                        }
                        UiText { Layout.fillWidth: true; Layout.margins: 8; font.pixelSize: 10; color: "#8e9fb5"; text: control.advanced ? qsTr("Vista avanzada · infraestructura visible") : control.infrastructureCount + qsTr(" concentrador(es) ocultos · ver en Configuración") }
                    }
                }
                Rectangle {
                    Layout.preferredWidth: 276; Layout.fillHeight: true
                    color: "#182231"; radius: 10; border.color: "#303f54"
                    ScrollView {
                        anchors.fill: parent; anchors.margins: 17
                        contentWidth: availableWidth
                        ColumnLayout {
                            width: parent.width; spacing: 8
                            UiText { text: qsTr("DETALLES"); color: "#90a5c1"; font.pixelSize: 10; font.letterSpacing: 1.5 }
                            UiText { Layout.fillWidth: true; text: window.picked.name || qsTr("Selecciona un dispositivo"); font.pixelSize: 17; font.weight: Font.DemiBold; wrapMode: Text.WordWrap; elide: Text.ElideNone }
                            UiText { text: window.picked.kind || ""; color: "#95aac5"; font.pixelSize: 11 }
                            Rectangle { Layout.fillWidth: true; height: 1; color: "#304056" }
                            Repeater {
                                model: window.picked.id !== undefined ? [{label: "VID:PID", value: window.picked.usbId}, {label: qsTr("Número de serie"), value: window.picked.serial}, {label: qsTr("Puerto"), value: window.picked.port}, {label: qsTr("Interfaces"), value: window.picked.interfaces}] : []
                                RowLayout {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    UiText { text: modelData.label; color: "#90a2ba"; font.pixelSize: 10; Layout.preferredWidth: 90 }
                                    UiText { text: modelData.value; font.pixelSize: 10; Layout.fillWidth: true; wrapMode: Text.WrapAnywhere; elide: Text.ElideNone }
                                }
                            }
                            UiText { visible: window.picked.sensitive || false; Layout.fillWidth: true; text: qsTr("Dispositivo sensible. El bloqueo está restringido para conservar el acceso al equipo."); color: "#dec18d"; font.pixelSize: 10; wrapMode: Text.WordWrap; elide: Text.ElideNone }
                            ActionButton {
                                objectName: "allowNowButton"
                                Layout.fillWidth: true; text: qsTr("Permitir ahora"); tone: "primary"
                                visible: window.picked.id !== undefined && window.picked.target !== "allow"
                                enabled: control.connected && !control.busy && (window.picked.canAllow || false)
                                onClicked: control.prepare("allow", false)
                            }
                            ActionButton {
                                objectName: "allowAlwaysButton"
                                Layout.fillWidth: true; text: qsTr("Permitir siempre")
                                visible: window.picked.id !== undefined
                                enabled: control.connected && !control.busy && (window.picked.canAllow || false)
                                onClicked: control.prepare("allow", true)
                            }
                            ActionButton {
                                objectName: "blockButton"
                                Layout.fillWidth: true; text: qsTr("Bloquear ahora"); tone: "danger"
                                visible: window.picked.id !== undefined && window.picked.target === "allow"
                                enabled: control.connected && !control.busy && (window.picked.canBlock || false)
                                onClicked: control.prepare("block", false)
                            }
                            UiText { Layout.fillWidth: true; text: qsTr("“Ahora” cambia el estado actual. “Siempre” guarda una regla en USBGuard."); color: "#8e9fb5"; font.pixelSize: 10; wrapMode: Text.WordWrap; elide: Text.ElideNone; visible: window.picked.id !== undefined }
                        }
                    }
                }
            }
        }

        ColumnLayout {
            visible: window.page === 1
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 12
            RowLayout {
                UiText { text: qsTr("Actividad de esta sesión"); font.pixelSize: 17; font.weight: Font.DemiBold }
                Item { Layout.fillWidth: true }
                ActionButton { text: qsTr("Exportar JSON"); onClicked: exportDialog.open() }
            }
            UiText { text: qsTr("Hasta 200 eventos desde que abriste la aplicación. No sustituye el registro del servicio."); color: "#93a5bd"; Layout.fillWidth: true; wrapMode: Text.WordWrap; elide: Text.ElideNone; font.pixelSize: 12 }
            ListView {
                Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 7
                model: control.events; ScrollBar.vertical: ScrollBar {}
                delegate: Rectangle {
                    required property var modelData
                    width: ListView.view.width; height: eventMessage.implicitHeight + 42; radius: 8; color: "#182231"
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 12; spacing: 5
                        UiText { text: modelData.time + "   /   " + modelData.category; color: "#8fa7c7"; font.pixelSize: 10 }
                        UiText { id: eventMessage; text: modelData.message; Layout.fillWidth: true; wrapMode: Text.WordWrap; elide: Text.ElideNone; font.pixelSize: 12 }
                    }
                }
            }
        }

        Rectangle {
            visible: window.page === 0 && !window.compact
            Layout.fillWidth: true; Layout.preferredHeight: 57
            radius: 9; color: "#141d2a"; border.color: "#28364a"
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 13; spacing: 6
                UiText { text: qsTr("ÚLTIMA ACTIVIDAD"); color: "#90a4bf"; font.pixelSize: 9; font.letterSpacing: 1.2 }
                UiText { Layout.fillWidth: true; text: control.events.length ? control.events[0].message : qsTr("Sin eventos"); font.pixelSize: 11 }
            }
        }
        RowLayout {
            UiText { text: qsTr("Desarrollado por Jan Herrera"); font.pixelSize: 10; color: "#8295af" }
            Item { Layout.fillWidth: true }
            UiText { text: qsTr("Cliente independiente  ·  v0.2.0  ·  GPL-3.0-or-later"); font.pixelSize: 10; color: "#8295af" }
        }
    }

    Dialog {
        id: confirmDialog; objectName: "confirmDialog"
        anchors.centerIn: parent; width: 440; modal: true
        title: control.confirmation.target === "block" ? qsTr("Bloquear dispositivo") : qsTr("Autorizar dispositivo")
        closePolicy: Popup.CloseOnEscape
        padding: 20
        header: UiText { text: confirmDialog.title; padding: 20; bottomPadding: 8; font.pixelSize: 15; font.weight: Font.DemiBold }
        Overlay.modal: Rectangle { color: "#b000080f" }
        background: Rectangle { color: "#1c2839"; border.color: "#465e7e"; radius: 12 }
        contentItem: ColumnLayout {
            spacing: 16
            UiText { text: control.confirmation.name || ""; font.pixelSize: 18; font.weight: Font.DemiBold; Layout.fillWidth: true; wrapMode: Text.WordWrap; elide: Text.ElideNone }
            UiText {
                Layout.fillWidth: true; wrapMode: Text.WordWrap; elide: Text.ElideNone
                text: control.confirmation.permanent ? qsTr("Se guardará una regla persistente. Esta decisión puede aplicarse en futuras conexiones y reinicios. Revisa las reglas si luego quieres revocarla.") : control.confirmation.target === "block" ? qsTr("El dispositivo dejará de estar autorizado. Desmonta las unidades de almacenamiento antes de continuar. No se guardará una regla permanente.") : qsTr("Se autorizará el dispositivo ahora. Al reconectar o reiniciar, USBGuard volverá a evaluar sus reglas.")
            }
            UiText { visible: control.confirmation.sensitive || false; text: qsTr("Incluye interfaces sensibles, como teclado o ratón. Autoriza únicamente si reconoces el dispositivo."); color: "#efd09a"; Layout.fillWidth: true; wrapMode: Text.WordWrap; elide: Text.ElideNone }
            UiText { visible: control.demo; text: qsTr("Esta acción es simulada."); color: "#e4cc8a" }
            RowLayout {
                Item { Layout.fillWidth: true }
                ActionButton { text: qsTr("Cancelar"); onClicked: control.cancel() }
                ActionButton { objectName: "confirmActionButton"; text: qsTr("Confirmar"); enabled: control.connected && !control.busy; tone: control.confirmation.target === "block" ? "danger" : "primary"; onClicked: control.confirm() }
            }
        }
        onRejected: control.cancel()
    }
    Connections {
        target: control
        function onConfirmationChanged() {
            if (control.confirmation.name !== undefined) confirmDialog.open()
            else confirmDialog.close()
        }
    }
    Dialog {
        id: about; objectName: "aboutDialog"; anchors.centerIn: parent; width: 450; modal: true; title: qsTr("Acerca de USBGuard Control")
        padding: 20
        header: UiText { text: about.title; padding: 20; bottomPadding: 8; font.pixelSize: 15; font.weight: Font.DemiBold }
        Overlay.modal: Rectangle { color: "#b000080f" }
        footer: Item {
            implicitHeight: 56
            ActionButton { anchors.right: parent.right; anchors.rightMargin: 20; text: qsTr("Cerrar"); onClicked: about.close() }
        }
        background: Rectangle { color: "#1c2839"; border.color: "#465e7e"; radius: 12 }
        contentItem: ColumnLayout {
            spacing: 14
            Image { source: "../assets/shield.svg"; Layout.preferredWidth: 56; Layout.preferredHeight: 56 }
            UiText { text: "Jan Herrera"; font.pixelSize: 23; font.weight: Font.DemiBold }
            UiText { text: qsTr("Desarrollador de la interfaz · Lupo-SysAdmin"); color: "#a3b9d6" }
            UiText { Layout.fillWidth: true; text: qsTr("USBGuard Control 0.2.0\nCopyright © 2026 Jan Herrera\nGPL-3.0-or-later · Software libre, sin garantía.\n\nCliente independiente. El motor USBGuard pertenece a sus respectivos autores. Qt y PySide6 pertenecen a sus respectivos titulares."); wrapMode: Text.WordWrap; elide: Text.ElideNone }
            RowLayout {
                ActionButton { text: qsTr("GitHub de Jan"); onClicked: Qt.openUrlExternally("https://github.com/Lupo-SysAdmin") }
                ActionButton { text: qsTr("Leer licencia"); onClicked: Qt.openUrlExternally("https://www.gnu.org/licenses/gpl-3.0.html") }
            }
        }
    }
    Dialog {
        id: settings; objectName: "settingsDialog"; anchors.centerIn: parent
        width: Math.min(600, window.width - 40); height: Math.min(730, window.height - 48)
        modal: true; title: qsTr("Configuración y conexión")
        padding: 20
        header: UiText { text: settings.title; padding: 20; bottomPadding: 8; font.pixelSize: 15; font.weight: Font.DemiBold }
        Overlay.modal: Rectangle { color: "#b000080f" }
        footer: Item {
            implicitHeight: 56
            ActionButton { anchors.right: parent.right; anchors.rightMargin: 20; text: qsTr("Cerrar"); onClicked: settings.close() }
        }
        background: Rectangle { color: "#1c2839"; border.color: "#465e7e"; radius: 12 }
        contentItem: ScrollView {
            id: settingsScroll; objectName: "settingsScroll"
            clip: true; contentWidth: availableWidth; rightPadding: 12
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ScrollBar.vertical.active: true
            ColumnLayout {
                objectName: "settingsContent"
                width: settingsScroll.availableWidth
                spacing: 12
                UiText { text: qsTr("Servicio del sistema"); font.weight: Font.Bold }
                UiText { visible: control.demo; text: qsTr("Esta acción es simulada."); color: "#e4cc8a"; Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone }
                Repeater {
                    model: control.serviceState.units || []
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true; implicitHeight: unitInfo.implicitHeight + 24
                        color: "#121e2c"; radius: 8
                        ColumnLayout {
                            id: unitInfo; anchors.left: parent.left; anchors.right: parent.right
                            anchors.top: parent.top; anchors.margins: 12; spacing: 5
                            RowLayout {
                                Layout.fillWidth: true
                                UiText { text: modelData.name === "usbguard.service" ? qsTr("Protección USB") : qsTr("Conexión con la interfaz"); Layout.fillWidth: true; font.weight: Font.DemiBold }
                                UiText { text: modelData.activeLabel; color: modelData.active === "active" ? "#73e2bb" : "#f1ba8c" }
                            }
                            UiText { text: modelData.bootLabel; color: "#a3b9d6"; Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone }
                        }
                    }
                }
                UiText { visible: !control.serviceState.manageable; text: qsTr("Revisa la guía de instalación: los servicios deben estar instalados, sin máscaras ni configuraciones de arranque especiales."); color: "#efd09a"; Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone }
                WrapCheckBox {
                    id: rememberService; objectName: "rememberService"
                    Layout.fillWidth: true; Layout.minimumWidth: 0
                    text: qsTr("Recordar esta elección al iniciar el sistema"); checked: true
                }
                UiText { Layout.fillWidth: true; text: qsTr("Con esta opción, Iniciar habilita el arranque automático y Detener lo deshabilita. Sin marcarla, solo cambia el estado actual."); color: "#a3b9d6"; wrapMode: Text.Wrap; elide: Text.ElideNone; font.pixelSize: 12 }
                RowLayout {
                    ActionButton { objectName: "startServiceButton"; text: qsTr("Iniciar servicio"); tone: "primary"; enabled: control.serviceState.manageable && !control.busy; onClicked: control.prepareService("start", rememberService.checked) }
                    ActionButton { objectName: "stopServiceButton"; text: qsTr("Detener servicio"); tone: "danger"; enabled: control.serviceState.manageable && !control.busy; onClicked: control.prepareService("stop", rememberService.checked) }
                }
                UiText { visible: control.serviceWorking; text: qsTr("Aplicando cambios… Completa la autenticación del sistema si se solicita."); Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; color: "#b3c7e3" }
                UiText { visible: !!control.serviceState.error; text: qsTr("No se completó la solicitud. Algunos cambios pueden haberse aplicado; revisa los estados mostrados."); Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; color: "#f5bba0" }
                UiText { visible: !!control.serviceState.error; text: control.serviceState.error || ""; Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; color: "#f5bba0"; font.pixelSize: 12 }
                UiText { visible: !!control.notice; text: control.notice; Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; color: "#73e2bb"; font.pixelSize: 12 }
                Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: "#34445a" }
                UiText { text: qsTr("Preferencias de la interfaz"); font.weight: Font.Bold }
                WrapCheckBox { objectName: "hubsCheckBox"; Layout.fillWidth: true; Layout.minimumWidth: 0; text: qsTr("Mostrar concentradores USB (vista avanzada)"); checked: control.advanced; onToggled: control.showInfrastructure(checked) }
                WrapCheckBox { objectName: "notificationsCheckBox"; Layout.fillWidth: true; Layout.minimumWidth: 0; text: qsTr("Notificaciones agrupadas mientras la aplicación está abierta"); checked: control.notifications; enabled: !control.demo; onToggled: control.setNotifications(checked) }
                UiText { text: qsTr("Política actual"); font.weight: Font.Bold }
                UiText { text: control.policy; Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; color: "#b3c7e3" }
                UiText { Layout.fillWidth: true; text: qsTr("Cerrar esta ventana no detiene USBGuard. Las reglas guardadas se conservan al iniciar o detener el servicio."); wrapMode: Text.Wrap; elide: Text.ElideNone; font.pixelSize: 12; color: "#a3b9d6" }
                ActionButton { text: qsTr("Volver a comprobar conexión"); enabled: !control.busy; onClicked: control.refresh() }
            }
        }
    }
    Dialog {
        id: serviceConfirm; objectName: "serviceConfirmDialog"
        anchors.centerIn: parent; width: Math.min(510, window.width - 40)
        modal: true; padding: 20; closePolicy: Popup.CloseOnEscape
        title: control.serviceConfirmation.action === "start" ? qsTr("Iniciar servicio") : qsTr("Detener servicio")
        header: UiText { text: serviceConfirm.title; padding: 20; bottomPadding: 8; font.pixelSize: 15; font.weight: Font.DemiBold }
        Overlay.modal: Rectangle { color: "#b000080f" }
        background: Rectangle { color: "#1c2839"; border.color: "#465e7e"; radius: 12 }
        contentItem: ColumnLayout {
            spacing: 16
            UiText {
                Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone
                text: control.serviceConfirmation.action === "start"
                    ? qsTr("Se iniciarán USBGuard y su conexión con la interfaz usando las reglas existentes. Antes de continuar, confirma que tu teclado, mouse y otros dispositivos necesarios están contemplados en esas reglas.")
                    : qsTr("Se detendrán USBGuard y su conexión con la interfaz. La protección dejará de gestionar nuevas conexiones. Los dispositivos ya bloqueados pueden seguir bloqueados; detener el servicio no equivale a autorizar todos los USB.")
            }
            UiText {
                Layout.fillWidth: true; wrapMode: Text.Wrap; elide: Text.ElideNone; color: "#efd09a"
                text: !control.serviceConfirmation.remember ? qsTr("Se conservará la configuración de arranque actual.")
                    : control.serviceConfirmation.action === "start" ? qsTr("Ambos servicios se iniciarán automáticamente al encender el equipo.")
                    : qsTr("Ambos servicios quedarán sin inicio automático al encender el equipo.")
            }
            UiText { visible: control.demo; text: qsTr("Esta acción es simulada."); color: "#e4cc8a" }
            RowLayout {
                Item { Layout.fillWidth: true }
                ActionButton { text: qsTr("Cancelar"); onClicked: control.cancelService() }
                ActionButton { objectName: "confirmServiceButton"; text: qsTr("Confirmar"); enabled: !control.busy; tone: control.serviceConfirmation.action === "stop" ? "danger" : "primary"; onClicked: control.confirmService() }
            }
        }
        onRejected: control.cancelService()
    }
    Connections {
        target: control
        function onServiceConfirmationChanged() {
            if (control.serviceConfirmation.action !== undefined) serviceConfirm.open()
            else serviceConfirm.close()
        }
    }
    FileDialog {
        id: exportDialog; title: qsTr("Exportar actividad de la sesión")
        fileMode: FileDialog.SaveFile; nameFilters: ["JSON (*.json)"]; defaultSuffix: "json"
        acceptLabel: qsTr("Guardar"); rejectLabel: qsTr("Cancelar")
        onAccepted: control.exportActivity(selectedFile.toString())
    }
}
