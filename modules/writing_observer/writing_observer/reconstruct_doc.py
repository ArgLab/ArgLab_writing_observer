'''
This can reconstruct a Google Doc from Google's JSON requests. It
is based on the reverse-engineering by James Somers in his blog
post about the Traceback extension. The code is, obviously, all
new.

See: `http://features.jsomers.net/how-i-reverse-engineered-google-docs/`
'''

import collections
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

"""
The placeholder character is used to fill gaps in the document, particularly
when there's a mismatch between the index and the length of the document's text (doc._text).
In an empty document, the insertion index (from the insert event `is`) is 1. However,
when the extension is started on a non-empty document, the first insertion index will be
greater than 1. This can lead to inconsistencies in indexing.
This placeholder is used to fill the 'gap' between len(doc._text) and the first insertion
index recorded in the logs.
This is done for the delete event ('ds') as well.
Say the first insert event in the logs is of a character 'a' with an index of 10.
This placeholder will be used to fill the gap between 1 and 10. Internally doc._text will
have 10 characters and when returning the output, all placeholders will be removed from
doc._text leaving only the character 'a'.
"""
PLACEHOLDER = '\x00'


def parse_tab_from_url(url: str) -> str:
    '''
    Extract the tab id from a Google Docs URL.
    '''
    if not url or "tab=" not in url:
        return "t.0"
    match = re.search(r"tab=([^&#]+)", url)
    return match.group(1) if match else "t.0"


class google_text(object):
    '''
    We encapsulate a string object to support a Google Doc snapshot at a
    point in time. Right now, this adds cursor position. In the future,
    we might annotate formatting and similar properties.
    '''
    def __new__(cls):
        '''
        Constructor. We create a blank document to be populated.
        '''
        new_object = object.__new__(cls)
        new_object._text = ""
        new_object._position = 0
        new_object._edit_metadata = {}
        new_object.fix_validity()
        return new_object

    def assert_validity(self):
        '''
        We do integrity checks. We store cursor length and text length in
        two lists for efficiency, and for now, this just confirms they're
        the same length.
        '''
        cursor_array_length = len(self._edit_metadata["cursor"])
        textlength_array_length = len(self._edit_metadata["length"])
        length_difference = cursor_array_length - textlength_array_length
        if length_difference != 0:
            raise Exception(
                "Edit metadata length doesn't match. This should never happen."
            )

    def fix_validity(self):
        '''
        Check we satisify invariants, and if not, fix them. This is helpful
        for graceful degredation. We also use this to initalize the object.
        '''
        errors_found = []

        if "cursor" not in self._edit_metadata:
            self._edit_metadata["cursor"] = []
            errors_found.append("No cursor array")
        if "length" not in self._edit_metadata:
            self._edit_metadata["length"] = []
            errors_found.append("No length array")

        # We expect edit metadata to be the same length. We went
        # from tabular to columnar which does not guarantee this
        # invariant, unfortunately. We should evaluate if this
        # optimization was premature, but it's a lot more compact.
        cursor_array_length = len(self._edit_metadata["cursor"])
        textlength_array_length = len(self._edit_metadata["length"])
        length_difference = cursor_array_length - textlength_array_length
        if length_difference > 0:
            print("Mismatching lengths. This should never happen!")
            self._edit_metadata["length"] += [0] * length_difference
            errors_found.append("Mismatching lengths")
        if length_difference < 0:
            print("Mismatching lengths. This should never happen!")
            self._edit_metadata["cursor"] += [0] * -length_difference
            errors_found.append("Mismatching lengths")
        return errors_found

    def from_json(json_rep):
        '''
        Class method to deserialize from JSON

        For null objects, it will create a new Google Doc.
        '''
        new_object = google_text.__new__(google_text)
        if json_rep is None:
            json_rep = {}
        new_object._text = json_rep.get('text', '')
        new_object._position = json_rep.get('position', 0)
        new_object._edit_metadata = json_rep.get('edit_metadata', {})
        new_object.fix_validity()
        return new_object

    def update(self, text):
        '''
        Update the text. Note that we should probably combine this
        with updating the cursor position, since if text updates,
        the cursor should always update too.
        '''
        self._text = text

    def len(self):
        '''
        Length of the string
        '''
        return len(self._text)

    @property
    def position(self):
        '''
        Cursor postion. Perhaps we should rename this?
        '''
        return self._position

    @position.setter
    def position(self, p):
        '''
        Update cursor position.

        Side effect: Update Deane arrays.
        '''
        self._edit_metadata['length'].append(len(self._text))
        self._edit_metadata['cursor'].append(p)
        self._position = p

    @property
    def edit_metadata(self):
        '''
        Return edit metadata. For now, this is length / cursor position
        arrays, but perhaps we should rename this as we expect more
        analytics.
        '''
        return self._edit_metadata

    def __str__(self):
        '''
        This returns __just__ the text of the document (no metadata)
        '''
        return self._text

    @property
    def json(self):
        '''
        This serializes to JSON.
        '''
        return {
            'text': self._text,
            'position': self._position,
            'edit_metadata': self._edit_metadata
        }


