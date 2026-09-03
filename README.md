# K5KHK Quisk / antenna-switch customizations

## Background

I run Quisk in a "remote head" configuration, but also use it for a local WSJT-X setup. My remote head is a custom iOS app. To connect my different radios to my one antenna, I use an antenna switch in a reverse configuration, so it's more like a radio switch. This antenna/radio switch uses a Raspberry Pi Pico to control the relays and is connected via Node-RED dashboard. This custom Quisk radio configuration combines both the remote head and the antenna switch.  

Additions to Quisk (installed as a git checkout at `~/quisk/quisk`). Nothing here
modifies tracked Quisk source, so the Quisk checkout stays pristine and updates
are just `cd ~/quisk/quisk && git pull && make`.

## Contents

| File | Purpose |
|------|---------|
| `hermes_antenna_switch.py` | Quisk hardware file. Subclass of `ac2yd.remote_hermes`. Routes the Quisk antenna button through a Node-RED HTTP endpoint, restores the selected antenna on startup (live query → saved file → 0), non-blocking HTTP so a dead endpoint can't freeze the GUI. |
| `quisk_conf.py` | Copy of `~/.quisk_conf.py`. |
| `nodered/antenna_switch_flow.json` | Full export of the Node-RED "Antenna Switch" tab (serial link to the Pico switch, dashboard buttons, `POST /select_antenna`). |
| `nodered/antenna_status_subflow.json` | Add-on: `GET /antenna_status` → sends `q;` to the switch → returns `{"ant1":bool,"ant2":bool,"ant3":bool,"ok":bool}`. Used by `hermes_antenna_switch.py` on startup. |

`antenna_switch_flow.json` was exported **before** the status subflow was added — after
importing the subflow into Node-RED, re-export the tab over that file so it is a single
current snapshot.

## Install

```sh
# hardware file: point Quisk at this copy
#   Quisk Config → radio → Hardware file  →  ~/quisk-k5khk/hermes_antenna_switch.py
# or symlink it into the checkout:
ln -sf ~/quisk-k5khk/hermes_antenna_switch.py ~/quisk/quisk/k5khk/hermes_antenna_switch.py

# config
ln -sf ~/quisk-k5khk/quisk_conf.py ~/.quisk_conf.py

# Node-RED: import nodered/antenna_switch_flow.json and nodered/antenna_status_subflow.json
```

Python dependency: `requests`.

## Notes

- `hermes_antenna_switch.py` does `from ac2yd.remote_hermes import Hardware`. That
  resolves because `quisk.py`'s directory is on `sys.path` at runtime, so the file
  works from outside the Quisk tree.
- Optional Quisk config knob: `antenna_startup_index = N` in `~/.quisk_conf.py`
  forces a fixed antenna at every startup (0→ant1, 1→ant2, 2→ant3, 3→all off).
- `~/.quisk_antenna_index` is runtime state written on each button press — not tracked.
- Node-RED serial protocol to the Pico: `q;` query, `s1;`/`s2;`/`s3;` select, `s0;` all off.

## Updating Quisk

```sh
cd ~/quisk/quisk && git pull && make
```

Nothing in this repo is at risk; the checkout holds only a symlink (or nothing, if
Quisk points straight at `~/quisk-k5khk`).
