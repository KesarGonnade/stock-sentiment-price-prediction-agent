# Stock Market Sentiment Intelligence & Price Prediction Agent

A Python-based stock market sentiment analysis and next-trading-session price prediction project covering **Hong Kong (HKEX)** and **South Korea (KRX)** markets.

The system collects financial news and social media discussions, classifies sentiment using a locally running Large Language Model (LLM), combines sentiment with historical stock market data, and evaluates a Ridge Regression model for predicting the next trading session's closing price.

## 🌐 Live Dashboard

Explore the interactive dashboard here:

[**View Live Dashboard**](https://kesargonnade.github.io/stock-sentiment-price-prediction-agent/)

---

## 1. Project Objectives

- Collect stock-related discussions from multiple social media sources.
- Collect financial news using Exa.
- Analyze text to identify relevant stock-related sentiment.
- Classify sentiment as positive, negative, or neutral.
- Combine sentiment observations with historical market data.
- Engineer market indicators and sentiment features.
- Predict the next available trading session's closing price.
- Evaluate model performance against a naïve baseline.
- Generate a visual report ranking stocks by mentions and sentiment.

## 2. Markets and Stocks Covered

### Hong Kong Stock Exchange (HKEX)

| Company | Ticker |
|---|---|
| Tencent Holdings | 0700.HK |
| Alibaba Group | 9988.HK |
| HSBC Holdings | 0005.HK |
| Xiaomi Corporation | 1810.HK |
| BYD Company | 1211.HK |

### South Korea Exchange (KRX)

| Company | Ticker |
|---|---|
| Samsung Electronics | 005930.KS |
| SK Hynix | 000660.KS |
| Hyundai Motor | 005380.KS |
| LG Energy Solution | 373220.KS |
| Kakao | 035720.KS |

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Data Processing | Python CSV, JSON, Statistics |
| Social Media Collection | Apify |
| Financial News Collection | Exa API |
| Sentiment Analysis | Ollama |
| Local LLM | Qwen 2.5:3b |
| Market Data | Yahoo Finance Chart API |
| Prediction Model | Ridge Regression |
| Visualization | HTML, CSS |
| Development Environment | VS Code |
| Version Control | Git and GitHub |

The implementation uses Python's built-in CSV and data-processing modules for the core pipeline, avoiding reliance on Pandas and NumPy.

## 4. System Architecture

The project follows a multi-stage data pipeline:

1. **Data Collection**
   - Collect social media posts using Apify.
   - Collect financial news using Exa.
   - Retrieve historical OHLCV stock market data.

2. **Data Preprocessing**
   - Normalize records from different sources.
   - Standardize timestamps and stock identifiers.
   - Review the relevance of collected content.
   - Remove irrelevant records from sentiment analysis.

3. **Sentiment Analysis**
   - Use Ollama with Qwen 2.5:3b.
   - Classify relevant content into positive, negative, and neutral sentiment.
   - Generate sentiment scores and explanations.

4. **Feature Engineering**
   - Calculate daily returns.
   - Calculate Simple Moving Averages (SMA 5 and SMA 20).
   - Calculate volatility.
   - Calculate volume changes.
   - Aggregate sentiment by trading session.

5. **Data Integration**
   - Combine daily sentiment observations with market features.
   - Prepare the next-trading-session closing price as the prediction target.

6. **Price Prediction**
   - Train a Ridge Regression model.
   - Use chronological training and testing.
   - Compare its performance with a zero-return baseline.

7. **Visualization**
   - Generate an HTML dashboard.
   - Display stock rankings, sentiment information, market indicators, and historical prediction results.

## 5. Data Sources

| Source | Purpose |
|---|---|
| Telegram | Stock-related discussions and updates |
| Naver Finance | South Korean stock discussions |
| YouTube | Additional stock-related discussions |
| LIHKG | Hong Kong discussion data |
| Exa | Financial news articles |
| Yahoo Finance Chart API | Historical market prices and volume |

The collected dataset contains records from multiple sources. Coverage is uneven across stocks and platforms, so the results should not be interpreted as representative of all investors.

## 6. Prediction Methodology

The prediction target is the next available trading session's closing return.

The model uses the following features:

- Daily Return Percentage
- Close versus SMA 5
- Close versus SMA 20
- Average Sentiment Score

The target return is calculated as:

`((Next Session Close - Current Close) / Current Close) × 100`

The predicted closing price is calculated from the current closing price and predicted return.

The model uses chronological train-test splitting to preserve the time order of observations.

## 7. Model Evaluation

The initial evaluation produced the following results:

| Metric | Ridge Regression | Zero-Return Baseline |
|---|---:|---:|
| MAE | 3.2556% | 1.9873% |
| RMSE | 4.0327% | 2.8771% |
| Directional Accuracy | 21.43% | 42.86% |

**Important:** The baseline performed better than Ridge Regression in the initial evaluation. The dataset is small, with only 28 integrated observations and 14 held-out test predictions. These results demonstrate an experimental pipeline, not a reliable financial forecasting system.

## 8. Dashboard

The project generates an HTML report at:

`reports/stock_sentiment_report.html`

The dashboard includes:

- Project overview and sentiment statistics.
- Hong Kong stock mention rankings.
- South Korea stock mention rankings.
- Stock-wise sentiment and market analysis.
- Latest available closing prices.
- 20-session descriptive support and resistance levels.
- Model evaluation metrics.
- Historical actual versus predicted returns.
- Methodology and limitations.

## 9. Project Setup

### Prerequisites

- Python 3.11 or later recommended.
- Git.
- Ollama.
- Qwen 2.5:3b model.
- API credentials for the configured data sources.

### Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd hengseng_sentiment_agent
```

### Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### Install dependencies

Install the dependencies listed in the project's `requirements.txt`, if provided:

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file in the project root and configure the API credentials required by the collection scripts.

Never commit `.env` or expose API tokens in the repository.

### Start Ollama

Install and start Ollama, then download the model:

```bash
ollama pull qwen2.5:3b
```

## 10. Running the Pipeline

Run the scripts from the project root in the appropriate pipeline order.

Generate market features:

```bash
python src/feature_engineering/market_features.py
```

Normalize collected sentiment data:

```bash
python src/preprocessing/normalize_data.py
```

Run relevance classification and sentiment analysis using the configured scripts:

```bash
python src/preprocessing/ollama_relevance_classifier_v2.py
python src/preprocessing/ollama_sentiment_analyzer.py
```

Aggregate daily sentiment:

```bash
python src/preprocessing/daily_sentiment_aggregator.py
```

Integrate sentiment and market features:

```bash
python src/preprocessing/integrate_sentiment_market.py
```

Prepare the prediction dataset:

```bash
python src/preprocessing/prepare_prediction_dataset.py
```

Train and evaluate the prediction model:

```bash
python src/models/linear_regression_model.py
```

Generate the visual report:

```bash
python src/reporting/generate_visual_report.py
```

Open the generated report:

```powershell
Start-Process reports/stock_sentiment_report.html
```

Data collection scripts require valid API credentials and may incur usage or API costs. Existing processed datasets can be used to reproduce the downstream pipeline without recollecting the original data.

## 11. Limitations

- The dataset contains a limited number of sentiment-market observations.
- Social media coverage is uneven across companies and exchanges.
- Some collected discussions may be news updates rather than investor opinions.
- Sentiment classification is performed by a small local language model and may contain classification errors.
- Session assignment uses assumed exchange cutoffs; official exchange calendars and exact source availability times were not independently verified.
- Market data in the collected files ends on 10 November 2026.
- Support and resistance are descriptive historical levels, not guaranteed price barriers.
- The prediction model has not demonstrated better performance than the naïve baseline.

**This project is for educational and experimental purposes only. It is not financial advice.**

## 12. Future Improvements

- Increase the historical sentiment dataset.
- Improve the coverage and balance of social media sources.
- Validate timestamp alignment against official exchange calendars.
- Improve relevance and sentiment classification accuracy.
- Evaluate additional prediction approaches using appropriate time-series validation.
- Add automated data updates and scheduled report generation.
- Improve interactive dashboard visualizations.

## 13. License

Add an appropriate open-source license before publishing the repository.

---

**Project:** Stock Market Sentiment Intelligence & Price Prediction Agent  
**Markets:** Hong Kong and South Korea  
**Language:** Python