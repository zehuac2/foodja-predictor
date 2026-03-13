import numpy as np
import pandas as pd

CSV_FILE = "restaurants.csv"


def load_data():
    """Load and sort restaurants CSV by date."""
    df = pd.read_csv(CSV_FILE, parse_dates=["date"], dayfirst=False)
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
    return df.sort_values("date")


def build_markov_model(df):
    """
    Build a transition matrix: rows = restaurant today, cols = restaurant tomorrow.
    Returns the matrix and the list of restaurant labels.
    """
    restaurants = sorted(df["restaurant"].unique())
    n = len(restaurants)

    # Assign each restaurant an integer index via a categorical dtype
    cat = pd.CategoricalDtype(categories=restaurants, ordered=False)
    df = df.copy()
    df["r_idx"] = df["restaurant"].astype(cat).cat.codes

    # Build a next_date column and merge to get all (today, tomorrow) pairs at once
    dates = df[["date"]].drop_duplicates().sort_values("date")
    dates = dates.assign(next_date=dates["date"].shift(-1)).dropna()
    # Only keep pairs where next_date is exactly one calendar day after date
    dates = dates[dates["next_date"] - dates["date"] == pd.Timedelta(days=1)]

    today_df = df.merge(dates, on="date")[["r_idx", "next_date"]]
    tomorrow_df = df.rename(columns={"date": "next_date", "r_idx": "r_next_idx"})
    pairs = today_df.merge(tomorrow_df, on="next_date")

    # Count transitions with bincount on flattened (r1*n + r2) indices
    flat = pairs["r_idx"].to_numpy(dtype=np.intp) * n + pairs["r_next_idx"].to_numpy(
        dtype=np.intp
    )
    matrix = np.bincount(flat, minlength=n * n).reshape(n, n).astype(np.float64)

    # Normalize rows to probabilities
    row_sums = matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    matrix /= row_sums

    return matrix, restaurants


def predict(df, matrix, restaurants, top_n=3, n_days=1):
    """
    Given today's restaurants, return the top_n most likely restaurants
    for each of the next n_days days using repeated matrix multiplication.

    Returns a list of n_days lists, each containing top_n restaurant names.
    Raises ValueError if the last date has no restaurant entries.
    """
    cat = pd.CategoricalDtype(categories=restaurants, ordered=False)
    last_date = df["date"].max()
    today_indices = (
        df[df["date"] == last_date]["restaurant"].astype(cat).cat.codes.to_numpy()
    )

    if len(today_indices) == 0:
        raise ValueError(
            f"No restaurant entries found for the last date ({last_date.date()})."
        )

    # Start with a uniform distribution over today's restaurants
    n = len(restaurants)
    scores = np.zeros(n)
    scores[today_indices] = 1.0 / len(today_indices)

    results = []
    for _ in range(n_days):
        scores = scores @ matrix
        top_indices = np.argsort(scores)[::-1][:top_n]
        results.append([restaurants[i] for i in top_indices])

    return results


def main():
    df = load_data()

    if df["date"].nunique() < 2:
        print("Not enough data to build a model (need at least 2 days).")
        return

    matrix, restaurants = build_markov_model(df)
    n_days = 5
    all_predictions = predict(df, matrix, restaurants, n_days=n_days)

    last_date = df["date"].max()
    last_date_str = last_date.strftime("%m/%d/%Y")
    print(
        f"Based on data through {last_date_str}, predicted restaurants for the next {n_days} days:"
    )
    for day_offset, day_predictions in enumerate(all_predictions, start=1):
        future_date = last_date + pd.Timedelta(days=day_offset)
        print(f"\n  {future_date.strftime('%m/%d/%Y')}:")
        for i, r in enumerate(day_predictions):
            print(f"    {i}: {r}")


if __name__ == "__main__":
    main()