def get_parsed_text(self):
    '''
    Returns the text ignoring the normal placeholders
    '''
    return self._text.replace(PLACEHOLDER, "")


def command_list(doc, commands):
    '''
    This will process a list of commands. It is helpful either when
    loading the history of a new doc, or in updating a document from
    new `save` requests.
    '''
    doc_state = DocState(user_id="", doc_id="")
    tab = doc_state.tabs["t.0"]
    tab.doc = doc
    for item in commands:
        doc_state._dispatch_cmd(item, "t.0", None)
    return tab.doc


def multi(doc, mts, ty):
    '''
    Handles a batch of commands.

    `mts` is the list of commands
    `ty` is always `mlti`
    '''
    doc = command_list(doc, mts)
    return doc


def insert(doc, ty, ibi, s):
    '''
    Insert new text.
    * `ty` is always `is`
    * `ibi` is where the insert happens
    * `s` is the string to insert
    '''
    # The index of the next character after the last character of the text
    nextchar_index = len(doc._text) + 1
    # If the insert index is greater than nextchar_index, insert placeholders to fill the gap
    # This occurs when the document has undergone modifications before the logger has been initialized
    if ibi > nextchar_index:
        insert(doc, ty, nextchar_index, PLACEHOLDER * (ibi - nextchar_index))
    doc.update("{start}{insert}{end}".format(
        start=doc._text[0:ibi - 1],
        insert=s,
        end=doc._text[ibi - 1:]
    ))

    doc.position = ibi + len(s)

    return doc


def delete(doc, ty, si, ei):
    '''
    Delete text.
    * `ty` is always `ds`
    * `si` is the index of the start of deletion
    * `ei` is the end
    '''
    # Index of the last character in the text. `si` and `ei` shouldn't go beyond that
    lastchar_index = len(doc._text)
    # If the deletion indexes are greater than nextchar_index, insert placeholders to fill the gap
    # This occurs when the document has undergone modifications before the logger has been initialized
    if si > lastchar_index:
        insert(doc, ty, lastchar_index + 1, PLACEHOLDER * (si - lastchar_index))
    if ei > lastchar_index:
        insert(doc, ty, lastchar_index + 1, PLACEHOLDER * (ei - lastchar_index))
    doc.update("{start}{end}".format(
        start=doc._text[0:si - 1],
        end=doc._text[ei:]
    ))

    doc.position = si

    return doc


def replace(doc, ty, snapshot):
    for entry in snapshot:

        # The index of the next character after the last
        # character of the text
        nextchar_index = len(doc._text) + 1
        if 'ty' in entry and entry['ty'] == 'is':

            s = entry['s']
            ibi = entry['ibi']
            if 'sl' in entry:
                sl = entry['sl']
            else:
                sl = len(s)

            # If the insert index is greater than
            # nextchar_index, insert placeholders
            # to fill the gap.
            #
            # This occurs when the document has undergone
            # modifications before the logger has been
            # initialized
            if ibi > nextchar_index:
                insert(doc,
                       ty,
                       nextchar_index,
                       PLACEHOLDER * (ibi - nextchar_index))

            doc.update("{start}{insert}{end}".format(
                start=doc._text[0:ibi - 1],
                insert=s,
                end=doc._text[ibi + sl - 1:]
            ))

    return doc


def alter(doc, si=None, ei=None, st=None, sm=None, ty=None, s=None, **kwargs):
    '''
    Alter commands change formatting.

    We ignore these for now, unless the command includes replacement text.
    '''
    if s is None or si is None or ei is None:
        return doc

    try:
        si_int = int(si)
        ei_int = int(ei)
    except (TypeError, ValueError):
        return doc

    # Replace text by deleting then inserting at the same position
    doc = delete(doc, ty, si_int, ei_int)
    doc = insert(doc, ty, si_int, s)
    return doc


def null(doc, **kwargs):
    '''
    Do nothing. Google sometimes makes null requests. There are also
    requests we don't know how to process.

    I'm not quite sure what these are. The command is not JavaScript's
    `null` but the string `'null'`
    '''
    return doc


