# breadprice.py
from typing import Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Common month header aliases -> canonical 3-letter form
_MONTH_ALIASES = {
    'jan': 'Jan', 'january': 'Jan', 'jan.': 'Jan',
    'feb': 'Feb', 'february': 'Feb', 'feb.': 'Feb',
    'mar': 'Mar', 'march': 'Mar', 'mar.': 'Mar',
    'apr': 'Apr', 'april': 'Apr', 'apr.': 'Apr',
    'may': 'May',
    'jun': 'Jun', 'june': 'Jun', 'jun.': 'Jun',
    'jul': 'Jul', 'july': 'Jul', 'jul.': 'Jul',
    'aug': 'Aug', 'august': 'Aug', 'aug.': 'Aug',
    'sep': 'Sep', 'sept': 'Sep', 'september': 'Sep', 'sep.': 'Sep', 'sept.': 'Sep',
    'oct': 'Oct', 'october': 'Oct', 'oct.': 'Oct',
    'nov': 'Nov', 'november': 'Nov', 'nov.': 'Nov',
    'dec': 'Dec', 'december': 'Dec', 'dec.': 'Dec',
}

def _normalize_month_headers(df: pd.DataFrame) -> pd.DataFrame:
    # Map common variants to canonical month names
    col_map = {}
    for c in df.columns:
        cl = str(c).strip().lower().rstrip('.')
        if cl in _MONTH_ALIASES:
            col_map[c] = _MONTH_ALIASES[cl]
    if col_map:
        df = df.rename(columns=col_map)
    return df

def load_and_clean_data(filename: str) -> pd.DataFrame:
    """
    Load the bread price data and clean it.
    Tries whitespace-separated first (handles ragged rows), then falls back to auto-detect.
    Handles UTF-8 BOM, comment lines (#), messy month headers, currency symbols, and duplicate years.
    """
    # Primary: regex whitespace separator; engine='python' supports regex + ragged rows
    df = pd.read_csv(
        filename, sep=r'\s+', engine='python', header=0, encoding='utf-8-sig', comment='#'
    )
    # Fallback: auto-detect delimiter if we clearly failed to split
    if df.shape[1] == 1:
        df = pd.read_csv(
            filename, sep=None, engine='python', header=0, encoding='utf-8-sig', comment='#'
        )

    # Normalize/clean header names (strip spaces, remove BOM if present)
    df.columns = [str(c).replace('\ufeff', '').strip() for c in df.columns]

    # Ensure we have a 'Year' column (case-insensitive fallback)
    if 'Year' not in df.columns:
        maybe_year = next((c for c in df.columns if str(c).strip().lower() == 'year'), None)
        if maybe_year:
            df = df.rename(columns={maybe_year: 'Year'})
        else:
            df = df.rename(columns={df.columns[0]: 'Year'})

    # Clean and coerce Year: extract a 4-digit year (handles "2022*", "FY2022", etc.)
    df['Year'] = df['Year'].astype(str).str.extract(r'(\d{4})', expand=False)
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df.dropna(subset=['Year'])
    df['Year'] = df['Year'].astype(int)

    # Normalize month headers
    df = _normalize_month_headers(df)

    # Ensure all month columns exist; add missing months as NaN
    for m in MONTHS:
        if m not in df.columns:
            df[m] = np.nan

    # Keep only month columns in the standard order plus Year
    cols = ['Year'] + MONTHS
    df = df.loc[:, [c for c in cols if c in df.columns]]

    # Convert month columns to numeric (strip $ and commas first)
    month_block = df[MONTHS].replace(r'[\$,]', '', regex=True).replace('', np.nan)
    df[MONTHS] = month_block.apply(pd.to_numeric, errors='coerce')

    # Sort and collapse duplicate years by averaging across duplicate rows (month-wise)
    df = df.set_index('Year').sort_index()
    if df.index.duplicated().any():
        df = df.groupby(level=0)[MONTHS].mean()

    # Ensure all months are present in final frame and in correct order
    for m in MONTHS:
        if m not in df.columns:
            df[m] = np.nan
    df = df[MONTHS]

    return df

