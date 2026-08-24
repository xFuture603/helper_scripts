#!/usr/bin/env python3
"""
Send batched Telegram notifications for SABnzbd events.

SABnzbd calls this script once per event (type, title, message). Each call
appends the event to a spool file and detaches a flusher process; the flusher
waits for a quiet period and then sends ONE grouped message per event kind, so
a season that Sonarr adds in one burst produces a single "Started" message.

Completions are spread over hours, so a quiet period cannot group them. Instead
a finished episode is held back while siblings of the same series are still in
the queue. The last episode's own event finds the queue clear and releases the
whole batch as one "Finished" message.

Config:
    Set this script under Config -> Notifications -> Script and set Parameters
    to "<bot_token> <chat_id>". SABnzbd passes that field through to the script
    as SAB_NOTIFICATION_PARAMETERS.

    SABnzbd calls the script as "<event> <title> <message>". It re-runs itself
    with "--flush" for the detached flusher; there is no other entry point.
"""

import fcntl
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

# Batching knobs. SABnzbd cannot pass extra CLI flags, so these are read from
# the environment instead of argparse.
QUIET_SECONDS = int(os.environ.get("SABTG_QUIET", "45"))
MAX_WAIT_SECONDS = int(os.environ.get("SABTG_MAX_WAIT", "600"))

STATE_DIR = os.path.join(tempfile.gettempdir(), "sabnzbd-telegram")
SPOOL_FILE = os.path.join(STATE_DIR, "events.jsonl")
SPOOL_LOCK = os.path.join(STATE_DIR, "spool.lock")
FLUSH_LOCK = os.path.join(STATE_DIR, "flush.lock")

# Matches "Show.Name.S03E07..." or "Show Name 3x07..."
SERIES_PATTERN = re.compile(
    r"^(?P<show>.+?)[.\s_-]+"
    r"(?:s(?P<season>\d{1,2})e\d{1,3}|(?P<season_alt>\d{1,2})x\d{2})",
    re.IGNORECASE,
)

# SABnzbd notification types we act on, mapped to our own event kinds
EVENT_KINDS = {"download": "start", "complete": "done", "failed": "failed"}
KIND_LABELS = (
    ("start", "\U0001f4e5", "Started"),
    ("done", "✅", "Finished"),
    ("failed", "❌", "Failed"),
)

# Configure logging. The flusher runs detached with stdout closed, so stderr is
# the only channel whose output still reaches "docker logs sabnzbd".
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)


def get_series_key(name):
    """
    Build a grouping key for a release name.

    Args:
        name: Release name, e.g. "Breaking.Bad.S03E07.1080p".

    Returns:
        A (show, season) tuple such as ("breaking bad", 3), or None if the name
        does not look like an episode.
    """
    match = SERIES_PATTERN.match(name)
    if not match:
        return None

    show = re.sub(r"[._]+", " ", match.group("show")).strip().lower()
    # Releases of one show disagree about the year: "Mayans M C 2018" == "Mayans M C"
    show = re.sub(r"\s+(19|20)\d{2}$", "", show)
    return show, int(match.group("season") or match.group("season_alt"))


def summarize_downloads(names):
    """
    Build the message body for a batch: one line per season, plain names else.

    Args:
        names: Release names belonging to a single event kind.

    Returns:
        Message body as a string.
    """
    if len(names) == 1:
        return names[0]

    groups = {}
    for name in names:
        groups.setdefault(get_series_key(name), []).append(name)

    lines = []
    for key, members in groups.items():
        if key and len(members) > 1:
            show, season = key
            lines.append(f"{show.title()} — Season {season} ({len(members)} episodes)")
        else:
            lines.extend(members)  # a lone episode is still just a name

    if len(lines) == 1:
        return lines[0]

    listed = "\n".join("• " + line for line in lines[:10])
    return f"{len(names)} downloads\n{listed}" + ("\n• …" if len(lines) > 10 else "")


def get_queue():
    """Fetch SABnzbd's queue, or return {} when the API is unreachable."""
    api_url = os.environ.get("SAB_API_URL")
    api_key = os.environ.get("SAB_API_KEY")
    if not api_url or not api_key:
        return {}

    query = urllib.parse.urlencode(
        {"mode": "queue", "output": "json", "apikey": api_key}
    )
    try:
        with urllib.request.urlopen(f"{api_url}?{query}", timeout=10) as response:
            return json.load(response)["queue"]
    except (OSError, ValueError, KeyError) as err:
        # An unreadable queue must not hold notifications hostage
        logging.warning("Could not read the SABnzbd queue: %s", err)
        return {}


