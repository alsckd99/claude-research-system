"""
Shared server utilities — safe port allocation and GPU selection.
Prevents conflicts when multiple users share the same machine.

Usage:
    from scripts.server_utils import find_free_port, find_free_gpus

    port = find_free_port(preferred=6006)  # TensorBoard
    gpus = find_free_gpus(n=1)             # 1 available GPU
"""
import os
import socket
import subprocess
from typing import Any


# --- Port allocation ---

def is_port_in_use(port: int, host: str = "0.0.0.0") -> bool:
    """Check if a port is already bound by any process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0


def find_free_port(preferred: int = 0, range_start: int = 10000, range_end: int = 65000) -> int:
    """Find a free port. Tries preferred first, then scans a range.

    Args:
        preferred: Try this port first (0 = skip).
        range_start: Start of scan range if preferred is taken.
        range_end: End of scan range.

    Returns:
        An available port number.
    """
    if preferred > 0 and not is_port_in_use(preferred):
        return preferred

    # let OS pick a random free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = s.getsockname()[1]
        return port


def find_free_port_in_range(start: int = 10000, end: int = 10100) -> int | None:
    """Find a free port within a specific range. Returns None if all taken."""
    for port in range(start, end):
        if not is_port_in_use(port):
            return port
    return None


# --- GPU allocation ---

def get_gpu_status() -> list[dict[str, Any]]:
    """Get GPU status via nvidia-smi. Returns list of GPU info dicts.

    Each dict: {id, name, memory_total, memory_used, memory_free, utilization, pids, users}
    """
    try:
        result = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return []
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    gpus = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            continue
        gpu_id = int(parts[0])
        gpus.append({
            "id": gpu_id,
            "name": parts[1],
            "memory_total": int(parts[2]),
            "memory_used": int(parts[3]),
            "memory_free": int(parts[4]),
            "utilization": int(parts[5]),
            "pids": _get_gpu_pids(gpu_id),
            "users": _get_gpu_users(gpu_id),
        })

    return gpus


def _get_gpu_pids(gpu_id: int) -> list[int]:
    """Get PIDs of processes using a specific GPU."""
    try:
        result = subprocess.run(
            ["nvidia-smi", f"--id={gpu_id}",
             "--query-compute-apps=pid", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10
        )
        pids = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line.isdigit():
                pids.append(int(line))
        return pids
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _get_gpu_users(gpu_id: int) -> set[str]:
    """Get usernames of users with processes on a specific GPU."""
    pids = _get_gpu_pids(gpu_id)
    users = set()
    for pid in pids:
        try:
            stat_file = f"/proc/{pid}/status"
            with open(stat_file) as f:
                for line in f:
                    if line.startswith("Uid:"):
                        uid = int(line.split()[1])
                        import pwd
                        users.add(pwd.getpwuid(uid).pw_name)
                        break
        except (FileNotFoundError, KeyError, ValueError, PermissionError):
            continue
    return users


def find_free_gpus(
    n: int = 1,
    min_free_memory_mb: int = 4000,
    avoid_other_users: bool = True,
) -> list[int]:
    """Find available GPUs that are not heavily used by other users.

    Args:
        n: Number of GPUs needed.
        min_free_memory_mb: Minimum free memory required (MB).
        avoid_other_users: If True, prefer GPUs not used by other users.

    Returns:
        List of GPU IDs. May be shorter than n if not enough available.
    """
    gpus = get_gpu_status()
    if not gpus:
        return []

    current_user = os.environ.get("USER", "")

    # score each GPU (higher = more available)
    scored = []
    for gpu in gpus:
        if gpu["memory_free"] < min_free_memory_mb:
            continue

        score = gpu["memory_free"]  # base: free memory

        other_users = gpu["users"] - {current_user}
        if avoid_other_users and other_users:
            score -= 100000  # heavily penalize GPUs used by others

        if gpu["utilization"] > 80:
            score -= 50000  # penalize high utilization

        # small bonus for completely empty GPUs
        if not gpu["pids"]:
            score += 10000

        scored.append((score, gpu["id"], gpu))

    scored.sort(reverse=True)
    selected = [gpu_id for _, gpu_id, _ in scored[:n]]

    return selected


def gpu_summary() -> str:
    """Human-readable GPU status summary for logging."""
    gpus = get_gpu_status()
    if not gpus:
        return "[gpu] nvidia-smi not available"

    current_user = os.environ.get("USER", "")
    lines = [f"[gpu] {len(gpus)} GPUs detected:"]

    for gpu in gpus:
        other_users = gpu["users"] - {current_user}
        user_str = ""
        if other_users:
            user_str = f" ⚠ used by: {', '.join(other_users)}"
        elif gpu["users"]:
            user_str = f" (my processes)"
        else:
            user_str = " (free)"

        lines.append(
            f"  GPU {gpu['id']}: {gpu['name']} — "
            f"{gpu['memory_free']}/{gpu['memory_total']}MB free, "
            f"{gpu['utilization']}% util{user_str}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    # standalone: print GPU and port status
    print(gpu_summary())
    print()
    port = find_free_port(preferred=6006)
    print(f"[port] free port (preferred 6006): {port}")
    port2 = find_free_port(preferred=8888)
    print(f"[port] free port (preferred 8888): {port2}")
