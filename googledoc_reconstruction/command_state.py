# -*- coding: utf-8 -*-
"""
Created on Sun Dec  7 20:54:05 2025

@author: Saminur Islam
"""

import collections
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional


PLACEHOLDER = "\x00"

def _insert_1based(text: str, ibi: int, s: str) -> str:
    """
    Insert string s at 1-based index ibi, using the same logic as the old
    google_text.insert: fill gaps with PLACEHOLDER if ibi is beyond the end.
    """
    # index of next char after last char (1-based)
    nextchar_index = len(text) + 1

    # If the insert index is greater than nextchar_index, fill the gap
    if ibi > nextchar_index:
        gap = ibi - nextchar_index
        # recursively insert the placeholders first
        text = _insert_1based(text, nextchar_index, PLACEHOLDER * gap)

    # now ibi is in [1, len(text)+1]
    # slice using 1-based logic (prefix up to ibi-1, then s, then suffix)
    return text[: ibi - 1] + s + text[ibi - 1 :]


def _delete_1based(text: str, si: int, ei: int) -> str:
    """
    Delete [si, ei) using the same semantics as the old google_text.delete.
    It also fills gaps with PLACEHOLDER if si/ei are beyond the current end.
    """
    lastchar_index = len(text)  # last valid char (1-based index)

    # If si is beyond the end, fill gap first
    if si > lastchar_index:
        gap = si - lastchar_index
        text = _insert_1based(text, lastchar_index + 1, PLACEHOLDER * gap)
        lastchar_index = len(text)

    # If ei is beyond the end, fill that gap too
    if ei > lastchar_index:
        gap = ei - lastchar_index
        text = _insert_1based(text, lastchar_index + 1, PLACEHOLDER * gap)

    # Now si, ei are in range. google_text used:
    #   start = text[0:si-1]
    #   end   = text[ei:]
    return text[: si - 1] + text[ei:]

@dataclass
class TabState:
    text: str = ""
    elements: Dict[str, dict] = field(default_factory=dict)
    name: Optional[str] = None          # human-readable tab name ("First Tab", "Second Tab", etc.)
    first_timestamp: Optional[int] = None  # when this tab first saw edits
    # NEW: dropdown metadata
    dropdown_defs: Dict[str, dict] = field(default_factory=dict)      # def_id -> ae command
    dropdown_elems: Dict[str, dict] = field(default_factory=dict)     # elem_id -> ae command (et == "dropdown")
    dropdown_instances: List[Tuple[int, str]] = field(default_factory=list)  # list of (spi, elem_id)



