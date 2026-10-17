import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def run_data_analysis(csv_file_path: str = "products_output.csv"):

    pd.set_option('display.float_format', lambda x: '%.2f' % x)

    # Load dataset
    df = pd.read_csv(csv_file_path)

    print("==================================================")
    print("           DATA QUALITY CONTROL REPORT            ")
    print("==================================================")

    # 1. Dataset Dimensions
    total_records = len(df)
    total_columns = len(df.columns)
    print(f"\n[+] Total records collected: {total_records}")
    print(f"[+] Total attributes (columns): {total_columns}")

    # 2. Missing Values Analysis (Count and Percentage)
    print("\n--- Missing Values per Column ---")
    missing_counts = df.isnull().sum()
    missing_percentages = (missing_counts / total_records) * 100
    missing_report = pd.DataFrame({
        "Missing (Count)": missing_counts,
        "Missing (%)": missing_percentages.round(2)
    })
    print(missing_report)

    # 3. Column Data Types Verification
    print("\n--- Column Data Types ---")
    print(df.dtypes)

    # Verify expected numeric columns
    numeric_candidates = ["price", "rating", "reviews_count", "warranty_months"]
    for col in numeric_candidates:
        if col in df.columns:
            is_numeric = np.issubdtype(df[col].dtype, np.number)
            print(f" -> Verification: '{col}' is numeric: {is_numeric}")

    # 4. Outlier Detection (Interquartile Range Method for Price)
    if "price" in df.columns and df["price"].dropna().count() > 0:
        print("\n--- Outlier Detection (Price) ---")
        q1 = df["price"].quantile(0.25)
        q3 = df["price"].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = df[(df["price"] < lower_bound) | (df["price"] > upper_bound)]
        print(f"Lower Bound: {lower_bound:.2f}, Upper Bound: {upper_bound:.2f}")
        print(f"Outliers detected: {len(outliers)}")
        if not outliers.empty:
            print("Sample outliers:")
            print(outliers[["id", "name", "price"]].head())

    print("\n==================================================")
    print("             DESCRIPTIVE STATISTICS               ")
    print("==================================================")

    # 5. Descriptive Statistics for Numerical Attributes
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        summary_stats = numeric_df.describe().T[["mean", "50%", "std", "min", "max"]]
        summary_stats.rename(columns={"50%": "median"}, inplace=True)
        
        # Calculate Mode separately
        mode_values = {}
        for col in numeric_df.columns:
            mode_series = df[col].mode()
            mode_values[col] = mode_series.iloc[0] if not mode_series.empty else np.nan
        summary_stats["mode"] = pd.Series(mode_values)

        # 25% and 75% quartiles
        summary_stats["q25"] = numeric_df.quantile(0.25)
        summary_stats["q75"] = numeric_df.quantile(0.75)

        print("\nDescriptive statistics table:")
        print(summary_stats[["mean", "median", "mode", "q25", "q75", "min", "max", "std"]].round(2))

    # 6. Correlation Analysis
    if "price" in df.columns and "rating" in df.columns:
        valid_subset = df[["price", "rating"]].dropna()
        if len(valid_subset) > 1:
            corr_val = valid_subset["price"].corr(valid_subset["rating"])
            print(f"\n--- Pearson Correlation: Price vs. Rating ---")
            print(f"Correlation coefficient: {corr_val:.4f}")

    # 7. Chart Generation
    print("\nGenerating charts (Histogram & Box-plot)...")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Histogram: Price Distribution
    if "price" in df.columns and df["price"].dropna().count() > 0:
        axes[0].hist(df["price"].dropna(), bins=15, color="steelblue", edgecolor="black")
        axes[0].set_title("Product Price Distribution (Histogram)")
        axes[0].set_xlabel("Price")
        axes[0].set_ylabel("Frequency")
        axes[0].grid(axis="y", linestyle="--", alpha=0.7)

    # Box-plot: Price Outliers
    if "price" in df.columns and df["price"].dropna().count() > 0:
        axes[1].boxplot(df["price"].dropna(), vert=True, patch_artist=True,
                        boxprops=dict(facecolor="lightblue", color="blue"))
        axes[1].set_title("Product Price Box-Plot")
        axes[1].set_ylabel("Price")
        axes[1].grid(axis="y", linestyle="--", alpha=0.7)

    plt.tight_layout()
    chart_output = "analysis_charts.png"
    plt.savefig(chart_output, dpi=300)
    print(f"[+] Visualizations saved successfully to '{chart_output}'")

if __name__ == "__main__":
    run_data_analysis("products_output.csv")