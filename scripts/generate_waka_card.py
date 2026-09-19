#!/usr/bin/env python3
import os
import sys
import json
import base64
import urllib.request
import urllib.error
from xml.sax.saxutils import escape

# Language color mapping matching github-stats-extended
LANG_COLORS = {
    "Dart": "#00B4AB",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#663399",
    "Python": "#3572A5",
    "C++": "#f34b7d",
    "Shell": "#89e051",
    "Markdown": "#083fa1",
    "JSON": "#292929",
    "YAML": "#cb171e",
    "PHP": "#4F5D95",
    "Rust": "#dea584",
    "Go": "#00ADD8",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Other": "#858585"
}

def get_api_key():
    key = os.environ.get("WAKATIME_API_KEY")
    if not key:
        cfg_path = os.path.expanduser("~/.wakatime.cfg")
        if os.path.exists(cfg_path):
            import configparser
            cfg = configparser.ConfigParser()
            cfg.read(cfg_path)
            key = cfg.get("settings", "api_key", fallback="")
    return key.strip() if key else ""

def fetch_data(api_key):
    user_id = "0a660cab-b061-4ee7-a358-4cc2b2f28437"
    public_url = f"https://wakatime.com/api/v1/users/{user_id}/stats?is_including_today=true"
    
    try:
        req = urllib.request.Request(public_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode())
            if "data" in res:
                return res["data"]
    except Exception as e:
        print(f"Public fetch failed: {e}, trying API key...", file=sys.stderr)

    if api_key:
        auth = base64.b64encode(api_key.encode()).decode()
        url = "https://wakatime.com/api/v1/users/current/stats/last_7_days?is_including_today=true"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Basic {auth}",
            "User-Agent": "WakaCardGenerator/1.0"
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode())
                return res.get("data", {})
        except Exception as e:
            print(f"Auth fetch failed: {e}", file=sys.stderr)

    return {}

