# WritingObserver – Google Docs Reconstruction

This repository reconstructs a Google Doc’s content (including tabs-as-sections, tables-as-text, and smart-chip dropdowns-as-text) from WritingObserver logs containing `google_docs_save` events. It supports **incremental reconstruction** across multiple sessions by persisting a per-document reconstruction state and updating the same reconstructed Google Doc on subsequent runs.

**Known limitation:** Images cannot be reconstructed because the logs do not contain image bytes or a retrievable image URL. Only opaque internal identifiers (e.g., `s-blob-v1-IMAGE-...`) are logged.

---

## What this project does

1. Reads `google_docs_save` events from a WritingObserver log file.
2. Applies events in chronological order to reconstruct document state.
3. Converts special structures (e.g., dropdowns) into readable text.
4. Creates a new reconstructed Google Doc on first run.
5. Updates the same reconstructed Google Doc on later runs.
6. Persists reconstruction state and document ID mappings.

---

## Repository structure (recommended)

```
.
├── main_reconstruction.py          # Entry point
├── ReconstructionState.py          # Cross-document reconstruction state
├── command_state.py                # DocState / TabState and command application
├── load_event.py                   # Log parsing → GoogleDocsSaveEvent
├── requirements.txt
├── state/
│   ├── reconstruction_state.pkl
│   ├── reconstructed_doc_ids.json
│   └── google_docs_save_pointers.json
└── README.md
```

---

## Requirements

- Python 3.9 or newer
- A Google account with access to Google Docs API

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Google Docs API setup

### 1. Create OAuth credentials

1. Go to Google Cloud Console.
2. Create or select a project.
3. Enable **Google Docs API**.
4. Configure OAuth consent screen.
5. Create OAuth Client ID:
   - Type: **Desktop application**
6. Download the JSON file and rename it to:

```
credentials.json
```

Place it in the same directory as `main_reconstruction.py`.

> ❗ Do NOT commit `credentials.json` or `token.json` to GitHub.

---

### 2. Token generation

On first run, the script will open an authentication flow and generate:

```
token.json
```

This file stores your OAuth refresh token and will be reused on future runs.

---

## Running the reconstruction (local machine)

1. Update the log path in `main_reconstruction.py`:

```python
log_path = "/path/to/study_log_new1.log"
```

2. Run:

```bash
python main_reconstruction.py
```

The script will:
- Parse new events
- Update reconstruction state
- Create or update the reconstructed Google Doc

---

## Incremental reconstruction across sessions

The system supports multiple runs over time:

- Each document stores a `last_timestamp`
- Only events newer than the last run are applied
- The same reconstructed Google Doc is updated

To reset everything, delete the `state/` directory.

---

## Running on Google Colab

1. Mount Drive:

```python
from google.colab import drive
drive.mount('/content/drive')
```

2. Navigate to the code directory:

```python
%cd /content/drive/MyDrive/WritingObserverProject/ReconstructionCode/Code
```

3. Install dependencies:

```python
!pip install -r requirements.txt
```

4. Run reconstruction:

```python
!python main_reconstruction.py
```

### Authentication note for Colab

For Colab, console-based OAuth is recommended (`flow.run_console()`), because browser-based local server auth may fail in non-interactive runs.

---

## Output format

- Tabs are rendered as sections:

```
First Tab
=========
<content>
```

- Dropdowns are rendered as:

```
DROPDOWN: Configuration Test – Option 1
```

---

## Known limitations

- **Images:** Not reconstructable (no image source in logs)
- **Tables:** Reconstructed as linearized text, not true Docs tables

---

## Code review guide

Main execution flow:

1. `load_event.py` → parse logs
2. `ReconstructionState.py` → manage per-doc state
3. `command_state.py` → apply commands (insert/delete/dropdown)
4. `main_reconstruction.py` → orchestrate reconstruction + Docs API updates

---

## Security & privacy

Do NOT commit:
- `credentials.json`
- `token.json`
- log files
- `state/` directory

Add them to `.gitignore`.

---

## License

Add license information here if distributing publicly.