def calculate_yearly_averages(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the average bread price for each year (across available months).
    """
    yearly_avg = df[MONTHS].mean(axis=1, skipna=True)
    return yearly_avg.dropna()

def create_visualization(
    yearly_avg: pd.Series,
    save_to: Optional[str] = None,
    show: bool = True
) -> Optional[Tuple[plt.Figure, plt.Axes]]:
    """
    Create a line plot showing bread prices over time.
    Optionally save to a file and/or display it.
    """
    if yearly_avg.empty:
        print("No data to plot (yearly averages are empty).")
        return None

    fig, ax = plt.subplots(figsize=(12, 6))

    years = yearly_avg.index.to_numpy()
    prices = yearly_avg.to_numpy()

    ax.plot(
        years, prices, marker='o', linewidth=2, markersize=7,
        color='#8B4513', markerfacecolor='#D2691E', markeredgewidth=1.2
    )

    ax.set_title(
        f'Average Bread Prices in the U.S. ({int(years.min())}-{int(years.max())})',
        fontsize=16, fontweight='bold'
    )
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Average Price (USD)', fontsize=12)
    ax.grid(True, alpha=0.3, linestyle='--')

    # Axis formatting
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:.2f}'))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.tick_params(axis='x', labelrotation=45)
    ax.margins(x=0.02)

    # Annotations for min and max (use offset in points to avoid going outside axes)
    year_min = int(yearly_avg.idxmin())
    year_max = int(yearly_avg.idxmax())
    min_price = float(yearly_avg.loc[year_min])
    max_price = float(yearly_avg.loc[year_max])

    if year_min == year_max:
        ax.annotate(
            f'Only data point: ${min_price:.3f}',
            xy=(year_min, min_price),
            xytext=(10, -15), textcoords='offset points',
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.5),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )
    else:
        ax.annotate(
            f'Lowest: ${min_price:.3f}',
            xy=(year_min, min_price),
            xytext=(10, -15), textcoords='offset points',
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.5),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )
        ax.annotate(
            f'Highest: ${max_price:.3f}',
            xy=(year_max, max_price),
            xytext=(10, 15), textcoords='offset points',
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.5),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )

    fig.tight_layout()

    if save_to:
        fig.savefig(save_to, dpi=150, bbox_inches='tight')
    if show:
        plt.show()

    return fig, ax

def print_summary_statistics(yearly_avg: pd.Series) -> None:
    """
    Print summary statistics about the bread prices.
    """
    ya = yearly_avg.dropna()
    if ya.empty:
        raise ValueError(
            "No valid yearly averages computed. Check that month columns parsed correctly "
            "and contain numeric values."
        )

    start_year = int(ya.index.min())
    end_year = int(ya.index.max())

    print("=" * 50)
    print("BREAD PRICE ANALYSIS REPORT")
    print("=" * 50)
    print(f"\nData Range: {start_year} - {end_year}")
    print(f"\nSummary Statistics:")
    print(f"  • Average price over all years: ${ya.mean():.3f}")
    print(f"  • Lowest average price: ${ya.min():.3f} (Year {ya.idxmin()})")
    print(f"  • Highest average price: ${ya.max():.3f} (Year {ya.idxmax()})")

    start_val = float(ya.loc[start_year])
    end_val = float(ya.loc[end_year])
    change = end_val - start_val
    if start_val == 0:
        pct_change_str = "N/A (start value is 0)"
    else:
        pct_change_str = f"{(change / start_val * 100):.1f}%"

    print(f"  • Price change from {start_year} to {end_year}: ${change:.3f}")
    print(f"  • Percentage change: {pct_change_str}")

    print(f"\nYear-by-Year Average Prices:")
    for year, price in ya.items():
        print(f"  {int(year)}: ${price:.3f}")
    print("=" * 50)

def main() -> None:
    """
    Main function to orchestrate the bread price analysis.
    """
    filename = 'breadprice.csv'

    try:
        print("Loading and cleaning data...")
        df = load_and_clean_data(filename)

        print("Calculating yearly averages...")
        yearly_avg = calculate_yearly_averages(df)

        print_summary_statistics(yearly_avg)

        print("\nGenerating visualization...")
        create_visualization(yearly_avg)

        print("\nAnalysis complete! The plot has been displayed.")

    except FileNotFoundError:
        print(f"Error: Could not find the file '{filename}'")
        print("Please ensure the CSV file is in the same directory as this script.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()