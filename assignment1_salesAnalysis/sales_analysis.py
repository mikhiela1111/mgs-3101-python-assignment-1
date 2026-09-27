"""
MGS 3101 - Assignment 1: Coffee Shop Sales Analysis
----------------------------------------------------
Dataset: Coffee Shop Sales (Maven Analytics, via Kaggle)
         149,116 transaction lines, 3 NYC locations, Jan 1 - Jun 30, 2023

What this script does:
  1. Stores basic sales values in variables (shop name, drinks, pastries, prices)
  2. Calculates drink revenue, pastry revenue, and total revenue
  3. Prints the written report (sales_analysis_report.txt)
  4. Uses an if/else statement to check whether total revenue is at least $500
  5. Produces the data behind each recommendation in the report
     (printed to the screen and saved as CSV files in the output/ folder)

How to run (from inside the assignment1_salesAnalysis folder):
  pip install pandas
  python sales_analysis.py
"""

from pathlib import Path

import pandas as pd

# File locations (relative to this script, so it runs from any folder)
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "coffee_shop_sales.csv"
REPORT_FILE = BASE_DIR / "sales_analysis_report.txt"
OUTPUT_DIR = BASE_DIR / "output"

# Product categories treated as "drinks" and "pastries" throughout
DRINK_CATEGORIES = ["Coffee", "Tea", "Drinking Chocolate"]
PASTRY_CATEGORY = "Bakery"


# ---------------------------------------------------------------------------
# PART 1 - Store values in variables
# One real day from the dataset: Hell's Kitchen location, June 30, 2023.
# Prices are the average price paid per item that day, rounded to cents.
# ---------------------------------------------------------------------------
shop_name = "Hell's Kitchen Coffee Shop"
drinks_sold = 352
price_per_drink = 3.10
pastries_sold = 65
price_per_pastry = 3.61

# ---------------------------------------------------------------------------
# PART 2 - Calculate drink and pastry revenue
# ---------------------------------------------------------------------------
drink_revenue = drinks_sold * price_per_drink
pastry_revenue = pastries_sold * price_per_pastry
total_revenue = drink_revenue + pastry_revenue


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def money(value):
    return f"${value:,.2f}"


def save_table(table, filename):
    OUTPUT_DIR.mkdir(exist_ok=True)
    table.to_csv(OUTPUT_DIR / filename)
    print(f"\n(saved to output/{filename})")


def print_daily_summary():
    print_header(f"DAILY SNAPSHOT - {shop_name}")
    print(f"Drinks sold:     {drinks_sold} x {money(price_per_drink)} = {money(drink_revenue)}")
    print(f"Pastries sold:   {pastries_sold} x {money(price_per_pastry)} = {money(pastry_revenue)}")
    print(f"Total revenue:   {money(total_revenue)}")

    # PART 4 - if/else check on the $500 revenue goal
    if total_revenue >= 500:
        print(f"Result: {shop_name} reached the $500 goal (total revenue is at least $500).")
    else:
        print(f"Result: {shop_name} did NOT reach the $500 goal (total revenue is below $500).")


# ---------------------------------------------------------------------------
# PART 3 - Print the written .txt report
# ---------------------------------------------------------------------------
def print_report():
    print_header("WRITTEN REPORT (sales_analysis_report.txt)")
    with open(REPORT_FILE, "r", encoding="utf-8") as report:
        print(report.read())


# ---------------------------------------------------------------------------
# PART 5 - Produce the data behind each recommendation
# ---------------------------------------------------------------------------
def load_data():
    sales = pd.read_csv(DATA_FILE)
    sales["revenue"] = sales["transaction_qty"] * sales["unit_price"]
    sales["transaction_date"] = pd.to_datetime(sales["transaction_date"])
    sales["month"] = sales["transaction_date"].dt.to_period("M").astype(str)
    sales["hour"] = pd.to_datetime(sales["transaction_time"], format="%H:%M:%S").dt.hour
    return sales


def dataset_overview(sales):
    print_header("DATASET OVERVIEW")
    print(f"Date range:        {sales['transaction_date'].min():%b %d, %Y} to "
          f"{sales['transaction_date'].max():%b %d, %Y}")
    print(f"Transaction lines: {len(sales):,}")
    print(f"Items sold:        {sales['transaction_qty'].sum():,}")
    print(f"Total revenue:     {money(sales['revenue'].sum())}")

    by_store = sales.groupby("store_location")["revenue"].sum().sort_values(ascending=False)
    print("\nRevenue by store:")
    for store, revenue in by_store.items():
        print(f"  {store:<16} {money(revenue)}")

    by_category = (
        sales.groupby("product_category")
        .agg(revenue=("revenue", "sum"), items_sold=("transaction_qty", "sum"))
        .sort_values("revenue", ascending=False)
    )
    by_category["share_of_revenue_%"] = (by_category["revenue"] / by_category["revenue"].sum() * 100).round(1)
    by_category["avg_price"] = (by_category["revenue"] / by_category["items_sold"]).round(2)
    by_category["revenue"] = by_category["revenue"].round(2)
    print("\nRevenue by product category:")
    print(by_category.to_string())
    save_table(by_category, "category_summary.csv")


