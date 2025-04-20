import reflex as rx
from ..templates import template

@template(route="/", title="Home")
def index() -> rx.Component:
    return rx.center(
        rx.text("this")
    ) 