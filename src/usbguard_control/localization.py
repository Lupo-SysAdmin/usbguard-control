# SPDX-FileCopyrightText: 2026 Jan Herrera
# SPDX-License-Identifier: GPL-3.0-or-later
from PySide6.QtCore import QObject, Property, QSettings, QTranslator, Signal, Slot
from .translations import EN_US, ES_419, translate


class Language(QObject):
    changed = Signal()
    saveFailed = Signal(str)

    def __init__(self, locale=None, settings=None):
        super().__init__()
        self.settings = settings
        saved = settings.value("language", "es-419") if settings else "es-419"
        self._locale = locale or saved
        if self._locale not in ("es-419", "en-US"):
            self._locale = "es-419"

    @Property(str, notify=changed)
    def locale(self):
        return self._locale

    @Slot(str)
    def setLocale(self, locale):
        if locale not in ("es-419", "en-US") or locale == self._locale:
            return
        self._locale = locale
        if self.settings:
            self.settings.setValue("language", locale)
            self.settings.sync()
            if self.settings.status() != QSettings.NoError:
                self.saveFailed.emit("No se pudo guardar la preferencia de idioma.")
        self.changed.emit()

    def text(self, value):
        return translate(value, self._locale)


class Translator(QTranslator):
    def __init__(self, language):
        super().__init__()
        self.language = language

    def isEmpty(self):
        return False

    def translate(self, context, sourceText, disambiguation=None, n=-1):
        # None becomes a null QString, allowing Qt's normal fallback; an empty
        # string would incorrectly hide text from other Qt components.
        return self.language.text(sourceText) if sourceText in EN_US or sourceText in ES_419 else None
