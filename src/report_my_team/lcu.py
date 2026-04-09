import base64
import logging
import re
import subprocess
import warnings
from dataclasses import dataclass

import httpx
import psutil

logger = logging.getLogger(__name__)

PROCESS_NAME = "LeagueClientUx.exe"
PORT_PATTERN = re.compile(r'--app-port="?(\d+)"?')
TOKEN_PATTERN = re.compile(r"--remoting-auth-token=([a-zA-Z0-9_-]+)")

# Suppress urllib3/httpx InsecureRequestWarning for the LCU self-signed cert
warnings.filterwarnings("ignore", message="Unverified HTTPS request")


@dataclass
class LcuCredentials:
    port: int
    auth_header: str  # pre-computed "Basic <base64>"


class LcuClient:
    """Manages LCU process detection, credentials, and an async HTTP client."""

    def __init__(self) -> None:
        self._credentials: LcuCredentials | None = None
        self._last_pid: int = 0
        self._http: httpx.AsyncClient = httpx.AsyncClient(verify=False)

    async def aclose(self) -> None:
        await self._http.aclose()

    def find_process(self) -> psutil.Process | None:
        for proc in psutil.process_iter(["name", "pid"]):
            try:
                if proc.info["name"] == PROCESS_NAME:
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return None

    def _credentials_from_process(self, proc: psutil.Process) -> LcuCredentials | None:
        try:
            # Primary: WMIC (matches original C# behavior on Windows)
            result = subprocess.run(
                [
                    "wmic",
                    "process",
                    "where",
                    f"Processid={proc.pid}",
                    "get",
                    "Commandline",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            cmdline = result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Fallback: psutil.cmdline() (works on Linux/WSL for dev/testing)
            try:
                cmdline = " ".join(proc.cmdline())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None

        port_match = PORT_PATTERN.search(cmdline)
        token_match = TOKEN_PATTERN.search(cmdline)
        if not port_match or not token_match:
            return None

        port = int(port_match.group(1))
        token = token_match.group(1)
        encoded = base64.b64encode(f"riot:{token}".encode()).decode()
        return LcuCredentials(port=port, auth_header=f"Basic {encoded}")

    def refresh_credentials(self) -> bool:
        """Poll for the LCU process and refresh credentials. Returns True if client is live."""
        proc = self.find_process()
        if proc is None:
            self._credentials = None
            return False

        # Only re-parse if the PID changed (new client instance)
        if proc.pid != self._last_pid:
            self._last_pid = proc.pid
            self._credentials = self._credentials_from_process(proc)

        return self._credentials is not None

    @property
    def is_connected(self) -> bool:
        return self._credentials is not None

    async def request(
        self,
        method: str,
        path: str,
        json_body: dict | None = None,
    ) -> tuple[int, bytes]:
        """Make an LCU API request. Returns (status_code, body). Returns (999, b"") on failure."""
        if self._credentials is None:
            return 999, b""
        url = f"https://127.0.0.1:{self._credentials.port}/{path}"
        headers = {"Authorization": self._credentials.auth_header}
        try:
            resp = await self._http.request(
                method, url, headers=headers, json=json_body
            )
            return resp.status_code, resp.content
        except httpx.RequestError as exc:
            logger.debug("LCU request failed: %s", exc)
            return 999, b""
