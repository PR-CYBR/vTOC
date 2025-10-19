# Raspberry Pi 5 Deployment Guide

The Raspberry Pi 5 can host a lightweight vTOC station when paired with disciplined resource management. This guide captures the
hardware expectations, operating system tuning, and service defaults that keep the board responsive while delegating heavier
workloads (Postgres, Supabase Auth) to managed infrastructure.

## Hardware prerequisites

| Component | Recommendation | Notes |
| --- | --- | --- |
| Raspberry Pi 5 | 8 GB RAM model | Lower memory SKUs will struggle when the backend, telemetry agents, and Docker services overlap. |
| Storage | 128 GB UHS-I microSD *or* NVMe HAT + SSD | Prefer NVMe for sustained writes; microSD must be rated A2/V30. |
| Power | Official 27 W USB-C PSU | Required to sustain USB 3 peripherals and PoE HAT draw. |
| Cooling | Active cooler or PoE HAT with fan | Keeps CPU below thermal throttle thresholds during sustained Docker workloads. |
| Networking | Gigabit Ethernet | Wi-Fi is supported but adds jitter for telemetry streams; wire the Pi whenever possible. |

Keep a USB-C console cable available for headless recovery. When deploying multiple low-power stations, stage a spare imaged
microSD/NVMe module to accelerate swaps.

## Operating system preparation

1. Flash the latest **Raspberry Pi OS Lite (64-bit)** image using Raspberry Pi Imager or `rpi-imager`. During flashing:
   - Enable SSH with key-based authentication.
   - Set the hostname to the station callsign (e.g., `vtoc-pi5-ops`).
   - Configure the locale and time zone that match the deployment theater.
2. Boot the Pi with keyboard/monitor attached for the first run or connect over the pre-configured SSH key.
3. Immediately update packages and firmware:
   ```bash
   sudo apt update && sudo apt full-upgrade -y
   sudo rpi-eeprom-update -a
   sudo reboot
   ```
4. Install baseline dependencies required by the bootstrap CLI:
   ```bash
   sudo apt install -y python3-full python3-venv git jq docker.io docker-compose-plugin
   ```
5. Add the `vtoc` operator account and join the Docker group:
   ```bash
   sudo adduser --gecos "vTOC Operator" vtoc
   sudo usermod -aG docker vtoc
   ```

## OS tuning for sustained uptime

Raspberry Pi OS defaults favor interactive use. Apply the following adjustments to keep the Pi responsive while running the
backend and telemetry connectors:

- **GPU memory split:** Set `gpu_mem=32` in `/boot/firmware/config.txt` to maximize RAM available to systemd services.
- **Cgroups v2:** Ensure `/boot/firmware/cmdline.txt` contains `cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory`. This
  unlocks proper container limits.
- **ZRAM:** Enable compressed RAM swap to absorb spikes without trashing the SD/NVMe device:
  ```bash
  sudo apt install -y zram-tools
  echo -e "ALGO=zstd\nPERCENT=50" | sudo tee /etc/default/zramswap
  sudo systemctl enable --now zramswap
  ```
- **Swapfile sizing:** Keep the disk-backed swap minimal (100–256 MB) to avoid wearing flash storage. When ZRAM is active,
  disable the default `/var/swap` by setting `CONF_SWAPSIZE=0` in `/etc/dphys-swapfile` and running `sudo systemctl disable --now dphys-swapfile`.
- **Power management:** If a PoE HAT supplies power, set the fan curve via `sudo raspi-config nonint do_fan 1 25 60` to
  engage cooling at 60 °C.

## Service enablement matrix

| Service | Action | Reason |
| --- | --- | --- |
| `ssh` | Enable | Primary access path; enforce key auth only. |
| `docker` | Enable | Hosts the backend container and optional agents. |
| `zramswap` | Enable | Provides RAM-backed swap. |
| `bluetooth` | Disable | Frees RAM and avoids RF noise when unused. |
| `hciuart` | Disable | Skip UART Bluetooth firmware when no BT devices are attached. |
| `triggerhappy` | Disable | Not needed on headless deployments. |
| `apt-daily.service` / `.timer` | Leave enabled | Maintains security updates; pair with unattended-upgrades. |
| `cups` / GUI services | Do not install | Saves CPU/memory for mission services. |

Apply disables via `sudo systemctl disable --now <service>` and confirm the changes after reboot.

## Bootstrap workflow on the Pi

Perform software setup as the `vtoc` user over SSH:

1. Clone the repository and move into it:
   ```bash
   git clone https://github.com/PR-CYBR/vTOC.git
   cd vTOC
   ```
2. Run the unified bootstrap targeting headless defaults:
   ```bash
   python3 -m scripts.bootstrap_cli setup local --headless --prefer-remote-supabase  # delegates Postgres to Supabase
   ```
   - `--headless` skips desktop prompts and assumes SSH-only access.
   - `--prefer-remote-supabase` leaves `DATABASE_URL` pointed at Supabase so the Pi avoids running Postgres locally.
3. Review `.env.station` for the assigned station role and copy it into `/etc/vtoc/`:
   ```bash
   sudo install -d -m 750 /etc/vtoc
   sudo install -m 640 .env.station /etc/vtoc/.env.station
   ```
4. Start the backend container stack with resource-conscious defaults:
   ```bash
   python3 -m scripts.bootstrap_cli compose up --profile low-power
   ```
   The low-power profile pins the backend, skips local Postgres, and keeps optional scrapers disabled unless explicitly requested.

## Operational notes

- Monitor CPU temperature with `watch -n 5 vcgencmd measure_temp` during the first mission to confirm the cooler sizing.
- Leverage `journalctl -u docker` and `docker stats` to catch runaway containers early.
- Use `sudo systemctl mask getty@tty1.service` if the Pi is permanently headless to reclaim a few MB of RAM.
- Schedule quarterly reboots after `apt` upgrades to pick up kernel and firmware changes.

With these defaults the Pi 5 stays within 2–3 GB RAM usage during normal operations while delegating data persistence to Supabase.
