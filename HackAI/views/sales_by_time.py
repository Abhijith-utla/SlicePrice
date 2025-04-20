import reflex as rx
import pandas as pd
from reflex.components.recharts import (
    bar_chart,
    bar,
    x_axis,
    y_axis,
    cartesian_grid,
    tooltip,
    responsive_container,
)

# Load and clean the data
df = pd.read_csv("HackAI/data/salesByTime.csv")

# Ensure Time is a string and sort by logical time order
df["Time"] = df["Time"].astype(str)

# Create a consistent sort order using pandas datetime
df["Time_Sort"] = pd.to_datetime(df["Time"], errors="coerce")
df = df.dropna(subset=["Time_Sort"]).sort_values("Time_Sort")

# Convert to dict for the chart
chart_data = df[["Time", "Net Sales"]].to_dict(orient="records")

def sales_by_time_chart() -> rx.Component:
    return rx.box(
        responsive_container(
            bar_chart(
                cartesian_grid(stroke_dasharray="3 3"),
                x_axis(data_key="Time"),
                y_axis(),
                tooltip(),
                bar(data_key="Net Sales", radius=[6, 6, 0, 0]),
                data=chart_data,
            ),
            width="100%",
            height=300,
        )
    )
