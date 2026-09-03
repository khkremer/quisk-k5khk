# Antenna switch for K5KHK: routes the Quisk antenna button through a
# Node-RED HTTP endpoint instead of the Hermes-Lite I/O board.
#
#  * The HTTP request runs on a short-lived daemon thread with a hard
#    timeout, so a slow / hung / unreachable Node-RED endpoint can never
#    block Quisk's wxPython GUI thread (OnButtonAntenna runs on it).
#  * On startup (post_open) the button is initialised to the antenna the
#    switch actually has selected: first try a live query to Node-RED
#    (/antenna_status), else fall back to the last selection saved in
#    STATE_FILE, else index 0.  The button label is set to match and the
#    selection is (re)asserted on the physical switch.
#  * Set  antenna_startup_index = N  in the Quisk config file to force a
#    fixed antenna at every startup instead of querying / restoring.

from ac2yd.remote_hermes import Hardware as BaseHardware
import os
import json
import threading
import requests

NODERED_URL  = "http://nodered.local:1880/select_antenna"
STATUS_URL   = "http://nodered.local:1880/antenna_status"
HTTP_TIMEOUT = 2                                       # seconds - never block the GUI
STATE_FILE   = os.path.expanduser("~/.quisk_antenna_index")
BUTTON_ID    = "Ant 0"                                 # idName of the antenna cycle button (== its labels[0])


class Hardware(BaseHardware):
  def __init__(self, app, conf):
    BaseHardware.__init__(self, app, conf)

  # ---- Node-RED HTTP ------------------------------------------------------
  def _post_antenna(self, data):
    # Runs on a background thread: must not touch wx or Quisk state.
    try:
      r = requests.post(NODERED_URL, json=data, timeout=HTTP_TIMEOUT)
      r.raise_for_status()
      print("select_antenna OK: %s -> %s" % (data, r.text.strip()))
    except Exception as e:
      print("select_antenna FAILED %s: %s" % (data, e))

  def select_antenna(self, ant1=False, ant2=False, ant3=False):
    data = {"ant1": ant1, "ant2": ant2, "ant3": ant3}
    print("select_antenna request: %s" % data)
    threading.Thread(target=self._post_antenna, args=(data,), daemon=True).start()

  def _select_by_index(self, index):
    if index == 0:
      self.select_antenna(ant1=True)
    elif index == 1:
      self.select_antenna(ant2=True)
    elif index == 2:
      self.select_antenna(ant3=True)
    else:
      self.select_antenna()               # all off

  # ---- persistence -----------------------------------------------------
  def _save_index(self, index):
    try:
      with open(STATE_FILE, "w") as f:
        json.dump({"antenna_index": index}, f)
    except Exception as e:
      print("antenna state save failed: %s" % e)

  def _query_index(self):
    # Ask Node-RED what the antenna switch currently has selected.
    # Returns an index 0..3, or None if the query is unavailable / inconclusive.
    try:
      r = requests.get(STATUS_URL, timeout=HTTP_TIMEOUT)
      r.raise_for_status()
      d = r.json()
    except Exception as e:
      print("antenna status query failed: %s" % e)
      return None
    if not isinstance(d, dict) or d.get("ok") is False:
      print("antenna status query inconclusive: %s" % (d,))
      return None
    if d.get("ant1"):
      return 0
    if d.get("ant2"):
      return 1
    if d.get("ant3"):
      return 2
    return 3                                 # nothing selected -> "all off"

  def _load_index(self):
    forced = getattr(self.conf, "antenna_startup_index", None)
    if forced is not None:
      return int(forced)
    index = self._query_index()             # live state from the switch
    if index is not None:
      return index
    try:
      with open(STATE_FILE) as f:            # last selection Quisk made
        return int(json.load(f)["antenna_index"])
    except Exception:
      return 0

  # ---- Quisk hooks ---------------------------------------------------
  def post_open(self):
    # Called once after open() and after sound is started; the GUI
    # buttons exist by now.
    BaseHardware.post_open(self)
    index = self._load_index()
    btn = getattr(self.application, "idName2Button", {}).get(BUTTON_ID)
    if btn is not None and hasattr(btn, "SetIndex"):
      index = max(0, min(index, len(btn.labels) - 1))
      self.antenna_index = index
      # Sets the button label AND fires OnButtonAntenna -> Node-RED.
      btn.SetIndex(index, do_cmd=True)
    else:
      print("antenna button %r not found; pushing index %d directly" % (BUTTON_ID, index))
      self.antenna_index = index
      self._select_by_index(index)

  def OnButtonAntenna(self, event):
    btn = event.GetEventObject()
    self.antenna_index = btn.index
    print("Antenna index = %s" % self.antenna_index)
    self._save_index(self.antenna_index)
    self._select_by_index(self.antenna_index)
