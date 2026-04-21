# Home Infrastructure — Claude Context

This project is for managing, scripting, and automating Sree's home lab infrastructure.

---

## Network Overview

- **Router/DNS**: Ubiquiti Dream Machine (UDM) — manages static IPs and `.home` hostnames
- **Primary subnet**: `192.168.1.x`
- **Smart devices subnet**: `192.168.2.x`

### Hosts

| Hostname | Alias | IP | Notes |
|---|---|---|---|
| `starboard.home` | carbon | `192.168.1.2` | Linux laptop |
| `bucket.home` | bucket | `192.168.1.174` | Synology NAS |
| `sparta.home` | sparta | DHCP (static lease) | Always-on Ubuntu 24.04 server, RTX 5060 Ti 16GB |
| `rpi.home` | rpi | `192.168.2.11` | Raspberry Pi Model B, smartdevices WiFi |
| `rome.home` | rome | TBD | Currently offline — planned always-on node |

---

## Machines

### sparta (`sree@sparta.home`)
- **OS**: Ubuntu 24.04.1 LTS
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

## SSH Shortcuts

```shell
ssh sree@sparta.home
ssh sree@starboard.home
ssh marcus@bucket.home
ssh sree@rpi.home
```

---

## Key TODOs (from Notion)

- Add rpi as k3s agent and point kubectl to the right server
- DNS server: ensure logical hostnames for all containers/services
- DHCP: control IPs of known services
- Explore OPNSense firewall

---

## Source Notes

Assembled from Notion pages:
- [Home infra](https://www.notion.so/306ed11845cd801b9cc0c03b0090219e) — primary host/service map
- [K3s](https://www.notion.so/7f7f65e54d0b4c4787eda27bd993605b) — Kubernetes setup
- [Filesystems / mounting](https://www.notion.so/303ed11845cd80c499fbe0ffbba02eea) — NFS/fstab
- [Shell network/connections](https://www.notion.so/8cca5f2bd1f14177afd1f18aa44ede4e) — networking commands
- [Home automation](https://www.notion.so/f9a7102f905140cc8c83d83452d6bf0a) — parent page with sub-pages
