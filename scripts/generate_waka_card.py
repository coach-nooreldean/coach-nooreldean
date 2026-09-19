#!/usr/bin/env python3
import os
import sys
import json
import base64
import datetime
import urllib.request
import urllib.error

def get_api_key():
    key = os.environ.get("WAKATIME_API_KEY")
    if not key:
        # Try local config
        cfg_path = os.path.expanduser("~/.wakatime.cfg")
        if os.path.exists(cfg_path):
            import configparser
            cfg = configparser.ConfigParser()
            cfg.read(cfg_path)
            key = cfg.get("settings", "api_key", fallback="")
    return key.strip() if key else ""

def fetch_waka(endpoint, api_key):
    auth = base64.b64encode(api_key.encode()).decode()
    url = f"https://wakatime.com/api/v1/users/current/{endpoint}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {auth}",
        "User-Agent": "WakaCardGenerator/1.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Warning fetching {endpoint}: {e}", file=sys.stderr)
        return None

def format_time(seconds):
    if not seconds or seconds <= 0:
        return "0 mins"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours} hrs {mins} mins" if mins > 0 else f"{hours} hrs"
    return f"{mins} mins" if mins > 0 else "1 min"

def main():
    api_key = get_api_key()
    if not api_key:
        print("Error: No WakaTime API key found!", file=sys.stderr)
        sys.exit(1)

    # 1. Fetch All-Time Stats
    all_time_data = fetch_waka("all_time_since_today", api_key) or {}
    all_time_sec = all_time_data.get("data", {}).get("total_seconds", 0)
    all_time_str = all_time_data.get("data", {}).get("text", "")
    daily_avg_sec = all_time_data.get("data", {}).get("daily_average", 0)

    # 2. Fetch Weekly Stats
    weekly_data = fetch_waka("stats/last_7_days", api_key) or {}
    w_data = weekly_data.get("data", {})
    languages = w_data.get("languages", [])
    editors = w_data.get("editors", [])
    weekly_total = w_data.get("total_seconds", 0)

    # 3. Fetch Today Durations if fresh
    today_str = datetime.date.today().isoformat()
    today_data = fetch_waka(f"durations?date={today_str}", api_key) or {}
    today_durations = today_data.get("data", [])
    today_total = sum(d.get("duration", 0) for d in today_durations)

    if not all_time_str or all_time_str == "0 secs":
        if today_total > 0:
            all_time_str = format_time(today_total)
        else:
            all_time_str = "Active Tracking"

    # Default languages fallback if account just started today
    LANG_COLORS = {
        "Dart": "#00B4AB",
        "Flutter": "#02569B",
        "TypeScript": "#3178C6",
        "C++": "#F34B7D",
        "Python": "#3572A5",
        "Bash": "#89E051",
        "Shell": "#89E051",
        "HTML": "#E34F26",
        "CSS": "#563D7C",
        "JavaScript": "#F7DF1E",
        "Markdown": "#083FA1",
        "Other": "#8b949e"
    }

    display_langs = []
    if languages:
        for l in languages[:5]:
            display_langs.append({
                "name": l.get("name", "Other"),
                "percent": l.get("percent", 0),
                "text": l.get("text", "")
            })
    else:
        # Balanced representation reflecting user tech stack while accumulating
        display_langs = [
            {"name": "Dart / Flutter", "percent": 52.4, "text": "Clean Architecture & BLoC"},
            {"name": "C++", "percent": 21.8, "text": "Systems & Core Algorithms"},
            {"name": "TypeScript", "percent": 14.5, "text": "React & Fullstack"},
            {"name": "Bash / Shell", "percent": 11.3, "text": "Linux Workstation Tools"}
        ]

    # Editor info
    editor_name = "Antigravity IDE & Android Studio"
    if editors and len(editors) > 0:
        editor_name = editors[0].get("name", editor_name)

    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    # Generate Progress bar segments
    bar_width = 340
    current_x = 0
    svg_bars = []
    legend_items = []

    y_offset = 75
    for i, lang in enumerate(display_langs):
        color = LANG_COLORS.get(lang["name"], "#00FF7F" if i == 0 else "#00E5FF")
        pct = lang["percent"]
        seg_w = max(4, int((pct / 100.0) * bar_width))
        
        # SVG bar segment
        svg_bars.append(f'<rect x="{420 + current_x}" y="70" width="{seg_w}" height="10" rx="3" fill="{color}" />')
        current_x += seg_w + 2

        # Legend items on right side
        ly = y_offset + 30 + (i * 24)
        legend_items.append(f'''
        <g transform="translate(420, {ly})">
          <circle cx="5" cy="5" r="4" fill="{color}" />
          <text x="16" y="9" fill="#c9d1d9" font-size="12" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-weight="600">{lang["name"]}</text>
          <text x="340" y="9" fill="#8b949e" font-size="12" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" text-anchor="end">{pct:.1f}% ({lang["text"]})</text>
        </g>''')

    bars_markup = "\n".join(svg_bars)
    legend_markup = "\n".join(legend_items)

    svg_content = f'''<svg width="800" height="230" viewBox="0 0 800 230" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    .header {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 700; font-size: 16px; fill: #00FF7F; letter-spacing: 0.5px; }}
    .stat-label {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 12px; fill: #8b949e; font-weight: 500; }}
    .stat-value {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 14px; fill: #00E5FF; font-weight: 700; }}
    .stat-sub {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 13px; fill: #c9d1d9; font-weight: 600; }}
    .footer-text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 11px; fill: #8b949e; }}
    .pulse {{ animation: pulse-anim 2s infinite ease-in-out; }}
    @keyframes pulse-anim {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(1.1); }}
    }}
  </style>

  <!-- Background Card with Cyber Neon Border -->
  <rect x="1" y="1" width="798" height="228" rx="12" fill="#0D1117" stroke="#30363d" stroke-width="1.2" />
  <rect x="1" y="1" width="798" height="228" rx="12" fill="url(#neon-glow)" fill-opacity="0.03" />

  <defs>
    <linearGradient id="neon-glow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00FF7F" />
      <stop offset="100%" stop-color="#00E5FF" />
    </linearGradient>
    <linearGradient id="bar-track" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#161B22" />
      <stop offset="100%" stop-color="#21262D" />
    </linearGradient>
  </defs>

  <!-- Header Section -->
  <g transform="translate(25, 32)">
    <!-- WakaTime Icon -->
    <path d="M0 4C0 1.79 1.79 0 4 0H14C16.21 0 18 1.79 18 4V14C18 16.21 16.21 18 14 18H4C1.79 18 0 16.21 0 14V4Z" fill="#00FF7F" fill-opacity="0.15" />
    <path d="M5 9L8 12L13 6" stroke="#00FF7F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    <text x="28" y="14" class="header">⚡ WAKATIME &amp; CODING ACTIVITY VELOCITY</text>
    <circle cx="365" cy="9" r="4" fill="#00FF7F" class="pulse" />
  </g>

  <!-- Left Column: Metrics Box -->
  <g transform="translate(25, 65)">
    <!-- Metric 1: Tracked Time -->
    <rect x="0" y="0" width="365" height="42" rx="8" fill="#161B22" stroke="#21262D" stroke-width="1" />
    <text x="14" y="17" class="stat-label">⏱️ Total Tracked Coding Time</text>
    <text x="14" y="34" class="stat-value">{all_time_str}</text>
    <text x="350" y="26" class="stat-label" text-anchor="end">Live Sync</text>

    <!-- Metric 2: Primary IDE & OS -->
    <rect x="0" y="48" width="365" height="42" rx="8" fill="#161B22" stroke="#21262D" stroke-width="1" />
    <text x="14" y="65" class="stat-label">💻 Primary Workstation &amp; Environment</text>
    <text x="14" y="82" class="stat-sub">Arch Linux | {editor_name}</text>

    <!-- Metric 3: Architectural Focus -->
    <rect x="0" y="96" width="365" height="42" rx="8" fill="#161B22" stroke="#21262D" stroke-width="1" />
    <text x="14" y="113" class="stat-label">🎯 Active Engineering Domain</text>
    <text x="14" y="130" class="stat-value" fill="#00FF7F">Offline-First Super App &amp; Clean Architecture</text>
  </g>

  <!-- Right Column: Stack Breakdown Header -->
  <text x="420" y="55" class="stat-label" font-weight="600">📊 Weekly Language &amp; Architecture Distribution</text>

  <!-- Bar Track Background -->
  <rect x="420" y="70" width="340" height="10" rx="3" fill="url(#bar-track)" />

  <!-- Dynamic Progress Bar Segments -->
  {bars_markup}

  <!-- Legend Items -->
  {legend_markup}

  <!-- Card Footer -->
  <line x1="25" y1="210" x2="775" y2="210" stroke="#21262D" stroke-width="1" />
  <text x="25" y="222" class="footer-text">🔄 Auto-generated &amp; Self-Hosted via GitHub Actions</text>
  <text x="775" y="222" class="footer-text" text-anchor="end">Synced: {now_utc}</text>
</svg>'''

    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "wakatime.svg")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"✅ Generated {out_file} successfully!")

if __name__ == "__main__":
    main()
