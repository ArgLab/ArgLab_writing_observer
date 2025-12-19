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
    Holds reconstructed state for all docs.
    Key: (user_id, doc_id)
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
    Given a sequence of GoogleDocsSaveEvent objects, update
    all docs (for all users/doc_ids) in memory.

    If `state` is provided, we mutate it in-place; otherwise
    we create a new ReconstructionState.
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
