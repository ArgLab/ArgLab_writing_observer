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
    """
    Represents the state of a single tab within a Google Doc.
    
    Tabs in Google Docs function as separate sections/pages that users can switch between.
    Each tab has independent content (text), metadata (name), and embedded elements (dropdowns, images).
    
    Key concepts:
    - Tabs are identified by unique IDs (e.g., 't.95y...')
    - Tabs can be renamed via 'ucp' (update caption) or created via 'ac' (add child) commands
    - Text editing (insert, delete, alter) operations target the current tab
    - Elements like dropdowns are tied to specific positions within a tab's text
    """
    text: str = ""  # The reconstructed text content of this tab
    elements: Dict[str, dict] = field(default_factory=dict)  # Embedded elements: elem_id -> metadata (images, etc.)
    name: Optional[str] = None  # Human-readable tab name (e.g., "First Tab", "Second Tab")
    first_timestamp: Optional[int] = None  # Client timestamp (ms) when this tab first received edits
    
    # Dropdown metadata: Smart-chip dropdowns are reconstructed from multiple command types
    dropdown_defs: Dict[str, dict] = field(default_factory=dict)  # Dropdown definitions: def_id -> 'ae' command (et == "dropdown-definition")
    dropdown_elems: Dict[str, dict] = field(default_factory=dict)  # Dropdown instances: elem_id -> 'ae' command (et == "dropdown")
    dropdown_instances: List[Tuple[int, str]] = field(default_factory=list)  # Positions where dropdowns appear: (text_position, elem_id)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "elements": self.elements,
            "name": self.name,
            "first_timestamp": self.first_timestamp,
            "dropdown_defs": self.dropdown_defs,
            "dropdown_elems": self.dropdown_elems,
            "dropdown_instances": self.dropdown_instances,
        }

    @staticmethod
    def from_dict(data: dict) -> "TabState":
        tab = TabState()
        if not data:
            return tab
        tab.text = data.get("text", "")
        tab.elements = data.get("elements", {}) or {}
        tab.name = data.get("name")
        tab.first_timestamp = data.get("first_timestamp")
        tab.dropdown_defs = data.get("dropdown_defs", {}) or {}
        tab.dropdown_elems = data.get("dropdown_elems", {}) or {}
        tab.dropdown_instances = data.get("dropdown_instances", []) or []
        return tab



