#!/opt/openclaw-venv/bin/python3
"""
OpenClaw + Open Interpreter integration.
Uses OpenRouter Gemini via the container venv as the LLM backend.
"""

import os
import sys
from pathlib import Path

# Load environment variables from openclaw/.env
_env_file = Path(__file__).parent / "openclaw" / ".env"
if _env_file.exists():
    with open(_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

# Required: OpenRouter API key from openclaw/.env (use Gemini via OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
if not OPENROUTER_API_KEY:
    print("[ERROR] OPENROUTER_API_KEY not found. Check openclaw/.env file.")
    sys.exit(1)

# Configure open-interpreter to talk to OpenRouter (Google Gemini)
os.environ["OPENAI_API_KEY"] = OPENROUTER_API_KEY
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

try:
    import interpreter as oi_module
    from interpreter import interpreter
except ImportError as e:
    print(f"[ERROR] Cannot import open-interpreter: {e}")
    print("Run: python3 -m pip install open-interpreter")
    sys.exit(1)

# Configure the interpreter
interpreter.llm.model = "openrouter/google/gemini-2.0-flash-lite-001"
interpreter.llm.api_key = OPENROUTER_API_KEY
interpreter.llm.api_base = "https://openrouter.ai/api/v1"
interpreter.llm.context_window = 64000
interpreter.llm.max_tokens = 4096
interpreter.llm.supports_functions = True

# Set safe mode and project context
interpreter.auto_run = True           # Auto-run generated code blocks to allow tool execution
interpreter.safe_mode = "none"      # minimized prompts to enable automated runs (use with caution)
interpreter.system_message = """
You are OpenClaw's AI assistant powered by Google Gemini (via OpenRouter).
You help with:
- Data processing and analysis using pandas
- OSM and Census data synchronization
- Operations and DevOps automation tasks
- Excel/CSV data merging and transformation

Working directory: /home/node/.openclaw
Python environment: /opt/openclaw-venv/bin/python3

## Available Libraries
- pandas 3.0.2       — DataFrame operations, merge, groupby, pivot
- openpyxl 3.1.5     — Read/write .xlsx files (Excel 2010+)
- numpy 2.4.4        — Numerical computation
- requests 2.33.1    — HTTP API calls
- seaborn 0.13.2     — Statistical data visualization (heatmap, barplot, boxplot, etc.)
- matplotlib 3.10.8  — Low-level plotting and chart export
- plotly 6.7.0       — Interactive charts (HTML output); use plotly.express for quick charts

## Key Data Files (F:\\vs-code-openclaw\\data\\ExcelData\\)
- 当前告警.xlsx       — 4434 rows × 9 cols: 告警等级,告警标题,告警对象,IP地址,处理状态,告警类型,告警时间,持续时间,通知结果
- 资产信息.xlsx       — 1235 rows × 5 cols: 资产类型,资产子类型,IP地址,资产状态,业务系统
- exportInstanceList.csv — asset export list
- 告警资产关联分析表_已完成.xlsx — merged output (4434 rows × 11 cols, 77.6% match rate)

## Plotly Patterns
```python
import plotly.express as px
from pathlib import Path

DATA_DIR = Path(r"F:\\vs-code-openclaw\\data\\ExcelData")

# Interactive bar chart - asset status
status_counts = result['资产状态'].value_counts().reset_index()
status_counts.columns = ['状态', '数量']
fig = px.bar(status_counts, x='状态', y='数量', title='资产状态分布', color='状态')
fig.write_html(str(DATA_DIR / 'asset_status.html'))  # open in browser

# Interactive pie chart
fig2 = px.pie(status_counts, names='状态', values='数量', title='资产状态占比')
fig2.write_html(str(DATA_DIR / 'asset_pie.html'))

# Interactive scatter
fig3 = px.scatter(result, x='告警时间', y='IP地址', color='资产状态', hover_data=['告警标题'])
fig3.write_html(str(DATA_DIR / 'alarm_scatter.html'))
```

## Matplotlib Patterns
```python
import matplotlib
matplotlib.use('Agg')          # Must set BEFORE importing pyplot on Windows
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path

DATA_DIR = Path(r"F:\\vs-code-openclaw\\data\\ExcelData")

# Optional: enable Chinese characters
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# Multi-panel figure
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Panel 1: bar chart
status_counts = result['资产状态'].value_counts()
axes[0].bar(status_counts.index, status_counts.values, color='steelblue')
axes[0].set_title('资产状态分布')
axes[0].set_xlabel('状态')
axes[0].set_ylabel('数量')

# Panel 2: time series line
result['告警时间_dt'] = pd.to_datetime(result['告警时间'])
daily = result.set_index('告警时间_dt').resample('D').size()
axes[1].plot(daily.index, daily.values, marker='o', color='tomato')
axes[1].set_title('每日告警趋势')
plt.xticks(rotation=30)

plt.tight_layout()
plt.savefig(DATA_DIR / 'analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved:', DATA_DIR / 'analysis.png')
```

## Seaborn/Matplotlib Patterns
```python
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for Windows
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path(r"F:\\vs-code-openclaw\\data\\ExcelData")

# Bar chart - asset status distribution
status_counts = result['资产状态'].value_counts()
sns.barplot(x=status_counts.index, y=status_counts.values)
plt.title('资产状态分布')
plt.tight_layout()
plt.savefig(DATA_DIR / 'asset_status.png', dpi=150)
plt.close()

# Heatmap - alarm count by hour
result['小时'] = pd.to_datetime(result['告警时间']).dt.hour
hour_status = result.pivot_table(index='小时', columns='资产状态', aggfunc='size', fill_value=0)
sns.heatmap(hour_status, annot=True, fmt='d', cmap='YlOrRd')
plt.savefig(DATA_DIR / 'alarm_heatmap.png', dpi=150)
plt.close()
```

## Excel Processing Patterns
```python
import pandas as pd, openpyxl
from pathlib import Path

DATA_DIR = Path(r"F:\\vs-code-openclaw\\data\\ExcelData")

# Read Excel
alarm_df  = pd.read_excel(DATA_DIR / "当前告警.xlsx")
asset_df  = pd.read_excel(DATA_DIR / "资产信息.xlsx")

# Read CSV with Chinese encoding
csv_df = pd.read_csv(DATA_DIR / "exportInstanceList.csv", encoding="utf-8-sig")

# Left merge on IP
result = pd.merge(alarm_df, asset_df[["IP地址","资产状态","业务系统"]],
                  on="IP地址", how="left")

# Save output
result.to_excel(DATA_DIR / "output.xlsx", index=False)
```

Use the container Python at /usr/bin/python3 when running scripts.
Always use encoding='utf-8-sig' for CSV files with Chinese characters.
"""

print("=" * 60)
print(" OpenClaw + Open Interpreter (OpenRouter / Gemini)")
print("=" * 60)
print(f" Model  : openrouter/google/gemini-2.0-flash-lite-001")
print(f" API    : https://openrouter.ai/api/v1")
print(f" Key    : {OPENROUTER_API_KEY[:8]}{'*' * 16}{OPENROUTER_API_KEY[-4:]}")
print(f" Safety : Auto-run enabled (interpreter.auto_run=True)")
print("=" * 60)
print(" Type your request. Type 'exit' to quit.\n")

def main():
    if len(sys.argv) > 1:
        # Non-interactive mode: pass command line args as prompt
        prompt = " ".join(sys.argv[1:])
        print(f"Running: {prompt}\n")
        result = chat_with_retries(prompt)
        print(result)
    else:
        # Interactive chat mode - wrap to add retry behavior
        try:
            while True:
                interpreter.chat()
                # after interactive runs, ensure data files are node-owned if possible
                try:
                    os.system("chown -R node:node /home/node/.openclaw/data 2>/dev/null || true")
                except Exception:
                    pass
        except KeyboardInterrupt:
            print('\nExiting.')


def chat_with_retries(prompt, retries=3):
    """Call interpreter.chat with simple retry logic to handle transient provider errors."""
    for attempt in range(1, retries + 1):
        try:
            res = interpreter.chat(prompt)
            # detect provider finish_reason errors in returned string
            if isinstance(res, str) and 'Provider finish_reason: error' in res:
                raise RuntimeError('provider_error')
            # after a successful run, attempt to fix permissions
            try:
                os.system("chown -R node:node /home/node/.openclaw/data 2>/dev/null || true")
            except Exception:
                pass
            return res
        except Exception as e:
            print(f"[WARN] chat attempt {attempt} failed: {e}")
            if attempt < retries:
                import time
                time.sleep(2 ** attempt)
                print("[INFO] retrying...")
                continue
            else:
                print("[ERROR] all retries failed, returning last error message")
                raise

if __name__ == "__main__":
    main()