def recommendation_1_pastry_attach_rate(sales):
    """Rec 1: Bundle a pastry with drinks - how many pastries sell per 100 drinks?"""
    print_header("RECOMMENDATION 1 - Drink + pastry bundle (pastry attach rate)")

    drinks = sales[sales["product_category"].isin(DRINK_CATEGORIES)]
    pastries = sales[sales["product_category"] == PASTRY_CATEGORY]

    table = pd.DataFrame({
        "drinks_sold": drinks.groupby("store_location")["transaction_qty"].sum(),
        "pastries_sold": pastries.groupby("store_location")["transaction_qty"].sum(),
        "pastry_revenue": pastries.groupby("store_location")["revenue"].sum().round(2),
    })
    table.loc["All stores"] = table.sum()
    table["pastries_per_100_drinks"] = (table["pastries_sold"] / table["drinks_sold"] * 100).round(1)
    print(table.to_string())

    # What-if: raise the attach rate from today's level to 20 per 100 drinks
    all_drinks = table.loc["All stores", "drinks_sold"]
    all_pastries = table.loc["All stores", "pastries_sold"]
    avg_pastry_price = pastries["revenue"].sum() / pastries["transaction_qty"].sum()
    target_pastries = all_drinks * 0.20
    extra_revenue = (target_pastries - all_pastries) * avg_pastry_price
    print(f"\nAverage pastry price: {money(avg_pastry_price)}")
    print(f"If pastries rose to 20 per 100 drinks, the chain would sell about "
          f"{target_pastries - all_pastries:,.0f} more pastries, worth about "
          f"{money(extra_revenue)} over six months (before any bundle discount).")
    save_table(table, "rec1_pastry_attach_rate.csv")


def recommendation_2_afternoon_traffic(sales):
    """Rec 2: Fill the afternoon lull - revenue by hour of day."""
    print_header("RECOMMENDATION 2 - Afternoon promotion (revenue by hour)")

    by_hour = sales.groupby("hour").agg(
        revenue=("revenue", "sum"),
        transactions=("transaction_id", "count"),
    )
    by_hour["share_of_revenue_%"] = (by_hour["revenue"] / by_hour["revenue"].sum() * 100).round(1)
    by_hour["revenue"] = by_hour["revenue"].round(2)
    print(by_hour.to_string())

    morning = by_hour.loc[7:10, "revenue"].sum()
    afternoon = by_hour.loc[12:17, "revenue"].sum()
    total = by_hour["revenue"].sum()
    print(f"\n7-10 AM (4 hours):  {money(morning)}  ({morning / total:.1%} of revenue)")
    print(f"12-5 PM (6 hours):  {money(afternoon)}  ({afternoon / total:.1%} of revenue)")
    print(f"Average revenue per morning hour:   {money(morning / 4)}")
    print(f"Average revenue per afternoon hour: {money(afternoon / 6)}")
    save_table(by_hour, "rec2_revenue_by_hour.csv")


def recommendation_3_growth_and_top_products(sales):
    """Rec 3: Plan staffing/inventory for growth and protect the top sellers."""
    print_header("RECOMMENDATION 3 - Plan for growth around the top sellers")

    by_month = sales.pivot_table(index="month", columns="store_location",
                                 values="revenue", aggfunc="sum").round(2)
    by_month["All stores"] = by_month.sum(axis=1)
    by_month["growth_vs_prior_month_%"] = (by_month["All stores"].pct_change() * 100).round(1)
    print("Monthly revenue by store:")
    print(by_month.to_string())

    first, last = by_month["All stores"].iloc[0], by_month["All stores"].iloc[-1]
    print(f"\nJanuary to June change: {money(first)} -> {money(last)} ({(last / first - 1):+.1%})")
    save_table(by_month, "rec3_monthly_revenue.csv")

    top_products = (
        sales.groupby("product_type")
        .agg(revenue=("revenue", "sum"), items_sold=("transaction_qty", "sum"))
        .sort_values("revenue", ascending=False)
        .head(10)
    )
    top_products["share_of_revenue_%"] = (top_products["revenue"] / sales["revenue"].sum() * 100).round(1)
    top_products["revenue"] = top_products["revenue"].round(2)
    print("\nTop 10 product types by revenue:")
    print(top_products.to_string())
    print(f"\nThe top 10 product types bring in {top_products['share_of_revenue_%'].sum():.1f}% of all revenue.")
    save_table(top_products, "rec3_top_products.csv")


def main():
    print_daily_summary()
    print_report()

    sales = load_data()
    dataset_overview(sales)
    recommendation_1_pastry_attach_rate(sales)
    recommendation_2_afternoon_traffic(sales)
    recommendation_3_growth_and_top_products(sales)


if __name__ == "__main__":
    main()
