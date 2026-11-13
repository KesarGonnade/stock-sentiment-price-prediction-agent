
import csv
import html
import statistics
from pathlib import Path
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"

INTEGRATED_FILE = DATA_DIR / "integrated_sentiment_market.csv"
PREDICTION_FILE = DATA_DIR / "prediction_results.csv"

OUTPUT_FILE = REPORT_DIR / "stock_sentiment_report.html"


def read_csv(path):
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def number(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe(value):
    return html.escape(str(value))


def sentiment_label(score):
    if score > 0.1:
        return "Bullish"
    if score < -0.1:
        return "Bearish"
    return "Neutral"


def money(value):
    if value is None:
        return "N/A"
    return f"{value:,.2f}"


def load_market_data():
    market = {}

    for path in DATA_DIR.glob("*_market_features.csv"):
        rows = read_csv(path)

        if not rows:
            continue

        ticker = rows[0]["Ticker"]
        rows.sort(key=lambda r: r["Date"])

        latest = rows[-1]
        recent = rows[-20:]

        market[ticker] = {
            "latest_date": latest["Date"],
            "close": number(latest["Close"]),
            "support": min(number(r["Low"]) for r in recent),
            "resistance": max(number(r["High"]) for r in recent),
        }

    return market


def load_stock_data():
    integrated = read_csv(INTEGRATED_FILE)
    predictions = read_csv(PREDICTION_FILE)
    market = load_market_data()

    # Latest available sentiment-market observation per stock.
    latest_sentiment = {}

    for row in integrated:
        ticker = row["Ticker"]

        if (
            ticker not in latest_sentiment
            or row["Date"] > latest_sentiment[ticker]["Date"]
        ):
            latest_sentiment[ticker] = row

    # Latest historical held-out prediction per stock.
    latest_prediction = {}

    for row in predictions:
        ticker = row["Ticker"]

        if (
            ticker not in latest_prediction
            or row["Date"] > latest_prediction[ticker]["Date"]
        ):
            latest_prediction[ticker] = row

    stocks = []

    for ticker, sentiment in latest_sentiment.items():

        market_info = market.get(ticker, {})
        prediction = latest_prediction.get(ticker)

        score = number(sentiment["Average_Sentiment_Score"])

        if prediction:
            predicted_return = number(
                prediction["Predicted_Return_Pct"]
            )
            predicted_close = number(
                prediction["Predicted_Next_Close"]
            )
            prediction_direction = (
                "Up" if predicted_return > 0
                else "Down" if predicted_return < 0
                else "Flat"
            )
        else:
            predicted_return = None
            predicted_close = None
            prediction_direction = "Not evaluated"

        stocks.append({
            "ticker": ticker,
            "name": sentiment["Stock_Name"],
            "exchange": sentiment["Exchange"],
            "sentiment_date": sentiment["Date"],
            "market_date": market_info.get("latest_date", "N/A"),
            "close": market_info.get("close"),
            "support": market_info.get("support"),
            "resistance": market_info.get("resistance"),
            "mentions": int(number(sentiment["Total_Mentions"])),
            "social": int(number(sentiment["Social_Mentions"])),
            "news": int(number(sentiment["News_Mentions"])),
            "positive": int(number(sentiment["Positive_Count"])),
            "negative": int(number(sentiment["Negative_Count"])),
            "neutral": int(number(sentiment["Neutral_Count"])),
            "sentiment_score": score,
            "sentiment_label": sentiment_label(score),
            "prediction_date": prediction["Date"] if prediction else "N/A",
            "predicted_return": predicted_return,
            "predicted_close": predicted_close,
            "prediction_direction": prediction_direction
        })

    return stocks, predictions


def make_mentions_chart(stocks, exchange):
    selected = sorted(
        [s for s in stocks if s["exchange"] == exchange],
        key=lambda s: s["mentions"],
        reverse=True
    )

    if not selected:
        return "<p>No data available.</p>"

    maximum = max(s["mentions"] for s in selected) or 1

    chart = ""

    for stock in selected:
        width = stock["mentions"] / maximum * 100

        chart += f"""
        <div class="bar-row">
            <div class="bar-label">{safe(stock['ticker'])}</div>
            <div class="bar-track">
                <div class="bar-fill" style="width:{width:.1f}%"></div>
            </div>
            <div class="bar-value">{stock['mentions']}</div>
        </div>
        """

    return chart


def make_stock_table(stocks, exchange):

    selected = [s for s in stocks if s["exchange"] == exchange]
    selected.sort(key=lambda s: s["mentions"], reverse=True)

    rows = ""

    for rank, stock in enumerate(selected, start=1):

        score_class = (
            "positive" if stock["sentiment_score"] > 0.1
            else "negative" if stock["sentiment_score"] < -0.1
            else "neutral"
        )

        predicted_return = (
            f"{stock['predicted_return']:.3f}%"
            if stock["predicted_return"] is not None
            else "N/A"
        )

        predicted_close = money(stock["predicted_close"])

        rows += f"""
        <tr>
            <td>{rank}</td>
            <td>
                <strong>{safe(stock['name'])}</strong>
                <div class="muted">{safe(stock['ticker'])}</div>
            </td>
            <td>{stock['mentions']}</td>
            <td>{stock['social']}</td>
            <td>{stock['news']}</td>
            <td>{stock['positive']}/{stock['negative']}/{stock['neutral']}</td>
            <td class="{score_class}">
                {stock['sentiment_score']:.3f}
                <div>{stock['sentiment_label']}</div>
            </td>
            <td>{money(stock['close'])}</td>
            <td>{money(stock['support'])}</td>
            <td>{money(stock['resistance'])}</td>
            <td>{predicted_return}</td>
            <td>{predicted_close}</td>
            <td>{safe(stock['prediction_direction'])}</td>
        </tr>
        """

    return rows


def calculate_metrics(predictions):

    if not predictions:
        return None

    actual = [
        number(r["Actual_Return_Pct"])
        for r in predictions
    ]

    predicted = [
        number(r["Predicted_Return_Pct"])
        for r in predictions
    ]

    baseline = [0.0] * len(actual)

    def metrics(target, forecast):
        errors = [
            p - a for a, p in zip(target, forecast)
        ]

        mae = sum(abs(e) for e in errors) / len(errors)

        rmse = (
            sum(e * e for e in errors) / len(errors)
        ) ** 0.5

        correct = sum(
            (a >= 0 and p >= 0) or (a < 0 and p < 0)
            for a, p in zip(target, forecast)
        )

        accuracy = correct / len(target) * 100

        return mae, rmse, accuracy

    return {
        "model": metrics(actual, predicted),
        "baseline": metrics(actual, baseline),
        "count": len(actual)
    }


def make_prediction_table(predictions):

    rows = ""

    predictions = sorted(
        predictions,
        key=lambda r: (r["Date"], r["Ticker"])
    )

    for row in predictions:

        actual = number(row["Actual_Return_Pct"])
        predicted = number(row["Predicted_Return_Pct"])

        rows += f"""
        <tr>
            <td>{safe(row['Date'])}</td>
            <td>{safe(row['Target_Date'])}</td>
            <td>{safe(row['Stock_Name'])}</td>
            <td>{actual:.3f}%</td>
            <td>{predicted:.3f}%</td>
            <td>{money(number(row['Actual_Next_Close']))}</td>
            <td>{money(number(row['Predicted_Next_Close']))}</td>
        </tr>
        """

    return rows


def build_report():

    if not INTEGRATED_FILE.exists():
        raise FileNotFoundError(
            f"Integrated dataset missing: {INTEGRATED_FILE}"
        )

    stocks, predictions = load_stock_data()

    if not stocks:
        raise ValueError("No stock data available for report.")

    hk = [s for s in stocks if s["exchange"] == "HKEX"]
    kr = [s for s in stocks if s["exchange"] == "KRX"]

    metrics = calculate_metrics(predictions)

    total_mentions = sum(s["mentions"] for s in stocks)
    positive = sum(s["positive"] for s in stocks)
    negative = sum(s["negative"] for s in stocks)
    neutral = sum(s["neutral"] for s in stocks)

    if metrics:
        model_mae, model_rmse, model_accuracy = metrics["model"]
        base_mae, base_rmse, base_accuracy = metrics["baseline"]

        metrics_html = f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <span>Ridge MAE</span>
                <strong>{model_mae:.3f}%</strong>
            </div>
            <div class="metric-card">
                <span>Baseline MAE</span>
                <strong>{base_mae:.3f}%</strong>
            </div>
            <div class="metric-card">
                <span>Ridge RMSE</span>
                <strong>{model_rmse:.3f}%</strong>
            </div>
            <div class="metric-card">
                <span>Ridge Directional Accuracy</span>
                <strong>{model_accuracy:.2f}%</strong>
            </div>
            <div class="metric-card">
                <span>Baseline Directional Accuracy</span>
                <strong>{base_accuracy:.2f}%</strong>
            </div>
            <div class="metric-card">
                <span>Historical Test Predictions</span>
                <strong>{metrics['count']}</strong>
            </div>
        </div>
        """
    else:
        metrics_html = "<p>No prediction results available.</p>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stock Market Sentiment Intelligence Report</title>

<style>
* {{ box-sizing: border-box; }}

body {{
    margin: 0;
    background: #f3f5f9;
    color: #202938;
    font-family: Arial, sans-serif;
}}

header {{
    background: #172554;
    color: white;
    padding: 35px 5%;
}}

header h1 {{ margin: 0 0 10px; }}

header p {{ color: #cbd5e1; margin: 0; }}

main {{
    max-width: 1500px;
    margin: auto;
    padding: 25px;
}}

section {{
    background: white;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 24px;
    box-shadow: 0 2px 9px rgba(0,0,0,.05);
}}

h2 {{ margin-top: 0; color: #172554; }}

.summary-grid, .metrics-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 15px;
}}

.summary-card, .metric-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px;
}}

.summary-card span, .metric-card span {{
    display: block;
    color: #64748b;
    font-size: 13px;
    margin-bottom: 9px;
}}

.summary-card strong, .metric-card strong {{
    font-size: 25px;
}}

.bar-row {{
    display: grid;
    grid-template-columns: 100px 1fr 35px;
    align-items: center;
    gap: 10px;
    margin: 12px 0;
}}

.bar-label {{ font-size: 13px; }}

.bar-track {{
    height: 15px;
    background: #e2e8f0;
    border-radius: 20px;
    overflow: hidden;
}}

.bar-fill {{
    height: 100%;
    background: #4169e1;
    border-radius: 20px;
}}

.bar-value {{ font-weight: bold; }}

.table-wrap {{ overflow-x: auto; }}

table {{
    border-collapse: collapse;
    width: 100%;
    min-width: 1250px;
    font-size: 13px;
}}

th, td {{
    text-align: left;
    padding: 12px 10px;
    border-bottom: 1px solid #e2e8f0;
    white-space: nowrap;
}}

th {{
    background: #f1f5f9;
    color: #334155;
}}

tr:hover {{ background: #f8fafc; }}

.muted {{
    color: #64748b;
    font-size: 11px;
    margin-top: 4px;
}}

.positive {{ color: #15803d; font-weight: bold; }}
.negative {{ color: #dc2626; font-weight: bold; }}
.neutral {{ color: #64748b; font-weight: bold; }}

.note {{
    background: #fff7ed;
    border-left: 4px solid #f59e0b;
    padding: 15px;
    line-height: 1.6;
    color: #7c2d12;
}}

footer {{
    text-align: center;
    color: #64748b;
    padding: 25px;
    font-size: 12px;
}}

@media print {{
    body {{ background: white; }}
    section {{ box-shadow: none; break-inside: avoid; }}
}}
</style>
</head>

<body>

<header>
    <h1>Stock Market Sentiment Intelligence</h1>
    <p>Hong Kong and South Korea | Historical market and sentiment analysis</p>
</header>

<main>

<section>
    <h2>Project Overview</h2>
    <div class="summary-grid">
        <div class="summary-card">
            <span>Stocks covered</span>
            <strong>{len(stocks)}</strong>
        </div>
        <div class="summary-card">
            <span>Total mentions in latest stock observations</span>
            <strong>{total_mentions}</strong>
        </div>
        <div class="summary-card">
            <span>Positive mentions</span>
            <strong>{positive}</strong>
        </div>
        <div class="summary-card">
            <span>Negative mentions</span>
            <strong>{negative}</strong>
        </div>
        <div class="summary-card">
            <span>Neutral mentions</span>
            <strong>{neutral}</strong>
        </div>
    </div>
</section>

<section>
    <h2>Hong Kong Stock Mention Rankings</h2>
    <p class="muted">Ranked by total mentions in each stock's latest available sentiment observation.</p>
    {make_mentions_chart(stocks, "HKEX")}
</section>

<section>
    <h2>South Korea Stock Mention Rankings</h2>
    <p class="muted">Ranked by total mentions in each stock's latest available sentiment observation.</p>
    {make_mentions_chart(stocks, "KRX")}
</section>

<section>
    <h2>Hong Kong Stock Analysis</h2>
    <div class="table-wrap">
    <table>
        <thead>
        <tr>
            <th>Rank</th><th>Stock</th><th>Mentions</th>
            <th>Social</th><th>News</th><th>Pos/Neg/Neu</th>
            <th>Avg Sentiment</th><th>Latest Close</th>
            <th>20-session Support</th><th>20-session Resistance</th>
            <th>Historical Predicted Return</th>
            <th>Historical Predicted Close</th><th>Predicted Direction</th>
        </tr>
        </thead>
        <tbody>{make_stock_table(stocks, "HKEX")}</tbody>
    </table>
    </div>
</section>

<section>
    <h2>South Korea Stock Analysis</h2>
    <div class="table-wrap">
    <table>
        <thead>
        <tr>
            <th>Rank</th><th>Stock</th><th>Mentions</th>
            <th>Social</th><th>News</th><th>Pos/Neg/Neu</th>
            <th>Avg Sentiment</th><th>Latest Close</th>
            <th>20-session Support</th><th>20-session Resistance</th>
            <th>Historical Predicted Return</th>
            <th>Historical Predicted Close</th><th>Predicted Direction</th>
        </tr>
        </thead>
        <tbody>{make_stock_table(stocks, "KRX")}</tbody>
    </table>
    </div>
</section>

<section>
    <h2>Model Evaluation</h2>
    <p>Ridge Regression compared with a zero-return naïve baseline.</p>
    {metrics_html}
    <div class="note">
        The model's predictions are historical held-out test predictions,
        not live forecasts. The dataset is very small, and the baseline
        performed better in the initial evaluation. Results should not be
        interpreted as reliable investment forecasts.
    </div>
</section>

<section>
    <h2>Historical Prediction Results</h2>
    <div class="table-wrap">
    <table>
        <thead>
        <tr>
            <th>Observation Date</th><th>Target Date</th><th>Stock</th>
            <th>Actual Return</th><th>Predicted Return</th>
            <th>Actual Close</th><th>Predicted Close</th>
        </tr>
        </thead>
        <tbody>{make_prediction_table(predictions)}</tbody>
    </table>
    </div>
</section>

<section>
    <h2>Methodology and Limitations</h2>
    <ul>
        <li>Social posts and financial news were collected from multiple sources.</li>
        <li>Sentiment was classified into positive, negative and neutral categories.</li>
        <li>Market features include daily returns, moving averages and volatility.</li>
        <li>Prediction target is the next available trading session's closing return.</li>
        <li>Support and resistance are descriptive 20-session low/high levels, not guaranteed price barriers.</li>
        <li>Sentiment and market observations cover a limited period and uneven number of records.</li>
        <li>Market data ends on 10 November 2026 in the collected files.</li>
        <li>Sentiment session assignment uses assumed exchange cutoffs; exact source availability times and official exchange calendars were not independently verified.</li>
        <li>Historical model performance does not establish future profitability or reliability.</li>
    </ul>
</section>

</main>

<footer>
    Generated from the project's local processed datasets.
    Historical analysis only — not investment advice.
</footer>

</body>
</html>
"""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(html_content, encoding="utf-8")

    print("\nVISUAL REPORT GENERATION")
    print("=" * 40)
    print("Stocks included:", len(stocks))
    print("Hong Kong stocks:", len(hk))
    print("South Korea stocks:", len(kr))
    print("Historical predictions:", len(predictions))
    print("Total latest-observation mentions:", total_mentions)
    print("\nReport saved:", OUTPUT_FILE)


if __name__ == "__main__":
    build_report()
