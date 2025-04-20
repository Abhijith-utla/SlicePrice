"""The analysis page of the app."""

import datetime
import reflex as rx
from ..components.card import card
from ..templates import template
from ..views.sales_by_time import sales_by_time_chart
from ..views.charts import (
    StatsState,
    area_toggle,
    orders_chart,
    revenue_chart,
    timeframe_select,
    users_chart,
    top_items_pie_chart,  # <-- add this
)
from ..views.stats_cards import stats_cards
from ..views.charts import (
    StatsState,
    area_toggle,
    orders_chart,
    revenue_chart,
    timeframe_select,
    users_chart,
    top_items_pie_chart,
)


def _time_data() -> rx.Component:
    return rx.hstack(
        rx.tooltip(
            rx.icon("info", size=20),
            content=f"{(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%b %d, %Y')} - {datetime.datetime.now().strftime('%b %d, %Y')}",
        ),
        rx.text("Last 30 days", size="4", weight="medium"),
        align="center",
        spacing="2",
        display=["none", "none", "flex"],
    )


def tab_content_header() -> rx.Component:
    return rx.hstack(
        _time_data(),
        area_toggle(),
        align="center",
        width="100%",
        spacing="4",
    )


@template(route="/analysis", title="Store Analysis", on_load=StatsState.randomize_data)
def analysis() -> rx.Component:
    """The analysis page.

    Returns:
        The UI for the analysis page.
    """
    return rx.vstack(
        rx.heading(f"Welcome, Your Store Analysis", size="5"),
        stats_cards(),
        # Existing charts card
        card(
            rx.hstack(
                tab_content_header(),
                rx.segmented_control.root(
                    rx.segmented_control.item("Users", value="users"),
                    rx.segmented_control.item("Revenue", value="revenue"),
                    rx.segmented_control.item("Orders", value="orders"),
                    margin_bottom="1.5em",
                    default_value="users",
                    on_change=StatsState.set_selected_tab,
                ),
                width="100%",
                justify="between",
            ),
            rx.match(
                StatsState.selected_tab,
                ("users", users_chart()),
                ("revenue", revenue_chart()),
                ("orders", orders_chart()),
            ),
        ),
        
        rx.grid(
            card(
                rx.hstack(
                    rx.icon("clock", size=20),
                    rx.text("Sales by Time of Day", size="4", weight="medium"),
                    align="center",
                    spacing="2",
                    margin_bottom="2.5em",
                ),
                sales_by_time_chart(),
            ),
            card(
                rx.hstack(
                    rx.hstack(
                        rx.icon("bar-chart", size=20),
                        rx.text("Top 6 Most Sold Items", size="4", weight="medium"),
                        align="center",
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.text("Select Year:", size="3"),
                        rx.select(
                            ["2023", "2024"],
                            value=StatsState.year,
                            on_change=StatsState.set_year,
                            width="8em",
                            size="2",
                        ),
                        spacing="3",
                    ),
                    align="center",
                    width="100%",
                    justify="between",
                ),
                top_items_pie_chart(),
            ),
            gap="1rem",
            grid_template_columns=[
                "1fr",
                "repeat(1, 1fr)",
                "repeat(2, 1fr)",
                "repeat(2, 1fr)",
                "repeat(2, 1fr)",
            ],
            width="100%",
        ),
        spacing="8",
        width="100%",
    )