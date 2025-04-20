import reflex as rx
import pandas as pd
from ..templates import template

# Load and process chart data
def load_chart_data(path, company_col, percentage_col):
    df = pd.read_csv(path)
    df = df[[company_col, percentage_col]]
    df.columns = ['name', 'uv']
    return df.to_dict(orient="records")

restaurant_chart_data = load_chart_data(
    "HackAI/data/restaurant_rankings.csv", "Company", "Positive %"
)

company_chart_data = load_chart_data(
    "HackAI/data/company_sentiment_comparison.csv", "Company", "Positive_Percentage"
)

# Basic vertical bar chart component
def bar_vertical(data):
    return rx.recharts.bar_chart(
        rx.recharts.bar(
            data_key="uv",
            stroke=rx.color("accent", 8),
            fill=rx.color("accent", 3),
        ),
        rx.recharts.x_axis(type_="number"),
        rx.recharts.y_axis(data_key="name", type_="category"),
        data=data,
        layout="vertical",
        margin={"top": 20, "right": 20, "left": 80, "bottom": 20},
        width="100%",
        height=300,
    )

# Chart card with header and bar chart
def chart_card(title: str, chart: rx.Component) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("bar-chart", size=20),
                rx.text(title, size="4", weight="medium"),
                align="center",
                spacing="2",
                margin_bottom="1em",
            ),
            chart,
        ),
        padding="3.5em",
        width="100%",
        
    )

# Menu item sentiment + aspects card
def menu_sentiment_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("pizza", size=20),
                rx.text("Based on Coustomer reviews on Yelp!!", size="4", weight="medium"),
                align="center",
                spacing="2",
                margin_bottom="1em",
            ),

            # Table-like text layout
            rx.text_area(
                "Item                     Positive   Negative   Total\n"
                "-----------------------------------------------------\n"
                "meat lovers             20         30         50\n"
                "naga habanero           30         10         40\n"
                "korean bbq              30         0          30\n"
                "habanero chicken        30         0          30\n"
                "harissa chicken         20         0          20\n"
                "4 cheese                20         0          20\n"
                "beef taco               20         0          20",
                as_="pre",  # ✅ Valid for Box
                font_family="monospace",
                background_color="gray.50",
                padding="1em",
                border_radius="md",
                width="100%",
                auto_height=True
            ),


            # Feedback aspects
            rx.hstack(
                rx.box(
                    rx.hstack(rx.icon("thumbs-up"), rx.text("Key Positive Aspects", weight="bold")),
                    rx.unordered_list(
                        rx.list_item("Great service"),
                        rx.list_item("Crispy crust"),
                        rx.list_item("Good flavors"),
                    ),
                    width="50%",
                ),
                rx.box(
                    rx.hstack(rx.icon("thumbs-down"), rx.text("Key Negative Aspects", weight="bold")),
                    rx.unordered_list(
                        rx.list_item("Issues with sauce"),
                        rx.list_item("Price concerns"),
                        rx.list_item("Small restaurant size"),
                    ),
                    width="50%",
                ),
                spacing="4",
                width="100%",
                justify="center",
                padding_top="1em",
            ),
        ),
        padding="3.5em",
        width="80%",
    )

@template(route="/competitor", title="Competitor Analysis")
def competitor() -> rx.Component:
    return rx.vstack(
        rx.heading("Restaurant Sentiment Analysis", size="5", margin_bottom="1em"),

        rx.grid(
            chart_card("Top Restaurant Rankings by Positive Sentiment", bar_vertical(restaurant_chart_data)),
            chart_card("Top pizzarias by Positive Sentiment", bar_vertical(company_chart_data)),
            gap="2em",
            grid_template_columns=["2fr", "1fr"],  # two-column layout
            width="80%",
        ),

        # New Menu Sentiment Card Below
        menu_sentiment_card(),

        spacing="8",
        width="100%",
        padding="3.5em",
        align="center"
    )