def generate_svg(data):
    languages = data.get("languages", [])
    total_time = data.get("human_readable_total_including_other_language") or data.get("human_readable_total") or "0 mins"
    
    active_langs = [l for l in languages if l.get("percent", 0) > 0 or l.get("total_seconds", 0) > 0][:8]
    if not active_langs:
        active_langs = [{"name": "Coding Active", "percent": 100.0, "text": total_time}]

    total_pct = sum(l.get("percent", 0) for l in active_langs)
    if total_pct > 0:
        for l in active_langs:
            l["calc_pct"] = round((l.get("percent", 0) / total_pct) * 100, 2)
    else:
        for l in active_langs:
            l["calc_pct"] = round(100.0 / len(active_langs), 2)

    width = 300
    progress_width = 250
    progress_height = 8
    
    rects = []
    current_x = 0.0
    for l in active_langs:
        w = round((progress_width * l["calc_pct"]) / 100.0, 2)
        if w > 0:
            color = LANG_COLORS.get(l["name"], "#858585")
            rects.append(f'''        <rect
          mask="url(#rect-mask)"
          data-testid="lang-progress"
          x="{current_x}"
          y="0"
          width="{w}"
          height="{progress_height}"
          fill="{color}"
        />''')
            current_x += w

    items = []
    for i, l in enumerate(active_langs):
        color = LANG_COLORS.get(l["name"], "#858585")
        name = escape(l["name"])
        pct_str = f'{l["calc_pct"]:.1f}%'
        time_str = escape(l.get("text", ""))
        label = f"{name} {pct_str} ({time_str})" if time_str else f"{name} {pct_str}"
        items.append((color, label))

    # If odd number of items, add a balanced summary badge
    if len(items) % 2 == 1:
        items.append(("#00E5FF", f"Tracked: {total_time}"))

    col1 = []
    col2 = []
    for i, (color, label) in enumerate(items):
        item_svg = f'''    <g class="stagger" style="animation-delay: {450 + i*150}ms">
      <circle cx="5" cy="6" r="5" fill="{color}" />
      <text data-testid="lang-name" x="15" y="10" class="lang-name">
        {label}
      </text>
    </g>'''
        if i % 2 == 0:
            col1.append((i // 2 * 25, item_svg))
        else:
            col2.append((i // 2 * 25, item_svg))

    col1_svg = "\n".join([f'<g transform="translate(0, {y})">\n{item}\n  </g>' for y, item in col1])
    col2_svg = "\n".join([f'<g transform="translate(0, {y})">\n{item}\n  </g>' for y, item in col2])

    card_height = 215

    svg = f'''<svg
  width="{width}"
  height="{card_height}"
  viewBox="0 0 {width} {card_height}"
  fill="none"
  xmlns="http://www.w3.org/2000/svg"
  role="img"
  aria-labelledby="descId"
>
  <title id="titleId">Weekly Coding Activity (WakaTime)</title>
  <desc id="descId">Tracked development velocity and language metrics</desc>
  <style>
    .header {{
      font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif;
      fill: #00FF7F;
      animation: fadeInAnimation 0.8s ease-in-out forwards;
    }}
    @supports(-moz-appearance: auto) {{
      .header {{ font-size: 15.5px; }}
    }}
    
    @keyframes slideInAnimation {{
      from {{ width: 0; }}
      to {{ width: calc(100% - 100px); }}
    }}
    @keyframes growWidthAnimation {{
      from {{ width: 0; }}
      to {{ width: 100%; }}
    }}
    .stat {{
      font: 600 14px 'Segoe UI', Ubuntu, "Helvetica Neue", Sans-Serif; fill: #c9d1d9;
    }}
    @supports(-moz-appearance: auto) {{
      .stat {{ font-size: 12px; }}
    }}
    .bold {{ font-weight: 700 }}
    .lang-name {{
      font: 400 11px "Segoe UI", Ubuntu, Sans-Serif;
      fill: #c9d1d9;
    }}
    .stagger {{
      opacity: 0;
      animation: fadeInAnimation 0.3s ease-in-out forwards;
    }}
    #rect-mask rect {{
      animation: slideInAnimation 1s ease-in-out forwards;
    }}
    .lang-progress {{
      animation: growWidthAnimation 0.6s ease-in-out forwards;
    }}
    .progress-background {{ fill: #ddd; }}
    
    @keyframes scaleInAnimation {{
      from {{ transform: translate(-5px, 5px) scale(0); }}
      to {{ transform: translate(-5px, 5px) scale(1); }}
    }}
    @keyframes fadeInAnimation {{
      from {{ opacity: 0; }}
      to {{ opacity: 1; }}
    }}
  </style>

  <rect
    data-testid="card-bg"
    class="card-bg"
    x="0.5"
    y="0.5"
    rx="4.5"
    height="99%"
    stroke="#e4e2e2"
    width="{width - 1}"
    fill="#0D1117"
    stroke-opacity="0"
  />

  <g data-testid="card-title" transform="translate(25, 35)">
    <g transform="translate(0, 0)">
      <text x="0" y="0" class="header" data-testid="header">Weekly Coding Activity</text>
    </g>
  </g>

  <g data-testid="main-card-body" transform="translate(0, 55)">
    <svg data-testid="lang-items" x="25">
      <mask id="rect-mask">
        <rect x="0" y="0" width="{progress_width}" height="{progress_height}" fill="white" rx="5"/>
      </mask>
      
{chr(10).join(rects)}

      <g transform="translate(0, 25)">
        <g transform="translate(0, 0)">
{col1_svg}
        </g>
        <g transform="translate(150, 0)">
{col2_svg}
        </g>
      </g>
    </svg>
  </g>
</svg>
'''
    return svg

def main():
    api_key = get_api_key()
    data = fetch_data(api_key)
    svg_content = generate_svg(data)
    
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "wakatime-card.svg")
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    print(f"Successfully generated matching WakaTime card: {out_path}")

if __name__ == "__main__":
    main()
