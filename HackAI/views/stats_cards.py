import reflex as rx
import pandas as pd
from reflex.components.radix.themes.base import LiteralAccentColor

# Load and process data
itemsales_2024 = pd.read_csv("HackAI/data/itemsales_2024.csv")
itemsales_2024["Total Sales"] = itemsales_2024["Total Sales"].replace(r'[\$,]', '', regex=True).astype(float)

combined_df = pd.read_csv("HackAI/data/combined_df.csv")
combined_df["Date"] = pd.to_datetime(combined_df["Date"])
combined_df["DayOfWeek"] = combined_df["Date"].dt.day_name()
combined_df["Hour"] = combined_df["Date"].dt.hour

# Metric 1: Most Profitable Day
most_profitable_day = combined_df.groupby("DayOfWeek")["Net Sales"].sum().sort_values(ascending=False).idxmax()

# Metric 2: Top-selling item in 2024
top_item_name = itemsales_2024.sort_values("Total Sales", ascending=False).iloc[0]["Item"]

# Metric 3: Peak Sales Hour
top_hour = combined_df.groupby("Hour")["Net Sales"].sum().idxmax()
peak_sales_hour = pd.to_datetime(str(top_hour), format="%H").strftime("%I:00 %p")

# Card generator
def stats_card(
    stat_name: str,
    value: str,
    icon: str,
    icon_color: LiteralAccentColor,
) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    rx.icon(tag=icon, size=34),
                    color_scheme=icon_color,
                    radius="full",
                    padding="0.7rem",
                ),
                rx.vstack(
                    rx.heading(
                        value,
                        size="6",
                        weight="bold",
                    ),
                    rx.text(stat_name, size="4", weight="medium"),
                    spacing="1",
                    height="100%",
                    align_items="start",
                    width="100%",
                ),
                height="100%",
                spacing="4",
                align="center",
                width="100%",
            ),
            spacing="3",
            align="center",
        ),
        size="3",
        width="100%",
        box_shadow="0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
    )

# Main stat card grid
def stats_cards() -> rx.Component:
    return rx.grid(
        stats_card(
            stat_name="Most Profitable Day",
            value=most_profitable_day,
            icon="calendar",
            icon_color="pink",
        ),
        stats_card(
            stat_name="Top-Selling Item",
            value=top_item_name,
            icon="star",
            icon_color="amber",
        ),
        stats_card(
            stat_name="Peak Sales Hour",
            value=peak_sales_hour,
            icon="clock",
            icon_color="cyan",
        ),
        gap="1rem",
        grid_template_columns=[
            "1fr",
            "repeat(1, 1fr)",
            "repeat(2, 1fr)",
            "repeat(3, 1fr)",
        ],
        width="100%",
        justify_content="center",
        align_items="center",
    )