def _touch_tab(tab, event_timestamp):
    if event_timestamp is None:
        return
    if tab.first_timestamp is None:
        tab.first_timestamp = event_timestamp
    tab.last_timestamp = event_timestamp


@dataclass
class CommandContext:
    doc_state: "DocState"
    current_tab: str
    event_timestamp: Optional[int]

    @property
    def tab(self) -> "TabState":
        return self.doc_state.tabs[self.current_tab]


def _cmd_is(ctx: CommandContext, ty=None, ibi=None, s=None, **kwargs):
    if ibi is None or s is None:
        return
    insert(ctx.tab.doc, ty, ibi, s)


def _cmd_ds(ctx: CommandContext, ty=None, si=None, ei=None, **kwargs):
    if si is None or ei is None:
        return
    delete(ctx.tab.doc, ty, si, ei)


def _cmd_as(ctx: CommandContext, **cmd):
    alter(ctx.tab.doc, **cmd)


def _cmd_rplc(ctx: CommandContext, ty=None, snapshot=None, **kwargs):
    if snapshot is None:
        return
    replace(ctx.tab.doc, ty, snapshot)


def _cmd_mlti(ctx: CommandContext, mts=None, **kwargs):
    for sub in mts or []:
        ctx.doc_state._dispatch_cmd(sub, ctx.current_tab, ctx.event_timestamp)


def _cmd_nm(ctx: CommandContext, nmr=None, nmc=None, **kwargs):
    target_tab = ctx.current_tab
    for item in reversed(nmr or []):
        if isinstance(item, str) and item.startswith("t."):
            target_tab = item
            break
    ctx.doc_state._dispatch_cmd(nmc or {}, target_tab, ctx.event_timestamp)


def _cmd_mkch(ctx: CommandContext, d=None, **kwargs):
    name = ctx.doc_state._extract_name_from_d(d)
    if name:
        ctx.tab.name = name


def _cmd_ucp(ctx: CommandContext, d=None, **kwargs):
    if not isinstance(d, list) or len(d) < 2:
        return
    tab_id = d[0] or ctx.current_tab
    name = ctx.doc_state._extract_name_from_d(d[1])
    if not name:
        return
    target = ctx.doc_state.tabs[tab_id]
    target.name = name
    _touch_tab(target, ctx.event_timestamp)


def _cmd_ac(ctx: CommandContext, d=None, **kwargs):
    if not isinstance(d, list) or len(d) < 2:
        return
    tab_id = d[0]
    if not isinstance(tab_id, str):
        return
    target = ctx.doc_state.tabs[tab_id]
    name = ctx.doc_state._extract_name_from_d(d[1])
    if name:
        target.name = name
    _touch_tab(target, ctx.event_timestamp)


def _cmd_ae(ctx: CommandContext, id=None, et=None, **kwargs):
    if not id:
        return
    if et == "dropdown-definition":
        ctx.tab.dropdown_defs[id] = {"id": id, "et": et, **kwargs}
        return
    if et == "dropdown":
        ctx.tab.dropdown_elems[id] = {"id": id, "et": et, **kwargs}
        return
    ctx.tab.elements[id] = {"id": id, "et": et, **kwargs}


def _cmd_te(ctx: CommandContext, id=None, spi=None, **kwargs):
    if not id or not isinstance(spi, int):
        return
    if id in ctx.tab.dropdown_elems:
        ctx.tab.dropdown_instances.append((spi, id))
        return
    insert(ctx.tab.doc, "is", spi, f"[{id}]")


def _cmd_null(ctx: CommandContext, **kwargs):
    return


# Centralized dispatch for all command types.
#
# Notes:
# - Some commands are formatting-only or suggested edits and are treated as no-ops.
# - Dropdown and element handling is routed through tab-aware handlers.
dispatch = {
    'mlti': _cmd_mlti,
    'nm': _cmd_nm,
    'mkch': _cmd_mkch,
    'ucp': _cmd_ucp,
    'ac': _cmd_ac,
    'ae': _cmd_ae,
    'te': _cmd_te,
    'as': _cmd_as,
    'ds': _cmd_ds,
    'is': _cmd_is,
    'rplc': _cmd_rplc,  # rplc is called as the first edit when a doc is created from a template
    'rvrt': _cmd_rplc,  # apparently logged after an undo
    'iss': _cmd_null,  # suggested insertion (ignored)
    'mefd': _cmd_null,  # suggestion
    'msfd': _cmd_null,  # suggestion
    'null': _cmd_null,
    'ord': _cmd_null,
    'ras': _cmd_null,  # suggestion. Autospell?
    'rte': _cmd_null,  # suggestion
    'rue': _cmd_null,  # suggestion
    'sas': _cmd_null,  # suggestion. Autospell?
    'sl': _cmd_null,
    'ste': _cmd_null,  # suggestion
    'sue': _cmd_null,  # suggestion
    'uefd': _cmd_null,  # suggestion
    'use': _cmd_null,  # suggestion
    'umv': _cmd_null,
    'usfd': _cmd_null,  # suggestion
    'ase': _cmd_null,  # suggestion
    'ast': _cmd_null,  # suggestion. Image?
    'astss': _cmd_null,  # suggestion. Autospell?
    'ue': _cmd_null,
    'de': _cmd_null,
    'dse': _cmd_null,  # suggestion
    'dss': _cmd_null,  # suggested deletion
}


