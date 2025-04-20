import datetime
import random
import reflex as rx
from reflex.components.radix.themes.base import (
    LiteralAccentColor,
)
import pandas as pd
import numpy as np

# Updated file paths with more flexible approach
try:
    df_2023 = pd.read_csv("HackAI/data/itemsales_2023.csv")
    df_2024 = pd.read_csv("HackAI/data/itemsales_2024.csv")
    combined_df = pd.read_csv('HackAI/data/combined_df.csv')
except FileNotFoundError:
    # Fallback paths
    try:
        df_2023 = pd.read_csv("data/itemsales_2023.csv")
        df_2024 = pd.read_csv("data/itemsales_2024.csv")
        combined_df = pd.read_csv('data/combined_df.csv')
    except FileNotFoundError:
        # Create sample data if files not found
        df_2023 = pd.DataFrame({
            "Item": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6"],
            "Quantity Sold": [120, 98, 75, 65, 50, 45]
        })
        df_2024 = pd.DataFrame({
            "Item": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6"],
            "Quantity Sold": [150, 110, 90, 70, 55, 40]
        })
        # Create sample combined data
        dates = pd.date_range(start='2023-01-01', periods=365*2)
        combined_df = pd.DataFrame({
            'Date': dates,
            'Net Sales': np.random.normal(1000, 200, len(dates))
        })

item_sales_data = {
    "2023": df_2023,
    "2024": df_2024,
}

# Generate sample data
daily_sample_data = []
monthly_sample_data = []
yearly_sample_data = []

# Initialize sample data
today = datetime.datetime.now()

# Daily data
for i in range(-15, 30):
    date = today + datetime.timedelta(days=i)
    forecast = 500 + 100 * np.sin(i / 10) + random.randint(-50, 50)
    actual = forecast + random.randint(-30, 30) if i <= 0 else None
    lower = forecast - 100
    upper = forecast + 100
    daily_sample_data.append({
        "name": date.strftime('%Y-%m-%d'),
        "actual": actual,
        "forecast": round(forecast, 2),
        "lower": round(lower, 2),
        "upper": round(upper, 2)
    })
    
# Monthly data
for i in range(-6, 12):
    date = today.replace(day=1) + datetime.timedelta(days=30*i)
    forecast = 15000 + 3000 * np.sin(i / 3) + random.randint(-1000, 1000)
    actual = forecast + random.randint(-500, 500) if i <= 0 else None
    lower = forecast - 2000
    upper = forecast + 2000
    monthly_sample_data.append({
        "name": date.strftime('%Y-%m'),
        "actual": actual,
        "forecast": round(forecast, 2),
        "lower": round(lower, 2),
        "upper": round(upper, 2)
    })
    
# Yearly data
current_year = today.year
for i in range(-2, 4):
    year = current_year + i
    forecast = 180000 + 20000 * i + random.randint(-5000, 5000)
    actual = forecast + random.randint(-10000, 10000) if i < 0 else None
    lower = forecast - 30000
    upper = forecast + 30000
    yearly_sample_data.append({
        "name": str(year),
        "actual": actual,
        "forecast": round(forecast, 2),
        "lower": round(lower, 2),
        "upper": round(upper, 2)
    })


# Unified State class combining both previous classes
class StatsState(rx.State):
    area_toggle: bool = True
    selected_tab: str = "daily"  # Changed default to daily
    timeframe: str = "Monthly"
    users_data = []
    revenue_data = []
    orders_data = []
    device_data = []
    yearly_device_data = []
    year: str = "2024"
    
    # Forecast data - initialize with sample data
    daily_data: list = daily_sample_data
    monthly_data: list = monthly_sample_data
    yearly_data: list = yearly_sample_data

    @rx.event
    def set_year(self, year: str):
        self.year = year

    @rx.event
    def set_selected_tab(self, tab: str | list[str]):
        self.selected_tab = tab if isinstance(tab, str) else tab[0]

    def toggle_areachart(self):
        self.area_toggle = not self.area_toggle
        
    # Use a class method instead of an instance method
    @classmethod
    def _generate_sample_data(cls):
        """Class method to initialize sample data if needed."""
        if not cls.daily_data:
            cls.daily_data = daily_sample_data
        if not cls.monthly_data:
            cls.monthly_data = monthly_sample_data
        if not cls.yearly_data:
            cls.yearly_data = yearly_sample_data


def area_toggle() -> rx.Component:
    return rx.cond(
        StatsState.area_toggle,
        rx.icon_button(
            rx.icon("area-chart"),
            size="2",
            cursor="pointer",
            variant="surface",
            on_click=StatsState.toggle_areachart,
        ),
        rx.icon_button(
            rx.icon("bar-chart-3"),
            size="2",
            cursor="pointer",
            variant="surface",
            on_click=StatsState.toggle_areachart,
        ),
    )

