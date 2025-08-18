# pip install nicegui plotly numpy
from nicegui import ui
import numpy as np
import plotly.express as px
import math

def make_city_fig(num_buildings: int, min_h: int, max_h: int,
                  min_w: int, max_w: int, gap: int = 1):
    # sanitize inputs
    num_buildings = max(1, int(num_buildings or 1))
    min_h = max(0, int(min_h or 0))
    max_h = max(min_h, int(max_h or min_h))
    min_w = max(1, int(min_w or 1))
    max_w = max(min_w, int(max_w or min_w))

    rng = np.random.default_rng()
    heights = rng.integers(min_h, max_h + 1, size=num_buildings)
    widths = rng.integers(min_w, max_w + 1, size=num_buildings)

    # Canvas: height = tallest possible, width = sum of widths + gaps
    H = max_h
    W = int(sum(widths) + gap * (num_buildings - 1))
    canvas_height = round(max(50, H, W/2))
    canvas_width = max(100, H*2, W)
    canvas = np.ones((canvas_height, canvas_width), dtype=np.uint8)  # white background

    x = max(0, math.floor(canvas.shape[1]/2 - sum(widths+1)/2))
    print(x)
    for w, h in zip(widths, heights):
        # Paint the building as black (0)
        if h > 0 and w > 0:
            canvas[0:h, x:x+w] = 0

            # Add 1x1 white "windows" inside the building:
            # - window columns at offsets 1, 3, 5, ... (leaving a 1-cell margin)
            # - window rows at 1, 3, 5, ... up to height
            # This yields 2 windows per "floor" for width 5, as requested.
            x_offsets = range(1, max(1, w-1), 2)  # 1,3,5,... < w
            y_offsets = range(1, h-1, 2)            # 1,3,5,... < h
            for xo in x_offsets:
                for yo in y_offsets:
                    canvas[yo, x + xo] = 2  # carve a white pixel window

        x += w + gap  # move to next building start (with gap)

    fig = px.imshow(
        canvas,
        origin='lower',
        aspect='equal',
        zmin=0, zmax=2,
        color_continuous_scale=[[0, 'black'], [0.5, '#56A2FF'], [1, "white"]],
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_showscale=False,
        title=f'Buildings: {num_buildings}, heights {min_h}-{max_h}, widths {min_w}-{max_w}',
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


with ui.card().classes('w-full max-w-4xl mx-auto'):
    ui.label('Building Row with Random Widths + Windows').classes('text-xl font-medium')

    with ui.row().classes('items-end gap-4'):
        num_buildings = ui.number('num_buildings', value=10, min=1, step=1, format='%d')
        min_height = ui.number('min_height', value=5, min=0, step=1, format='%d')
        max_height = ui.number('max_height', value=20, min=0, step=1, format='%d')
        min_width = ui.number('min_width', value=3, min=1, step=1, format='%d')
        max_width = ui.number('max_width', value=7, min=1, step=1, format='%d')

    with ui.row().classes('items-center gap-6 mt-2'):
        auto_switch = ui.switch('auto-regenerate', value=True)
        manual_button = ui.button('Regenerate now', color='primary')


    plot = ui.plotly(make_city_fig(num_buildings.value,
                                   min_height.value, max_height.value,
                                   min_width.value, max_width.value)).classes('w-full h-[600px]')

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

        plot.figure = make_city_fig(num_buildings.value,
                                    mn_h, mx_h,
                                    mn_w, mx_w)
        plot.update()

    # when any param changes: only regenerate if auto mode is ON
    def maybe_regenerate(*_):
        if auto_switch.value:
            regenerate()

    for field in (num_buildings, min_height, max_height, min_width, max_width):
        field.on_value_change(maybe_regenerate)

    # manual regenerate button
    manual_button.on_click(regenerate)


# Change host/port if 8080 is in use:
# ui.run(host='0.0.0.0', port=8081)
ui.run()
