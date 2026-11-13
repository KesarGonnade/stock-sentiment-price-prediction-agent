
import csv
import math
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "data" / "processed" / "prediction_dataset.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "prediction_results.csv"

# Keep the feature count small because the dataset has only 28 rows.
FEATURES = [
    "Daily_Return_Pct",
    "Close_vs_SMA5_Pct",
    "Close_vs_SMA20_Pct",
    "Average_Sentiment_Score"
]

RIDGE_ALPHA = 1.0


def read_dataset():
    with open(DATA_FILE, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def solve_linear_system(matrix, vector):
    """Solve Ax = b using Gaussian elimination."""
    n = len(vector)
    augmented = [
        [float(matrix[i][j]) for j in range(n)] + [float(vector[i])]
        for i in range(n)
    ]

    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(augmented[r][i]))

        if abs(augmented[pivot][i]) < 1e-12:
            raise ValueError("Model matrix is singular.")

        augmented[i], augmented[pivot] = augmented[pivot], augmented[i]

        divisor = augmented[i][i]
        for j in range(i, n + 1):
            augmented[i][j] /= divisor

        for r in range(n):
            if r == i:
                continue

            factor = augmented[r][i]
            for j in range(i, n + 1):
                augmented[r][j] -= factor * augmented[i][j]

    return [augmented[i][n] for i in range(n)]


def standardize(train_x, test_x):
    """Calculate scaling parameters from training data only."""
    means = []
    scales = []

    for column in range(len(FEATURES)):
        values = [row[column] for row in train_x]
        mean = sum(values) / len(values)

        variance = sum((v - mean) ** 2 for v in values) / len(values)
        scale = math.sqrt(variance)

        if scale < 1e-12:
            scale = 1.0

        means.append(mean)
        scales.append(scale)

    def transform(data):
        return [
            [(row[j] - means[j]) / scales[j] for j in range(len(FEATURES))]
            for row in data
        ]

    return transform(train_x), transform(test_x)


def fit_ridge(train_x, train_y, alpha):
    """Fit Ridge Regression using the normal equation."""
    feature_count = len(FEATURES)
    dimension = feature_count + 1

    # Add intercept column.
    x = [[1.0] + row for row in train_x]

    matrix = [[0.0] * dimension for _ in range(dimension)]
    vector = [0.0] * dimension

    for row, target in zip(x, train_y):
        for i in range(dimension):
            vector[i] += row[i] * target

            for j in range(dimension):
                matrix[i][j] += row[i] * row[j]

    # Do not regularize the intercept.
    for i in range(1, dimension):
        matrix[i][i] += alpha

    return solve_linear_system(matrix, vector)


def predict(model, features):
    return [
        model[0] + sum(
            coefficient * value
            for coefficient, value in zip(model[1:], row)
        )
        for row in features
    ]


def calculate_metrics(actual, predicted):
    errors = [
        prediction - target
        for target, prediction in zip(actual, predicted)
    ]

    mae = sum(abs(error) for error in errors) / len(errors)

    rmse = math.sqrt(
        sum(error ** 2 for error in errors) / len(errors)
    )

    correct_direction = sum(
        (target >= 0 and prediction >= 0)
        or (target < 0 and prediction < 0)
        for target, prediction in zip(actual, predicted)
    )

    directional_accuracy = (
        correct_direction / len(actual)
    ) * 100

    return mae, rmse, directional_accuracy


def main():
    print("\nRIDGE REGRESSION PRICE PREDICTION")
    print("=" * 45)

    if not DATA_FILE.exists():
        print("Prediction dataset not found:", DATA_FILE)
        return

    records = read_dataset()

    if len(records) < 10:
        print("Not enough records to run this experiment.")
        return

    # Sort by date. All stocks from the same date stay in
    # the same chronological train/test partition.
    records.sort(key=lambda r: (r["Date"], r["Ticker"]))

    dates = sorted(set(row["Date"] for row in records))

    split_index = max(1, int(len(dates) * 0.8))
    split_index = min(split_index, len(dates) - 1)

    test_dates = set(dates[split_index:])

    train_records = [r for r in records if r["Date"] not in test_dates]
    test_records = [r for r in records if r["Date"] in test_dates]

    if len(train_records) <= len(FEATURES):
        print("Insufficient training records for selected features.")
        return

    def extract_features(row):
        return [float(row[name]) for name in FEATURES]

    train_x = [extract_features(r) for r in train_records]
    test_x = [extract_features(r) for r in test_records]

    train_y = [float(r["Target_Return_Pct"]) for r in train_records]
    test_y = [float(r["Target_Return_Pct"]) for r in test_records]

    train_x_scaled, test_x_scaled = standardize(train_x, test_x)

    model = fit_ridge(train_x_scaled, train_y, RIDGE_ALPHA)

    model_predictions = predict(model, test_x_scaled)

    # Naive baseline: predict zero price change.
    baseline_predictions = [0.0] * len(test_y)

    model_mae, model_rmse, model_direction = calculate_metrics(
        test_y, model_predictions
    )

    base_mae, base_rmse, base_direction = calculate_metrics(
        test_y, baseline_predictions
    )

    # Save individual test predictions.
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as file:

        columns = [
            "Date", "Target_Date", "Ticker", "Stock_Name",
            "Actual_Return_Pct", "Predicted_Return_Pct",
            "Baseline_Return_Pct", "Current_Close",
            "Predicted_Next_Close", "Actual_Next_Close"
        ]

        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        for row, actual, predicted_return in zip(
            test_records, test_y, model_predictions
        ):
            current_close = float(row["Close"])

            predicted_close = current_close * (
                1 + predicted_return / 100
            )

            writer.writerow({
                "Date": row["Date"],
                "Target_Date": row["Target_Date"],
                "Ticker": row["Ticker"],
                "Stock_Name": row["Stock_Name"],
                "Actual_Return_Pct": round(actual, 4),
                "Predicted_Return_Pct": round(predicted_return, 4),
                "Baseline_Return_Pct": 0,
                "Current_Close": current_close,
                "Predicted_Next_Close": round(predicted_close, 4),
                "Actual_Next_Close": row["Target_Close_Next_Day"]
            })

    print("\nDATA SPLIT")
    print("--------------------------------")
    print("Total records:", len(records))
    print("Training records:", len(train_records))
    print("Testing records:", len(test_records))
    print("Training dates:", len(dates[:split_index]))
    print("Testing dates:", len(test_dates))

    print("\nMODEL PERFORMANCE")
    print("--------------------------------")
    print("Ridge Regression:")
    print(f"MAE: {model_mae:.4f}%")
    print(f"RMSE: {model_rmse:.4f}%")
    print(f"Directional accuracy: {model_direction:.2f}%")

    print("\nNAIVE BASELINE (ZERO RETURN)")
    print("--------------------------------")
    print(f"MAE: {base_mae:.4f}%")
    print(f"RMSE: {base_rmse:.4f}%")
    print(f"Directional accuracy: {base_direction:.2f}%")

    print("\nSaved predictions:", OUTPUT_FILE)

    print("\nIMPORTANT:")
    print("This is an experimental model with a very small dataset.")
    print("Performance metrics are not evidence of reliable forecasting.")


if __name__ == "__main__":
    main()
