# -*- coding: utf-8 -*-
"""
Created on Sun Dec  7 20:58:10 2025

@author: Saminur Islam
"""

from __future__ import print_function
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from command_state import DocState
from command_state import PLACEHOLDER
from typing import List
from load_event import IncrementalGoogleDocsSaveReader, read_google_docs_save_log

from ReconstructionState import (
    reconstruct_from_events,
    load_reconstruction_state,
    save_reconstruction_state,
)
# Dict, Tuple, Iterator, Optional, Any

SCOPES = ["https://www.googleapis.com/auth/documents"]

STATE_PATH = "state/reconstruction_state.pkl"
RECON_MAP_PATH = "state/reconstructed_doc_ids.json"

'''Add small helpers to store a mapping from original doc → reconstructed doc '''
import json

def load_recon_map(path: str = RECON_MAP_PATH) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_recon_map(mapping: dict, path: str = RECON_MAP_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)


def get_docs_service():
    """
    Returns an authenticated Docs API client.
    Requires credentials.json (OAuth client) in the working directory.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("docs", "v1", credentials=creds)


def build_full_text(doc_state: DocState) -> str:
    """
    Build the full plain-text representation for a doc_state, with one section per tab.
    
    MULTI-TAB RENDERING STRATEGY:
    Since the reconstructed Google Doc is a plain text document (not multi-tabbed),
    each tab from the original document is rendered as a separate section with:
    - Section header: The tab's name (e.g., "First Tab", "Overview")
    - Section separator: Line of equals signs (e.g., "==========")
    - Content: The reconstructed text from that tab
    - Spacing: Blank lines between sections for readability
    
    TAB ORDERING:
    Tabs are sorted by first_timestamp (when they first received edits), ensuring
    that the rendering reflects the logical creation order of tabs.
    
    ELEMENT RECONSTRUCTION:
    - Dropdowns: Rendered as readable text like "DROPDOWN: Priority – High"
    - Images: Shown as placeholders like "[s-blob-v1-IMAGE-...]" (binary data not in logs)
    - Placeholders: Text gaps filled with PLACEHOLDER (\x00) are removed
    
    OUTPUT FORMAT:
    Tab A
    =====
    
    Content of Tab A...
    
    Tab B
    =====
    
    Content of Tab B...
    
    Args:
        doc_state: DocState object with all tabs and their content
    
    Returns:
        Full plain text with all tabs as sections
    """
    parts: List[str] = []

    def _tab_sort_key(item):
        tab_id, tab_state = item
        return tab_state.first_timestamp or 0

    for tab_id, tab in sorted(doc_state.tabs.items(), key=_tab_sort_key):
        display_name = tab.name or tab_id

        parts.append(f"{display_name}\n")
        parts.append(f"{'=' * len(display_name)}\n\n")

        cleaned_text = tab.text.replace(PLACEHOLDER, "")
        parts.append(cleaned_text)
        parts.append("\n\n")

    return "".join(parts) if parts else ""


def update_reconstructed_doc(service, doc_id: str, doc_state: DocState) -> None:
    """
    Overwrite an existing reconstructed Google Doc with the latest
    text from doc_state.
    """
    full_text = build_full_text(doc_state)

    # Get current endIndex so we can delete (almost) everything
    doc = service.documents().get(documentId=doc_id).execute()
    body = doc.get("body", {})
    content = body.get("content", [])
    if not content:
        end_index = 1
    else:
        # endIndex of the last structural element (includes trailing newline)
        end_index = content[-1].get("endIndex", 1)

    requests = []

    # Delete everything except the final newline character.
    # Docs API doesn't allow us to delete the last newline in a segment.
    if end_index > 2:
        requests.append({
            "deleteContentRange": {
                "range": {
                    "startIndex": 1,
                    "endIndex": end_index - 1   # <-- key change
                }
            }
        })

    # Insert our new content at index 1
    if full_text:
        requests.append({
            "insertText": {
                "location": {"index": 1},
                "text": full_text,
            }
        })

    if requests:
        service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests},
        ).execute()



def create_reconstructed_doc(service, doc_state: DocState,
                             title_prefix: str = "Reconstructed") -> str:
    title = f"{title_prefix} - {doc_state.doc_id[:20]}"

    created = service.documents().create(body={"title": title}).execute()
    new_doc_id = created.get("documentId")

    full_text = build_full_text(doc_state)

    if full_text:
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": full_text,
                }
            }
        ]
        service.documents().batchUpdate(
            documentId=new_doc_id,
            body={"requests": requests},
        ).execute()

    return new_doc_id


# ---------- Example usage ----------

log_path = "logs/study_log_new.log" # first log! to see the cursor properly working chekc with study_log_new1.log after using the first one
pointer_path = "state/google_docs_save_pointers.json"

reader = IncrementalGoogleDocsSaveReader(pointer_path)

# 1) Load previous reconstruction state (if any)
recon_state = load_reconstruction_state(STATE_PATH)

# # 2) Get only NEW events since last run
# events = list(reader.iter_new_events(log_path))
all_events  = list(read_google_docs_save_log(log_path))

print(f"Total events in log: {len(all_events)}")
new_events = []
for ev in all_events:
    key = (ev.user_id, ev.doc_id)
    doc_state = recon_state.docs.get(key)

    # If we have already seen this doc and timestamp is not newer, skip
    if doc_state is not None and doc_state.last_timestamp is not None:
        if ev.timestamp <= doc_state.last_timestamp:
            continue

    new_events.append(ev)

print(f"New events to apply: {len(new_events)}")
# Nothing new? then nothing to do.
if not new_events:
    print("No new google_docs_save events found.")
else:
    # 3) Apply new events on top of existing state
    recon_state = reconstruct_from_events(new_events, recon_state)

    # 4) Persist updated pointers and state
    # reader.save()
    save_reconstruction_state(recon_state, STATE_PATH)

    # 5) Talk to Docs
    service = get_docs_service()
    recon_map = load_recon_map()

    for (user_id, doc_id), doc_state in recon_state.docs.items():
        print(f"Updating reconstruction for user={user_id}, original doc={doc_id}")

        # Make dropdowns readable
        doc_state.expand_dropdowns()

        # Look up existing reconstructed doc id (if any)
        recon_doc_id = recon_map.get(doc_id)

        if recon_doc_id is None:
            # First time -> create a new reconstructed doc
            recon_doc_id = create_reconstructed_doc(service, doc_state)
            recon_map[doc_id] = recon_doc_id
            print(f"  -> created new reconstructed doc: {recon_doc_id}")
        else:
            # Subsequent runs -> update the same reconstructed doc
            update_reconstructed_doc(service, recon_doc_id, doc_state)
            print(f"  -> updated existing reconstructed doc: {recon_doc_id}")

    save_recon_map(recon_map)
