import subprocess
import time
import logging
import sys
import json
import os
import re
import shutil
import threading
import requests  # pyright: ignore[reportMissingModuleSource]
import socket    # Added for native watchdog
import asyncio   # Needed to drive twikit's async client from sync code
from datetime import datetime
from typing import Optional, Dict, Any, List
import signal    # Needed for graceful shutdown handling

# ==============================================================================
# 🔌 EXTERNAL LIBRARY IMPORTS & FALLBACKS
# ==============================================================================

try:
    # Selenium is required for the Rumble kill switch (force-ending the
    # output broadcast once it hits the max age limit).
    from selenium import webdriver  # pyright: ignore[reportMissingImports]
    from selenium.webdriver.common.by import By  # pyright: ignore[reportMissingImports]
    from selenium.webdriver.chrome.options import Options  # pyright: ignore[reportMissingImports]
    from selenium.webdriver.support.ui import WebDriverWait  # pyright: ignore[reportMissingImports]
    from selenium.webdriver.support import expected_conditions as EC  # pyright: ignore[reportMissingImports]
except ImportError:
    print("CRITICAL: Missing Selenium library. Please run 'pip install selenium' or update dependencies.")
    sys.exit(1)

# Local imports
try:
    from notify import send_discord_embed  # pyright: ignore[reportMissingImports]
except ImportError as e:
    print(f"WARNING: Missing 'notify' library for Discord integration. {e}. Using silent fallback.")
    def send_discord_embed(*args, **kwargs):
        pass


