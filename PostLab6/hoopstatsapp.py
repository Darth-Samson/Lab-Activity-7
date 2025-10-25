"""
File: hoopstatsapp.py

The application for analyzing basketball stats.
"""

import pandas as pd
from hoopstatsview import HoopStatsView


def cleanStats(frame: pd.DataFrame) -> pd.DataFrame:
    """Cleans the basketball stats DataFrame by splitting
    makes-attempts columns into separate makes and attempts columns.

    This function performs a three-step cleaning process:
    1. Removes the original column (e.g., "8-15" format)
    2. Creates two new numeric columns for makes and attempts
    3. Inserts the new columns with proper headings

    Args:
        frame: A pandas DataFrame with basketball statistics

    Returns:
        A cleaned copy of the DataFrame with split columns
    """
    # Work on a copy to avoid mutating the caller's DataFrame in-place
    frame = frame.copy()

    # Normalize/trim column names to avoid surprises (e.g., trailing spaces)
    frame.columns = [str(c).strip() for c in frame.columns]

    # Define columns to clean: (original_name, makes_name, attempts_name)
    columns_to_clean = [
        ("FG", "FGM", "FGA"),       # Field Goals Made/Attempted
        ("3PT", "3PTM", "3PTA"),    # 3-Pointers Made/Attempted
        ("FT", "FTM", "FTA"),       # Free Throws Made/Attempted
    ]

    for old_col, makes_col, attempts_col in columns_to_clean:
        if old_col not in frame.columns:
            continue

        # Skip if already split (prevents ValueError on re-insert)
        if makes_col in frame.columns or attempts_col in frame.columns:
            # Drop original if it's still around
            frame.drop(columns=[old_col], errors="ignore", inplace=True)
            continue

        # Position of the original column to keep logical order
        col_position = frame.columns.get_loc(old_col)

        # Ensure we are working with string values and split safely using regex
        # This extracts two groups of digits around a single hyphen, ignoring spaces
        split_df = (
            frame[old_col]
            .astype(str)
            .str.strip()
            .str.extract(r"^\s*(\d+)\s*-\s*(\d+)\s*$")
        )

        # Convert to numeric; non-conforming rows become NaN instead of raising
        makes = pd.to_numeric(split_df[0], errors="coerce")
        attempts = pd.to_numeric(split_df[1], errors="coerce")

        # Insert new columns next to where the original column was
        frame.insert(col_position, makes_col, makes)
        frame.insert(col_position + 1, attempts_col, attempts)

        # Remove the original combined column
        frame.drop(columns=[old_col], inplace=True)

    return frame


def main():
    """Creates the data frame and view and starts the app."""
    csv_path = "cleanbrogdonstats.csv"

    # Be tolerant of delimiter issues (comma vs whitespace)
    try:
        # sep=None with engine='python' will try to sniff the delimiter
        frame = pd.read_csv(csv_path, sep=None, engine="python")
    except Exception:
        # Fallback: treat as whitespace-delimited
        frame = pd.read_csv(csv_path, delim_whitespace=True)

    # Clean the data using our cleanStats function
    frame = cleanStats(frame)

    # Launch the GUI
    HoopStatsView(frame).mainloop()


if __name__ == "__main__":
    main()