def _create_gradient(color: LiteralAccentColor, id: str) -> rx.Component:
    return (
        rx.el.svg.defs(
            rx.el.svg.linear_gradient(
                rx.el.svg.stop(
                    stop_color=rx.color(color, 7), offset="5%", stop_opacity=0.8
                ),
                rx.el.svg.stop(
                    stop_color=rx.color(color, 7), offset="95%", stop_opacity=0
                ),
                x1=0,
                x2=0,
                y1=0,
                y2=1,
                id=id,
            ),
        ),
    )

def _custom_tooltip(color: LiteralAccentColor) -> rx.Component:
    return (
        rx.recharts.graphing_tooltip(
            separator=" : ",
            content_style={
                "backgroundColor": rx.color("gray", 1),
                "borderRadius": "var(--radius-2)",
                "borderWidth": "1px",
                "borderColor": rx.color(color, 7),
                "padding": "0.5rem",
                "boxShadow": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
            },
            is_animation_active=True,
        ),
    )

def top_items_pie_chart() -> rx.Component:
    def pie_for_year(year: str):
        df = item_sales_data[year]
        df_sorted = df.sort_values("Quantity Sold", ascending=False).head(6)
        data = df_sorted[["Item", "Quantity Sold"]].rename(
            columns={"Item": "name", "Quantity Sold": "value"}
        ).to_dict("records")

        colors = [
            "var(--blue-8)",
            "var(--green-8)",
            "var(--purple-8)",
            "var(--orange-8)",
            "var(--cyan-8)",
            "var(--red-8)",
        ]

        cells = [rx.recharts.cell(fill=colors[i % len(colors)]) for i in range(len(data))]

        return rx.recharts.pie_chart(
            rx.recharts.pie(
                data=data,
                data_key="value",
                name_key="name",
                cx="50%",
                cy="50%",
                padding_angle=1,
                inner_radius="70",
                outer_radius="100",
                label=True,
                *cells
            ),
            rx.recharts.legend(),
            height=300,
        )

    return rx.cond(
        StatsState.year == "2023",
        pie_for_year("2023"),
        pie_for_year("2024"),
    )

def daily_forecast_graph() -> rx.Component:
    """Render the daily forecast graph."""
    return rx.vstack(
        rx.heading("Daily Sales Forecast", size="3"),
        rx.recharts.composed_chart(
            rx.recharts.area(
                data_key="forecast",
                stroke="#8884d8",
                fill="#8884d8",
                fill_opacity=0.3,
                name="Forecast"
            ),
            rx.recharts.line(
                data_key="actual",
                type_="monotone",
                stroke="#ff7300",
                name="Actual"
            ),
            rx.recharts.area(
                data_key="lower",
                stroke="#82ca9d",
                fill="#82ca9d",
                fill_opacity=0.1,
                name="Lower Bound"
            ),
            rx.recharts.area(
                data_key="upper",
                stroke="#82ca9d",
                fill="#82ca9d",
                fill_opacity=0.1,
                name="Upper Bound"
            ),
            rx.recharts.x_axis(
                data_key="name",
                label="Date",
            ),
            rx.recharts.y_axis(label="Sales"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            rx.recharts.brush(
                data_key="name", 
                height=30, 
                stroke="#8884d8"
            ),
            data=StatsState.daily_data,  # Using directly
            width="100%",
            height=350,
        ),
        width="100%",
    )

def monthly_forecast_graph() -> rx.Component:
    """Render the monthly forecast graph."""
    return rx.vstack(
        rx.heading("Monthly Sales Forecast", size="3"),
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="forecast",
                stroke="#8884d8",
                fill="#8884d8",
                name="Forecast"
            ),
            rx.recharts.x_axis(
                data_key="name",
                label="Month"
            ),
            rx.recharts.y_axis(label="Sales"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
            data=StatsState.monthly_data,  # Using directly
            width="100%",
            height=300,
        ),
        width="100%",
    )

def yearly_forecast_graph() -> rx.Component:
    """Render the yearly forecast graph."""
    return rx.vstack(
        rx.heading("Yearly Sales Forecast", size="3"),
        rx.recharts.line_chart(
            rx.recharts.line(
                data_key="forecast",
                stroke="#8884d8",
                type_="monotone",
                stroke_width=2,
                name="Forecast"
            ),
            rx.recharts.line(
                data_key="lower",
                stroke="#82ca9d",
                stroke_dasharray="3 3",
                type_="monotone",
                name="Lower Bound"
            ),
            rx.recharts.line(
                data_key="upper",
                stroke="#82ca9d",
                stroke_dasharray="3 3",
                type_="monotone",
                name="Upper Bound"
            ),
            rx.recharts.x_axis(
                data_key="name",
                label="Year"
            ),
            rx.recharts.y_axis(label="Sales"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
            data=StatsState.yearly_data,  # Using directly
            width="100%",
            height=300,
        ),
        width="100%",
    )

