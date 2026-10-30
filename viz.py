"""
CodeAlpha Data Analytics Internship - Task 3: Data Visualization
Input : data/books_clean.csv   (created by eda.py)
Output: images/viz/*.png (individual charts) and images/dashboard.png

Usage:
    pip install pandas matplotlib seaborn
    python viz.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

DATA = Path("data/books_clean.csv")
OUT = Path("images/viz")
DASH = Path("images/dashboard.png")
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#2E6FBA"
ORANGE = "#E8833A"
GREY = "#7A7A7A"
PLACEHOLDERS = {"Default", "Add a comment"}  # not real genres (see EDA)
MIN_CAT = 10  # minimum books for a fair category comparison

sns.set_theme(style="whitegrid", context="notebook")

df = pd.read_csv(DATA)
real = df[~df["category"].isin(PLACEHOLDERS)]  # genres only
df["price_band"] = pd.cut(
    df["price_gbp"],
    bins=[10, 20, 30, 40, 50, 60],
    right=False,
    labels=["£10-20", "£20-30", "£30-40", "£40-50", "£50-60"],
)
MEAN_PRICE = df["price_gbp"].mean()
MEDIAN_PRICE = df["price_gbp"].median()


# ---------------------------------------------------------------------------
# Each chart is a function that draws on a given axis, so the same code is
# used for the single-chart files and for the dashboard.
# ---------------------------------------------------------------------------
def plot_price_dist(ax):
    sns.histplot(df["price_gbp"], bins=25, color=BLUE, ax=ax)
    ax.axvline(MEAN_PRICE, color=ORANGE, linestyle="--", label=f"Mean £{MEAN_PRICE:.2f}")
    ax.axvline(MEDIAN_PRICE, color=GREY, linestyle=":", label=f"Median £{MEDIAN_PRICE:.2f}")
    ax.set_title("Prices are spread evenly from £10 to £60", weight="bold")
    ax.set_xlabel("Price (GBP)")
    ax.set_ylabel("Number of books")
    ax.legend()


def plot_rating_counts(ax):
    counts = df["rating"].value_counts().sort_index()
    bars = ax.bar(counts.index.astype(str), counts.values, color=BLUE)
    ax.bar_label(bars, padding=3)
    ax.set_title("Ratings are balanced across all five stars", weight="bold")
    ax.set_xlabel("Star rating")
    ax.set_ylabel("Number of books")


def plot_price_by_rating(ax):
    sns.boxplot(data=df, x="rating", y="price_gbp", color=BLUE, ax=ax)
    ax.axhline(MEAN_PRICE, color=ORANGE, linestyle="--", label="Overall mean")
    ax.set_title("Price barely changes with rating", weight="bold")
    ax.set_xlabel("Star rating")
    ax.set_ylabel("Price (GBP)")
    ax.legend()


def plot_top_categories(ax):
    top = real["category"].value_counts().head(10).sort_values()
    bars = ax.barh(top.index, top.values, color=BLUE)
    ax.bar_label(bars, padding=3)
    ax.set_title("Top 10 genres by number of books", weight="bold")
    ax.set_xlabel("Number of books")


def plot_avg_price_category(ax):
    stats = real.groupby("category")["price_gbp"].agg(["mean", "count"])
    stats = stats[stats["count"] >= MIN_CAT].sort_values("mean")
    picks = pd.concat([stats.head(5), stats.tail(5)])
    colors = [BLUE] * 5 + [ORANGE] * 5
    bars = ax.barh(picks.index, picks["mean"], color=colors)
    ax.bar_label(bars, fmt="£%.2f", padding=3)
    ax.axvline(MEAN_PRICE, color=GREY, linestyle="--")
    ax.set_title("Genre prices: 5 cheapest vs 5 priciest", weight="bold")
    ax.set_xlabel(f"Average price (GBP), genres with {MIN_CAT}+ books")
    ax.set_xlim(0, picks["mean"].max() * 1.15)


def plot_desc_scatter(ax):
    cap = df["desc_len"].quantile(0.99)
    sns.regplot(
        data=df, x="desc_len", y="price_gbp", ax=ax,
        scatter_kws={"alpha": 0.35, "s": 18, "color": BLUE},
        line_kws={"color": ORANGE},
    )
    ax.set_xlim(0, cap)
    ax.set_title("Longer descriptions do not mean higher prices", weight="bold")
    ax.set_xlabel("Description length (characters, top 1% cut off)")
    ax.set_ylabel("Price (GBP)")


def plot_price_band_heatmap(ax):
    table = pd.crosstab(df["price_band"], df["rating"])
    sns.heatmap(table, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax)
    ax.set_title("Books by price band and rating", weight="bold")
    ax.set_xlabel("Star rating")
    ax.set_ylabel("Price band")


def plot_correlation(ax):
    cols = ["price_gbp", "rating", "stock_count", "desc_len"]
    corr = df[cols].corr(method="spearman")
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                vmin=-1, vmax=1, square=True, ax=ax)
    ax.set_title("Spearman correlations: all close to zero", weight="bold")


INDIVIDUAL = {
    "01_price_distribution": (plot_price_dist, (7, 4.5)),
    "02_rating_counts": (plot_rating_counts, (6.5, 4.5)),
    "03_price_by_rating": (plot_price_by_rating, (7, 4.5)),
    "04_top_categories": (plot_top_categories, (8, 5)),
    "05_avg_price_by_category": (plot_avg_price_category, (9, 5)),
    "06_price_vs_description": (plot_desc_scatter, (7.5, 4.5)),
    "07_price_band_heatmap": (plot_price_band_heatmap, (7, 4.5)),
    "08_correlation_heatmap": (plot_correlation, (6.5, 5.5)),
}

for name, (func, size) in INDIVIDUAL.items():
    fig, ax = plt.subplots(figsize=size, constrained_layout=True)
    func(ax)
    fig.savefig(OUT / f"{name}.png", dpi=150)
    plt.close(fig)
    print(f"saved {OUT / (name + '.png')}")

# ---------------------------------------------------------------------------
# Dashboard: six key charts on one page
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(21, 11), constrained_layout=True)
for ax, func in zip(
    axes.ravel(),
    [plot_price_dist, plot_rating_counts, plot_price_by_rating,
     plot_top_categories, plot_avg_price_category, plot_desc_scatter],
):
    func(ax)
fig.suptitle(
    "Books to Scrape: market snapshot of 1,000 books "
    "(price is not driven by rating, genre or description length)",
    fontsize=19, weight="bold",
)
fig.savefig(DASH, dpi=150)
plt.close(fig)
print(f"saved {DASH}")

# ---------------------------------------------------------------------------
# Data story: numbers behind the charts
# ---------------------------------------------------------------------------
print("\nDATA STORY - key numbers")
print(f"- {len(df)} books, price £{df['price_gbp'].min():.2f} to £{df['price_gbp'].max():.2f}, "
      f"mean £{MEAN_PRICE:.2f}")
share = df["rating"].value_counts(normalize=True).sort_index() * 100
print("- Rating shares (%): " + ", ".join(f"{k}-star {v:.1f}" for k, v in share.items()))
by_rating = df.groupby("rating")["price_gbp"].mean().round(2)
print("- Average price by rating: " + ", ".join(f"{k}-star £{v}" for k, v in by_rating.items()))
print("- Largest real genres: " + ", ".join(real["category"].value_counts().head(3).index))