class DocState:
    """
    In-memory representation of one Google Doc reconstructed from
    google_docs_save bundles. Handles multiple tabs.
    """

    def __init__(self, user_id: str, doc_id: str):
        self.user_id = user_id
        self.doc_id = doc_id
        # tab_id -> TabState
        self.tabs: Dict[str, TabState] = collections.defaultdict(TabState)

        # some meta
        self.last_server_time: Optional[float] = None
        self.last_timestamp: Optional[int] = None
        self.last_url: Optional[str] = None
        self.chrome_identity: Dict[str, Optional[str]] = {}

    # --- main public entry ---

    @staticmethod
    def _extract_name_from_d(data):
        """
        The mkch/ac/ucp commands put tab names into deeply nested lists like:
        [ '', [[], [1, 'First Tab']] ]
        or
        [ 't.95y...', [1, 'Tab 2'], [1] ]

        This walks the structure and returns the first string it finds.
        """
        def _walk(x):
            if isinstance(x, str):
                return x
            if isinstance(x, list):
                for item in x:
                    r = _walk(item)
                    if r:
                        return r
            return None

        return _walk(data)

    def expand_dropdowns(self) -> None:
        """
        After all events have been applied, replace the single-character
        dropdown icon at each recorded position with a readable placeholder
        like 'DROPDOWN: Configuration Test – Option 1'.
        """
        for tab in self.tabs.values():
            if not tab.dropdown_instances:
                continue

            # Process from right to left so earlier replacements do not affect
            # positions of later ones.
            for spi, elem_id in sorted(tab.dropdown_instances, key=lambda x: x[0], reverse=True):
                dropdown_cmd = tab.dropdown_elems.get(elem_id)
                if not dropdown_cmd:
                    continue

                epm = dropdown_cmd.get("epm", {})
                def_id = epm.get("dde_di")
                selected_item_id = epm.get("dde-sii")
                selected_fallback_value = epm.get("dde-fdv")  # text of selected option

                # Look up the definition to get config name and items
                def_cmd = tab.dropdown_defs.get(def_id, {})
                ddefe = def_cmd.get("epm", {}).get("ddefe-ddi", {})
                config_name = def_cmd.get("epm", {}).get("ddefe-t", "Dropdown")
                items = ddefe.get("cv", {}).get("opValue", [])

                # Try to find the selected item label
                selected_label = selected_fallback_value
                for item in items:
                    if item.get("di-id") == selected_item_id:
                        selected_label = item.get("di-dv") or item.get("di-v") or selected_label
                        break

                human = f"DROPDOWN: {config_name} – {selected_label}"

                # Replace the single icon character at [spi] (1-based) with `human`
                # tab.text[spi-1] should currently be ''
                if 1 <= spi <= len(tab.text):
                    tab.text = tab.text[: spi - 1] + human + tab.text[spi:]

    def apply_bundle(self, bundle: dict, default_tab: str, event_timestamp: Optional[int] = None) -> None:
        """
        Apply one google_docs_save bundle.

        event_timestamp is used to approximate tab creation / ordering.
        """
        commands = bundle.get("commands", [])
        for cmd in commands:
            self._apply_cmd(cmd, default_tab, event_timestamp)

    # --- command handlers (same idea as before) ---

        # --- command handlers (same idea as before) ---

    def _apply_cmd(self, cmd: dict, current_tab: str, event_timestamp: Optional[int] = None) -> None:
        ty = cmd.get("ty")
        if not ty:
            return

        # ensure the tab exists and record first edit timestamp
        tab = self.tabs[current_tab]
        if event_timestamp is not None and tab.first_timestamp is None:
            tab.first_timestamp = event_timestamp

        # Multi-command wrapper
        if ty == "mlti":
            for sub in cmd.get("mts", []):
                self._apply_cmd(sub, current_tab, event_timestamp)
            return

        # nm: "new mutation" with routing info (often contains tab id)
        if ty == "nm":
            target_tab = current_tab
            nmr = cmd.get("nmr") or []
            # heuristic: LAST string starting with 't.' is the tab id
            for x in reversed(nmr):
                if isinstance(x, str) and x.startswith("t."):
                    target_tab = x
                    break
            inner_cmd = cmd.get("nmc", {})
            self._apply_cmd(inner_cmd, target_tab, event_timestamp)
            return


        # ----- TAB METADATA COMMANDS -----

        # mkch: initial tab name(s) (e.g. [[1, "Tab 1"]])
        if ty == "mkch":
            data = cmd.get("d")
            name = self._extract_name_from_d(data)
            if name:
                tab = self.tabs[current_tab]
                tab.name = name
            return

        # ucp: update caption / rename tab
        # d looks like: ['t.95y...', [[], [1, 'Second Tab']]]
        # or ['', [[], [1, 'First Tab']]]
        if ty == "ucp":
            data = cmd.get("d")
            if not isinstance(data, list) or len(data) < 2:
                return
            tab_id = data[0] or current_tab
            name = self._extract_name_from_d(data[1])
            if name:
                tstate = self.tabs[tab_id]
                tstate.name = name
                if event_timestamp is not None and tstate.first_timestamp is None:
                    tstate.first_timestamp = event_timestamp
            return

        # ac: add child (new tab)
        # d looks like: ['t.95y...', [1, 'Tab 2'], [1]]
        if ty == "ac":
            data = cmd.get("d")
            if not isinstance(data, list) or len(data) < 2:
                return
            tab_id = data[0]
            if not isinstance(tab_id, str):
                return
            name = self._extract_name_from_d(data[1])
            tstate = self.tabs[tab_id]
            if name:
                tstate.name = name
            if event_timestamp is not None and tstate.first_timestamp is None:
                tstate.first_timestamp = event_timestamp
            return

        # ----- TEXT EDITING COMMANDS -----

        # Insert string (1-based indices, placeholder-aware)
        if ty == "is":
            tab = self.tabs[current_tab]
            s = cmd.get("s", "")
            ibi = cmd.get("ibi")
            
            # In your old code, ibi is 1-based, and if missing, you don't get an insert.
            # Fall back to "append" if ibi missing, using 1-based len+1.
            if ibi is None:
                ibi = len(tab.text) + 1

            try:
                ibi_int = int(ibi)
            except (TypeError, ValueError):
                ibi_int = len(tab.text) + 1

            tab.text = _insert_1based(tab.text, ibi_int, s)
            return

        # Delete substring [si, ei) (1-based indices, placeholder-aware)
        if ty == "ds":
            tab = self.tabs[current_tab]
            si = cmd.get("si")
            ei = cmd.get("ei")

            # If indexes are missing, nothing to do
            if si is None or ei is None:
                return

            try:
                si_int = int(si)
                ei_int = int(ei)
            except (TypeError, ValueError):
                return

            # DS uses [si, ei) semantics; this matches your old implementation
            tab.text = _delete_1based(tab.text, si_int, ei_int)
            return

        # Alter substring [si, ei) -> s
        # IMPORTANT: many 'as' commands are *style only* (no 's').
        # If there is no 's', we treat it as style and ignore.
        if ty == "as":
            if "s" not in cmd:
                # style-only 'as' — do not touch text
                return

            tab = self.tabs[current_tab]
            s = cmd.get("s", "")
            si = cmd.get("si")
            ei = cmd.get("ei")

            if si is None or ei is None:
                return

            try:
                si_int = int(si)
                ei_int = int(ei)
            except (TypeError, ValueError):
                return

            # emulate "delete then insert" at the same 1-based location
            tab.text = _delete_1based(tab.text, si_int, ei_int)
            tab.text = _insert_1based(tab.text, si_int, s)
            return

        # ----- ELEMENT COMMANDS (images, inline objects, dropdowns, etc.) -----

        if ty == "ae":
            tab = self.tabs[current_tab]
            el_id = cmd.get("id")
            if not el_id:
                return
        
            et = cmd.get("et")
        
            # Dropdown definition (holds the options)
            if et == "dropdown-definition":
                tab.dropdown_defs[el_id] = cmd
                return
        
            # Actual dropdown element (one instance tied to a definition)
            if et == "dropdown":
                tab.dropdown_elems[el_id] = cmd
                return
        
            # Fallback: other elements (images, etc.)
            tab.elements[el_id] = cmd
            return

        # te: tie element into the text at position 'spi' (1-based)
        # We now special-case dropdowns to reconstruct a readable token.
        if ty == "te":
            tab = self.tabs[current_tab]
            el_id = cmd.get("id")
            spi = cmd.get("spi")
        
            if not el_id or not isinstance(spi, int):
                return
        
            # Is this tying a dropdown element?
            if el_id in tab.dropdown_elems:
                # DON'T touch tab.text here.
                # Just remember that at logical position `spi` there is this dropdown.
                tab.dropdown_instances.append((spi, el_id))
                return
        
            # For non-dropdown elements (e.g. images) you can keep old behavior:
            placeholder = f"[{el_id}]"
            tab.text = _insert_1based(tab.text, spi, placeholder)
            return



        # Other types (headings, document style, etc.) are formatting only.
        # We ignore them to keep indices consistent but text intact.
        return
