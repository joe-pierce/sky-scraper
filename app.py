# pip install nicegui plotly numpy
from nicegui import ui

from src.canvas import make_city_fig

with ui.header().classes("items-center justify-between px-4"):
    ui.label("Skyline Generator").classes("text-xl panel-title")

with ui.splitter(value=28, limits=(15, 85)).classes("w-full h-screen") as split:
    # LEFT: controls
    with split.before, ui.element("div").classes("py-5"):
        with ui.row().classes("items-end gap-4"):
            num_buildings = ui.number("num_buildings", value=10, min=1, step=1, format="%d")

        with ui.row().classes("items-end gap-4"):
            min_height = ui.number("min_height", value=5, min=0, step=1, format="%d")
            max_height = ui.number("max_height", value=25, min=0, step=1, format="%d")

        with ui.row().classes("items-end gap-4"):
            min_width = ui.number("min_width", value=3, min=1, step=1, format="%d")
            max_width = ui.number("max_width", value=10, min=1, step=1, format="%d")

        with ui.row().classes("items-center gap-6 mt-2"):
            night_switch = ui.switch("day/night", value=False)
            auto_switch = ui.switch("auto-regenerate", value=True)
        manual_button = ui.button("Regenerate now", color="primary")

    # RIGHT: plot
    with split.after:
        plot = ui.plotly(
            make_city_fig(
                num_buildings.value,
                min_height.value,
                max_height.value,
                min_width.value,
                max_width.value,
                night_switch.value,
            )
        ).classes("w-full h-screen")

    def regenerate(*_):
        # clamp and auto-swap min/max pairs if needed
        mn_h, mx_h = int(min_height.value or 0), int(max_height.value or 0)
        if mn_h > mx_h:
            mn_h, mx_h = mx_h, mn_h
            min_height.value, max_height.value = mn_h, mx_h

        mn_w, mx_w = int(min_width.value or 1), int(max_width.value or 1)
        if mn_w > mx_w:
            mn_w, mx_w = mx_w, mn_w
            min_width.value, max_width.value = mn_w, mx_w

        plot.figure = make_city_fig(num_buildings.value, mn_h, mx_h, mn_w, mx_w, night_switch.value)
        plot.update()

    def maybe_regenerate(*_):
        if auto_switch.value:
            regenerate()

    for field in (
        num_buildings,
        min_height,
        max_height,
        min_width,
        max_width,
        night_switch,
    ):
        field.on_value_change(maybe_regenerate)

    manual_button.on_click(regenerate)

ui.run()
