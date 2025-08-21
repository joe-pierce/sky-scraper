# pip install nicegui plotly numpy
from nicegui import ui

from src.canvas import make_city_fig

with ui.header().classes("items-center justify-between px-4"):
    ui.label("Skyline Generator").classes("text-xl panel-title")

with ui.splitter(value=35, limits=(30, 85)).classes("w-full h-screen") as split:
    # LEFT: controls
    with split.before, ui.element("div").classes("h-full w-full flex flex-col py-5 min-w-[300px]"):
        with ui.row().classes("items-center gap-4 p-2"):
            num_buildings_lbl = ui.label("Number of buildings: 10")
            num_buildings = ui.slider(
                min=1,
                max=100,
                value=10,
                on_change=lambda e: num_buildings_lbl.set_text(f"Number of buildings: {e.value}"),
            ).props("label").classes('flex-1')

        with ui.row().classes("items-end gap-4 p-2"):
            min_max_height_lbl = ui.label("Building height: Min: 5, Max: 25")
            min_max_height= ui.range(min=1, max=100, value={'min': 5, 'max': 25}, on_change=lambda e: min_max_height_lbl.set_text(f"Building height: Min: {e.value['min']}, Max: {e.value['max']}")).props("label").classes('flex-1')
            # min_height = ui.number("min_height", value=5, min=0, step=1, format="%d")
            # max_height = ui.number("max_height", value=25, min=0, step=1, format="%d")

        with ui.row().classes("items-end gap-4 p-2"):
            min_max_width_lbl = ui.label("Building width: Min: 5, Max: 25")
            min_max_width= ui.range(min=1, max=50, value={'min': 3, 'max': 10}, on_change=lambda e: min_max_width_lbl.set_text(f"Building width: Min: {e.value['min']}, Max: {e.value['max']}")).props("label").classes('flex-1')
            # min_width = ui.number("min_width", value=3, min=1, step=1, format="%d")
            # max_width = ui.number("max_width", value=10, min=1, step=1, format="%d")

        with ui.row().classes("items-center gap-6 mt-2 p-2"):
            night_switch = ui.switch("day/night", value=False)
            auto_switch = ui.switch("auto-regenerate", value=True)
        with ui.row().classes("items-center gap-6 mt-2 p-2"):
            manual_button = ui.button("Regenerate now", color="primary")

    # RIGHT: plot
    with split.after:
        plot = ui.plotly(
            make_city_fig(
                num_buildings.value,
                min_max_height.value["min"],
                min_max_height.value["max"],
                min_max_width.value["min"],
                min_max_width.value["max"],
                night_switch.value,
            )
        ).classes("w-full h-screen")

    def regenerate(*_):
        # clamp and auto-swap min/max pairs if needed
        mn_h, mx_h = int(min_max_height.value["min"] or 0), int(min_max_height.value["max"] or 0)
        if mn_h > mx_h:
            mn_h, mx_h = mx_h, mn_h
            min_max_height.value["min"], min_max_height.value["max"] = mn_h, mx_h

        mn_w, mx_w = int(min_max_width.value["min"] or 1), int(min_max_width.value["max"] or 1)
        if mn_w > mx_w:
            mn_w, mx_w = mx_w, mn_w
            min_max_width.value["min"], min_max_width.value["max"] = mn_w, mx_w

        plot.figure = make_city_fig(num_buildings.value, mn_h, mx_h, mn_w, mx_w, night_switch.value)
        plot.update()

    def maybe_regenerate(*_):
        if auto_switch.value:
            regenerate()

    for field in (
        num_buildings,
        min_max_height,
        min_max_width,
        night_switch,
    ):
        field.on_value_change(maybe_regenerate)

    manual_button.on_click(regenerate)

ui.run()
