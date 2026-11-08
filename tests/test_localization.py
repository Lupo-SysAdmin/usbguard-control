import json
from pathlib import Path
import re
from string import Formatter
from PySide6.QtCore import QSettings
from usbguard_control.localization import Language
from usbguard_control.translations import EN_US, message, translate


def test_every_qml_translation_is_in_the_english_catalog():
    qml = Path(__file__).parents[1] / "src/usbguard_control/qml/Main.qml"
    keys = re.findall(r'qsTr\(("(?:[^"\\]|\\.)*")\)', qml.read_text())
    assert len(keys) > 50
    assert all(json.loads(key) in EN_US for key in keys)


def test_translation_placeholders_are_preserved():
    def fields(text):
        return {name for _, name, _, _ in Formatter().parse(text) if name is not None}
    for source, target in EN_US.items():
        assert fields(source) == fields(target), source


def test_language_preference_survives_restart_and_rejects_unknown_locale(tmp_path):
    path = str(tmp_path / "preferences.ini")
    language = Language(settings=QSettings(path, QSettings.IniFormat))
    assert language.locale == "es-419"
    language.setLocale("en-US")
    restored = Language(settings=QSettings(path, QSettings.IniFormat))
    assert restored.locale == "en-US"
    restored.setLocale("es-ES")
    assert restored.locale == "en-US"
    restored.setLocale("es-419")
    assert restored.text("Permitir ahora") == "Permitir ahora"


def test_translates_messages_without_translating_user_supplied_device_names():
    event = message("{status}: {name} · {scope}", status=message("Permitido"),
                    name="Almacenamiento", scope=message("regla guardada #{id}", id=42))
    assert translate(event, "en-US") == "Allowed: Almacenamiento · saved rule #42"
    assert translate(event, "es-419") == "Permitido: Almacenamiento · regla guardada #42"
