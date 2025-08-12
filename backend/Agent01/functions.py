import re
import pandas as pd
import os
import io
import random
import base64
import matplotlib.pyplot as plt
from pandas.api.types import (
    is_numeric_dtype,
    is_datetime64_any_dtype,
)
from config import settings
import logging
import time
import json
from datetime import datetime
from openai import OpenAI, OpenAIError
import openai

# --- Globals & Configuration ---
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("finbot")
from config import settings
client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = (
    # System prompt for OpenAI agent
    "You are Abacus, an AI financial advisor."
    "If a user ever asks for any advice or suggestions, make sure to assist and guide them properly."
    "Always express monetary values in UK pounds sterling (symbol '£', code 'GBP')."
    "If the source data uses another currency, first convert amounts approximately to GBP and mention the assumed rate in parentheses."
    "Never display any currency symbol other than £."
    "◆ **Transaction cleansing & categorisation**\n"
    "  1. Trim whitespace, drop emojis, fix double-spaces, make merchant/payee lower-case for matching.\n"
    "     • Groceries  • Utilities  • Housing  • Transport  • Health\n"
    "     • Dining & Entertainment  • Subscriptions  • Education  • Income\n"
    "     • Transfers  • Other\n"
    "  3. If a transaction is truly ambiguous, label it 'Uncategorised' and flag it.\n\n"
    "◆ **Aggregation guidance**\n"
    "  • Whenever the user asks for a *summary*, *spending*, or *break-down*, "
    "aggregate totals by category **and** by any date range mentioned (inclusive).\n"
    "  • Respond with a Markdown table: | Category | Total £ | % of total |, sorted by highest spend.\n"
    "  • Provide short insights: which 3 categories dominate, any unusual spikes, etc.\n\n"
    "◆ **Data cleansing for charts**\n"
    "  • Before plotting, drop rows where either column is null, non-numeric, or negative.\n"
    "  • Clamp any value outside the 1st–99th percentile to the nearest boundary and flag it.\n"
    "  • Round all numeric values to two decimal places.\n"
    "  • If fewer than 3 valid data points remain, output:\n"
    "      { \"action\": \"error\", \"message\": \"Not enough valid data to plot.\" }\n\n"
    "◆ Column-picking rule\n"
    "  • If the user asks for a chart of *spending*, *expenses*, *income*, or similar "
    "and supplies only categorical columns, automatically choose the most suitable "
    "numeric column:\n"
    "      1. Prefer any column whose name contains 'amount', 'total', 'cost', "
    "         'value', 'balance', or 'price' (case-insensitive).\n"
    "      2. Otherwise pick the numeric column with the largest absolute sum.\n"
    "  • Include that numeric column in the JSON you return so the backend can "
    "    aggregate the data correctly.\n\n"
    "---\n"
    "When the user explicitly asks for a bar, pie or line chart, respond **only** with this JSON (no extra words, no Markdown):\n"
    "{\n"
    "  \"action\":  \"plot\",\n"
    "  \"kind\":    \"bar | pie | line\",\n"
    "  \"columns\": [\"ColA\", \"ColB\"],\n"
    "  \"title\":   \"Optional title\",\n"
    "  \"data\":    [ {\"ColA\": value1, \"ColB\": value2}, … ]\n"
    "}\n"
    "Do **not** wrap the JSON in back-ticks.\n\n"
    f"Reply in clear, friendly language. current date and time {now}"
)

_CURRENCY_RE = re.compile(r"[^\d.,\-]")
_MONEY_RE = re.compile(r"(amount|cost|price|total|value|balance|paid|spend|debit|credit)", re.I)

# --- Data Cleaning Utilities ---
def coerce_numeric(col: pd.Series) -> pd.Series:
    """Try VERY HARD to turn a column into floats."""
    if pd.api.types.is_numeric_dtype(col):
        return col
    if pd.api.types.is_datetime64_any_dtype(col):
        return col
    if pd.api.types.is_bool_dtype(col):
        return col.astype("int64")
    if col.dtype == "object":
        cleaned = (
            col.astype(str)
               .str.replace(_CURRENCY_RE, "", regex=True)
               .str.replace(",", "")
        )
        nums = pd.to_numeric(cleaned, errors="coerce")
        if nums.notna().mean() >= 0.10:
            return nums
    return col

def read_excel_any(data: bytes, filename: str) -> pd.DataFrame:
    """Read any Excel or CSV file and coerce columns to numeric if possible."""
    ext = os.path.splitext(filename)[-1].lower()
    if ext == ".csv":
        try:
            return pd.read_csv(io.BytesIO(data))
        except UnicodeDecodeError:
            return pd.read_csv(io.BytesIO(data), encoding="latin-1")
    engine_hint = {
        ".xlsx": "openpyxl",
        ".xls":  "xlrd",
        ".xlsm": "openpyxl",
        ".ods":  "odf",
    }.get(ext)
    df = pd.read_excel(io.BytesIO(data), engine=engine_hint)
    df = df.apply(coerce_numeric)
    return df

# --- DataFrame Summary & Sampling ---
def summarise_dataframe(df: pd.DataFrame) -> dict:
    """Return summary statistics for a DataFrame."""
    summary = {
        "num_rows": int(df.shape[0]),
        "num_columns": int(df.shape[1]),
        "columns": [],
    }
    for col in df.columns:
        s = df[col]
        info = {
            "name": str(col),
            "dtype": str(s.dtype),
            "nulls": int(s.isna().sum()),
        }
        if pd.api.types.is_numeric_dtype(s):
            nums = pd.to_numeric(s, errors="coerce")
            info.update(
                min=float(nums.min()),
                max=float(nums.max()),
                mean=float(nums.mean()),
                sum=float(nums.sum()),
            )
        else:
            top = s.value_counts(dropna=True).head(5).to_dict()
            info["top_values"] = {str(k): int(v) for k, v in top.items()}
        summary["columns"].append(info)
    return summary

