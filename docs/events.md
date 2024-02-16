Event Format Notes
==================

Our event format is inspired in part by:

* IMS Caliper
* xAPI/Tincan
* edX tracking log events

None of these are _quite_ right for our application, but several are
close. They're pretty good standards!

Limitations of industry formats
-------------------------------

*Verbosity* Both Caliper and xAPI require a lot of cruft to be
appended to the events. For example, we have random ID GUIDs, URLs,
and all sorts of other redundancy on each event. Having things have
either *a little* bit of context (e.g. a header) or *a little*
rationale (e.g. IDs which point into a data store) is sometimes good,
but too much is a problem. With too much redundancy, events can get
massive:

* Our speed in handling large data scales with data size. Megabytes
  can be done instantly, gigabytes in minutes, and terabytes in
  hours. Cutting data sizes makes working with data easier.
* Repeating oneself can lead to inconsistent data. Data formats where
  data goes one place (or where redundancy is *intentional* and
  *engineered* for data correction) is more robust and less bug-prone.

*Envelopes* Caliper payloads are bundled in JSON envelopes. This is
a horrible format since:

* It results in a lot of additional parsing...
* ... of very large JSON objects
* If there's an error or incompatibility anywhere, you can easily lose
  a whole block of data
* You can't process events in realtime, for example, for formative
  feedback

Text files with one JSON event per line are more robust and more
scalable:

* They can be processed as a stream, without loading the whole file
* Individual corrupt events don't break the entire pipeline -- you can
  skip bad events
* They can be streamed over a network
* They can be preprocessed without decoding. For example, one can
  filter a file for a particular type of event, student ID, or
  otherwise with a plain text search. The primary goal of first-stage
  preprocessing is simply to quickly cut down data size, so it doesn't
  need to be reject 100% of irrelevant events.

*Details* In many cases, the details of a format are inappropriate for
a given purpose. There are event types which are in neither
Tincan/xAPI nor Caliper, and don't fit neatly into their
frameworks. For example:

* Formats specify timestamps with great precision, while coarse events
  (such as a student graduating) don't maintain that precision.
* In one of our clients, events are generated without a user
  identifier, which is then added by the server once the user is
  authenticated. For these events, validation fails.
* Related to the above, fields are sometimes repeated (e.g. client-side
  timestamp, server-side timestamp, and further timestamps as the event
  is processed by downstream systems). Much of this fits into security;
  downstream systems _should not_ trust data from upstream systems. For
  example, a student shouldn't be able to fake submitting a homework
  assignment earlier than they did, and a school should not be able to
  backdate a state exam response.

There are similar minor mismatches to e.g. group events, very frequent
events (such as typing), and other types of events not fully
anticipated when the standards were created.

I'd like to emphasize that in contrast to most industry formats, these
are quite good. They're not fundamentally broken.

How we'd like to leverage industry formats
------------------------------------------

Fortunately, we don't need 100% compatibility for pretty good
interoperability. Our experience is that event formats are almost
never interchangeable between systems; even with standardized formats,
the meaning changes based on the pedagogical design. This level of
compatibility is enough to give pretty interoperability, without being
constrained by details of these formats.

Our goal is to be compatible where convenient. Pieces we'd like to
borrow:

* Critically, the universe has converged on events as JSON lines. This
  already allows for common data pipelines.
* We can borrow vocabulary -- verbs, nouns, and similar.
* We can borrow field formats, where sensible

With this level of standardization, adapting to data differences is
typically already less work than adapting to differences in underlying
pedagogy.

Where we are
------------

We have not yet done more careful engineering of our event
format. Aside from a JSON-event-per-line, the above level of
compatibility is mostly aspirational.

