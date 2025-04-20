"""Sidebar component for the app."""

import reflex as rx
from .. import styles

# Define the page config with display name and icon for each route
PAGE_CONFIG = {
    "/": ("Home", "home"),
    "/analysis": ("Analysis", "bar-chart"),
    "/competitor": ("Competitor", "activity"),
    "/upload": ("Upload", "upload"),
}


def sidebar_header() -> rx.Component:
    return rx.hstack(
        rx.color_mode_cond(
            rx.image(src="/reflex_black.svg", height="1.5em"),
            rx.image(src="/reflex_white.svg", height="1.5em"),
        ),
        rx.spacer(),
        align="center",
        width="100%",
        padding="0.35em",
        margin_bottom="1em",
    )


def sidebar_footer() -> rx.Component:
    return rx.hstack(
        rx.spacer(),
        rx.color_mode.button(style={"opacity": "0.8", "scale": "0.95"}),
        justify="start",
        align="center",
        width="100%",
        padding="0.35em",
    )


def sidebar_item(text: str, icon: str, url: str) -> rx.Component:
    active = (rx.State.router.page.path == url.lower()) | (
        (rx.State.router.page.path == "/") & (url == "/")
    )

    return rx.link(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text, size="3", weight="regular"),
            color=rx.cond(active, styles.accent_text_color, styles.text_color),
            style={
                "_hover": {
                    "background_color": rx.cond(active, styles.accent_bg_color, styles.gray_bg_color),
                    "color": rx.cond(active, styles.accent_text_color, styles.text_color),
                    "opacity": "1",
                },
                "opacity": rx.cond(active, "1", "0.95"),
            },
            align="center",
            border_radius=styles.border_radius,
            width="100%",
            spacing="2",
            padding="0.35em",
        ),
        underline="none",
        href=url,
        width="100%",
    )


def sidebar() -> rx.Component:
    from reflex.page import get_decorated_pages

    pages = get_decorated_pages()
    filtered_pages = [page for page in pages if page["route"] in PAGE_CONFIG]
    ordered_pages = sorted(filtered_pages, key=lambda page: list(PAGE_CONFIG.keys()).index(page["route"]))

    return rx.flex(
        rx.vstack(
            sidebar_header(),
            rx.vstack(
                *[
                    sidebar_item(PAGE_CONFIG[page["route"]][0], PAGE_CONFIG[page["route"]][1], page["route"])
                    for page in ordered_pages
                ],
                spacing="1",
                width="100%",
            ),
            rx.spacer(),
            sidebar_footer(),
            justify="end",
            align="end",
            width=styles.sidebar_content_width,
            height="100dvh",
            padding="1em",
        ),
        display=["none", "none", "none", "none", "none", "flex"],
        max_width=styles.sidebar_width,
        width="auto",
        height="100%",
        position="sticky",
        justify="end",
        top="0px",
        left="0px",
        flex="1",
        bg=rx.color("gray", 2),
    )
