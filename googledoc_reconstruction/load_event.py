# -*- coding: utf-8 -*-
"""
Created on Sun Dec  7 20:53:14 2025

@author: Saminur Islam
"""

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Iterator, Optional, Any


# ---------- Helpers ----------

def parse_tab_from_url(url: str) -> str:
    """
    Extracts the tab id from a Google Docs URL.
    
    MULTI-TAB URL STRUCTURE:
    Google Docs URLs include a 'tab' query parameter that identifies which tab the user is on:
       https://docs.google.com/document/d/{doc_id}/edit#gid=0&tab=t.4n9p3wa3df6o
    
    This function extracts that tab identifier (e.g., 't.4n9p3wa3df6o') so events can be
    routed to the correct tab during reconstruction.
    
    TAB ID FORMAT:
    - Tab IDs start with 't.' followed by alphanumeric characters
    - Special tab: 't.0' is the default/initial tab
    - Examples: 't.0', 't.95y...', 't.4n9p3wa3df6o'
    
    Args:
        url: A Google Docs URL string, may contain 'tab=' parameter
    
    Returns:
        The extracted tab_id (e.g., 't.4n9p3wa3df6o')
        If no tab parameter found, returns 't.0' as default tab
    
    Example:
        >>> parse_tab_from_url("https://docs.google.com/.../edit?tab=t.95y...")
        't.95y...'
        
        >>> parse_tab_from_url("https://docs.google.com/.../edit")
        't.0'
    """
    if not url or "tab=" not in url:
        return "t.0"
    m = re.search(r"tab=([^&]+)", url)
    return m.group(1) if m else "t.0"


# ---------- Data structures ----------

@dataclass
class GoogleDocsSaveEvent:
    """
    Flattened view of a google_docs_save event from WritingObserver log.
    This is the primary data structure fed into the reconstruction pipeline.
    
    MULTI-TAB EVENT STRUCTURE:
    Each event captures a user's save action in a Google Doc, which may involve one or more tabs.
    The event includes:
    - Document identification (user_id, doc_id)
    - Tab information (tab_id extracted from the URL)
    - Command bundles (commands that modified the document/tab)
    - Timing information (client and server timestamps)
    
    COMMAND BUNDLES:
    The 'bundles' list contains command bundles, where each bundle is a dict with:
    - 'commands': list of individual commands to apply to the current tab
    - Commands include tab metadata (mkch, ucp, ac), text editing (is, ds, as),
      and element operations (ae, te)
    
    TIMING:
    - timestamp: Client-side time (milliseconds) when the event was created
    - server_time: Server-side time (epoch seconds) when event was received
    These are used to chronologically order events and track when tabs were created/edited.
    
    Attributes:
        user_id: Unique identifier for the user making edits
        doc_id: Unique identifier for the Google Doc being edited
        url: The full URL of the doc (contains tab_id in query parameter)
        tab_id: Extracted tab identifier (e.g., 't.0', 't.95y...'); routes commands to correct tab
        timestamp: Client timestamp in milliseconds (when user made changes)
        server_time: Server timestamp in epoch seconds (when WritingObserver received event)
        chrome_identity: Dict with extension identity info
        bundles: List of command bundles to apply to the document
    """
    user_id: str
    doc_id: str
    url: str
    tab_id: str
    timestamp: int          # client.timestamp in ms
    server_time: float      # server.time (epoch seconds)
    chrome_identity: Dict[str, Optional[str]]
    bundles: list           # client.bundles (raw)


@dataclass
class Pointer:
    """
    Per (user, doc, tab) pointer so we only re-read new events.
    """
    last_timestamp: int = 0           # max client.timestamp seen
    last_server_time: float = 0.0     # max server.time seen


# key type for pointer dict
DocKey = Tuple[str, str, str]   # (user_id, doc_id, tab_id)


# ---------- Pointer persistence ----------

