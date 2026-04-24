#!/usr/bin/env python3
"""
Add a DNS A record to the UDM Pro's dnsmasq configuration.

Usage:
    ./scripts/add-dns-record.py <hostname> <ip>

Example:
    ./scripts/add-dns-record.py ollama.sparta.home 192.168.1.3

What it does:
    1. Backs up the current JSON config to udm-backups/<timestamp>/
    2. Reads the JSON, adds the new hostRecord entry
    3. Writes a new versioned JSON file and rotates the symlink
    4. Appends host-record to the live main.conf for immediate effect
    5. SIGHUPs dnsmasq to reload

On next UDM Pro reboot the record comes cleanly from the JSON.
"""

import sys
import json
import hashlib
import subprocess
import os
from datetime import datetime

UDM_HOST = "root@192.168.1.1"
JSON_PATH = "/data/udapi-config/udapi-net-cfg.json"
DNSMASQ_MAIN_CONF = "/run/dnsmasq.dns.conf.d/main.conf"
DNSMASQ_PID_FILE = "/run/dnsmasq-main.pid"

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(PROJECT_DIR, "udm-backups")


def ssh(cmd, input_data=None):
    result = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", UDM_HOST, cmd],
        input=input_data,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"SSH error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def backup(remote_path):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest_dir = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(remote_path)
    local_path = os.path.join(dest_dir, filename)
    subprocess.run(
        ["scp", "-q", f"{UDM_HOST}:{remote_path}", local_path],
        check=True,
    )
    print(f"  Backed up → udm-backups/{timestamp}/{filename}")
    return local_path


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <hostname> <ip>")
        sys.exit(1)

    hostname = sys.argv[1]
    ip = sys.argv[2]

    print(f"Adding DNS record: {hostname} → {ip}")

    # 1. Backup current JSON
    backup(JSON_PATH)

    # 2. Read current JSON
    real_path = ssh(f"readlink -f {JSON_PATH}")
    raw = ssh(f"cat '{real_path}'")
    cfg = json.loads(raw)

    records = cfg["services"]["dnsForwarder"]["hostRecords"]

    # Check for duplicates
    for r in records:
        if r.get("hostName") == hostname:
            print(f"  Record already exists: {hostname} — nothing to do.")
            return

    # 3. Append new record
    records.append({
        "hostName": hostname,
        "registerNonQualified": False,
        "address": {
            "address": ip,
            "version": "v4",
        },
    })

    # 4. Serialize and write new versioned file
    new_content = json.dumps(cfg, separators=(",", ":"))
    new_hash = hashlib.md5(new_content.encode()).hexdigest()
    new_filename = f"udapi-net-cfg-{new_hash}.json"
    new_path = f"/data/udapi-config/{new_filename}"

    ssh(f"cat > '{new_path}' && chmod 600 '{new_path}'", input_data=new_content)
    print(f"  Wrote {new_filename}")

    # 5. Rotate symlinks (prev ← current, current ← new)
    ssh(
        f"ln -sfn '{real_path}' /data/udapi-config/udapi-net-cfg.json.prev && "
        f"ln -sfn '{new_path}' /data/udapi-config/udapi-net-cfg.json"
    )
    print(f"  Symlink rotated")

    # 6. Append to live main.conf for immediate effect (before next UDM reboot)
    ssh(f"echo 'host-record={hostname},{ip}' >> {DNSMASQ_MAIN_CONF}")
    print(f"  Appended to main.conf")

    # 7. SIGHUP dnsmasq to reload
    ssh(f"kill -HUP $(cat {DNSMASQ_PID_FILE})")
    print(f"  dnsmasq reloaded")

    print(f"Done. {hostname} → {ip} is now live.")


if __name__ == "__main__":
    main()
