"""Bounded subprocesses and Apple Container CLI integration; no shell evaluation."""
from dataclasses import asdict, dataclass
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import subprocess
import tempfile
import time
import uuid


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    duration_s: float
    reason: str

    def dict(self):
        return asdict(self)


def command(argv, timeout=30, max_output=1_000_000, cwd=None, env=None):
    """Kill this process group on deadline/output limit, including descendants."""
    started = time.monotonic()
    proc = subprocess.Popen([str(v) for v in argv], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True, cwd=cwd, env=env)
    chunks = {"stdout": bytearray(), "stderr": bytearray()}
    reason = "completed"
    total = 0
    with selectors.DefaultSelector() as sel:
        sel.register(proc.stdout, selectors.EVENT_READ, "stdout")
        sel.register(proc.stderr, selectors.EVENT_READ, "stderr")
        while sel.get_map():
            if time.monotonic() - started >= timeout:
                reason = "timeout"
                break
            for key, _ in sel.select(timeout=min(0.1, timeout)):
                data = os.read(key.fileobj.fileno(), 8192)
                if not data:
                    sel.unregister(key.fileobj)
                    continue
                remaining = max(0, max_output - total)
                chunks[key.data].extend(data[:remaining])
                total += len(data)
                if total > max_output:
                    reason = "output_limit"
                    break
            if reason != "completed":
                break
        if reason != "completed":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            rc = proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            rc = proc.wait(timeout=2)
    proc.stdout.close()
    proc.stderr.close()
    return CommandResult(rc, chunks["stdout"].decode(errors="replace"),
                         chunks["stderr"].decode(errors="replace"),
                         time.monotonic() - started, reason)


class AppleContainer:
    def __init__(self):
        self.binary = os.environ.get("CONTAINER_BIN") or shutil.which("container")

    def require(self):
        if not self.binary:
            raise RuntimeError("Apple Container is not installed. See docs/SETUP.md. No host execution fallback is used.")

    def call(self, args, timeout=60, max_output=1_000_000):
        self.require()
        return command([self.binary, *args], timeout=timeout, max_output=max_output)

    def status(self):
        if not self.binary:
            return {"available": False, "message": "Install Apple Container on an Apple silicon Mac"}
        try:
            r = self.call(["list", "--format", "json"], timeout=5)
            return {"available": r.returncode == 0, "message": r.stderr or r.stdout[:500]}
        except (OSError, RuntimeError) as e:
            return {"available": False, "message": str(e)}

    @staticmethod
    def name(prefix="job"):
        return "lab-" + re.sub("[^a-z0-9-]", "", prefix.lower())[:24] + "-" + uuid.uuid4().hex[:12]

    def cleanup(self, name):
        if not re.fullmatch(r"lab-[a-z0-9-]+-[0-9a-f]{12}", name):
            raise ValueError("Refusing to remove a container not created by this lab")
        return self.call(["delete", "--force", name], timeout=20)

    def run(self, image, argv, *, cpus=1, memory_mb=512, timeout=30,
            mounts=(), network="none", max_output=1_000_000, user=None, read_only_root=False):
        if not 1 <= cpus <= 8 or not 128 <= memory_mb <= 8192:
            raise ValueError("Resource allocation is outside lab limits")
        name = self.name()
        args = ["run", "--name", name, "--rm", "--cpus", str(cpus), "--memory", f"{memory_mb}m",
                "--network", network, "--cap-drop", "ALL"]
        if user:
            args += ["--user", user]
        if read_only_root:
            args += ["--read-only", "--tmpfs", "/tmp:size=16M,mode=1777"]
        with tempfile.TemporaryDirectory(prefix="lab-mount-") as staging:
            for i, (host, guest, mode) in enumerate(mounts):
                host = Path(host).resolve()
                if not host.is_dir() or mode not in ("ro", "rw") or ":" in str(host):
                    raise ValueError("Invalid mount")
                if mode == "ro":
                    # Background VM helpers may not access protected macOS folders.
                    # Snapshot only the explicitly supplied input into a private temp dir.
                    staged = Path(staging) / str(i)
                    if host.is_dir():
                        shutil.copytree(host, staged, ignore=shutil.ignore_patterns("__pycache__"))
                    else:
                        shutil.copy2(host, staged)
                    host = staged
                args += ["--volume", f"{host}:{guest}:{mode}"]
            try:
                result = self.call([*args, image, *argv], timeout=timeout, max_output=max_output)
            finally:
                self.cleanup(name)
        return result
