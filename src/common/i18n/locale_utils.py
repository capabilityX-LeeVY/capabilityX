from common.handler.settingsHandler import DynamicConfig
from config.paths import I18N_LOCALE
from typing import Union


class LocaleManager:
    _locale_config = DynamicConfig(I18N_LOCALE)
    _default_locale = "en_US"

    @classmethod
    def normalize(cls, locale: Union[str, None] = None) -> str:
        locale = locale or cls._default_locale
        locale_mapping = cls._locale_config.get("locale_mapping", default={})
        return locale_mapping.get(locale, locale) if locale_mapping else locale
