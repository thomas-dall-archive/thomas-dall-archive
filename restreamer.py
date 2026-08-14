import subprocess
import time
import logging
import sys
import json
import os
import re
import shutil
import threading
import requests # pyright: ignore[reportMissingModuleSource]
import xml.etree.ElementTree as ET
import socket # Added for native watchdog
from datetime import datetime
from typing import Optional, Dict, Any, List
import signal  # Needed for graceful shutdown handling

# ==============================================================================
# 🔌 EXTERNAL LIBRARY IMPORTS & FALLBACKS
# ==============================================================================

try:
    # Selenium is required for web automation (Rumble kill switch)
    from selenium import webdriver # pyright: ignore[reportMissingImports]
    from selenium.webdriver.common.by import By # pyright: ignore[reportMissingImports]
    from selenium.webdriver.chrome.options import Options # pyright: ignore[reportMissingImports]
    from selenium.webdriver.support.ui import WebDriverWait # pyright: ignore[reportMissingImports]
    from selenium.webdriver.support import expected_conditions as EC # pyright: ignore[reportMissingImports]
except ImportError:
    print("CRITICAL: Missing Selenium library. "
          "Please run 'pip install selenium' or update dependencies.")
    sys.exit(1)

# Local imports
try:
    from notify import send_discord_embed # pyright: ignore[reportMissingImports]
except ImportError as e:
    print(f"WARNING: Missing 'notify' library for Discord integration. {e}. "
          "Using silent fallback.")
    def send_discord_embed(*args, **kwargs):
        pass


