"""
CodeAlpha Data Analytics Internship - Task 2: Exploratory Data Analysis
Input : data/books_raw.csv   (created by scraper.py)
Output: data/books_clean.csv, images/*.png, eda_report.txt

Usage:
    pip install pandas matplotlib scipy
    python eda.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save charts to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

DATA = Path("data/books_raw.csv")
CLEAN = Path("data/books_clean.csv")
IMG = Path("images")
REPORT = Path("eda_report.txt")
ALPHA = 0.05
MIN_CAT = 10  # only compare categories with at least this many books

IMG.mkdir(exist_ok=True)
lines = []


def say(text=""):
    print(text)
    lines.append(str(text))


def section(title):
    say("\n" + "=" * 72)
    say(title)
    say("=" * 72)


def verdict(p):
    return "Reject H0 (significant)" if p < ALPHA else "Fail to reject H0 (not significant)"


# ---------------------------------------------------------------------------
# 0. Questions we want to answer BEFORE looking at the data
# ---------------------------------------------------------------------------
section("0. QUESTIONS ASKED BEFORE ANALYSIS")
say("Q1. How many books are there, and what do the variables look like?")
say("Q2. Is the data clean (missing values, duplicates, impossible values)?")
say("Q3. How are prices and ratings distributed?")
say("Q4. Which categories are largest, and which are the most expensive?")
say("Q5. Are there anomalies (unusually priced books, tiny categories)?")
say("Q6. H1: Do higher-priced books get higher ratings?")
say("Q7. H2: Does price differ across star-rating groups?")
say("Q8. H3: Does price differ across categories?")
say("Q9. H4: Are books with longer descriptions priced differently?")

# ---------------------------------------------------------------------------
# 1. Structure
# ---------------------------------------------------------------------------
section("1. DATA STRUCTURE")
df = pd.read_csv(DATA)
say(f"Rows: {df.shape[0]}   Columns: {df.shape[1]}")
say("\nColumn types:")
say(df.dtypes.to_string())
say("\nFirst 3 rows:")
say(df.head(3).drop(columns=["description", "image_url"]).to_string())

# ---------------------------------------------------------------------------
# 2. Data quality
# ---------------------------------------------------------------------------
section("2. DATA QUALITY CHECKS")
issues = []

missing = df.isna().sum()
say("Missing values per column:")
say(missing.to_string())
if missing.sum() > 0:
    issues.append(f"{int(missing.sum())} missing values in total")

empty_desc = int((df["description"].fillna("").str.strip() == "").sum())
say(f"\nBooks with an empty description: {empty_desc}")
if empty_desc:
    issues.append(f"{empty_desc} books have no description")

dup_upc = int(df.duplicated("upc").sum())
dup_title = int(df.duplicated("title").sum())
say(f"Duplicate UPC codes: {dup_upc}")
say(f"Duplicate titles   : {dup_title}")
if dup_upc:
    issues.append(f"{dup_upc} duplicate UPCs (rows dropped in cleaning)")
if dup_title:
    issues.append(f"{dup_title} repeated titles (check if they are different editions)")

bad_price = int((df["price_gbp"] <= 0).sum())
say(f"Non-positive prices: {bad_price}")
if bad_price:
    issues.append(f"{bad_price} books with price <= 0")

bad_rating = int((~df["rating"].between(1, 5)).sum())
say(f"Ratings outside 1-5: {bad_rating}")
if bad_rating:
    issues.append(f"{bad_rating} ratings outside 1-5")

constant = [c for c in df.columns if df[c].nunique(dropna=False) == 1]
say(f"Constant columns (no information): {constant if constant else 'none'}")
if constant:
    issues.append(f"Constant columns carry no information: {constant}")

# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------
df = df.drop_duplicates("upc").copy()
df["in_stock"] = df["in_stock"].astype(str).str.lower().eq("true")
df["description"] = df["description"].fillna("")
df["desc_len"] = df["description"].str.len()
df["category"] = df["category"].fillna("Unknown").str.strip()
df = df[df["price_gbp"] > 0]
df.to_csv(CLEAN, index=False)
say(f"\nCleaned dataset: {len(df)} rows saved to {CLEAN}")

# ---------------------------------------------------------------------------
# 3. Descriptive statistics
# ---------------------------------------------------------------------------
section("3. DESCRIPTIVE STATISTICS")
num_cols = ["price_gbp", "rating", "stock_count", "num_reviews", "desc_len"]
say(df[num_cols].describe().round(2).to_string())
say(f"\nSkewness of price : {df['price_gbp'].skew():.2f}")
say(f"Number of categories: {df['category'].nunique()}")
say("\nTop 10 categories by number of books:")
say(df["category"].value_counts().head(10).to_string())

# ---------------------------------------------------------------------------
# 4. Trends and patterns
# ---------------------------------------------------------------------------
section("4. TRENDS AND PATTERNS")
rating_counts = df["rating"].value_counts().sort_index()
say("Books per star rating:")
say(pd.DataFrame({"count": rating_counts,
                  "percent": (rating_counts / len(df) * 100).round(1)}).to_string())

say("\nAverage price by star rating:")
say(df.groupby("rating")["price_gbp"].agg(["count", "mean", "median"]).round(2).to_string())

cat_stats = (df.groupby("category")["price_gbp"]
             .agg(["count", "mean", "median"]).round(2))
big = cat_stats[cat_stats["count"] >= MIN_CAT].sort_values("mean", ascending=False)
say(f"\nMost expensive categories (>= {MIN_CAT} books):")
say(big.head(5).to_string())
say(f"\nCheapest categories (>= {MIN_CAT} books):")
say(big.tail(5).to_string())

say(f"\nShare of books in stock: {df['in_stock'].mean() * 100:.1f}%")

# ---------------------------------------------------------------------------
# 5. Anomalies
# ---------------------------------------------------------------------------
section("5. ANOMALIES / OUTLIERS")
q1, q3 = df["price_gbp"].quantile([0.25, 0.75])
iqr = q3 - q1
low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
outliers = df[(df["price_gbp"] < low) | (df["price_gbp"] > high)]
say(f"IQR rule: prices outside [{low:.2f}, {high:.2f}] are outliers")
say(f"Price outliers found: {len(outliers)}")
if len(outliers):
    say(outliers.nlargest(5, "price_gbp")[["title", "category", "price_gbp"]].to_string())

say("\n5 most expensive books:")
say(df.nlargest(5, "price_gbp")[["title", "price_gbp"]].to_string(index=False))
say("\n5 cheapest books:")
say(df.nsmallest(5, "price_gbp")[["title", "price_gbp"]].to_string(index=False))

tiny = cat_stats[cat_stats["count"] < 5]
say(f"\nCategories with fewer than 5 books: {len(tiny)}")
if len(tiny):
    issues.append(f"{len(tiny)} categories have fewer than 5 books (unreliable averages)")

# ---------------------------------------------------------------------------
# 6. Hypothesis tests
# ---------------------------------------------------------------------------
section("6. HYPOTHESIS TESTS  (alpha = 0.05)")

sample = df["price_gbp"].sample(min(500, len(df)), random_state=42)
sw_stat, sw_p = stats.shapiro(sample)
say(f"Normality check (Shapiro-Wilk on price): p = {sw_p:.4g}")
if sw_p < ALPHA:
    say("-> Price is not normally distributed, so rank-based tests are used.")
else:
    say("-> Price looks roughly normal; rank-based tests are still a safe choice.")

# H1
rho, p = stats.spearmanr(df["price_gbp"], df["rating"])
say("\nH1: price and rating are related (Spearman correlation)")
say("    H0: no monotonic relationship")
say(f"    rho = {rho:.3f}, p = {p:.4g} -> {verdict(p)}")

# H2
groups = [g["price_gbp"].values for _, g in df.groupby("rating") if len(g) > 1]
if len(groups) >= 2:
    h, p = stats.kruskal(*groups)
    say("\nH2: price differs across star ratings (Kruskal-Wallis)")
    say("    H0: price distributions are the same for every rating")
    say(f"    H = {h:.3f}, p = {p:.4g} -> {verdict(p)}")

# H3
cats = big.index
groups = [df.loc[df["category"] == c, "price_gbp"].values for c in cats]
if len(groups) >= 2:
    h, p = stats.kruskal(*groups)
    say(f"\nH3: price differs across categories with >= {MIN_CAT} books (Kruskal-Wallis)")
    say("    H0: price distributions are the same in every category")
    say(f"    H = {h:.3f}, p = {p:.4g} -> {verdict(p)}  ({len(groups)} categories tested)")

# H4
rho, p = stats.spearmanr(df["desc_len"], df["price_gbp"])
say("\nH4: description length and price are related (Spearman correlation)")
say("    H0: no monotonic relationship")
say(f"    rho = {rho:.3f}, p = {p:.4g} -> {verdict(p)}")

say("\nNote: with ~1000 rows even a tiny effect can be 'significant'. "
    "Always read rho / H together with the p-value to judge practical size.")

# ---------------------------------------------------------------------------
# 7. Charts used as evidence
# ---------------------------------------------------------------------------
section("7. CHARTS SAVED")

plt.figure(figsize=(7, 4))
plt.hist(df["price_gbp"], bins=30, edgecolor="black")
plt.axvline(df["price_gbp"].median(), color="red", linestyle="--", label="median")
plt.title("Distribution of book prices")
plt.xlabel("Price (GBP)")
plt.ylabel("Number of books")
plt.legend()
plt.tight_layout()
plt.savefig(IMG / "price_distribution.png", dpi=150)
plt.close()

plt.figure(figsize=(6, 4))
rating_counts.plot(kind="bar", edgecolor="black")
plt.title("Books per star rating")
plt.xlabel("Rating")
plt.ylabel("Number of books")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(IMG / "rating_counts.png", dpi=150)
plt.close()

plt.figure(figsize=(7, 4))
df.boxplot(column="price_gbp", by="rating", grid=False)
plt.suptitle("")
plt.title("Price by star rating")
plt.xlabel("Rating")
plt.ylabel("Price (GBP)")
plt.tight_layout()
plt.savefig(IMG / "price_by_rating.png", dpi=150)
plt.close()

top_cat = big.sort_values("mean").tail(10)
plt.figure(figsize=(8, 5))
plt.barh(top_cat.index, top_cat["mean"])
plt.title(f"Average price: top 10 categories (>= {MIN_CAT} books)")
plt.xlabel("Average price (GBP)")
plt.tight_layout()
plt.savefig(IMG / "avg_price_by_category.png", dpi=150)
plt.close()

for name in ["price_distribution", "rating_counts", "price_by_rating", "avg_price_by_category"]:
    say(f"  images/{name}.png")

# ---------------------------------------------------------------------------
# 8. Issues to handle in later analysis
# ---------------------------------------------------------------------------
section("8. DATA ISSUES TO ADDRESS IN FURTHER ANALYSIS")
if not issues:
    say("No major issues were detected automatically.")
for i, item in enumerate(issues, 1):
    say(f"{i}. {item}")
say("General notes:")
say("- Prices are in GBP and excl. tax; stock_count only reflects the snapshot day.")
say("- Ratings are discrete (1-5), so use rank-based or categorical methods.")
say("- This is a practice website, so results describe this dataset, not the real book market.")

REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nFull report saved to {REPORT}")