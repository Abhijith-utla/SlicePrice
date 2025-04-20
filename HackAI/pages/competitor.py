import reflex as rx
import pandas as pd
import os
from reflex.components.radix.themes.base import LiteralAccentColor
from ..templates import template
from ..components.card import card  # Reusable card component

# Load CSV
csv_path = "data/restaurant_rankings.csv"
companies = []
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    companies = df[["Company", "Positive %"]].to_dict(orient="records")

# Define colors
colors: list[LiteralAccentColor] = ["blue", "crimson", "plum", "green", "amber"]

# Each competitor item
def progress_card(company: str, percentage: float, color: LiteralAccentColor) -> rx.Component:
    return rx.hstack(
        rx.text(company.replace("_", " "), size="4", weight="bold", width="30%"),
        rx.flex(
            rx.text(
                f"{percentage:.1f}%",
                position="absolute",
                top="50%",
                left="95%",
                transform="translate(-50%, -50%)",
                size="2",
            ),
            rx.progress(
                value=int(percentage),
                height="20px",
                color_scheme=color,
                width="100%",
            ),
            position="relative",
            width="100%",
        ),
        width="100%",
        align="center",
        justify="between",
    )

@template(route="/competitor", title="Competitor Analysis")
def competitor() -> rx.Component:
    return rx.vstack(
        rx.heading("Competitor Sentiment Rankings", size="5"),
        card(
            rx.hstack(
                rx.icon("globe", size=20),
                rx.text("Pizza Brand Sentiment", size="4", weight="medium"),
                align="center",
                spacing="2",
                margin_bottom="2.5em",
            ),
            rx.vstack(
                *[
                    progress_card(entry["Company"], entry["Positive %"], colors[i % len(colors)])
                    for i, entry in enumerate(companies)
                ],
                spacing="4",
            ),
        ),
        spacing="8",
        width="100%",
        padding="2em",
        background_color="#f9f9f9",
    )
