import reflex as rx
from ..templates import template

@template(route="/upload", title="Upload Your data")
def upload() -> rx.Component:
    return rx.center(
        rx.text("this")
    ) 

def prediction_dashboard() -> rx.Component:
    """Create a dashboard for sales predictions."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("bar-chart", size=20),
                rx.heading("Sales Prediction Dashboard", size="4", weight="medium"),
                rx.spacer(),
                rx.number_input(
                    default_value=30,
                    min_=7,
                    max_=90,
                    value=StatsState.prediction_window,
                    on_change=StatsState.set_prediction_window,
                    width="6em",
                    size="2",
                ),
                rx.text("days", size="3"),
                rx.button(
                    "Generate Prediction",
                    on_click=StatsState.generate_predictions,
                    variant="soft",
                    color="blue",
                    size="2",
                    loading=StatsState.is_loading_prediction,
                ),
                width="100%",
                spacing="3",
                align="center",
            ),
            rx.cond(
                StatsState.show_prediction,
                rx.vstack(
                    # Show the chart
                    rx.recharts.line_chart(
                        rx.recharts.line(
                            type_="monotone",
                            data_key="Sales",
                            stroke=rx.color("blue", 9),
                            stroke_width=2,
                        ),
                        rx.recharts.x_axis(data_key="Date"),
                        rx.recharts.y_axis(),
                        rx.recharts.tooltip(),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        data=StatsState.formatted_prediction_data,
                        height=300,
                    ),
                    # Show metrics below the chart
                    rx.hstack(
                        rx.vstack(
                            rx.text("Pred. Min Sales", size="2", color="gray"),
                            rx.text(
                                f"${min([d['Sales'] for d in StatsState.formatted_prediction_data] or [0]):.2f}",
                                size="4",
                                weight="bold",
                            ),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Pred. Max Sales", size="2", color="gray"),
                            rx.text(
                                f"${max([d['Sales'] for d in StatsState.formatted_prediction_data] or [0]):.2f}",
                                size="4",
                                weight="bold",
                            ),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Pred. Avg Sales", size="2", color="gray"),
                            rx.text(
                                f"${sum([d['Sales'] for d in StatsState.formatted_prediction_data] or [0]) / max(len(StatsState.formatted_prediction_data), 1):.2f}",
                                size="4",
                                weight="bold",
                            ),
                            spacing="1",
                        ),
                        width="100%",
                        justify="around",
                        margin_top="1em",
                    ),
                    # Show the generated image if available
                    rx.cond(
                        StatsState.prediction_image != "",
                        rx.image(
                            src=StatsState.prediction_image,
                            height="300px",
                            width="100%",
                            border_radius="md",
                            margin_top="1.5em",
                        ),
                    ),
                    width="100%",
                ),
                rx.vstack(
                    rx.center(
                        rx.vstack(
                            rx.icon("chart", size=48, color="gray"),
                            rx.text(
                                "No prediction data available", 
                                color="gray",
                                size="3",
                            ),
                            rx.text(
                                "Click 'Generate Prediction' to forecast sales",
                                color="gray",
                                size="2",
                            ),
                            spacing="2",
                            padding="2em",
                        )
                    ),
                    spacing="4",
                    height="300px",
                    width="100%",
                ),
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
    )