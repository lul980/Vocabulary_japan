"""Ventana del panel dentro de Anki.

Agrega "Diccionario" a la barra de arriba (junto a Estadísticas) y a
Herramientas. La ventana es un AnkiWebView que carga web/dashboard.html;
Python lee la colección en segundo plano y le pasa el JSON a la página.

Proyecto de Raul Juarez.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from aqt import gui_hooks, mw
from aqt.qt import QAction, QDialog, QVBoxLayout, qconnect
from aqt.utils import restoreGeom, saveGeom, showWarning
from aqt.webview import AnkiWebView

from .collector import build_dashboard_data, resolve_deck_id

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
GEOM_KEY = "anki_diccionario_dashboard"
WEB_EXPORTS = r"web/.*\.(css|js|html|svg|png|woff2?)$"

LABELS = {
    "es": {"menu": "Diccionario japonés", "toolbar": "Diccionario",
           "tip": "Ver tu progreso de vocabulario", "error": "No se pudo leer el mazo:"},
    "en": {"menu": "Japanese dictionary", "toolbar": "Dictionary",
           "tip": "See your vocabulary progress", "error": "Couldn't read the deck:"},
}

_dialog: Optional["DashboardDialog"] = None


# --------------------------------------------------------------------------
# Configuración e idioma
# --------------------------------------------------------------------------

def get_config() -> Dict[str, Any]:
    return mw.addonManager.getConfig(__name__) or {}


def save_config(config: Dict[str, Any]) -> None:
    mw.addonManager.writeConfig(__name__, config)


def resolve_language(pref: str = "auto") -> str:
    if pref in ("es", "en"):
        return pref
    try:
        from anki import lang as anki_lang
        code = str(getattr(anki_lang, "current_lang", "") or "")
    except Exception:
        code = ""
    return "es" if code.lower().startswith("es") else "en"


def labels() -> Dict[str, str]:
    return LABELS[resolve_language(get_config().get("language", "auto"))]


# --------------------------------------------------------------------------
# Ventana
# --------------------------------------------------------------------------

class DashboardDialog(QDialog):
    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle(labels()["menu"])
        self.setMinimumSize(720, 560)
        self.resize(1120, 840)
        restoreGeom(self, GEOM_KEY)

        self.web = AnkiWebView(parent=self, title="anki_diccionario")
        self.web.set_bridge_command(self._on_bridge_cmd, self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web)
        self.setLayout(layout)

        self._load_page()
        self.show()
        # web.eval() espera a que la página termine de cargar, así que es seguro pedir los datos ya
        self.refresh()

    def _load_page(self) -> None:
        package = mw.addonManager.addonFromModule(__name__)
        base = f"/_addons/{package}/web"
        with open(os.path.join(ADDON_DIR, "web", "dashboard.html"), encoding="utf-8") as fh:
            body = fh.read()
        self.web.stdHtml(
            body,
            css=[f"{base}/dashboard.css"],
            js=[f"{base}/dictionary.js", f"{base}/review.js", f"{base}/dashboard.js"],
            context=self,
        )

    # La página manda "adic:refresh" (botón Actualizar) y "adic:deck:<id>" (selector de mazo)
    def _on_bridge_cmd(self, cmd: str) -> Any:
        if cmd == "adic:refresh":
            self.refresh()
        elif cmd.startswith("adic:deck:"):
            try:
                deck_id = int(cmd.rsplit(":", 1)[1])
            except ValueError:
                return None
            config = get_config()
            config["deck"] = mw.col.decks.name(deck_id)
            save_config(config)
            self.refresh(deck_id)
        elif cmd.startswith("adic:browse:"):
            try:
                note_id = int(cmd.rsplit(":", 1)[1])
            except ValueError:
                return None
            open_in_browser(note_id)
        return None

    def refresh(self, deck_id: Optional[int] = None) -> None:
        config = get_config()

        def op(col) -> Dict[str, Any]:
            did = deck_id or resolve_deck_id(col, config.get("deck", ""))
            data = build_dashboard_data(col, did, config)
            data["language"] = resolve_language(config.get("language", "auto"))
            return data

        try:
            from aqt.operations import QueryOp
        except ImportError:  # Anki muy viejo: lo hacemos directo
            self._send(op(mw.col))
            return

        query = QueryOp(parent=self, op=op, success=self._send)
        if hasattr(query, "failure"):
            query = query.failure(self._on_error)
        query.run_in_background()

    def _send(self, data: Dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False)
        self.web.eval(f"window.AnkiDiccionario && AnkiDiccionario.render({payload});")

    def _on_error(self, error: Exception) -> None:
        showWarning(f"{labels()['error']}\n{error}", parent=self)

    def reject(self) -> None:  # cerrar con la X o con Esc
        global _dialog
        saveGeom(self, GEOM_KEY)
        try:
            self.web.cleanup()
        except Exception:
            pass
        _dialog = None
        super().reject()


def open_in_browser(note_id: int) -> None:
    """Abre el explorador de Anki mostrando la tarjeta de esa palabra."""
    import aqt

    search = f"nid:{note_id}"
    try:
        aqt.dialogs.open("Browser", mw, search=(search,))
    except TypeError:  # versiones viejas sin el parámetro search
        browser = aqt.dialogs.open("Browser", mw)
        browser.search_for(search)


def open_dashboard() -> None:
    global _dialog
    if not mw.col:
        return
    if _dialog is not None:
        _dialog.show()
        _dialog.raise_()
        _dialog.activateWindow()
        _dialog.refresh()
        return
    _dialog = DashboardDialog()


def _close_dialog() -> None:
    if _dialog is not None:
        _dialog.reject()


def _add_toolbar_link(links: list, toolbar: Any) -> None:
    text = labels()
    try:
        links.append(toolbar.create_link(
            "anki_diccionario", text["toolbar"], open_dashboard, tip=text["tip"], id="anki_diccionario",
        ))
    except Exception:
        pass  # si la barra cambia en otra versión, queda el menú de Herramientas


def setup() -> None:
    mw.addonManager.setWebExports(__name__, WEB_EXPORTS)

    # Botón directo en la barra de menús (junto a Migaku, AnKing...): un solo clic.
    # Es una acción sin submenú, así que al picarle abre la ventana de una vez.
    top = QAction(labels()["toolbar"], mw)
    top.setToolTip(labels()["tip"])
    qconnect(top.triggered, open_dashboard)
    mw.form.menubar.addAction(top)

    # También en Herramientas (en Mac la barra de menús no muestra acciones sueltas)
    action = QAction(labels()["menu"], mw)
    qconnect(action.triggered, open_dashboard)
    mw.form.menuTools.addAction(action)

    gui_hooks.top_toolbar_did_init_links.append(_add_toolbar_link)
    gui_hooks.profile_will_close.append(_close_dialog)
