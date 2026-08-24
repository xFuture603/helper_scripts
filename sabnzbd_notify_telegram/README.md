# Batched Telegram Notifications For Sabnzbd

This script sends SABnzbd notifications to a Telegram chat, but batches them
first. Instead of one message per download it groups a burst of events into a
single message.

## Description

SABnzbd calls the script once per event. Each call appends the event to a spool
file and detaches a flusher process. The flusher waits for a quiet period
(no new events for a few seconds) and then sends ONE grouped message per event
kind.

Completions are spread over hours, so a quiet period alone cannot group them.
A finished episode is therefore held back while siblings of the same series are
still in the SABnzbd queue. The last episode of the season finds the queue clear
and releases the whole batch as a single "Finished" message.

Messages are sent as plain text on purpose, since release names are full of
`_ * [ ]` characters that break Telegram's Markdown parser.

## Use Cases

- Stop a season pack from spamming your Telegram chat with dozens of messages.
- Get one readable summary per series and season instead of per episode.
- Keep an eye on failed downloads without muting the whole chat.

## Requirements

- Python 3 (no external libraries required)
- A Telegram bot token and the chat ID you want to notify
- SABnzbd 3 or higher

## Setup

1. Place the script in SABnzbd's scripts directory and make it executable:

   ```sh
   chmod +x sabnzbd_notify_telegram.py
   ```

2. In SABnzbd go to `Config -> Notifications -> Notification Script`, select the
   script, and set `Parameters` to your bot token and chat ID, separated by a
   space:

   ```
   123456789:AAExampleBotToken abcdef 987654321
   ```

   SABnzbd passes this field to the script as `SAB_NOTIFICATION_PARAMETERS`.

3. Enable at least the `Added NZB`, `Job finished` and `Failed` notifications.

## Usage

There is nothing to run by hand. SABnzbd calls the script once per event and
passes three positional arguments:

```sh
sabnzbd_notify_telegram.py <event> <title> <message>
```

`event`: SABnzbd notification type (`download`, `complete`, `failed`, ...). All
other types are ignored.

`title`: Notification title. Unused.

`message`: Notification body. Its first line is used as the release name.

The script re-runs itself with `--flush` to start the detached flusher, which
waits for the quiet period and then sends the spooled batch.

## Environment Variables

SABnzbd cannot pass extra command line flags to a notification script, so the
tuning knobs are read from the environment.

`SABTG_QUIET`: Seconds of silence before a batch is sent (default: `45`).

`SABTG_MAX_WAIT`: Upper bound for how long a batch is held (default: `600`).

`SAB_API_URL` and `SAB_API_KEY`: Set by SABnzbd itself, nothing to configure.
The script uses them to see which series are still downloading and to append the
remaining queue time to each message. If the API is unreachable, nothing is held
back and every event is sent as soon as the quiet period passes.

## Behavior

Spool and lock files live in a `sabnzbd-telegram` directory inside the system
temp directory.

Only one flusher waits at a time. Events that arrive while it waits join its
batch.

If the SABnzbd API is unreachable, the queue is treated as empty rather than
holding notifications hostage.

Held-back events are released by the next event's flusher, not by a background
daemon, so the very last completion of a series is what sends the batch.

Errors are logged to stderr, which SABnzbd keeps in its own log
(`docker logs sabnzbd` for containerized setups).

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