## Google Docs Events
* [google_docs_save](#google_docs_save)
  * doc_id - ID of the document
  * url - URL of the document
  * bundles - A list containing one object (commands)
    * commands - Shows a list of commands (any/all the below commands can be shown)
        * [is](#insert-command) - Insert characters
        * [ds](#delete-command) - Delete characters
        * [as](#alter-command) - Alter characters
        * [iss](#suggest-add) - Suggest add
        * [msfd](#suggest-delete) - Suggest delete
        * [sas](#suggest-format) - Suggest format
        * [ras](#reject-suggest-format) - Reject suggest format
        * [usfd](#reject-suggest-delete) - Reject suggest delete
        * [ae](#image-insert-command) - Image add
        * [te](#image-index-command) - Image index
        * [de](#image-delete-command) - Image delete
        * [ue](#image-alter-command) - Image modify
        * [mlti](#multiple-commands) - Multiple commands
  * rev - The total number of edits made in the document
  * timestamp - The UNIX timestamp
  * event - Event type
  * event_type - Event type
  * source
  * version
  * ts - The UNIX timestamp
  * human_ts - Timestamp in human readable form
  * wa_source
        
* [keystroke](#keystroke)
* [mouseclick](#mouse-clicks)
  * mouseclick : all corresponding locations and details of the mouseclick
    * button
    * buttons
    * clientX
    * clientY
    * layerX
    * layerY
    * offsetX
    * offsetY
    * screenX
    * screenY
    * movementX
    * movementY
    * altKey, ctrlKey, metaKey, shiftKey
    * which
    * isTrusted
    * timeStamp
    * type
    * target.id
    * target.className
    * target.innerText
    * target.localName
    * target.parentNode.id
    * target.parentNode.className
    * target.parentNode.nodeType
    * target.parentNode.localName
  * frameindex
  * object: specifications about the document (present in all event types)
  * event : relists the event type
* [attention](#attention)
  * event_type
  * attention
  * frameindex
  * object
  * event
  * readyState
  * wa_source
  * source
  * version
  * ts
  * human_ts
  
### Data Format Examples
General json format of events

#### google_docs_save
The **commands** key of the json is the key that generally gets modified depending on the commands. In this case the **insert** event is shown.
```
{
  "doc_id": "1aV-wHLpITbSLEiTTOfX68W1GGnZKmiAWvlFeHR9JDcA",
  "url": "https://docs.google.com/document/d/1aV-wHLpITbSLEiTTOfX68W1GGnZKmiAWvlFeHR9JDcA/save?id=1aV-wHLpITbSLEiTTOfX68W1GGnZKmiAWvlFeHR9JDcA&sid=55ba02cf1e5d7984&vc=1&c=1&w=1&flr=0&smv=47&smb=%5B47%2C%20%5D&token=AC4w5Vi4lJSAlGE0hsYVEGl1h6ZykpEdkQ%3A1696548340555&includes_info_params=true&cros_files=false",
  "bundles": [
    {
      "commands": [
        {
          "ty": "is",
          "ibi": 65,
          "s": "oidj"
        }
      ],
      "sid": "55ba02cf1e5d7984",
      "reqId": 15
    }
  ],
  "rev": [
    "620"
  ],
  "timestamp": 1696696860521,
  "event": "google_docs_save",
  "event_type": "google_docs_save",
  "source": "org.mitros.writing_analytics",
  "version": "alpha",
  "ts": 1696696860523,
  "human_ts": "Sat Oct 07 2023 12:41:00 GMT-0400 (Eastern Daylight Time)",
  "wa_source": null
}
```
##### insert command
ty - Command type  
ibi - Index where the characters got inserted  
s - The characters that got inserted  
```
{
  "ty": "is",
  "ibi": 196,
  "s": "test"
}
```
##### delete command
ty - Command type  
si - Start index (where the deletion started)  
ei - End index (where the deletion ended)  
```
{
  "ty": "ds",
  "si": 196,
  "ei": 196
}
```
##### alter command
ty - Command type  
st - Shows which section was altered (possible values - paragraph, text, doco_anchor)  
si - Start index (where the alteration started)  
ei - End index (where the alteration ended)  
sm - The specific components that got altered. (Depends on 'st')  

* paragraph - This happens when a user aligns a paragraph (left, center, right, justify)
  ```
  {
    "ty": "as",
    "st": "paragraph",
    "si": 17,
    "ei": 17,
    "sm": {
        "ps_ls": 1,
        "ps_lslm": 1,
        "ps_ls_i": false,
        "ps_lslm_i": false
    }
  }
  ```

* text - This happens when a user modifies a text (change font, italics, bold, underline, etc..)
  ```
  {
    "ty": "as",
    "st": "text",
    "si": 17,
    "ei": 17,
    "sm": {
        "ts_fs_i": False,
        "ts_fs": 12,
    }
  }
  ```

* doco_anchor (suggestions/comments)  
  When a comment is inserted

  ```
  {
    "ty": "as",
    "st": "doco_anchor",
    "si": 67,
    "ei": 68,
    "sm": {
      "das_a": {
        "cv": {
          "op": "insert",
          "opIndex": 0,
          "opValue": "kix.wt2awnbw17lt"
        }
      }
    }
  }
  ```

  When a comment is deleted

  ```
  {
    "ty": "as",
    "st": "doco_anchor",
    "si": 102,
    "ei": 106,
    "sm": {
      "das_a": {
        "cv": {
          "op": "delete",
          "opIndex": 0
        }
      }
    }
  }
  ```
##### suggest add
Triggered when user suggests an addition
* When user adds characters  
  ty - Command type  
  sugid - The unique suggestion id  
  ibi - Index where suggestion is added  
  s - The suggestion that is added (String)  
  ```
  {
    "ty": "iss",
    "sugid": "suggest.s9ygmmpf1hwn",
    "ibi": 5,
    "s": "T"
  }
  ```
* When user deletes characters  
  ty - Command type  
  si - Start index (where the deletion started)  
  ei - End index (where the deletion ended)  
  ```
  {
    "ty": "dss",
    "si": 23,
    "ei": 23
  }
  ```
##### suggest delete
When users suggest a deletion  
ty - Command type  
sugid - Suggestion id  
si - Start index (where the deletion started)  
ei - End index (where the deletion ended)  
```
{
  "ty": "msfd",
  "sugid": "suggest.99icybo07j9s",
  "si": 41,
  "ei": 41
}
```
##### suggest format
Similar to [alter](#alter-command)  
sugid - Suggestion id  
```
{
  "ty": "sas",
  "st": "text",
  "si": 40,
  "ei": 42,
  "sm": {
    "ts_ff_i": true,
    "ts_bd_i": false,
    "ts_bd": true,
    "ts_tw": 400
  },
  "sugid": "suggest.otzprniiy6uz"
}
```
##### reject suggest format
When the user rejects a suggestion of type format
```
{
  "ty": "ras",
  "sugid": "suggest.ep2z2ofnvxs3",
  "si": 3,
  "ei": 4
}
```
##### reject suggest delete
When the user rejects a suggestion of type delete
```
{
  "ty": "usfd",
  "sugid": "suggest.ep2z2ofnvxs3",
  "si": 3,
  "ei": 4
}
```
##### image insert command
ty - Command type  
et  
id - Unique id of the image  
epm  
```
{
  "ty": "ae",
  "et": "inline",
  "id": "kix.k7hljq20dbwr",
  "epm": {
    "ee_eo": {
      "eo_ml": 9,
      "eo_mr": 9,
      "eo_mt": 9,
      "eo_mb": 9,
      "i_cid": "PLACEHOLDER_55ba02cf1e5d7984_0",
      "eo_type": 0,
      "i_wth": 468,
      "i_ht": 289,
      "eo_at": "Points scored",
      "eo_ad": "",
      "eo_lco": {
        "lc_ct": 1,
        "lc_sci": "1YHZ6nUWuIl3illzgk8BPpLQ5cchnZ2gX8DqpWKmOAsY",
        "lc_srk": "",
        "lc_oi": "1087145314",
        "lc_cs": "6GpqxB5Gn0QcyuNkPZd5cQ=="
      }
    }
  }
}
```
##### image index command
ty - Command type  
id - Unique id of the image  
spi - Index where the image got added  
```
{
  "ty": "te",
  "id": "kix.k7hljq20dbwr",
  "spi": 196
}
```

##### image delete command
ty - Command type  
id - Unique id of the image  
```
{
  "ty": "de",
  "id": "kix.k7hljq20dbwr",
}
```
##### image alter command
ty - Command type  
id - Unique id of the image  
epm  
```
{
  "ty": "ue",
  "id": "kix.k7hljq20dbwr",
  "epm": {
    "ee_eo": {
    "i_wth": 323.625,
    "i_ht": 199.67247596153848
    }
  }
}
```
##### multiple commands
ty - Command type  
mts - The list of commands (Can be any of the above 7 commands)  
```
{
  "ty": "mlti",
  "mts": [
    {
      "ty": "is",
      "ibi": 1,
      "s": "H"
    },
    {
      "ty": "as",
      "st": "text",
      "si": 1,
      "ei": 1,
      "sm": {
        "ts_bd_i": true,
        "ts_fs_i": false,
        "ts_fs": 12,
        "ts_ff_i": true,
        "ts_it_i": true,
        "ts_sc_i": true,
        "ts_st_i": true,
        "ts_tw": 400,
        "ts_un_i": true,
        "ts_va_i": true,
        "ts_bgc2_i": true,
        "ts_fgc2_i": true
      }
    }
  ]
}
```

  
#### keystroke
```
{
  "event_type": "keystroke",
  "keystroke": {
    "altKey": false,
    "charCode": 0,
    "code": "Enter",
    "ctrlKey": false,
    "isComposing": false,
    "isTrusted": true,
    "key": "Enter",
    "keyCode": 13,
    "location": 0,
    "metaKey": false,
    "repeat": true,
    "shiftKey": false,
    "target.className": "",
    "target.id": "",
    "target.nodeType": 1,
    "target.localName": "div",
    "timeStamp": 148555773.79999995,
    "type": "keydown",
    "which": 13
  },
  "frameindex": "0",
  "object": {
    "type": "http://schema.learning-observer.org/writing-observer/",
    "title": "Untitled document",
    "id": "1aV-wHLpITbSLEiTTOfX68W1GGnZKmiAWvlFeHR9JDcA",
    "url": "https://docs.google.com/document/d/1aV-wHLpITbSLEiTTOfX68W1GGnZKmiAWvlFeHR9JDcA/edit?pli=1"
    },
  "event": "keystroke",
  "readyState": "complete",
  "wa_source": null,
  "source": "org.mitros.writing_analytics",
  "version": "alpha",
```
#### Mouse-Clicks
```
{
  "event_type":"mouseclick"
  "mouseclick":
    {
    "button":0,
    "buttons":0,
    "clientX":95,
    "clientY":178,
    "layerX":160,
    "layerY":128,
    "offsetX":160,
    "offsetY":128,
    "screenX":779,
    "screenY":264,
    "movementX":0,
    "movementY":0,
    "altKey":false,
    "ctrlKey":false,
    "metaKey":false,
    "shiftKey":false,
    "which":1,
    "isTrusted":true,
    "timeStamp":4098834.1,
    "type":"mouseup",
    "target.id":"",
    "target.className":"kix-canvas-tile-content",
    "target.innerText":"",
    "target.nodeType":1,
    "target.localName":"canvas",
    "target.parentNode.id":"",
    "target.parentNode.className":"kix-page-paginated canvas-first-page",
    "target.parentNode.nodeType":1,
    "target.parentNode.localName":"div"
    },
  "frameindex":"10",
  "object":
    {
    "type":"http://schema.learning-observer.org/writing-observer/",
    "title":"hi","id":"1IwKSHtw5S4O_5ekG20XXpnKfTxRfXum6JGs1-uGYp3I",
    "url":"https://docs.google.com/documen/d/1IwKSHtw5S4O_5ekG20XXpnKfTxRfXum6JGs1-uGYp3I/edit"
    },
  "event":"mouseclick",
  "readyState":"complete",
  "wa_source":null,
  "source":"org.mitros.writing_analytics",
  "version":"alpha",
  "ts":1697561755869,
  "human_ts":"Tue Oct 17 2023 12:55:55 GMT-0400 (Eastern Daylight Time)
"}

```
#### attention
```
{
  "event_type": "attention",
  "attention": {
    "bubbles": true,
    "cancelable": false,
    "isTrusted": true,
    "timeStamp": 148851417.8,
    "relatedTarget.className": "kix-header-footer-bubble-menu-button docs-material goog-flat-menu-button goog-inline-block goog-flat-menu-button-hover goog-flat-menu-button-active",
    "relatedTarget.id": "kix-header-footer-bubble-menu-0",
    "target.className": "docs-texteventtarget-iframe docs-offscreen-z-index docs-texteventtarget-iframe-negative-top",
    "target.id": "",
    "target.nodeType": 1,
    "target.localName": "iframe",
    "target.parentNode.className": "docs-gm docsCommonGMDCDialog docs-material docs-grille-gm3",
    "target.parentNode.id": "",
    "target.parentNode.innerText": "Untitled document\nSaving\u2026\n\u00a0\n\u00a0\nShare\nFileEditViewInsertFormatToolsExtensionsHelp\n\u00a0Normal text\n\u00a0Arial\n\u00a0\n\u00a0\n\u00a0\n\u00a0\nEditing\n\u00a0\n9\n8\n7\n6\n5\n4\n3\n2\n1\n1\n2\n3\n4\n5\n6\n7\n8\nHeader\nDifferent first page\nOptions\n11\n10\n9\n8\n7\n6\n5\n4\n3\n2\n1\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\nTurn on screen reader support\nTo enable screen reader support, press Ctrl+Alt+Z To learn about keyboard shortcuts, press Ctrl+slash",
    "target.parentNode.nodeType": 1,
    "target.parentNode.localName": "body",
    "type": "focusout"
  },
  "frameindex": "1",
  "object": {
    "type": "http://schema.learning-observer.org/writing-observer/",
    "title": "Untitled document",
    "id": "1aV-wHLpITbSLEiTTOfX68W1GGnZKmiAWvlFeHR9JDcA",
    "url": "https://docs.google.com/document/d/1aV-wHLpITbSLEiTTOfX68W1GGnZKmiAWvlFeHR9JDcA/edit?pli=1"
  },
  "event": "attention",
  "readyState": "complete",
  "wa_source": null,
  "source": "org.mitros.writing_analytics",
  "version": "alpha",
  "ts": 1696697171229,
  "human_ts": "Sat Oct 07 2023 12:46:11 GMT-0400 (Eastern Daylight Time)"
}
```

## Tracking User offline edits in Google Docs

When a user goes offline and attempts to edit the Google Docs document, the changes made are saved locally on the device. Simultaneously, Google Docs tries to trigger a ``google_docs_save`` event during edits. Its important to note that the event being fired is a duplicate of the last ``google_docs_save`` just before the user went offline.
When the user comes back online, Google Docs triggers a new ``google_docs_save`` event containing all the changes made during the offline mode. 

So, to track when a user went offline, one can iterate through the logs and check where the  ``rev`` counter of the ``google_docs_save`` is repeated.

Sample implementation in python - 
```
from collections import Counter

events = dict() #json output of all logs
revisions = []
for event in events:
    if event['event'] == 'google_docs_save':
        revisions.append(event['rev'][0])

counts = Counter(revisions) # gets a counter of each revision

for rev,count in counts.items():
    if count > 1: # we only want revisions that are duplicates
        print(rev)
```
This prints out the revision numbers of the last save event before a user went offline. The ``rev + 1`` is going to be the revision that contains all the changes a user made during offline mode


## How comments are saved

When comments are modified, a sync event gets triggered which outputs data of type list.

## Google Autocorrect

The autocorrect feature of google docs either auto capitalizes the first letter of the word at the start of a sentence or autocorrects the spelling of a work.
When they auto capitalize a letter, there is no way of knowing if google docs intervened in the modification of the text, from the save events. 

However when they autocorrects the spelling of a word, a list of actions will be sent in the google_docs_save event

Example when i typed hllo, and google docs autocorrected it to hello
```[
  {
    "commands": [
      {
        "ty": "is",
        "ibi": 51,
        "s": " "
      },
      {
        "ty": "mlti",
        "mts": [
          {
            "ty": "ds",
            "si": 45,
            "ei": 50
          },
          {
            "ty": "is",
            "ibi": 45,
            "s": "testing"
          },
          {
            "ty": "as",
            "st": "comment",
            "si": 45,
            "ei": 51,
            "sm": {
              "cs_cids": {
                "cv": {
                  "op": "set",
                  "opValue": [
                    
                  ]
                }
              }
            }
          },
          {
            "ty": "as",
            "st": "doco_anchor",
            "si": 45,
            "ei": 51,
            "sm": {
              "das_a": {
                "cv": {
                  "op": "set",
                  "opValue": [
                    
                  ]
                }
              }
            }
          },
          {
            "ty": "as",
            "st": "ignore_spellcheck",
            "si": 45,
            "ei": 51,
            "sm": {
              "isc_osh": null,
              "isc_smer": true
            }
          },
          {
            "ty": "as",
            "st": "import_warnings",
            "si": 45,
            "ei": 51,
            "sm": {
              "iws_iwids": {
                "cv": {
                  "op": "set",
                  "opValue": [
                    
                  ]
                }
              }
            }
          },
          {
            "ty": "as",
            "st": "link",
            "si": 45,
            "ei": 51,
            "sm": {
              "lnks_link": null
            }
          },
          {
            "ty": "as",
            "st": "markup",
            "si": 45,
            "ei": 51,
            "sm": {
              "ms_id": {
                "cv": {
                  "op": "set",
                  "opValue": [
                    
                  ]
                }
              }
            }
          },
          {
            "ty": "as",
            "st": "named_range",
            "si": 45,
            "ei": 51,
            "sm": {
              "nrs_ei": {
                "cv": {
                  "op": "set",
                  "opValue": [
                    
                  ]
                }
              }
            }
          },
          {
            "ty": "as",
            "st": "suppress_feature",
            "si": 45,
            "ei": 51,
            "sm": {
              "sfs_sst": false
            }
          },
          {
            "ty": "as",
            "st": "text",
            "si": 45,
            "ei": 51,
            "sm": {
              "ts_bd_i": true,
              "ts_fs_i": true,
              "ts_ff_i": true,
              "ts_it_i": true,
              "ts_sc_i": true,
              "ts_st_i": true,
              "ts_tw": 400,
              "ts_un_i": true,
              "ts_va_i": true,
              "ts_bgc2_i": true,
              "ts_fgc2_i": true
            }
          }
        ]
      }
    ],
    "sid": "63d4de46fcf13d9c",
    "reqId": 227
  }
]```

  