def load_pointers(pointer_path: str) -> Dict[DocKey, Pointer]:
    """
    Load pointer state from JSON file.
    If file doesn't exist, return empty dict.
    JSON structure:
    {
        "user_id|doc_id|tab_id": {
            "last_timestamp": ...,
            "last_server_time": ...
        },
        ...
    }
    """
    if not os.path.exists(pointer_path):
        return {}

    with open(pointer_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    pointers: Dict[DocKey, Pointer] = {}
    for key_str, data in raw.items():
        user_id, doc_id, tab_id = key_str.split("|", 2)
        pointers[(user_id, doc_id, tab_id)] = Pointer(
            last_timestamp=data.get("last_timestamp", 0),
            last_server_time=data.get("last_server_time", 0.0),
        )
    return pointers


def save_pointers(pointer_path: str, pointers: Dict[DocKey, Pointer]) -> None:
    """
    Save pointer state to JSON file.
    """
    os.makedirs(os.path.dirname(pointer_path), exist_ok=True)
    out: Dict[str, Any] = {}
    for (user_id, doc_id, tab_id), ptr in pointers.items():
        key_str = "|".join([user_id, doc_id, tab_id])
        out[key_str] = asdict(ptr)

    with open(pointer_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)


# ---------- Incremental log reader ----------

class IncrementalGoogleDocsSaveReader:
    """
    Reads a log file (main_log.jsonl or *.study.log) incrementally and yields
    only NEW google_docs_save events per (user_id, doc_id, tab_id).

    It uses a pointer file (JSON) to remember the last client.timestamp
    processed for each (user, doc, tab).
    """

    def __init__(self, pointer_path: str):
        self.pointer_path = pointer_path
        self.pointers: Dict[DocKey, Pointer] = load_pointers(pointer_path)

    # --- public API ---

    def iter_new_events(
        self,
        log_path: str,
        only_user: Optional[str] = None,
        only_doc: Optional[str] = None,
    ) -> Iterator[GoogleDocsSaveEvent]:
        """
        Iterate over NEW google_docs_save events in a given log file.

        - If only_user is given, only events for that user_id are yielded.
        - If only_doc is given, only events for that doc_id are yielded.

        After iterating, call `save()` to persist updated pointers.
        """
        with open(log_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                # Some log lines are: "<json>\t<iso_timestamp>".
                # We only want the JSON part.
                json_part = line.split("\t", 1)[0]

                try:
                    ev = json.loads(json_part)
                except json.JSONDecodeError:
                    # You can log or print if you want to debug malformed lines
                    # print(f"Skipping malformed json on line {line_no}")
                    continue

                client = ev.get("client", {})

                # We only care about google_docs_save
                event_type = client.get("event") or ev.get("event")
                if event_type != "google_docs_save":
                    continue

                # ---- extract identifiers ----
                auth = client.get("auth", {})
                user_id = auth.get("user_id") or auth.get("safe_user_id")
                if not user_id:
                    # Can't index by user; skip
                    continue

                doc_id = (
                    client.get("doc_id")
                    or client.get("object", {}).get("id")
                    or ev.get("doc_id")
                )
                if not doc_id:
                    # Can't index by doc; skip
                    continue

                if only_user and user_id != only_user:
                    continue
                if only_doc and doc_id != only_doc:
                    continue

                url = (
                    client.get("url")
                    or client.get("object", {}).get("url")
                    or ev.get("url", "")
                )
                tab_id = parse_tab_from_url(url)

                chrome_identity = (
                    client.get("chrome_identity")
                    or ev.get("metadata", {}).get("chrome_identity")
                    or {}
                )
                # Some logs put bundles only under client
                bundles = client.get("bundles", [])

                # client.timestamp (ms) is your main ordering for save events
                ts = client.get("timestamp") or ev.get("timestamp") or 0
                try:
                    ts_int = int(ts)
                except (TypeError, ValueError):
                    ts_int = 0

                server_time = ev.get("server", {}).get("time", 0.0)
                try:
                    server_time_f = float(server_time)
                except (TypeError, ValueError):
                    server_time_f = 0.0

                key: DocKey = (user_id, doc_id, tab_id)
                ptr = self.pointers.get(key)

                # If we have processed this timestamp already, skip
                if ptr is not None and ts_int <= ptr.last_timestamp:
                    continue

                # Construct the flattened event object
                gds_event = GoogleDocsSaveEvent(
                    user_id=user_id,
                    doc_id=doc_id,
                    url=url,
                    tab_id=tab_id,
                    timestamp=ts_int,
                    server_time=server_time_f,
                    chrome_identity={
                        "email": chrome_identity.get("email"),
                        "id": chrome_identity.get("id"),
                    },
                    bundles=bundles,
                )

                # Update pointer in-memory
                new_last_ts = ts_int
                new_last_server_time = max(
                    server_time_f,
                    ptr.last_server_time if ptr is not None else 0.0,
                )
                self.pointers[key] = Pointer(
                    last_timestamp=new_last_ts,
                    last_server_time=new_last_server_time,
                )

                yield gds_event

    def save(self) -> None:
        """
        Persist pointer state to disk.
        Call this after you've finished processing events.
        """
        save_pointers(self.pointer_path, self.pointers)
        


def read_google_docs_save_log(
    log_path: str,
    only_user: Optional[str] = None,
    only_doc: Optional[str] = None,
) -> Iterator[GoogleDocsSaveEvent]:
    """
    Simple helper to read *all* google_docs_save events from a log file
    (no pointer / incremental logic).

    You can optionally filter by user_id and/or doc_id.
    """
    with open(log_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            # Lines are often "<json>\\t<iso_ts>"
            json_part = line.split("\t", 1)[0]

            try:
                ev = json.loads(json_part)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue

            client = ev.get("client", {})

            # Only care about google_docs_save
            event_type = client.get("event") or ev.get("event")
            if event_type != "google_docs_save":
                continue

            # ---- extract identifiers ----
            auth = client.get("auth", {})
            user_id = auth.get("user_id") or auth.get("safe_user_id")
            if not user_id:
                continue

            if only_user and user_id != only_user:
                continue

            doc_id = (
                client.get("doc_id")
                or client.get("doc", {}).get("id")
                or ev.get("client", {})
                    .get("doc_id")  # sometimes nested again
            )
            if not doc_id:
                continue

            if only_doc and doc_id != only_doc:
                continue

            url = (
                client.get("url")
                or client.get("object", {}).get("url")
                or ev.get("url", "")
            )
            tab_id = parse_tab_from_url(url)

            chrome_identity = (
                client.get("chrome_identity")
                or ev.get("metadata", {}).get("chrome_identity")
                or {}
            )
            bundles = client.get("bundles", [])

            ts = client.get("timestamp") or ev.get("timestamp") or 0
            try:
                ts_int = int(ts)
            except (TypeError, ValueError):
                ts_int = 0

            server_time = ev.get("server", {}).get("time", 0.0)
            try:
                server_time_f = float(server_time)
            except (TypeError, ValueError):
                server_time_f = 0.0

            yield GoogleDocsSaveEvent(
                user_id=user_id,
                doc_id=doc_id,
                url=url,
                tab_id=tab_id,
                timestamp=ts_int,
                server_time=server_time_f,
                chrome_identity={
                    "email": chrome_identity.get("email"),
                    "id": chrome_identity.get("id"),
                },
                bundles=bundles,
            )


