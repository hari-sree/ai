# Home Infrastructure — Claude Context

This project is for managing, scripting, and automating Sree's home lab infrastructure.

---

## Conventions

### Scripts
All scripts for this project live in the `scripts/` folder. Whenever a new script needs to be created, always place it there.

### UDM Pro — backup before changes
Before modifying any file on the UDM Pro via SSH, first SCP a copy of that file to the `udm-backups/` folder in this project. Structure: `udm-backups/<YYYY-MM-DD_HH-MM-SS>/<filename>`. This gives a simple timestamped version history. The `scripts/add-dns-record.py` script does this automatically; replicate the same pattern in any future scripts that touch UDM Pro files.

---

## Network Overview

- **Router/DNS**: Ubiquiti Dream Machine Pro (UDM Pro) at `192.168.1.1` — manages static IPs and `.home` hostnames
- **Primary subnet**: `192.168.1.x`
- **Smart devices subnet**: `192.168.2.x`

### Hosts

| Hostname | Alias | IP | Notes |
|---|---|---|---|
| `starboard.home` | carbon | `192.168.1.2` | Linux laptop |
| `bucket.home` | bucket | `192.168.1.174` | Synology NAS |
| `sparta.home` | sparta | `192.168.1.3` | Always-on Ubuntu 24.04 server, RTX 5060 Ti 16GB |
| `rpi.home` | rpi | `192.168.2.11` | Raspberry Pi Model B, smartdevices WiFi |
| `rome.home` | rome | TBD | Currently offline — planned always-on node |

---

## ⚠️ UDM Pro — Changes Require Explicit Confirmation

SSH access to the UDM Pro is configured (keys set up, `root@192.168.1.1`). However:

> **IMPORTANT: Never make any changes to the UDM Pro via SSH or otherwise without explicitly asking Sree for confirmation first.** This includes dnsmasq config, firewall rules, network settings, or any other system modification. Read-only commands (status checks, reading config files) are fine without asking.

> **IMPORTANT: Always back up affected files to `udm-backups/<timestamp>/` before making any change** (see Conventions above).

---

## UDM Pro — DNS Configuration

DNS on the UDM Pro is served by **dnsmasq**. The configuration is fully managed by `ubios-udapi-server` — never edit the generated files directly.

### Config generation chain

```
/data/udapi-config/udapi-net-cfg.json   ← source of truth, persists across reboots
        ↓  read by
ubios-udapi-server (PID ~2299)
        ↓  generates
/run/dnsmasq.dns.conf.d/main.conf       ← auto-generated, DO NOT edit directly (lives in tmpfs)
        ↓  read by
dnsmasq
```

### Key file locations

| Path | Description |
|---|---|
| `/data/udapi-config/udapi-net-cfg.json` | Symlink to current versioned config |
| `/data/udapi-config/udapi-net-cfg-<hash>.json` | Actual versioned config files |
| `/data/udapi-config/udapi-net-cfg.json.prev` | Symlink to previous version |
| `/run/dnsmasq.dns.conf.d/main.conf` | Generated dnsmasq config (volatile) |
| `/run/dnsmasq.dns.conf.d/hosts.d/leases` | Dynamic DHCP lease hostnames (volatile) |
| `/run/dnsmasq-main.pid` | dnsmasq PID file |

### DNS record format in the JSON

All `.home` hostnames are stored as `hostRecord` objects under `services.dnsForwarder.hostRecords`:

```json
{
  "hostName": "sparta.home",
  "registerNonQualified": false,
  "address": {
    "address": "192.168.1.3",
    "version": "v4"
  }
}
```

### How to add a new DNS record

Use the script — it handles backup, JSON editing, symlink rotation, and dnsmasq reload:

```bash
./scripts/add-dns-record.py <hostname> <ip>
# Example:
./scripts/add-dns-record.py ollama.sparta.home 192.168.1.3
```

The script:
1. Backs up the current JSON to `udm-backups/<timestamp>/`
2. Adds the new `hostRecord` to the JSON
3. Writes a new versioned JSON file and updates the symlink
4. Appends `host-record=` to the live `main.conf` for immediate effect
5. Sends SIGHUP to dnsmasq to reload

> On next UDM Pro reboot, the record comes cleanly from the JSON (no manual step needed).

### Current custom DNS records (sparta subdomains)