class RestreamerService:
    """
    A robust, object-oriented service to monitor video signals (YouTube/Wix)
    and restream them via FFmpeg while monitoring external conditions.
    """

    # --- Class Attributes & Constants ---
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'restreamer-config.json')

    # --- Decaying fallback-polling schedule ---
    FALLBACK_BURST_INTERVAL_SECONDS = 60     # how often to check right after going idle
    FALLBACK_BURST_WINDOW_SECONDS = 300      # how long the "burst" period lasts (5 min)
    FALLBACK_IDLE_INTERVAL_SECONDS = 900     # how often to check once settled into long-term idle (15 min)

    # --- FFmpeg launch failure backoff ---
    QUICK_FAILURE_THRESHOLD_SECONDS = 30     # ffmpeg dying sooner than this is treated as a failure, not a normal stream end
    BASE_BACKOFF_SECONDS = 30
    MAX_BACKOFF_SECONDS = 600

    # --- FFmpeg health monitoring ---
    MONITOR_TICK_SECONDS = 10                # how often to wake and check ffmpeg's health (cheap, local checks only)
    RUMBLE_CHECK_EVERY_N_TICKS = 6           # ~60s cadence for the Rumble age check (this one's a network call)
    STALL_TIMEOUT_SECONDS = 60               # ffmpeg alive but no -progress update for this long => consider it stalled

    # --- Proactive CDN URL-expiry refresh ---
    EXPIRY_REFRESH_MARGIN_SECONDS = 300      # swap to a fresh URL this long before the known expiry, not after a 403

    # --- RTMP destination rejection handling ---
    RTMP_REJECTION_BACKOFF_SECONDS = 45
    RTMP_REJECTION_PHRASES = ["invalid stream key", "server error"]

    # --- Input-lag based stall detection ---
    INPUT_LAG_STALL_SECONDS = 90

    def __init__(self):
        """Initializes the service: loads config, sets up logging, validates."""
        # 1. Setup standard Python logging
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            stream=sys.stdout)
        self.logger = logging.getLogger(__name__)

        # Initialize all necessary operational state
        self.process: Optional[subprocess.Popen] = None
        self._shutdown_requested = False
        self._consecutive_quick_failures = 0

        # Decaying fallback-poll scheduling: service starts idle, so the
        # first fallback check is allowed immediately (burst mode).
        self._idle_since: float = time.time()
        self._next_fallback_check_at: float = 0.0

        # 2. Run config load, config validation, and dependency checks
        self._load_config()
        self._validate_config()
        self._validate_dependencies()

        # 3. Tell systemd startup is done. Required now that the unit is
        # Type=notify: systemd blocks `systemctl start` until it sees
        # READY=1 (or hits TimeoutStartSec and gives up). Sent here --
        # after config/dependency checks pass -- rather than at the very
        # top of __init__, so "ready" actually means "verified runnable",
        # not just "process exists."
        self.notify_ready()

    def _sd_notify(self, message: bytes) -> None:
        """Low-level helper: send a raw sd_notify-protocol message to
        systemd's notify socket, if one is configured. Shared by
        notify_ready() and notify_watchdog() so there's one place that
        handles the abstract-namespace socket quirk and failure logging."""
        notify_socket = os.getenv('NOTIFY_SOCKET')
        if notify_socket:
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
                # Handle abstract namespace (starts with @)
                if notify_socket.startswith('@'):
                    notify_socket = '\0' + notify_socket[1:]
                sock.connect(notify_socket)
                sock.sendall(message)
                sock.close()
            except Exception as e:
                self.logger.warning(f"Failed to send sd_notify message {message!r}: {e}")

    def notify_ready(self):
        """Tell systemd startup has finished. Only meaningful for
        Type=notify units -- harmless no-op otherwise (NOTIFY_SOCKET won't
        be set, so _sd_notify is a no-op)."""
        self._sd_notify(b'READY=1')

    def notify_watchdog(self):
        """Notify systemd that the service is alive without external dependencies."""
        self._sd_notify(b'WATCHDOG=1')

    def _load_config(self):
        """Loads the main configuration file and extracts variables."""
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
            self.logger.info("✅ Configuration loaded successfully.")

            # Load paths
            paths = self.config.get("paths", {})
            self.PYTHON_ENV = paths.get("python_env", "/usr/bin/python3")
            self.COOKIE_FILE = paths.get("cookie_file", "")
            self.RUMBLE_COOKIE_JSON = paths.get("rumble_cookies_json", "")

            # Load settings
            settings = self.config.get("settings", {})
            self.IDLE_POLL_INTERVAL_SECONDS = settings.get("check_interval", 30)
            self.MAX_STREAM_AGE_HOURS = settings.get("max_stream_age_hours", 23.5)

        except FileNotFoundError:
            self.logger.critical(f"CRITICAL: Config file '{self.CONFIG_FILE}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            self.logger.critical(f"CRITICAL: Config file '{self.CONFIG_FILE}' is invalid JSON.")
            sys.exit(1)

    def _validate_config(self):
        """Validates required config keys exist so missing config fails fast."""
        streams = self.config.get("streams", {})
        api = self.config.get("api", {})

        required_keys = ["rtmp_url", "stream_key"]
        missing = [k for k in required_keys if not streams.get(k)]
        if missing:
            self.logger.critical(
                f"CRITICAL: Config is missing required streams key(s): {', '.join(missing)}"
            )
            sys.exit(1)

        has_wix = bool(api.get("wix_base_url") and api.get("wix_secret"))
        has_youtube_fallback = bool(streams.get("youtube_url"))
        if not has_wix and not has_youtube_fallback:
            self.logger.critical(
                "CRITICAL: Config has neither Wix ('wix_base_url' + 'wix_secret') "
                "nor a fallback 'youtube_url' configured -- the service would "
                "never have a way to find a stream."
            )
            sys.exit(1)

    def _validate_dependencies(self):
        """Checks for critical external dependencies (yt-dlp, ffmpeg)."""
        try:
            subprocess.run(
                [self.PYTHON_ENV, "-m", "yt_dlp", "--version"],
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.critical(
                f"CRITICAL: 'yt-dlp' command failed or path is wrong. "
                f"Is {self.PYTHON_ENV} correct? Error: {e}"
            )
            sys.exit(1)

        if shutil.which("ffmpeg") is None:
            self.logger.critical(
                "CRITICAL: 'ffmpeg' was not found on PATH. "
                "Install it or fix PATH before running this service."
            )
            sys.exit(1)

    # ==========================================================================
    # 🧩 UTILITY METHODS (Core Logic Components)
    # ==========================================================================

    def _interruptible_sleep(self, seconds: float) -> None:
        """Sleeps in small increments so a shutdown request is noticed within
        ~1 second instead of waiting out a full long sleep.

        Also pings the systemd watchdog every iteration. This matters
        because notify_watchdog() was previously only called once per full
        monitor_and_restream() loop iteration -- at the top, before this
        sleep. A 30s idle sleep plus a slow Wix/yt-dlp round-trip on the
        same iteration could together exceed WatchdogSec=60s with no ping
        in between, causing systemd to silently kill a perfectly healthy
        process. Pinging on every ~1s tick here closes that gap for the
        sleep portion specifically.
        """
        deadline = time.time() + seconds
        while time.time() < deadline and not self._shutdown_requested:
            self.notify_watchdog()
            time.sleep(min(1, deadline - time.time()))

    def _parse_video_id_from_xml(self, xml_data: str) -> Optional[str]:
        """Parses the raw XML Atom feed payload to extract a video ID."""
        try:
            root = ET.fromstring(xml_data)
            for elem in root.iter():
                if 'videoId' in elem.tag:
                    return elem.text.strip() # pyright: ignore[reportOptionalMemberAccess]
        except Exception:
            pass

        # Fallback mechanism
        try:
            start_tag = '<yt:videoId>'
            end_tag = '</yt:videoId>'
            if start_tag in xml_data and end_tag in xml_data:
                start_index = xml_data.find(start_tag) + len(start_tag)
                end_index = xml_data.find(end_tag, start_index)
                return xml_data[start_index:end_index].strip()
        except Exception:
            pass

        return None

    def _get_direct_stream_url(self, youtube_url: str) -> Optional[str]:
        """Checks YouTube live status using yt-dlp and returns the direct URL."""
        self.logger.info(f"Checking live status for → {youtube_url}")
        cmd = [
            self.PYTHON_ENV, "-m", "yt_dlp",
            "--force-ipv4",
            "--cookies", self.COOKIE_FILE,
            "--dump-json",
            "--no-warnings",
            "--extractor-args", "youtube:player_client=web,android,ios,tv,mweb,android_vr",
            # Prefer a single combined (non-HLS) stream URL. YouTube's live
            # HLS manifest only carries a rolling ~30s window, which starves
            # ffmpeg's output muxer to Rumble a few seconds in. Fall back to
            # "best" (which may be HLS) only if nothing else is available.
            "-f", "best[protocol!*=m3u8]/best",
            youtube_url
        ]

        try:
            # Ping right before this call: its own timeout (60s) equals
            # WatchdogSec, so a single slow/retried yt-dlp invocation could
            # otherwise exhaust the entire watchdog window with no ping in
            # between -- this was the likely cause of the ~71s restart loop
            # seen before this fix (idle sleep + a slow Wix/yt-dlp round
            # trip on the same iteration, no ping until the next loop top).
            self.notify_watchdog()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                try:
                    video_metadata = json.loads(result.stdout)
                    is_live = (video_metadata.get('is_live') is True or
                               video_metadata.get('live_status') == 'is_live')

                    if is_live:
                        resolved_url = video_metadata.get('url')
                        protocol = video_metadata.get('protocol', '')
                        if resolved_url and 'm3u8' in protocol:
                            self.logger.warning(
                                "⚠️ Only an HLS manifest was available for this "
                                "broadcast (no progressive format). More prone "
                                "to short disconnects than usual."
                            )
                        self.logger.info("✅ ACTIVE LIVE STREAM DETECTED")
                        return resolved_url
                    else:
                        self.logger.debug("Not currently live (VOD/ended/premiere)")
                        return None

                except json.JSONDecodeError:
                    self.logger.error("Failed to parse yt-dlp JSON.")
                    return None

            stderr_lower = (result.stderr or "").lower()
            failure_phrases = [
                "not currently live",
                "live event has ended",
                "this video is not available"
            ]
            if any(phrase in stderr_lower for phrase in failure_phrases):
                self.logger.debug("Stream check determined: Not live or ended.")
                return None
            else:
                self.logger.error(f"yt-dlp failed (exit {result.returncode}): "
                                  f"{result.stderr.strip()}")
                return None

        except subprocess.TimeoutExpired:
            self.logger.warning("yt-dlp timed out.")
            return None
        except Exception as e:
            self.logger.exception(f"Stream check failed due to exception: {e}")
            return None

    def _extract_url_expiry(self, url: str) -> Optional[float]:
        """Pulls the CDN-signed expiration timestamp out of a resolved
        YouTube URL, if present. Handles both the query-param form
        (?expire=1234567890) used on direct videoplayback URLs and the
        path-segment form (/expire/1234567890/) used on manifest URLs.
        Returns None if no plausible expiry could be found."""
        match = re.search(r'expire[=/](\d{9,11})', url)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    def _mark_wix_processed(self, msg_id: str) -> bool:
        """Marks a Wix message as processed with retries."""
        api = self.config.get("api", {})
        for attempt in range(3):
            try:
                url = (f"{api.get('wix_base_url')}/markprocessed?"
                       f"secret={api.get('wix_secret')}")
                r = requests.post(url, json={"id": msg_id}, timeout=15)
                r.raise_for_status()
                self.logger.info(f"Wix message {msg_id} marked processed.")
                return True
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Wix ACK failed (attempt {attempt+1}/3) "
                                    f"for msg {msg_id}. Error: {e}")
            time.sleep(2)

        self.logger.error(f"Failed to mark msg {msg_id} processed after 3 attempts.")
        return False

    def _get_rumble_stream_age(self) -> Optional[float]:
        """Queries the Rumble API for stream uptime in seconds."""
        api = self.config.get("api", {})
        if not api.get("rumble_stats_url"):
            return None

        try:
            resp = requests.get(api["rumble_stats_url"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            livestreams = data.get("livestreams", [])

            if livestreams:
                active_stream = next((s for s in livestreams if s.get("is_live")), None)
                if active_stream and active_stream.get("is_live"):
                    created_on_str = active_stream.get("created_on")
                    if created_on_str:
                        try:
                            # Handle common ISO format variations, especially
                            # a trailing 'Z' (UTC) suffix.
                            created_time = datetime.fromisoformat(
                                created_on_str.replace('Z', '+00:00')
                            )
                            created_ts = created_time.timestamp()
                            rumble_now = data.get("now", time.time())
                            return rumble_now - created_ts
                        except ValueError:
                            self.logger.error("Could not parse datetime for Rumble age.")
                            return None

        except requests.exceptions.ConnectionError as e:
            self.logger.warning(f"Temporary DNS/Connection glitch (Rumble age check): {e}. Retrying next tick.")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP error checking Rumble age: {e}")
            return None
        except Exception as e:
            self.logger.exception(f"Unexpected error checking Rumble age: {e}")

        return None

    def _force_end_rumble_via_web(self):
        """Uses Selenium to automate 'End Livestream' button click on Rumble."""
        self.logger.info("🌐 Launching headless browser to force end Rumble livestream...")

        driver = None
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            driver = webdriver.Chrome(options=options)

            driver.get("https://rumble.com")
            time.sleep(2)

            if os.path.exists(self.RUMBLE_COOKIE_JSON):
                with open(self.RUMBLE_COOKIE_JSON, "r") as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        c = {k: cookie[k] for k in ['name', 'value', 'domain', 'path', 'secure'] if k in cookie}
                        if 'expiry' in cookie:
                            c['expiry'] = int(cookie['expiry'])
                        elif 'expirationDate' in cookie:
                            c['expiry'] = int(cookie['expirationDate'])
                        try:
                            driver.add_cookie(c)
                        except Exception:
                            continue
                driver.refresh()
                self.logger.info("🔑 Rumble cookies successfully injected.")
            else:
                self.logger.error("❌ Missing cookie file. Web termination aborted.")
                return

            driver.get("https://rumble.com/account/live-streaming")

            wait = WebDriverWait(driver, 15)
            end_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.action-button.action-end-live-stream"))
            )
            end_button.click()
            self.logger.info("🎯 Clicked 'End Livestream' button...")

            confirm_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.round-button.confirm-yes.bg-green"))
            )
            confirm_button.click()
            self.logger.info("✅ Clicked 'Yes' confirmation button!")

            time.sleep(5)
        except Exception as e:
            # Save a screenshot before quitting so we can see exactly what
            # the headless browser was looking at when it failed -- whether
            # that's a login screen (cookies expired/invalid), a blank page
            # (load failure), or the dashboard with a differently-named
            # button (Rumble changed their markup). Without this, the only
            # signal is a TimeoutException with no visual context.
            if driver:
                try:
                    screenshot_path = "/home/tda/rumble_selenium_failure.png"
                    driver.save_screenshot(screenshot_path)
                    self.logger.error(
                        f"📸 Screenshot saved to {screenshot_path} -- "
                        f"check this to see what the page looked like when "
                        f"the button click failed."
                    )
                except Exception as screenshot_err:
                    self.logger.warning(
                        f"Could not save failure screenshot: {screenshot_err}"
                    )
            self.logger.exception(f"❌ Failed to invoke web button click: {e}")
        finally:
            if driver:
                driver.quit()
                self.logger.info("🌐 Headless browser session finalized and closed.")


    @staticmethod
    def _watch_ffmpeg_progress(process: subprocess.Popen, state: Dict[str, Any]) -> None:
        """Reads ffmpeg's `-progress` stream and records the last time
        out_time_ms actually *advanced*. Runs in a background thread for the
        lifetime of the ffmpeg process so the main loop can detect a stalled
        stream (alive but not moving data) rather than only an outright
        crash.

        Deliberately does NOT bump last_update just because a line arrived.
        When ffmpeg is internally looping on its own -reconnect logic against
        a dead HLS source, it can keep emitting -progress lines (sometimes
        with a repeated/stale out_time_ms) without any real data moving. If
        last_update tracked "a line arrived" instead of "out_time_ms grew",
        that keeps resetting the stall clock and the 60s stall timeout never
        fires -- which is exactly what let a dead source run ~6 minutes
        before ffmpeg's own output side finally broke the pipe.
        """
        if process.stdout is None:
            return
        try:
            for line in process.stdout:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key == "out_time_ms":
                    try:
                        new_val = int(value)
                    except ValueError:
                        # Sometimes ffmpeg emits "N/A" here; ignore, don't
                        # treat it as progress.
                        continue

                    prev_val = state.get("out_time_ms")
                    state["out_time_ms"] = new_val

                    # Only this counts as real, observed progress.
                    if prev_val is None or new_val > prev_val:
                        state["last_update"] = time.time()
        except Exception:
            # If the pipe closes/errors, the main loop's poll()/stall checks
            # will take over -- nothing more to do here.
            pass

    def _watch_ffmpeg_stderr(self, process: subprocess.Popen, state: Dict[str, Any]) -> None:
        """Reads ffmpeg's stderr in the background, mirrors each line into
        the service log (since stderr is now piped instead of inherited, it
        would otherwise vanish from the journal), flags explicit RTMP
        destination rejections (e.g. "Invalid stream key") so the main loop
        can apply a dedicated cooldown instead of a generic quick-failure
        backoff, and watches for ffmpeg's own "lag of Ns" input-stall
        warnings so a genuinely dead source gets caught quickly instead of
        waiting on the (less reliable, in this case) -progress-based stall
        check."""
        if process.stderr is None:
            return
        lag_pattern = re.compile(r'lag of ([\d.]+)s')
        try:
            for line in process.stderr:
                line = line.rstrip()
                if not line:
                    continue
                self.logger.warning(f"[ffmpeg] {line}")
                line_lower = line.lower()

                if any(phrase in line_lower for phrase in self.RTMP_REJECTION_PHRASES):
                    state["rtmp_rejected"] = True
                    state["rtmp_rejection_line"] = line

                lag_match = lag_pattern.search(line)
                if lag_match:
                    try:
                        lag_seconds = float(lag_match.group(1))
                    except ValueError:
                        lag_seconds = None
                    if lag_seconds is not None and lag_seconds >= self.INPUT_LAG_STALL_SECONDS:
                        state["input_lag_stalled"] = True
                        state["input_lag_seconds"] = lag_seconds
        except Exception:
            pass

    # ==========================================================================
    # 📡 ORCHESTRATION METHODS (The Main Control Flow)
    # ==========================================================================

    def _check_for_stream_signals(
        self, current_wix_msg_id: Optional[str]
    ) -> "tuple[Optional[str], Optional[str], Optional[str]]":
        """Handles the Wix and Fallback signal detection logic.

        Returns (stream_url, source_url, wix_msg_id). `source_url` is the
        YouTube watch URL that `stream_url` was resolved from -- kept around
        so a proactive CDN-expiry refresh can re-resolve a fresh URL for the
        same broadcast later without re-running signal discovery from
        scratch.
        """
        stream_url = None
        source_url = None

        api = self.config.get("api", {})
        streams = self.config.get("streams", {})

        # --- WIX PHASE (always checked first, every cycle, no YouTube cost) ---
        if api.get("wix_base_url") and api.get("wix_secret"):
            try:
                self.logger.info("[STATUS] Checking Wix message queue...")
                # Ping right before a blocking network call (up to 15s) --
                # this runs before the idle sleep, so a slow/retried request
                # here couldn't otherwise get a watchdog ping until the next
                # full loop iteration.
                self.notify_watchdog()
                url = (f"{api['wix_base_url']}/bunkermessages?"
                       f"secret={api['wix_secret']}")
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()

                messages: List[Dict] = resp.json().get("messages", [])
                if messages:
                    self.logger.info(f"Found {len(messages)} pending Wix messages.")
                    for msg in messages[:6]:
                        msg_id = msg.get("_id")
                        video_id = self._parse_video_id_from_xml(msg.get("payload", ""))
                        if not video_id:
                            self._mark_wix_processed(msg_id) # pyright: ignore[reportArgumentType]
                            continue

                        self.logger.info(f"Wix Hit → Video ID: {video_id}")
                        send_discord_embed("live", "📬 New Stream Signal (Wix)",
                                           f"Video ID: `{video_id}`", 0x3498db)

                        target_url = f"https://www.youtube.com/watch?v={video_id}"
                        candidate = self._get_direct_stream_url(target_url)

                        if candidate:
                            return candidate, target_url, msg_id
                        else:
                            self._mark_wix_processed(msg_id) # type: ignore

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Wix query failed due to HTTP/Network error: {e}")
            except Exception as e:
                self.logger.exception(f"Wix processing encountered a failure: {e}")

        # --- FALLBACK PHASE (decaying-interval direct YouTube polling) ---
        if stream_url is None and streams.get("youtube_url"):
            now = time.time()
            if now >= self._next_fallback_check_at:
                self.logger.info("[STATUS] Falling back to direct YouTube URL polling.")
                candidate = self._get_direct_stream_url(streams["youtube_url"])

                idle_elapsed = now - self._idle_since
                interval = (self.FALLBACK_BURST_INTERVAL_SECONDS
                            if idle_elapsed < self.FALLBACK_BURST_WINDOW_SECONDS
                            else self.FALLBACK_IDLE_INTERVAL_SECONDS)
                self._next_fallback_check_at = now + interval

                if candidate:
                    self.logger.info("✅ Fallback live stream found!")
                    send_discord_embed("live", "⚡ Fallback Recovery",
                                       "Direct polling found live stream", 0x2ecc71)
                    stream_url = candidate
                    source_url = streams["youtube_url"]
            else:
                remaining = self._next_fallback_check_at - now
                self.logger.debug(f"Fallback polling waiting {remaining:.0f}s before next check.")

        return stream_url, source_url, current_wix_msg_id

    def _run_ffmpeg_stream(
        self, stream_url: str, source_url: Optional[str], wix_msg_id: Optional[str]
    ) -> "tuple[float, Optional[str], bool]":
        """Manages the FFmpeg process lifecycle and monitoring loop.

        Returns (elapsed_seconds, refreshed_url, rtmp_rejected). rtmp_rejected
        is True only when ffmpeg's stderr showed an explicit destination-side
        rejection (e.g. "Invalid stream key") -- the caller uses this to
        apply a dedicated cooldown instead of the normal exponential backoff.
        """
        self.logger.info("🔄 Starting FFmpeg restream to target...")

        streams = self.config.get("streams", {})
        api = self.config.get("api", {})

        rtmp_url = streams.get('rtmp_url')
        stream_key = streams.get('stream_key', 'rumble-channel-123456')
        if rtmp_url and not rtmp_url.endswith('/'):
            full_rtmp_target = f"{rtmp_url}/{stream_key}"
        else:
            full_rtmp_target = f"{rtmp_url}{stream_key}"

        ffmpeg_cmd = [
            "ffmpeg", "-hide_banner",
            "-loglevel", "warning", "-nostats",
            # Reconnect/resilience flags carried over from the old script.
            # These let ffmpeg's input layer ride through brief HLS segment
            # stalls / network blips instead of dying outright -- without
            # these the same transient hiccups that always existed turn
            # into a hard "Broken pipe" / "Connection reset by peer" on the
            # output muxer a few seconds in.
            "-timeout", "15000000",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "3",
            "-reconnect_on_network_error", "1",
            "-fflags", "+discardcorrupt",
            "-i", stream_url,
            "-c:v", "copy", "-c:a", "copy",
            "-f", "flv", "-flvflags", "no_duration_filesize",
            "-progress", "pipe:1",
            full_rtmp_target
        ]

        start_time = time.time()
        try:
            self.process = subprocess.Popen(
                ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1
            )
        except (FileNotFoundError, PermissionError) as e:
            self.logger.critical(f"CRITICAL: Could not launch ffmpeg ({e}).")
            sys.exit(1)

        progress_state: Dict[str, Any] = {"last_update": time.time(), "out_time_ms": None}
        progress_thread = threading.Thread(
            target=self._watch_ffmpeg_progress,
            args=(self.process, progress_state),
            daemon=True
        )
        progress_thread.start()

        stderr_state: Dict[str, Any] = {
            "rtmp_rejected": False,
            "rtmp_rejection_line": None,
            "input_lag_stalled": False,
            "input_lag_seconds": None,
        }
        stderr_thread = threading.Thread(
            target=self._watch_ffmpeg_stderr,
            args=(self.process, stderr_state),
            daemon=True
        )
        stderr_thread.start()

        expiry_ts = self._extract_url_expiry(stream_url) if source_url else None
        refresh_at: Optional[float] = None
        if expiry_ts:
            refresh_at = expiry_ts - self.EXPIRY_REFRESH_MARGIN_SECONDS
            self.logger.info(
                f"🕐 This stream URL expires at "
                f"{datetime.fromtimestamp(expiry_ts).strftime('%Y-%m-%d %H:%M:%S')}; "
                f"will proactively refresh at "
                f"{datetime.fromtimestamp(refresh_at).strftime('%Y-%m-%d %H:%M:%S')}."
            )
        else:
            self.logger.debug("Could not find an expiry timestamp in this URL; "
                              "relying on crash/stall recovery only for this run.")

        stall_reason: Optional[str] = None
        refreshed_url: Optional[str] = None
        # Explicit flag: only set True when the 23.5h Rumble stream-age limit
        # is actually hit. This -- and *only* this -- should gate the
        # Selenium "End Livestream" call below. It must never be inferred
        # from the CDN URL-expiry refresh succeeding/failing, since those
        # are two unrelated timers (~6hr HLS URL expiry vs ~24hr Rumble VOD
        # cutoff) that happen to share the same monitoring loop.
        max_age_hit = False
        tick = 0

        try:
            while self.process.poll() is None:
                # 🔔 KICK THE WATCHDOG HERE TOO
                self.notify_watchdog()

                self._interruptible_sleep(self.MONITOR_TICK_SECONDS)
                tick += 1

                if self._shutdown_requested:
                    self.logger.info("Shutdown requested; stopping FFmpeg.")
                    break

                if refresh_at and time.time() >= refresh_at and source_url:
                    self.logger.info(
                        "🔄 Approaching CDN URL expiry; resolving a fresh URL "
                        "before it cuts us off..."
                    )
                    candidate = self._get_direct_stream_url(source_url)
                    if candidate:
                        self.logger.info("✅ Fresh URL acquired. Swapping over.")
                        refreshed_url = candidate
                        break
                    else:
                        self.logger.warning(
                            "Could not resolve a fresh URL yet (broadcast may have "
                            "briefly dropped); keeping the current connection and "
                            "trying again shortly."
                        )
                        refresh_at = time.time() + (self.MONITOR_TICK_SECONDS * 3)

                seconds_since_progress = time.time() - progress_state["last_update"]
                if seconds_since_progress > self.STALL_TIMEOUT_SECONDS:
                    stall_reason = f"No FFmpeg progress for {seconds_since_progress:.0f}s"
                    self.logger.warning(f"⚠️ {stall_reason}; treating stream as stalled.")
                    break

                if stderr_state["input_lag_stalled"]:
                    stall_reason = (
                        f"FFmpeg reported an input lag of "
                        f"{stderr_state['input_lag_seconds']:.0f}s (source likely ended)"
                    )
                    self.logger.warning(f"⚠️ {stall_reason}; treating stream as stalled.")
                    break

                if (api.get("rumble_stats_url")
                        and tick % self.RUMBLE_CHECK_EVERY_N_TICKS == 0):
                    stream_age = self._get_rumble_stream_age()
                    if stream_age is not None:
                        age_hours = stream_age / 3600
                        self.logger.info(f"📊 Current Rumble stream age: {age_hours:.2f} hrs")

                        if age_hours >= self.MAX_STREAM_AGE_HOURS:
                            self.logger.warning(f"⏰ Stream hit max limit "
                                                f"({self.MAX_STREAM_AGE_HOURS}h). Terminating...")
                            max_age_hit = True
                            self.process.terminate()
                            break

        except Exception as e:
            self.logger.exception(f"Monitoring loop error detected: {e}")
        finally:
            if self.process is not None and self.process.poll() is None:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.logger.warning("FFmpeg hung. Sending KILL signal.")
                    self.process.kill()

            # Only press Rumble's "End Livestream" button when we actually
            # hit the 23.5h max-age limit. A failed/incomplete CDN-expiry
            # refresh, a stall, a shutdown request, or any other exit path
            # must NOT end the Rumble livestream -- doing so creates a brand
            # new Rumble stream instead of letting ffmpeg simply reconnect
            # to the same one, which is the exact bug being fixed here.
            if max_age_hit:
                self._force_end_rumble_via_web()

            if not refreshed_url and wix_msg_id:
                self._mark_wix_processed(wix_msg_id)

        elapsed = time.time() - start_time
        if refreshed_url:
            self.logger.info(f"Proactively refreshed stream URL after {elapsed:.0f}s.")
        elif stderr_state["rtmp_rejected"]:
            self.logger.warning(
                f"Stream ended after {elapsed:.0f}s due to an explicit RTMP "
                f"destination rejection: {stderr_state['rtmp_rejection_line']!r}"
            )
        elif stall_reason:
            self.logger.warning(f"Stream ended due to stall detection after {elapsed:.0f}s.")
        else:
            self.logger.info(f"FFmpeg stream ended after {elapsed:.0f}s.")

        return elapsed, refreshed_url, stderr_state["rtmp_rejected"]

    def monitor_and_restream(self) -> None:
        """Main control loop. Runs until signaled to stop."""
        self.logger.info("🚀 Starting Restreamer Service Main Loop.")

        pending_stream_url: Optional[str] = None
        pending_source_url: Optional[str] = None
        pending_wix_id: Optional[str] = None

        while not self._shutdown_requested:
            # 🔔 KICK THE WATCHDOG
            self.notify_watchdog()
            
            try:
                if pending_stream_url:
                    stream_url = pending_stream_url
                    source_url = pending_source_url
                    last_wix_id = pending_wix_id
                    pending_stream_url = None
                    pending_source_url = None
                    pending_wix_id = None
                else:
                    stream_url, source_url, last_wix_id = self._check_for_stream_signals(None)

                if stream_url:
                    self.logger.info("Stream detected. Starting FFmpeg process.")
                    elapsed, refreshed_url, rtmp_rejected = self._run_ffmpeg_stream(
                        stream_url, source_url, last_wix_id
                    )

                    if refreshed_url:
                        self.logger.info("🔁 Continuing stream with refreshed URL.")
                        pending_stream_url = refreshed_url
                        pending_source_url = source_url
                        pending_wix_id = last_wix_id
                        self._consecutive_quick_failures = 0
                        continue

                    self._idle_since = time.time()
                    self._next_fallback_check_at = 0.0

                    if rtmp_rejected:
                        # Rumble explicitly rejected the connection (e.g.
                        # "Invalid stream key"), most likely because the
                        # backend hadn't released the key from a just-ended
                        # broadcast yet. Don't count this against the normal
                        # quick-failure streak -- give it a dedicated,
                        # fixed cooldown instead so we don't slam into the
                        # same not-yet-released window again.
                        self.logger.warning(
                            f"RTMP destination rejected the connection after "
                            f"{elapsed:.0f}s. Cooling down "
                            f"{self.RTMP_REJECTION_BACKOFF_SECONDS}s before retrying "
                            f"to give Rumble time to release the stream key."
                        )
                        self._interruptible_sleep(self.RTMP_REJECTION_BACKOFF_SECONDS)
                    elif elapsed < self.QUICK_FAILURE_THRESHOLD_SECONDS:
                        self._consecutive_quick_failures += 1
                        backoff = min(
                            self.MAX_BACKOFF_SECONDS,
                            self.BASE_BACKOFF_SECONDS * (2 ** (self._consecutive_quick_failures - 1))
                        )
                        self.logger.warning(
                            f"FFmpeg exited after only {elapsed:.0f}s "
                            f"({self._consecutive_quick_failures} quick failure(s) in a row). "
                            f"Backing off {backoff:.0f}s before retrying."
                        )
                        self._interruptible_sleep(backoff)
                    else:
                        self._consecutive_quick_failures = 0
                else:
                    self.logger.info("No active stream signal found. Waiting before re-polling...")
                    self._interruptible_sleep(self.IDLE_POLL_INTERVAL_SECONDS)

            except Exception as e:
                self.logger.critical(f"Unrecoverable loop error: {type(e).__name__} - {e}")
                raise

        self.logger.info("Monitor loop exited gracefully.")


# ==============================================================================
# 🚀 MAIN EXECUTION BLOCK (Entry Point)
# ==============================================================================

restreamer: Optional[RestreamerService] = None

def signal_handler(sig, frame) -> None:
    print("\n[SIGNAL RECEIVED] Initiating graceful shutdown...")
    if restreamer is not None:
        restreamer._shutdown_requested = True
        if restreamer.process and restreamer.process.poll() is None:
            print("Stopping FFmpeg so the main loop can clean up...")
            restreamer.process.terminate()

def main() -> None:
    global restreamer

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        restreamer = RestreamerService()
        restreamer.monitor_and_restream()
    except Exception as e:
        print(f"\n[FINAL FATAL EXCEPTION] Service failed to run: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
