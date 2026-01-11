# -*- coding: utf-8 -*-
"""
Created on Sun Dec  7 20:54:42 2025

@author: Saminur Islam
"""


from typing import Dict,Tuple,Iterable

import os
import pickle

from load_event import GoogleDocsSaveEvent
from command_state import DocState

STATE_PATH = "state/reconstruction_state.pkl"

class ReconstructionState:
    """
    Holds reconstructed state for all documents across all users.
    
    TAB MANAGEMENT AT THE DOCUMENT LEVEL:
    This class manages the reconstruction state for multiple documents, where each document
    can have multiple tabs. The docs dictionary uses (user_id, doc_id) as the key and stores
    a DocState object for each document.
    
    Key responsibilities:
    1. Track which documents are being reconstructed (via their user_id, doc_id pairs)
    2. Route events to the correct DocState for processing
    3. Persist state to disk for incremental reconstruction across sessions
    
    WORKFLOW:
    1. For each GoogleDocsSaveEvent, extract (user_id, doc_id)
    2. Get or create a DocState for that document
    3. Pass the event's bundles to DocState.apply_bundle() with the event's tab_id
    4. After all events are processed, call expand_dropdowns() on each document
    5. Save the entire ReconstructionState for the next session
    
    USAGE:
    - First run: load_reconstruction_state() creates empty ReconstructionState
    - Process events: reconstruct_from_events(events, state) populates it
    - Save: save_reconstruction_state(state) persists to disk
    - Next run: load_reconstruction_state() retrieves previous state, events update it incrementally
    """

    def __init__(self):
        self.docs: Dict[Tuple[str, str], DocState] = {}

    def get_or_create_doc(self, user_id: str, doc_id: str) -> DocState:
        key = (user_id, doc_id)
        if key not in self.docs:
            self.docs[key] = DocState(user_id, doc_id)
        return self.docs[key]
    
    

def load_reconstruction_state(path: str = STATE_PATH) -> "ReconstructionState":
    if not os.path.exists(path):
        return ReconstructionState()
    with open(path, "rb") as f:
        return pickle.load(f)


def save_reconstruction_state(state: "ReconstructionState",
                              path: str = STATE_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(state, f)


def reconstruct_from_events(
    events: Iterable["GoogleDocsSaveEvent"],
    state: "ReconstructionState" = None,
) -> "ReconstructionState":
    """
    Given a sequence of GoogleDocsSaveEvent objects, update all docs (for all users/doc_ids) in memory.

    If `state` is provided, we mutate it in-place; otherwise we create a new ReconstructionState.
    
    MULTI-TAB RECONSTRUCTION LOGIC:
    This function handles the core reconstruction workflow:
    
    1. SORT EVENTS: Events are sorted by (server_time, timestamp) to ensure correct order.
       This is critical for multi-tab documents where edits may arrive out of order.
    
    2. ROUTE TO TAB: Each event has:
       - tab_id: Extracted from the event's URL (e.g., 't.0', 't.4n9p3wa3df6o')
       - bundles: List of command bundles to apply
       Each bundle is applied to the specific tab via apply_bundle(bundle, tab_id, timestamp)
    
    3. COMMAND PROCESSING: Within each bundle, commands like:
       - Tab metadata (mkch, ucp, ac) update tab names and create/rename tabs
       - Text editing (is, ds, as) modify tab content
       - Element commands (ae, te) embed dropdowns, images, etc.
    
    4. TRACKING METADATA: Per-document metadata is updated:
       - last_server_time: Latest server timestamp seen
       - last_timestamp: Latest client timestamp seen  
       - last_url: Most recent URL (includes tab_id)
       - chrome_identity: Extension identity info
    
    Args:
        events: Iterable of GoogleDocsSaveEvent objects from WritingObserver log
        state: Existing ReconstructionState to update. If None, creates new one.
    
    Returns:
        The updated ReconstructionState with all events applied
    """
    if state is None:
        state = ReconstructionState()

    # Sort events chronologically to ensure the right order
    sorted_events = sorted(
        events,
        key=lambda e: (e.server_time, e.timestamp)
    )

    for ev in sorted_events:
        doc = state.get_or_create_doc(ev.user_id, ev.doc_id)

        # update per-doc meta
        doc.last_server_time = ev.server_time
        doc.last_timestamp = ev.timestamp
        doc.last_url = ev.url
        doc.chrome_identity = ev.chrome_identity

        for bundle in ev.bundles:
            # pass event timestamp for tab ordering
            doc.apply_bundle(bundle, ev.tab_id, event_timestamp=ev.timestamp)

    return state