All point to `192.168.1.3` (Sparta's LAN IP):

| Hostname | Purpose |
|---|---|
| `ollama.sparta.home` | Ollama LLM inference → Traefik → host port 11434 |
| `jupyter.sparta.home` | JupyterLab → Traefik → host port 8888 |
| `claude.sparta.home` | OpenClaw Gateway → Traefik → host port 18789 (502 — bound to localhost, pending fix) |
| `openwebui.sparta.home` | Open WebUI → Traefik → k8s pod port 8080 |

---

## Machines

### sparta (`sree@sparta.home`)
- **OS**: Ubuntu 24.04.1 LTS
- **IP**: `192.168.1.3`
- **GPU**: NVIDIA RTX 5060 Ti — 16GB VRAM
- **Role**: Primary AI experimentation node and always-on compute server. Main host for running AI services, LLM inference, and GPU workloads.
- **Systemd services**:
  - NFS mount from bucket (NAS)
  - Jupyter notebook
  - k3s agent (Kubernetes worker)
- **AI services**: Ollama (local LLM inference)

### starboard (`sree@starboard.home`)
- **Role**: Main desktop/workstation
- **Systemd services**:
  - SSH port forwarding to sparta's Claw UI

### bucket (`marcus@bucket.home`)
- **Role**: Synology NAS
- **SSH**: `ssh marcus@bucket.home`
- **NFS exports**: `/volume1/plex` (and others)

### rome (`sree@rome.home`)
- **Status**: Currently offline — being set up, will be always-on going forward
- **Role**: TBD (specs and services to be documented once online)
- **Note**: "Rome" always refers to this home lab node, not the city.

### rpi (`sree@rpi.home`)
- **Hardware**: Raspberry Pi Model B
- **Short hostname**: `fd88`
- **Network**: Tethered to smartdevices WiFi (`192.168.2.x`)
- **Role**: Potential k3s worker node

---

## NFS / Storage

NAS (bucket.home) serves NFS shares. Clients (sparta etc.) mount via fstab for automount.

```shell
# Check NFS exports on NAS
showmount -e bucket.home

# Mount manually
sudo mount -t nfs bucket.home:/volume1/plex /mnt/bucket/plex

# Unmount
sudo umount -lf /mnt/bucket/plex

# Mount all fstab entries
sudo mount -a
```

**fstab entry** (for automount on boot):
```
bucket.home:/volume1/plex  /mnt/bucket/plex  nfs  defaults,_netdev,x-systemd.automount,x-systemd.requires=network-online.target  0  0
```

> Note: Map all NFS users to admin with `sys` security — NFS otherwise matches by Linux UID.

---

## Networking — Tailscale VPN

Tailscale is running across all primary devices, forming a private mesh VPN in addition to the local `.home` network.

**Enrolled devices:**
- Mac laptop (primary workstation)
- Sparta (Ubuntu server)
- Linux laptop (starboard)
- Mobile phone

This means services on Sparta (Ollama, Grafana, k3s API, etc.) can be reached via Tailscale IP even when not on the home LAN — useful for remote access without opening ports.

---

## Kubernetes (k3s)

k3s cluster running on the home network.

- **Server node**: `sparta`
- **Worker nodes**: sparta (k3s agent), rpi (planned)
- **API port**: `6443`
- **Mac kubeconfig**: `~/.kube/config-k3s`

```shell
# Common cluster commands
sudo k3s kubectl get nodes
sudo k3s kubectl get pods --all-namespaces

# Port-forward Grafana
kubectl --namespace monitoring port-forward svc/monitoring-grafana 3000:80

# Agent status (on worker node)
sudo systemctl status k3s-agent
journalctl -u k3s-agent -f

# Restart server
sudo systemctl restart k3s
```

---

## Ollama (Local LLM)

Running on sparta. Access via SSH tunnel or direct if on same network.

```shell
# On sparta
ollama list
ollama run <model>
```

---

## Caddy — Reverse Proxy (sparta)

Caddy runs on sparta but is **not used for subdomain routing** (Traefik owns port 80 via k3s).
Caddy currently only serves the `sparta.home` health check.

Config: `/etc/caddy/Caddyfile`

---

## Services — Home Network Access

All services are exposed via **Traefik** (k3s ingress, port 80) and DNS records on the UDM Pro.
Use `scripts/add-dns-record.py` to add new subdomains.

### Host services (non-k8s) — k8s/host-services.yaml
Exposed via Service + manual Endpoints pointing to `192.168.1.3`:

| URL | Host port | Notes |
|---|---|---|
| `http://ollama.sparta.home` | 11434 | Ollama LLM inference ✅ |
| `http://jupyter.sparta.home` | 8888 | JupyterLab ✅ |
| `http://claude.sparta.home` | 18789 | OpenClaw Gateway ❌ bound to 127.0.0.1 only |

### k8s services — k8s/open-webui.yaml
Running as pods inside the cluster, exposed via standard Service + Ingress:

| URL | Image | Notes |
|---|---|---|
| `http://openwebui.sparta.home` | `ghcr.io/open-webui/open-webui:main` | Connects to Ollama via `ollama-host` Service ✅ |

> PVC `open-webui-data` (5Gi, local-path) stores chat history and settings.

---

## SSH Shortcuts

```shell
ssh sree@sparta.home
ssh root@192.168.1.1   # UDM Pro (read-only without confirmation)
ssh sree@starboard.home
ssh marcus@bucket.home
ssh sree@rpi.home
```

---

## Key TODOs

- DNS server: ensure logical hostnames for all containers/services
- **Expose Sparta services to all home nodes (phone, laptop, etc.)**
  - [x] Subtask 1: Expose services running directly on Sparta (non-Kubernetes) — Caddy subdomains set up for Ollama, JupyterLab, OpenClaw; DNS A records added via script
  - [ ] Subtask 2: Expose services running inside the k3s cluster — make them reachable from outside the cluster (via Ingress, NodePort, or Tailscale)

---

## Source Notes

Assembled from Notion pages:
- [Home infra](https://www.notion.so/306ed11845cd801b9cc0c03b0090219e) — primary host/service map
- [K3s](https://www.notion.so/7f7f65e54d0b4c4787eda27bd993605b) — Kubernetes setup
- [Filesystems / mounting](https://www.notion.so/303ed11845cd80c499fbe0ffbba02eea) — NFS/fstab
- [Shell network/connections](https://www.notion.so/8cca5f2bd1f14177afd1f18aa44ede4e) — networking commands
- [Home automation](https://www.notion.so/f9a7102f905140cc8c83d83452d6bf0a) — parent page with sub-pages