def sample_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return a random sample of the DataFrame within configured row limits."""
    n = max(settings.SAMPLE_MIN_ROWS,
            min(settings.SAMPLE_MAX_ROWS, len(df)))
    if len(df) <= n:
        return df
    random.seed(42)
    return df.iloc[random.sample(range(len(df)), n)]

# --- OpenAI API Utilities ---
def _with_system_prompt(messages: list[dict]) -> list[dict]:
    """Ensure SYSTEM_PROMPT is the first message exactly once."""
    if not messages or SYSTEM_PROMPT not in messages[0].get("content", ""):
        return [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    return messages

def call_openai(messages: list[dict]) -> str:
    """Wrapper that injects the system prompt and returns the assistant's reply."""
    prepared = _with_system_prompt(messages)
    for attempt in range(4):
        try:
            logger.info("Prompt sent to OpenAI:\n%s", json.dumps(prepared, indent=2, ensure_ascii=False))
            resp = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=prepared,
                temperature=0.3,
            )
            return resp.choices[0].message.content
        except OpenAIError as e:
            logger.error("OpenAI error: %s", e)
            time.sleep(2 ** attempt)
    raise RuntimeError("OpenAI API failure after retries")

# --- DataFrame Column Utilities ---
def _split_cols(df: pd.DataFrame, cols: list[str]) -> tuple[list[str], list[str]]:
    """Return (categoricals, numerics) preserving user order."""
    cats, nums = [], []
    for c in cols:
        if c not in df.columns:
            continue
        (nums if is_numeric_dtype(df[c]) else cats).append(c)
    return cats, nums

def _all_numeric(df: pd.DataFrame) -> list[str]:
    """Return all numeric columns in the DataFrame."""
    return [c for c in df.columns if is_numeric_dtype(df[c])]

def _best_numeric(df: pd.DataFrame) -> str | None:
    """Pick the most likely 'money' column or the numeric with largest movement."""
    nums = _all_numeric(df)
    if not nums:
        return None
    for c in nums:
        if _MONEY_RE.search(c):
            return c
    return max(nums, key=lambda c: df[c].abs().sum())

# --- Chart Data Cleaning ---
def _clean_chart_data(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Clean chart data: drop nulls, clamp outliers, round, remove negatives."""
    df = df.dropna(subset=cols)
    for c in cols:
        if c not in df.columns or not is_numeric_dtype(df[c]):
            continue
        lower = df[c].quantile(0.01)
        upper = df[c].quantile(0.99)
        df[c] = df[c].clip(lower, upper).round(2)
        df = df[df[c] >= 0]
    return df

# --- Chart Creation ---
def make_chart(df: pd.DataFrame, kind: str, columns: list[str], prompt: str = "") -> str:
    """
    Create a PNG chart (bar, line, pie) and return it base-64 encoded.
    Cleans data before plotting. Returns error JSON if not enough valid data.
    """
    cols = [c for c in columns if c in df.columns]
    if not cols:
        raise ValueError(f"No valid columns among {columns}")

    df = _clean_chart_data(df, cols)
    if len(df) < 3:
        return json.dumps({"action": "error", "message": "Not enough valid data to plot."})

    fig, ax = plt.subplots()
    cats, nums = _split_cols(df, cols)

    # --- Bar/Line Chart Logic ---
    if kind in ("bar", "line"):
        if cats and len(cats) > 0 and is_datetime64_any_dtype(df[cats[0]]):
            plot_df = df.set_index(cats[0])[nums or _all_numeric(df)]
            plot_df.plot(kind=kind, ax=ax)
        elif cats and nums:
            gb = df.groupby(cats[0])[nums].sum()
            gb.plot(kind=kind, ax=ax)
        elif not nums and cats:
            maybe = _best_numeric(df)
            if maybe:
                series = df.groupby(cats[0])[maybe].sum()
                series.plot(kind=kind, ax=ax)
                nums = [maybe]
            else:
                df[cats[0]].value_counts().plot(kind="bar", ax=ax)
        elif nums:
            df[nums].plot(kind=kind, ax=ax)

    # --- Pie Chart Logic ---
    elif kind == "pie":
        if cats and not nums:
            best_num = _best_numeric(df)
            nums = [best_num] if best_num else []
        if cats and nums:
            series = df.groupby(cats[0])[nums[0]].sum()
        elif cats:
            series = df[cats[0]].value_counts()
        elif nums:
            series = df[nums[0]].value_counts()
        else:
            return json.dumps({"action": "error", "message": "Not enough valid data to plot."})

        # Handle negatives for spending/expense/outflow
        if any(w in prompt.lower() for w in ("spend", "expense", "outflow")):
            series = series[series < 0]
        if (series < 0).all():
            series = -series
        elif (series < 0).any():
            series = series.abs()
        series = series[series != 0]
        if len(series) < 3:
            return json.dumps({"action": "error", "message": "Not enough valid data to plot."})
        series.plot(kind="pie", autopct="%1.1f%%", ax=ax)

    else:
        raise ValueError(f"Unsupported chart type: {kind}")

    ax.set_title(f"{kind.title()} – {', '.join(cols or nums)}")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()