def get_pending_series(queue, finished=()):
    """
    Collect series still sitting in the queue.

    Args:
        queue: Queue dictionary as returned by get_queue().
        finished: Release names we just saw finish and should ignore.

    Returns:
        Set of (show, season) keys still downloading.
    """
    done = {name.removesuffix(".nzb") for name in finished}
    keys = {
        get_series_key(slot.get("filename", ""))
        for slot in queue.get("slots", [])
        if slot.get("filename", "").removesuffix(".nzb") not in done
    }
    return keys - {None}


def split_ready_events(events, still_downloading):
    """
    Split spooled events into sendable and held-back ones.

    Args:
        events: Spooled event dictionaries.
        still_downloading: Series keys that are still in the queue.

    Returns:
        A (ready, held) tuple; a finished episode waits while its siblings are
        still queued.
    """
    ready, held = [], []
    for event in events:
        held_back = (
            event["kind"] != "start"
            and get_series_key(event["name"]) in still_downloading
        )
        if held_back:
            held.append(event)
        else:
            ready.append(event)
    return ready, held


def send_telegram_message(text):
    """Send one plain-text message to the configured Telegram chat."""
    parameters = os.environ.get("SAB_NOTIFICATION_PARAMETERS", "").split()
    if len(parameters) != 2:
        logging.error(
            "Set Parameters in Config->Notifications to: <bot_token> <chat_id>"
        )
        sys.exit(1)

    token, chat_id = parameters
    # Plain text on purpose: release names are full of _ * [ ] that break Markdown
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data, timeout=15) as response:
        response.read()


def spool_events(events):
    """Append events to the spool, both newly arrived and held-back ones."""
    if not events:
        return

    os.makedirs(STATE_DIR, exist_ok=True)
    with open(SPOOL_LOCK, "w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with open(SPOOL_FILE, "a", encoding="utf-8") as spool:
            spool.writelines(json.dumps(event) + "\n" for event in events)


def drain_spool():
    """Read every spooled event and truncate the spool file."""
    with open(SPOOL_LOCK, "w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            with open(SPOOL_FILE, encoding="utf-8") as spool:
                events = [json.loads(line) for line in spool if line.strip()]
        except FileNotFoundError:
            events = []
        open(SPOOL_FILE, "w", encoding="utf-8").close()
    return events


def get_last_event_time():
    """Return the timestamp of the newest spooled event, or 0 if empty."""
    try:
        with open(SPOOL_FILE, encoding="utf-8") as spool:
            timestamps = (json.loads(line)["ts"] for line in spool if line.strip())
            return max(timestamps, default=0)
    except FileNotFoundError:
        return 0


def send_notifications(events, queue):
    """Send one grouped message per event kind, with queue status appended."""
    for kind, icon, verb in KIND_LABELS:
        names = [event["name"] for event in events if event["kind"] == kind]
        if not names:
            continue

        text = f"{icon} {verb}: {summarize_downloads(names)}"
        timeleft, sizeleft = queue.get("timeleft"), queue.get("sizeleft")
        if timeleft and timeleft != "0:00:00":
            text += f"\n⏳ Queue: {timeleft} left ({sizeleft})"
        elif kind != "start":
            text += "\n⏳ Queue empty"

        logging.info("Sending %s notification for %d download(s)", kind, len(names))
        send_telegram_message(text)


def flush_spool():
    """Wait for a quiet period, then send everything the queue has released."""
    lock = open(FLUSH_LOCK, "w", encoding="utf-8")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return  # a flusher is already waiting; our event joins its batch

    deadline = time.time() + MAX_WAIT_SECONDS
    while (
        time.time() < deadline and time.time() - get_last_event_time() < QUIET_SECONDS
    ):
        time.sleep(min(QUIET_SECONDS, 5))

    events = drain_spool()
    if not events:
        return

    queue = get_queue()
    finished = [event["name"] for event in events if event["kind"] != "start"]
    ready, held = split_ready_events(events, get_pending_series(queue, finished))
    spool_events(held)
    # ponytail: held events (and anything spooled while we send) wait for the next
    # event's flusher rather than a polling daemon. The last episode of a series
    # always produces one, so the common case releases on time.
    if ready:
        send_notifications(ready, queue)


def main():
    """Spool the SABnzbd event we were called with, or run the flusher."""
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    if event == "--flush":
        flush_spool()
        return

    kind = EVENT_KINDS.get(event)
    if not kind:
        return  # startup, warning, queue_done, ... not our business

    # SABnzbd passes (type, title, message); the release name is the first line
    # of the message
    message = sys.argv[3] if len(sys.argv) > 3 else ""
    name = next(iter(message.splitlines()), "").strip() or "unknown"
    spool_events([{"kind": kind, "name": name, "ts": time.time()}])

    # stderr is inherited on purpose: the flusher is detached, so this is the
    # only way its errors reach you (docker logs sabnzbd)
    subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "--flush"],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    main()
