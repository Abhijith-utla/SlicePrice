import reflex as rx
from ..templates import template

@template(route="/", title="Slice Price | Sauce Bros")
def index():
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("bar-chart", size=20),
                rx.text("The", size="4", weight="medium"),
                align="center",
                spacing="2",
                margin_bottom="1em",
            ),
        ),
        padding="3.5em",
        width="100%",
        
    )