@dataclass
class TabState:
    '''
    Represents the state of a single tab within a Google Doc.
    '''
    doc: google_text = field(default_factory=google_text)
    elements: Dict[str, dict] = field(default_factory=dict)
    name: Optional[str] = None
    first_timestamp: Optional[int] = None
    last_timestamp: Optional[int] = None
    dropdown_defs: Dict[str, dict] = field(default_factory=dict)
    dropdown_elems: Dict[str, dict] = field(default_factory=dict)
    dropdown_instances: List[Tuple[int, str]] = field(default_factory=list)

    @property
    def text(self) -> str:
        return self.doc._text

    @text.setter
    def text(self, value: str) -> None:
        self.doc._text = value or ""

    def to_dict(self) -> dict:
        return {
            "text": self.doc._text,
            "position": self.doc.position,
            "edit_metadata": self.doc.edit_metadata,
            "elements": self.elements,
            "name": self.name,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "dropdown_defs": self.dropdown_defs,
            "dropdown_elems": self.dropdown_elems,
            "dropdown_instances": self.dropdown_instances,
        }

    @staticmethod
    def from_dict(data: dict) -> "TabState":
        tab = TabState()
        if not data:
            return tab
        tab.doc = google_text.from_json(data)
        tab.elements = data.get("elements", {}) or {}
        tab.name = data.get("name")
        tab.first_timestamp = data.get("first_timestamp")
        tab.last_timestamp = data.get("last_timestamp")
        tab.dropdown_defs = data.get("dropdown_defs", {}) or {}
        tab.dropdown_elems = data.get("dropdown_elems", {}) or {}
        tab.dropdown_instances = data.get("dropdown_instances", []) or []
        return tab


class DocState:
    '''
    In-memory representation of one Google Doc reconstructed from bundles.
    '''
    def __init__(self, user_id: str, doc_id: str):
        self.user_id = user_id
        self.doc_id = doc_id
        self.tabs: Dict[str, TabState] = collections.defaultdict(TabState)
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

    @staticmethod
    def _extract_name_from_d(data):
        def _walk(item):
            if isinstance(item, str):
                if item.startswith("t."):
                    return None
                return item
            if isinstance(item, list):
                for child in item:
                    found = _walk(child)
                    if found:
                        return found
            return None

        return _walk(data)

    def apply_bundle(self, bundle: dict, default_tab: str, event_timestamp: Optional[int] = None) -> None:
        commands = bundle.get("commands", [])
        for cmd in commands:
            self._dispatch_cmd(cmd, default_tab, event_timestamp)

    def _dispatch_cmd(self, cmd: dict, current_tab: str, event_timestamp: Optional[int] = None) -> None:
        ty = cmd.get("ty")
        if not ty:
            return

        ctx = CommandContext(self, current_tab, event_timestamp)
        _touch_tab(ctx.tab, event_timestamp)
        handler = dispatch.get(ty)
        if handler:
            handler(ctx, **cmd)


def _render_tab_text(tab: TabState) -> str:
    text = tab.doc._text
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


def render_tab_text(tab: TabState) -> str:
    return _render_tab_text(tab)


def render_full_text(doc_state: DocState) -> str:
    parts: List[str] = []

    def _tab_sort_key(item):
        _tab_id, tab_state = item
        return tab_state.first_timestamp or 0

    for tab_id, tab in sorted(doc_state.tabs.items(), key=_tab_sort_key):
        display_name = tab.name or tab_id
        parts.append(f"{display_name}\n")
        parts.append(f"{'=' * len(display_name)}\n\n")
        parts.append(_render_tab_text(tab))
        parts.append("\n\n")

    return "".join(parts) if parts else ""

if __name__ == '__main__':
    google_json = json.load(open("sample3.json"))
    docs_history = google_json['client']['history']['changelog']
    docs_history_short = [t[0] for t in docs_history]
    doc = google_text()
    doc = command_list(doc, docs_history_short)
    print(doc)
    print(doc.position)
    print(doc.edit_metadata)