class DocState:
    """
    In-memory representation of one Google Doc reconstructed from google_docs_save bundles.
    
    TABS IN GOOGLE DOCS:
    Google Docs supports multiple "tabs" (introduced in 2024), which function as independent
    sections/pages within a single document. Each tab has:
    - Unique ID (e.g., 't.0', 't.95y...', 't.4n9p3wa3df6o')
    - Metadata: name, creation time
    - Content: text with embedded elements (dropdowns, images)
    
    DocState tracks all tabs for a document and reconstructs their content from command bundles.
    The 'tab_id' in events (extracted from URL 'tab=' parameter or included in commands) routes
    text edits to the appropriate tab.
    
    COMMANDS AND THEIR RELATIONSHIP TO TABS:
    - 'mkch': Initial tab metadata setup (sets tab names)
    - 'ucp': Update caption/rename tab (modifies existing tab name)
    - 'ac': Add child tab (creates new tab)
    - 'nm': New mutation with routing (routes a command to a specific tab via 'nmr' field)
    - 'is', 'ds', 'as': Text editing commands (insert, delete, substitute) - affect current tab
    - 'ae': Add element (dropdowns, images) - stores metadata tied to current tab
    - 'te': Tie element into text (embeds element at specific position in current tab)
    - 'mlti': Multi-command wrapper (contains multiple sub-commands)
    
    The reconstruction process:
    1. Events arrive with a tab_id (from URL or command routing)
    2. Commands are applied to the appropriate TabState
    3. Text editing commands update tab.text
    4. Element commands store metadata in tab.elements/dropdown_defs/dropdown_elems
    5. After all events, expand_dropdowns() converts stored dropdown metadata into readable text
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

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "doc_id": self.doc_id,
            "tabs": {tab_id: tab.to_dict() for tab_id, tab in self.tabs.items()},
            "last_server_time": self.last_server_time,
            "last_timestamp": self.last_timestamp,
            "last_url": self.last_url,
            "chrome_identity": self.chrome_identity,
        }

    @staticmethod
    def from_dict(data: dict) -> "DocState":
        doc = DocState(data.get("user_id", ""), data.get("doc_id", ""))
        doc.tabs = collections.defaultdict(TabState)
        for tab_id, tab_data in (data.get("tabs") or {}).items():
            doc.tabs[tab_id] = TabState.from_dict(tab_data)
        doc.last_server_time = data.get("last_server_time")
        doc.last_timestamp = data.get("last_timestamp")
        doc.last_url = data.get("last_url")
        doc.chrome_identity = data.get("chrome_identity", {}) or {}
        return doc

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

                human = f"DROPDOWN: {config_name} - {selected_label}"

                # Replace the single icon character at [spi] (1-based) with `human`
                # tab.text[spi-1] should currently be ''
                if 1 <= spi <= len(tab.text):
                    tab.text = tab.text[: spi - 1] + human + tab.text[spi:]

    def apply_bundle(self, bundle: dict, default_tab: str, event_timestamp: Optional[int] = None) -> None:
        """
        Apply one google_docs_save bundle to this document.
        
        A bundle contains multiple commands that were executed together. This method
        extracts commands from the bundle and applies each one in order.
        
        Args:
            bundle: dict containing 'commands' list from google_docs_save event
            default_tab: The tab_id to use if a command does not specify a different tab
                        (extracted from event URL or passed through)
            event_timestamp: Client timestamp (ms) from the event; used to track when
                           tabs first received edits (important for tab ordering)
        
        The default_tab is significant because:
        - Most text editing commands (is, ds, as) apply to the current/default tab
        - Some commands (nm: new mutation) may override this with their own tab routing (nmr field)
        - Tab metadata commands (mkch, ucp, ac) can reference specific tab_ids
        """
        commands = bundle.get("commands", [])
        for cmd in commands:
            self._apply_cmd(cmd, default_tab, event_timestamp)

    # --- command handlers (same idea as before) ---

    def _apply_cmd(self, cmd: dict, current_tab: str, event_timestamp: Optional[int] = None) -> None:
        """
        Apply a single command to the appropriate tab.
        
        COMMAND ROUTING TO TABS:
        Commands specify which tab they operate on through several mechanisms:
        1. 'nm' (new mutation): Contains routing info (nmr) that may specify a tab_id
        2. 'ucp' (update caption), 'ac' (add child): First data field may contain tab_id
        3. Default: Text editing & element commands use current_tab parameter
        
        SUPPORTED COMMAND TYPES:
        TAB METADATA:
          - mkch: Set initial tab name(s)
          - ucp: Update caption (rename tab)
          - ac: Add child (create new tab)
        
        TEXT EDITING:
          - is: Insert string at 1-based index
          - ds: Delete substring [si, ei)
          - as: Alter substring (delete then insert)
        
        ELEMENTS (EMBEDDED OBJECTS):
          - ae: Add element (dropdowns, images) - stores metadata
          - te: Tie element into text - embeds element at position
        
        CONTROL FLOW:
          - mlti: Multi-command wrapper - contains multiple sub-commands
        
        Args:
            cmd: The command dict with 'ty' (type) and type-specific fields
            current_tab: Default tab_id if command doesn't specify otherwise
            event_timestamp: For tracking when tabs first received edits
        """
        ty = cmd.get("ty")
        if not ty:
            return

        # Ensure the tab exists and record first edit timestamp
        # This helps track when tabs were created/first edited
        tab = self.tabs[current_tab]
        if event_timestamp is not None and tab.first_timestamp is None:
            tab.first_timestamp = event_timestamp

        # MLTI: Multi-command wrapper
        # Contains multiple sub-commands in 'mts' field; recursively apply each one
        if ty == "mlti":
            for sub in cmd.get("mts", []):
                self._apply_cmd(sub, current_tab, event_timestamp)
            return

        # NM: "New mutation" with routing info
        # This command can specify which tab to route to via the 'nmr' (new mutation routing) field.
        # The nmr is a list that may contain a tab_id (string starting with 't.').
        # We use a heuristic: the LAST string starting with 't.' in nmr is the target tab.
        # The actual command to execute is in 'nmc' (new mutation command).
        if ty == "nm":
            target_tab = current_tab  # Default to current tab if routing not found
            nmr = cmd.get("nmr") or []
            # Heuristic: LAST string starting with 't.' is the tab id
            # (handles cases where multiple tab refs might be present)
            for x in reversed(nmr):
                if isinstance(x, str) and x.startswith("t."):
                    target_tab = x
                    break
            inner_cmd = cmd.get("nmc", {})
            self._apply_cmd(inner_cmd, target_tab, event_timestamp)
            return


        # ========== TAB METADATA COMMANDS ==========
        # These commands manage tab creation, naming, and deletion.
        # They enable multi-tab document structure where each tab functions as a separate section.

        # MKCH: "Make channel" - Initialize tab metadata (typically tab names)
        # Command structure: {'ty': 'mkch', 'd': [nested list containing tab names]}
        # Data format: d contains deeply nested lists like [[1, "Tab 1"]]
        # Purpose: Set up initial tab name(s) when document is created or tabs are added
        # Result: Updates tab.name to human-readable value (e.g., "First Tab")
        if ty == "mkch":
            data = cmd.get("d")
            name = self._extract_name_from_d(data)
            if name:
                tab = self.tabs[current_tab]
                tab.name = name
            return

        # UCP: "Update caption" - Rename existing tab
        # Command structure: {'ty': 'ucp', 'd': [tab_id_or_empty, nested_data_with_name, ...]}
        # Data format: d[0] is tab_id ('t.95y...') or empty string (uses current_tab)
        #              d[1] contains nested list with new name
        # Example: ['t.95y...', [[], [1, 'Second Tab']]]
        # Example: ['', [[], [1, 'First Tab']]]
        # Purpose: Rename a tab (user changes "Tab 1" to "Overview", etc.)
        # Result: Updates specified tab's name; records timestamp if first edit
        if ty == "ucp":
            data = cmd.get("d")
            if not isinstance(data, list) or len(data) < 2:
                return
            tab_id = data[0] or current_tab  # If empty string, use current tab
            name = self._extract_name_from_d(data[1])
            if name:
                tstate = self.tabs[tab_id]
                tstate.name = name
                # Track when this tab first received operations
                if event_timestamp is not None and tstate.first_timestamp is None:
                    tstate.first_timestamp = event_timestamp
            return

        # AC: "Add child" - Create new tab
        # Command structure: {'ty': 'ac', 'd': [new_tab_id, name_data, ...]}
        # Data format: d[0] is unique new tab_id (e.g., 't.95y...')
        #              d[1] contains nested list with tab name
        # Example: ['t.95y...', [1, 'Tab 2'], [1]]
        # Purpose: Create a new tab in the document (user clicks "+ Tab" or duplicate)
        # Result: Initializes new TabState with name; records creation timestamp
        if ty == "ac":
            data = cmd.get("d")
            if not isinstance(data, list) or len(data) < 2:
                return
            tab_id = data[0]  # The new tab's unique identifier
            if not isinstance(tab_id, str):
                return
            name = self._extract_name_from_d(data[1])
            tstate = self.tabs[tab_id]  # Creates new TabState via defaultdict
            if name:
                tstate.name = name
            # Record when this tab was created
            if event_timestamp is not None and tstate.first_timestamp is None:
                tstate.first_timestamp = event_timestamp
            return

        # ========== TEXT EDITING COMMANDS ==========
        # These commands modify the text content of a tab.
        # All use 1-based indexing and are placeholder-aware (handle gaps filled with \x00).

        # IS: "Insert string" - Add text at specified position
        # Command structure: {'ty': 'is', 's': string_to_insert, 'ibi': 1_based_insert_position}
        # Semantics: Insert 's' before position 'ibi' (1-based)
        # Example: ibi=1 means insert at start, ibi=len(text)+1 means append
        # Placeholder handling: Uses _insert_1based which fills gaps with PLACEHOLDER (\x00)
        # Purpose: User types, copy-pastes, or undo restores text
        # Result: tab.text modified with new string inserted at position
        if ty == "is":
            tab = self.tabs[current_tab]
            s = cmd.get("s", "")
            ibi = cmd.get("ibi")
            
            # ibi is 1-based. If missing, fall back to append (len+1)
            if ibi is None:
                ibi = len(tab.text) + 1

            try:
                ibi_int = int(ibi)
            except (TypeError, ValueError):
                ibi_int = len(tab.text) + 1

            tab.text = _insert_1based(tab.text, ibi_int, s)
            return

        # DS: "Delete substring" - Remove text in range [si, ei)
        # Command structure: {'ty': 'ds', 'si': start_1based, 'ei': end_1based}
        # Semantics: Delete text from position si (inclusive) to ei (exclusive), 1-based
        # Example: si=1, ei=5 deletes characters at positions 1,2,3,4 (not 5)
        # Placeholder handling: Preserves PLACEHOLDERs; may fill new gaps
        # Purpose: User deletes, backspace, undo, or cut operations
        # Result: tab.text modified with substring removed
        if ty == "ds":
            tab = self.tabs[current_tab]
            si = cmd.get("si")
            ei = cmd.get("ei")

            # If indexes are missing, nothing to delete
            if si is None or ei is None:
                return

            try:
                si_int = int(si)
                ei_int = int(ei)
            except (TypeError, ValueError):
                return

            # DS uses [si, ei) semantics; si is included, ei is excluded
            tab.text = _delete_1based(tab.text, si_int, ei_int)
            return

        # AS: "Alter substring" - Replace text in range [si, ei) with new string
        # Command structure: {'ty': 'as', 's': replacement_string, 'si': start_1based, 'ei': end_1based}
        # Semantics: Delete [si, ei), then insert 's' at si
        # Example: Replace "old" with "new" at positions 1-4
        # IMPORTANT: Many 'as' commands are STYLE-ONLY (no 's' field); these are ignored
        # Style-only 'as': Only changes formatting/style, doesn't change text content
        # Placeholder handling: Combines delete and insert logic
        # Purpose: User replaces text, formatting changes, or undo operations
        # Result: tab.text modified with substring replaced
        if ty == "as":
            if "s" not in cmd:
                # Style-only 'as' command — formatting change only, no text modification
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

            # Emulate "delete then insert" as a single operation at the same 1-based location
            tab.text = _delete_1based(tab.text, si_int, ei_int)
            tab.text = _insert_1based(tab.text, si_int, s)
            return

        # ========== ELEMENT COMMANDS (embedded objects in text) ==========
        # These commands manage embedded elements like dropdowns, images, and other inline objects.
        # Elements are stored separately and tied into the text via 'te' commands.

        # AE: "Add element" - Register an element (dropdown, image, etc.) with metadata
        # Command structure: {'ty': 'ae', 'id': element_id, 'et': element_type, 'epm': element_metadata}
        # Element types (et field):
        #   - 'dropdown-definition': Defines a dropdown menu (holds available options)
        #   - 'dropdown': A dropdown instance tied to a definition (holds selected value)
        #   - Other types: Images, inline objects, etc.
        # Metadata (epm):
        #   - For dropdown-definition: Contains option list (items), config name
        #   - For dropdown: Contains selected item ID and fallback value
        # Purpose: Create dropdown definitions when first added, create dropdown instances
        # Result: Stores metadata in appropriate tab dictionary for later reconstruction
        if ty == "ae":
            tab = self.tabs[current_tab]
            el_id = cmd.get("id")
            if not el_id:
                return
        
            et = cmd.get("et")
        
            # DROPDOWN DEFINITION: Holds the available options and configuration
            # Stored separately because multiple dropdown instances may share one definition
            # Example: A "Priority" dropdown used in multiple places shares one definition
            if et == "dropdown-definition":
                tab.dropdown_defs[el_id] = cmd
                return
        
            # DROPDOWN ELEMENT: One specific dropdown instance with a selected value
            # References a definition and stores which option is currently selected
            # Example: This dropdown's value is "High"
            if et == "dropdown":
                tab.dropdown_elems[el_id] = cmd
                return
        
            # FALLBACK: Other elements (images, shapes, etc.)
            # These are stored but cannot be reconstructed from logs (e.g., images lack binary data)
            tab.elements[el_id] = cmd
            return

        # TE: "Tie element" - Embed element into text at specific position
        # Command structure: {'ty': 'te', 'id': element_id, 'spi': 1_based_position}
        # Semantics: Place element 'id' at position 'spi' (1-based) in tab.text
        # Purpose: Insert a placeholder for an element (dropdown, image) into document text
        # Result: For dropdowns, records position for later reconstruction as readable text
        #         For other elements, inserts placeholder (e.g., "[image-123]")
        if ty == "te":
            tab = self.tabs[current_tab]
            el_id = cmd.get("id")
            spi = cmd.get("spi")
        
            if not el_id or not isinstance(spi, int):
                return
        
            # DROPDOWN SPECIAL HANDLING:
            # For dropdowns, we don't insert text here. Instead, we record the position
            # so expand_dropdowns() can later reconstruct readable text like:
            # "DROPDOWN: Priority – High" at the correct position.
            # This deferred approach allows us to gather all metadata before reconstruction.
            if el_id in tab.dropdown_elems:
                # Record this dropdown's position for post-processing
                tab.dropdown_instances.append((spi, el_id))
                return
        
            # NON-DROPDOWN ELEMENTS (e.g., images):
            # For now, insert a simple placeholder. Images cannot be fully reconstructed
            # since binary data is not included in logs.
            placeholder = f"[{el_id}]"
            tab.text = _insert_1based(tab.text, spi, placeholder)
            return



        # Other types (headings, document style, etc.) are formatting only.
        # We ignore them to keep indices consistent but text intact.
        return


def _render_tab_text(tab: TabState) -> str:
    text = tab.text
    if tab.dropdown_instances:
        for spi, elem_id in sorted(tab.dropdown_instances, key=lambda x: x[0], reverse=True):
            dropdown_cmd = tab.dropdown_elems.get(elem_id)
            if not dropdown_cmd:
                continue

            epm = dropdown_cmd.get("epm", {})
            def_id = epm.get("dde_di")
            selected_item_id = epm.get("dde-sii")
            selected_fallback_value = epm.get("dde-fdv")

            def_cmd = tab.dropdown_defs.get(def_id, {})
            ddefe = def_cmd.get("epm", {}).get("ddefe-ddi", {})
            config_name = def_cmd.get("epm", {}).get("ddefe-t", "Dropdown")
            items = ddefe.get("cv", {}).get("opValue", [])

            selected_label = selected_fallback_value
            for item in items:
                if item.get("di-id") == selected_item_id:
                    selected_label = item.get("di-dv") or item.get("di-v") or selected_label
                    break

            human = f"DROPDOWN: {config_name} - {selected_label}"
            if 1 <= spi <= len(text):
                text = text[: spi - 1] + human + text[spi:]

    return text.replace(PLACEHOLDER, "")


def render_full_text(doc_state: DocState) -> str:
    parts: List[str] = []

    def _tab_sort_key(item):
        tab_id, tab_state = item
        return tab_state.first_timestamp or 0

    for tab_id, tab in sorted(doc_state.tabs.items(), key=_tab_sort_key):
        display_name = tab.name or tab_id
        parts.append(f"{display_name}\n")
        parts.append(f"{'=' * len(display_name)}\n\n")
        parts.append(_render_tab_text(tab))
        parts.append("\n\n")

    return "".join(parts) if parts else ""
