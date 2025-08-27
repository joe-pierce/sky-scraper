# pip install nicegui plotly numpy
import dotenv

dotenv.load_dotenv()
from nicegui import ui, run

from src.canvas import make_city_fig
from src.enhance import enhance

rgb_dict = {"latest": None}

with ui.header().classes("items-center justify-between px-4"):
    ui.label("Skyline Generator").classes("text-xl panel-title")

with ui.splitter(value=35, limits=(30, 85)).classes("w-full h-screen") as split:
    with split.before, ui.element("div").classes("h-full w-full flex flex-col py-5 min-w-[300px]"):
        ui.label("Number of buildings").style("font-size: 1.2em; font-weight: 500").classes(
            "px-2 pt-2"
        )
        with ui.row().classes("items-center gap-4 p-2 pt-1"):
            num_buildings_lbl = ui.label("10")
            num_buildings = (
                ui.slider(
                    min=1,
                    max=100,
                    value=10,
                    on_change=lambda e: num_buildings_lbl.set_text(f"{e.value}"),
                )
                .props("label")
                .classes("flex-1")
            )

        ui.label("Building height").style("font-size: 1.2em; font-weight: 500").classes("px-2 pt-2")
        with ui.row().classes("items-end gap-4 p-2 pt-1"):
            min_max_height_lbl = ui.label("Min: 5 Max: 25")
            min_max_height = (
                ui.range(
                    min=1,
                    max=100,
                    value={"min": 5, "max": 25},
                    on_change=lambda e: min_max_height_lbl.set_text(
                        f"Min: {e.value['min']} Max: {e.value['max']}"
                    ),
                )
                .props("label")
                .classes("flex-1")
            )

        ui.label("Building width").style("font-size: 1.2em; font-weight: 500").classes("px-2 pt-2")

        with ui.row().classes("items-end gap-4 p-2 pt-1"):
            min_max_width_lbl = ui.label("Min: 5 Max: 25")
            min_max_width = (
                ui.range(
                    min=1,
                    max=50,
                    value={"min": 3, "max": 10},
                    on_change=lambda e: min_max_width_lbl.set_text(
                        f"Min: {e.value['min']} Max: {e.value['max']}"
                    ),
                )
                .props("label")
                .classes("flex-1")
            )

        with ui.row().classes("items-center gap-6 mt-2 p-2"):
            night_switch = ui.switch("day/night", value=False)
            auto_switch = ui.switch("auto-regenerate", value=True)
        with ui.row().classes("items-center gap-6 mt-2 p-2"):
            manual_button = ui.button("Regenerate now", color="primary")
        with ui.row().classes("items-center gap-6 mt-2 p-2"):
            enhance_btn = ui.button("Enhance", color="secondary")

            # def on_enhance_click():
            #     try:
            #         if rgb_dict["latest"] is None:
            #             ui.notify("Generate a skyline first")
            #             return
            #         # Choose backend:
            #         plot.figure = enhance(rgb_dict["latest"])  # local

            #         plot.update()
            #     except Exception as e:
            #         ui.notify(f"Enhance failed: {e}", color="negative")

            async def on_enhance_click():
                try:
                    if rgb_dict["latest"] is None:
                        ui.notify("Generate a skyline first")
                        return
                    ui.notify("Enhancing…", type="info")
                    # run in a worker thread (non-blocking)
                    fig = await run.io_bound(enhance, rgb_dict["latest"])
                    plot.figure = fig
                    plot.update()
                    ui.notify("Done!", type="positive")
                except Exception as e:
                    ui.notify(f"Enhance failed: {e}", color="negative")

            enhance_btn.on_click(on_enhance_click)

    with split.after:
        plot, rgb = make_city_fig(
            num_buildings.value,
            min_max_height.value["min"],
            min_max_height.value["max"],
            min_max_width.value["min"],
            min_max_width.value["max"],
            night_switch.value,
        )
        plot = ui.plotly(plot).classes("w-full h-screen")
        rgb_dict["latest"] = rgb

    def regenerate(*_):
        mn_h, mx_h = int(min_max_height.value["min"] or 0), int(min_max_height.value["max"] or 0)
        if mn_h > mx_h:
            mn_h, mx_h = mx_h, mn_h
            min_max_height.value["min"], min_max_height.value["max"] = mn_h, mx_h

        mn_w, mx_w = int(min_max_width.value["min"] or 1), int(min_max_width.value["max"] or 1)
        if mn_w > mx_w:
            mn_w, mx_w = mx_w, mn_w
            min_max_width.value["min"], min_max_width.value["max"] = mn_w, mx_w

        plot.figure, rgb = make_city_fig(
            num_buildings.value, mn_h, mx_h, mn_w, mx_w, night_switch.value
        )
        rgb_dict["latest"] = rgb
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