class XRestreamerService:
    """
    A robust, object-oriented service to monitor video signals from X (Twitter)
    and restream them via FFmpeg.

    Broadcast discovery is performed exclusively via twikit (cookie-based scrape)
    of the target account's recent posts. The official X API is not used.
    """

    # --- Class Attributes & Constants ---
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'restreamer-config.json')

    # --- Decaying fallback-polling schedule ---
    FALLBACK_BURST_INTERVAL_SECONDS = 60     # how often to check right after going idle
    FALLBACK_BURST_WINDOW_SECONDS = 300      # how long the "burst" period lasts (5 min)
    FALLBACK_IDLE_INTERVAL_SECONDS = 900     # how often to check once settled into long-term idle (15 min)

    # --- FFmpeg launch failure backoff ---
    QUICK_FAILURE_THRESHOLD_SECONDS = 30
    BASE_BACKOFF_SECONDS = 30
    MAX_BACKOFF_SECONDS = 600

    # --- FFmpeg health monitoring ---
    MONITOR_TICK_SECONDS = 10
    RUMBLE_CHECK_EVERY_N_TICKS = 6            # ~60s cadence for the Rumble age check (network call)
    STALL_TIMEOUT_SECONDS = 60

    # --- Proactive CDN URL-expiry refresh ---
    EXPIRY_REFRESH_MARGIN_SECONDS = 300

    # --- RTMP destination rejection handling ---
    RTMP_REJECTION_BACKOFF_SECONDS = 45
    RTMP_REJECTION_PHRASES = ["invalid stream key", "server error", "connection refused"]

    # --- Input-lag based stall detection ---
    INPUT_LAG_STALL_SECONDS = 90

    def __init__(self):
        """Initializes the service: loads config, sets up logging, validates."""
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            stream=sys.stdout)
        self.logger = logging.getLogger(__name__)

        self.process: Optional[subprocess.Popen] = None
        self._shutdown_requested = False
        self._consecutive_quick_failures = 0

        self._idle_since: float = time.time()
        self._next_fallback_check_at: float = 0.0

        self._load_config()
        self._validate_config()
        self._validate_dependencies()
        self.notify_ready()

    def _sd_notify(self, message: bytes) -> None:
        """Helper to send sd_notify protocol messages to systemd."""
        notify_socket = os.getenv('NOTIFY_SOCKET')
        if notify_socket:
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
                if notify_socket.startswith('@'):
                    notify_socket = '\0' + notify_socket[1:]
                sock.connect(notify_socket)
                sock.sendall(message)
                sock.close()
            except Exception as e:
                self.logger.warning(f"Failed to send sd_notify message {message!r}: {e}")

    def notify_ready(self):
        self._sd_notify(b'READY=1')

    def notify_watchdog(self):
        self._sd_notify(b'WATCHDOG=1')

    def _load_config(self):
        """Loads the main configuration file and extracts variables."""
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
            self.logger.info("✅ Configuration loaded successfully.")

            paths = self.config.get("paths", {})
            self.PYTHON_ENV = paths.get("python_env", "/usr/bin/python3")
            self.COOKIE_FILE = paths.get("cookie_file", "")
            self.X_SCRAPE_COOKIES_FILE = paths.get("x_scrape_cookies_json", "")
            self.RUMBLE_COOKIE_JSON = paths.get("rumble_cookies_json", "")

            settings = self.config.get("settings", {})
            self.IDLE_POLL_INTERVAL_SECONDS = settings.get("check_interval", 30)
            self.MAX_STREAM_AGE_HOURS = settings.get("max_stream_age_hours", 23.5)

            self._x_user_id_cache: Dict[str, str] = {}

        except FileNotFoundError:
            self.logger.critical(f"CRITICAL: Config file '{self.CONFIG_FILE}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            self.logger.critical(f"CRITICAL: Config file '{self.CONFIG_FILE}' is invalid JSON.")
            sys.exit(1)

    def _validate_config(self):
        """Validates required config keys exist."""
        streams = self.config.get("streams", {})
        required_keys = ["rtmp_url", "stream_key"]
        missing = [k for k in required_keys if not streams.get(k)]
        if missing:
            self.logger.critical(f"CRITICAL: Config missing streams key(s): {', '.join(missing)}")
            sys.exit(1)

        x_url = streams.get("x_url")
        x_username = streams.get("x_username")

        if not x_url and not x_username:
            self.logger.critical(
                "CRITICAL: Config needs either streams.x_url (a fixed broadcast URL) "
                "or streams.x_username (an account to auto-discover broadcasts for)."
            )
            sys.exit(1)

        if x_username:
            if not self.X_SCRAPE_COOKIES_FILE:
                self.logger.critical(
                    "CRITICAL: streams.x_username is set but paths.x_scrape_cookies_json "
                    "is not configured. The scrape path is the only supported discovery method."
                )
                sys.exit(1)
            if not os.path.exists(self.X_SCRAPE_COOKIES_FILE):
                self.logger.critical(
                    f"CRITICAL: paths.x_scrape_cookies_json '{self.X_SCRAPE_COOKIES_FILE}' "
                    "does not exist. Log into x.com in a browser and export auth_token/ct0 "
                    "(and related cookies) into this JSON file first."
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
            self.logger.critical(f"CRITICAL: 'yt-dlp' failed or path is wrong. Error: {e}")
            sys.exit(1)

        if shutil.which("ffmpeg") is None:
            self.logger.critical("CRITICAL: 'ffmpeg' not found on PATH.")
            sys.exit(1)

    # ==========================================================================
    # 🧩 UTILITY METHODS
    # ==========================================================================

    def _interruptible_sleep(self, seconds: float) -> None:
        """Sleeps incrementally while kicking systemd watchdog."""
        deadline = time.time() + seconds
        while time.time() < deadline and not self._shutdown_requested:
            self.notify_watchdog()
            time.sleep(min(1, deadline - time.time()))

    def _extract_x_url_from_text(self, text: str) -> Optional[str]:
        """Parses raw text/payloads to find an X broadcast or tweet URL."""
        pattern = r'(https?://(?:twitter|x)\.com/(?:i/broadcasts/|[^/]+/status/)\w+)'
        match = re.search(pattern, text)
        return match.group(1) if match else None

    def _get_direct_stream_url(self, x_url: str) -> Optional[str]:
        """Checks X/Twitter live status using yt-dlp and returns the direct HLS .m3u8 URL."""
        self.logger.info(f"Checking live status for X → {x_url}")

        cmd = [
            self.PYTHON_ENV, "-m", "yt_dlp",
            "--force-ipv4",
            "--dump-json",
            "--no-warnings",
            "-f", "best",  # Select best stream (X uses HLS m3u8 playlists)
            x_url
        ]

        # Use cookie file if configured (highly recommended for Twitter)
        if self.COOKIE_FILE and os.path.exists(self.COOKIE_FILE):
            cmd.extend(["--cookies", self.COOKIE_FILE])

        try:
            self.notify_watchdog()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                try:
                    video_metadata = json.loads(result.stdout)
                    is_live = (video_metadata.get('is_live') is True or
                               video_metadata.get('live_status') == 'is_live')

                    if is_live:
                        resolved_url = video_metadata.get('url')
                        self.logger.info("✅ ACTIVE X LIVE STREAM DETECTED")
                        return resolved_url
                    else:
                        self.logger.debug("X Broadcast is not currently live.")
                        return None

                except json.JSONDecodeError:
                    self.logger.error("Failed to parse yt-dlp JSON.")
                    return None

            stderr_lower = (result.stderr or "").lower()
            if "not currently live" in stderr_lower or "offline" in stderr_lower:
                self.logger.debug("X Stream determined: Not live.")
                return None
            else:
                self.logger.error(f"yt-dlp failed (exit {result.returncode}): {result.stderr.strip()}")
                return None

        except subprocess.TimeoutExpired:
            self.logger.warning("yt-dlp timed out during X check.")
            return None
        except Exception as e:
            self.logger.exception(f"Stream check failed due to exception: {e}")
            return None

    def _extract_url_expiry(self, url: str) -> Optional[float]:
        """Pulls CDN-signed expiration timestamp out of an m3u8/media URL if present."""
        match = re.search(r'exp=(\d{9,11})|expire[=/](\d{9,11})', url)
        if not match:
            return None
        try:
            ts = match.group(1) or match.group(2)
            return float(ts)
        except ValueError:
            return None

    @staticmethod
    def _watch_ffmpeg_progress(process: subprocess.Popen, state: Dict[str, Any]) -> None:
        """Monitors ffmpeg `-progress` pipe for stalls."""
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
                        continue

                    prev_val = state.get("out_time_ms")
                    state["out_time_ms"] = new_val

                    if prev_val is None or new_val > prev_val:
                        state["last_update"] = time.time()
        except Exception:
            pass

    def _watch_ffmpeg_stderr(self, process: subprocess.Popen, state: Dict[str, Any]) -> None:
        """Monitors ffmpeg stderr for RTMP rejection and lag stalls."""
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
                        if lag_seconds >= self.INPUT_LAG_STALL_SECONDS:
                            state["input_lag_stalled"] = True
                            state["input_lag_seconds"] = lag_seconds
                    except ValueError:
                        pass
        except Exception:
            pass

    # ==========================================================================
    # 📡 ORCHESTRATION METHODS
    # ==========================================================================

    def _find_latest_broadcast_url_via_scrape(self, username: str) -> Optional[str]:
        """Zero-cost broadcast discovery: reads the account's public timeline via twikit,
        authenticated with YOUR OWN cookies (not the target account's). Unofficial/ToS-gray —
        can break if X changes internals, and heavy polling risks the cookie account getting
        flagged. Prefer a secondary account's cookies over your main one."""
        try:
            from twikit import Client  # pyright: ignore[reportMissingImports]
        except ImportError:
            self.logger.error("twikit not installed. Run: pip install twikit")
            return None

        username = username.lstrip("@")

        async def _fetch() -> Optional[str]:
            client = Client("en-US")
            client.load_cookies(self.X_SCRAPE_COOKIES_FILE)

            cached_id = self._x_user_id_cache.get(f"scrape:{username}")
            if cached_id:
                user_id = cached_id
            else:
                user = await client.get_user_by_screen_name(username)
                user_id = user.id
                self._x_user_id_cache[f"scrape:{username}"] = user_id

            tweets = await client.get_user_tweets(user_id, "Tweets", count=5)
            for tweet in tweets:
                found = self._extract_x_url_from_text(getattr(tweet, "text", "") or "")
                if found:
                    return found
            return None

        try:
            return asyncio.run(_fetch())
        except Exception as e:
            self.logger.warning(f"Scrape-based broadcast lookup failed: {e}")
            return None

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
                    self.logger.warning(f"Could not save failure screenshot: {screenshot_err}")
            self.logger.exception(f"❌ Failed to invoke web button click: {e}")
        finally:
            if driver:
                driver.quit()
                self.logger.info("🌐 Headless browser session finalized and closed.")

    def _check_for_stream_signals(self) -> "tuple[Optional[str], Optional[str]]":
        """Handles X signal polling: either a fixed x_url, or auto-discovery via x_username
        using the twikit scrape path only."""
        streams = self.config.get("streams", {})
        now = time.time()

        if now < self._next_fallback_check_at:
            return None, None

        x_target_url = streams.get("x_url")
        x_username = streams.get("x_username")

        # Prefer auto-discovery when a username is configured
        if x_username:
            self.logger.info(f"[STATUS] Checking @{x_username}'s recent posts for a broadcast link (scrape)...")
            discovered = self._find_latest_broadcast_url_via_scrape(x_username)
            if discovered:
                x_target_url = discovered
                self.logger.info(f"[STATUS] Discovered broadcast URL: {discovered}")
            else:
                self.logger.debug(f"[STATUS] No broadcast link found in @{x_username}'s recent posts.")

        # Schedule the next discovery attempt (decaying interval)
        idle_elapsed = now - self._idle_since
        interval = (self.FALLBACK_BURST_INTERVAL_SECONDS
                    if idle_elapsed < self.FALLBACK_BURST_WINDOW_SECONDS
                    else self.FALLBACK_IDLE_INTERVAL_SECONDS)
        self._next_fallback_check_at = now + interval

        if x_target_url:
            self.logger.info("[STATUS] Polling X broadcast URL...")
            candidate = self._get_direct_stream_url(x_target_url)

            if candidate:
                self.logger.info("✅ X live stream found!")
                send_discord_embed("live", "⚡ Stream Detected", "Found live stream on X", 0x1da1f2)
                return candidate, x_target_url

        return None, None

    def _run_ffmpeg_stream(
        self, stream_url: str, source_url: Optional[str]
    ) -> "tuple[float, Optional[str], bool]":
        """Manages FFmpeg lifecycle pushing to RTMP target."""
        self.logger.info("🔄 Starting FFmpeg restream from X...")

        streams = self.config.get("streams", {})
        rtmp_url = streams.get('rtmp_url')
        stream_key = streams.get('stream_key', '')

        full_rtmp_target = f"{rtmp_url.rstrip('/')}/{stream_key}"

        ffmpeg_cmd = [
            "ffmpeg", "-hide_banner",
            "-loglevel", "warning", "-nostats",
            "-timeout", "15000000",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
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
        threading.Thread(target=self._watch_ffmpeg_progress, args=(self.process, progress_state), daemon=True).start()

        stderr_state: Dict[str, Any] = {
            "rtmp_rejected": False,
            "rtmp_rejection_line": None,
            "input_lag_stalled": False,
            "input_lag_seconds": None
        }
        threading.Thread(target=self._watch_ffmpeg_stderr, args=(self.process, stderr_state), daemon=True).start()

        expiry_ts = self._extract_url_expiry(stream_url) if source_url else None
        refresh_at = (expiry_ts - self.EXPIRY_REFRESH_MARGIN_SECONDS) if expiry_ts else None

        stall_reason: Optional[str] = None
        refreshed_url: Optional[str] = None
        max_age_hit = False
        tick = 0
        api = self.config.get("api", {})

        try:
            while self.process.poll() is None:
                self.notify_watchdog()
                self._interruptible_sleep(self.MONITOR_TICK_SECONDS)
                tick += 1

                if self._shutdown_requested:
                    self.logger.info("Shutdown requested; stopping FFmpeg.")
                    break

                # URL Refresh Handling
                if refresh_at and time.time() >= refresh_at and source_url:
                    self.logger.info("🔄 Re-resolving fresh playlist URL from X...")
                    candidate = self._get_direct_stream_url(source_url)
                    if candidate:
                        self.logger.info("✅ Fresh URL acquired.")
                        refreshed_url = candidate
                        break
                    else:
                        refresh_at = time.time() + (self.MONITOR_TICK_SECONDS * 3)

                # Stall Checks
                if (time.time() - progress_state["last_update"]) > self.STALL_TIMEOUT_SECONDS:
                    stall_reason = "No FFmpeg progress detected (Stream Stalled)"
                    break

                if stderr_state["input_lag_stalled"]:
                    stall_reason = f"FFmpeg input lag ({stderr_state['input_lag_seconds']:.0f}s)"
                    break

                # Rumble (output) max-age check
                if (api.get("rumble_stats_url")
                        and tick % self.RUMBLE_CHECK_EVERY_N_TICKS == 0):
                    stream_age = self._get_rumble_stream_age()
                    if stream_age is not None:
                        age_hours = stream_age / 3600
                        self.logger.info(f"📊 Current Rumble stream age: {age_hours:.2f} hrs")

                        if age_hours >= self.MAX_STREAM_AGE_HOURS:
                            self.logger.warning(f"⏰ Stream hit max limit ({self.MAX_STREAM_AGE_HOURS}h). Terminating...")
                            max_age_hit = True
                            self.process.terminate()
                            break

        except Exception as e:
            self.logger.exception(f"Monitoring loop error: {e}")
        finally:
            if self.process is not None and self.process.poll() is None:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()

            # Only press Rumble's "End Livestream" button when we actually
            # hit the max-age limit.
            if max_age_hit:
                self._force_end_rumble_via_web()

        elapsed = time.time() - start_time
        return elapsed, refreshed_url, stderr_state["rtmp_rejected"]

    def monitor_and_restream(self) -> None:
        """Main control loop."""
        self.logger.info("🚀 Starting X Restreamer Service Loop (scrape-only discovery).")

        pending_stream_url: Optional[str] = None
        pending_source_url: Optional[str] = None

        while not self._shutdown_requested:
            self.notify_watchdog()

            try:
                if pending_stream_url:
                    stream_url = pending_stream_url
                    source_url = pending_source_url
                    pending_stream_url = None
                    pending_source_url = None
                else:
                    stream_url, source_url = self._check_for_stream_signals()

                if stream_url:
                    self.logger.info("Starting FFmpeg restream process...")
                    elapsed, refreshed_url, rtmp_rejected = self._run_ffmpeg_stream(stream_url, source_url)

                    if refreshed_url:
                        pending_stream_url = refreshed_url
                        pending_source_url = source_url
                        self._consecutive_quick_failures = 0
                        continue

                    self._idle_since = time.time()
                    self._next_fallback_check_at = 0.0

                    if rtmp_rejected:
                        self.logger.warning(f"RTMP rejected connection. Cooling down {self.RTMP_REJECTION_BACKOFF_SECONDS}s.")
                        self._interruptible_sleep(self.RTMP_REJECTION_BACKOFF_SECONDS)
                    elif elapsed < self.QUICK_FAILURE_THRESHOLD_SECONDS:
                        self._consecutive_quick_failures += 1
                        backoff = min(self.MAX_BACKOFF_SECONDS, self.BASE_BACKOFF_SECONDS * (2 ** (self._consecutive_quick_failures - 1)))
                        self.logger.warning(f"Quick failure ({elapsed:.0f}s elapsed). Backing off {backoff:.0f}s...")
                        self._interruptible_sleep(backoff)
                    else:
                        self._consecutive_quick_failures = 0
                else:
                    self._interruptible_sleep(self.IDLE_POLL_INTERVAL_SECONDS)

            except Exception as e:
                self.logger.critical(f"Unrecoverable loop error: {type(e).__name__} - {e}")
                raise

        self.logger.info("Exited gracefully.")


# ==============================================================================
# 🚀 MAIN EXECUTION BLOCK
# ==============================================================================

restreamer: Optional[XRestreamerService] = None

def signal_handler(sig, frame) -> None:
    print("\n[SIGNAL RECEIVED] Initiating graceful shutdown...")
    if restreamer is not None:
        restreamer._shutdown_requested = True
        if restreamer.process and restreamer.process.poll() is None:
            restreamer.process.terminate()

def main() -> None:
    global restreamer
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        restreamer = XRestreamerService()
        restreamer.monitor_and_restream()
    except Exception as e:
        print(f"\n[FATAL ERROR] Service failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()