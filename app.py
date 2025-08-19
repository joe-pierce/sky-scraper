# pip install nicegui plotly numpy
from nicegui import ui
import numpy as np
import plotly.express as px
import math

# One master palette for all colors (IDs -> RGB)
colour_dict = {
    0: [70, 70, 70],  # buildings: black
    1: [86, 162, 255],  # day sky: light blue
    2: [255, 215, 0],  # yellow/gold (sun, moon, or windows at night)
    3: [255, 255, 255],  # white (windows at day, stars, etc.)
    4: [10, 20, 60],  # night sky: very dark blue,
    5: [255, 255, 150] # stars
}

STAR_DENSITY = 0.01  # fraction of sky pixels that become stars at night 


def to_rgb(
    canvas: np.ndarray, palette: dict[int, list[int]], default=(255, 255, 255)
) -> np.ndarray:
    """Map integer canvas -> (H,W,3) uint8 RGB using a palette dict."""
    size = int(max(canvas.max(), max(palette.keys()))) + 1
    lut = np.tile(np.array(default, dtype=np.uint8), (size, 1))
    for k, rgb in palette.items():
        lut[int(k)] = np.array(rgb, dtype=np.uint8)
    return lut[canvas]  # (H,W,3)


def make_spiky_sun(
    size: int = 20,
    core_radius: int = 6,
    spike_len: int = 4,
    num_spikes: int = 12,
    bg: int = 1,
    sun_val: int = 2,
    thickness: int = 1,
) -> np.ndarray:
    """
    Return a (size x size) uint8 array with a circular sun (sun_val) and radial spikes on a bg background.
    - core_radius: radius of the filled circle
    - spike_len: length of spikes extending beyond the core
    - num_spikes: number of spikes around the circle
    - thickness: pixel thickness of spikes (1 or 2 look best at 20x20)
    """
    size = int(size)
    sun = np.full((size, size), bg, dtype=np.uint8)

    # center at pixel center for symmetry (works well for even sizes like 20)
    cx = (size - 1) / 2.0
    cy = (size - 1) / 2.0

    # filled circular core
    yy, xx = np.ogrid[:size, :size]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    sun[dist <= core_radius] = sun_val

    # radial spikes
    angles = np.linspace(0.0, 2.0 * np.pi, num_spikes, endpoint=False)
    for theta in angles:
        for r in range(core_radius, core_radius + spike_len + 1):
            x = int(round(cx + r * np.cos(theta)))
            y = int(round(cy + r * np.sin(theta)))
            if 0 <= x < size and 0 <= y < size:
                sun[y, x] = sun_val
                if thickness >= 2:
                    # thicken by touching neighbors orthogonal to ray direction
                    # (simple 4-neighborhood; looks good at small sizes)
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        xx2, yy2 = x + dx, y + dy
                        if 0 <= xx2 < size and 0 <= yy2 < size:
                            sun[yy2, xx2] = sun_val

    return sun


def make_moon(
    size: int = 20, radius: int = 7, offset: int = 4, bg: int = 1, moon_val: int = 2
) -> np.ndarray:
    """Crescent moon (☾): big disc minus a shifted disc."""
    size = int(size)
    arr = np.full((size, size), bg, dtype=np.uint8)
    cx = (size - 1) / 2.0
    cy = (size - 1) / 2.0
    yy, xx = np.ogrid[:size, :size]
    dist_main = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    dist_cut = np.sqrt((xx - (cx + offset)) ** 2 + (yy - cy) ** 2)
    arr[dist_main <= radius] = moon_val
    arr[dist_cut <= radius] = bg
    return arr

def sprinkle_stars(canvas: np.ndarray, sky_code: int, star_code: int, density: float, rng: np.random.Generator, min_star_height: int):
    """Randomly set ~density fraction of sky pixels to star_code (1px stars)."""
    sky_mask = (canvas == sky_code)
    sky_coords = np.argwhere(sky_mask)
    sky_coords = sky_coords[sky_coords[:, 0] > min_star_height]
    if sky_coords.size == 0:
        return
    n = max(1, int(len(sky_coords) * density))
    n = min(n, len(sky_coords))
    idx = rng.choice(len(sky_coords), size=n, replace=False)
    sel = sky_coords[idx]
    canvas[sel[:, 0], sel[:, 1]] = star_code


def make_city_fig(
    num_buildings: int,
    min_h: int,
    max_h: int,
    min_w: int,
    max_w: int,
    nighttime: bool,
    gap: int = 1,
):
    BUILDING = 0
    SKY = 4 if nighttime else 1
    WINDOW = 2 if nighttime else 3
    CELESTIAL = 2
    STARS = 5

    # sanitize inputs
    num_buildings = max(1, int(num_buildings or 1))
    min_h = max(0, int(min_h or 0))
    max_h = max(min_h, int(max_h or min_h))
    min_w = max(1, int(min_w or 1))
    max_w = max(min_w, int(max_w or min_w))

    rng = np.random.default_rng()
    heights = rng.integers(min_h, max_h + 1, size=num_buildings)
    widths = rng.integers(min_w, max_w + 1, size=num_buildings)

    # Canvas size (a bit generous so everything fits and can be centered)
    H = max_h
    W = int(sum(widths) + gap * (num_buildings - 1))
    canvas_height = round(max(50, H, W / 2))
    canvas_width = max(100, H * 2, W)
    canvas = np.full(
        (canvas_height, canvas_width), SKY, dtype=np.uint8
    )  # 1 = sky blue background

    # tiny sun (values use the palette: 1=blue, 2=yellow, etc.)

    # add sun/moon (top-right, 1px margin)
    if nighttime:
        moon = make_moon(size=20, radius=7, offset=4, bg=SKY, moon_val=CELESTIAL)
        canvas[-moon.shape[0] - 1 : -1, -moon.shape[1] - 1 : -1] = moon
        sprinkle_stars(canvas, sky_code=SKY, star_code=STARS, density=STAR_DENSITY, rng=rng, min_star_height=min_h)

    else:
        sun = make_spiky_sun(
            size=20,
            core_radius=6,
            spike_len=4,
            num_spikes=12,
            bg=SKY,
            sun_val=CELESTIAL,
        )
        canvas[-sun.shape[0] - 1 : -1, -sun.shape[1] - 1 : -1] = sun

    # center the row of buildings
    total_with_gaps = sum(widths + 1) - 1  # width + 1-gap per building, minus last gap
    x = max(0, math.floor(canvas.shape[1] / 2 - total_with_gaps / 2))

    # draw buildings
    for w, h in zip(widths, heights):
        if h > 0 and w > 0:
            # building body: 0 = black
            canvas[0:h, x : x + w] = BUILDING

            # 1x1 windows: set to 3 (white) at columns 1,3,5,... and rows 1,3,5,...
            for xo in range(1, max(1, w - 1), 2):
                for yo in range(1, max(1, h - 1), 2):
                    canvas[yo, x + xo] = WINDOW

        x += w + gap

    # map to RGB pixels and plot
    rgb = to_rgb(canvas, colour_dict)  # (H,W,3) uint8
    fig = px.imshow(rgb, origin="lower", aspect="equal")

    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        # title=f"Buildings: {num_buildings}, heights {min_h}-{max_h}, widths {min_w}-{max_w}",
        xaxis_visible=False,
        yaxis_visible=False,
    )
    return fig


with ui.card().classes("w-full mx-auto"):
    ui.label("Skyline generator").classes(
        "text-xl font-medium"
    )

    with ui.row().classes("items-end gap-4"):
        num_buildings = ui.number("num_buildings", value=10, min=1, step=1, format="%d")
    with ui.row().classes("items-end gap-4"):
        min_height = ui.number("min_height", value=5, min=0, step=1, format="%d")
        max_height = ui.number("max_height", value=20, min=0, step=1, format="%d")
    with ui.row().classes("items-end gap-4"):
        min_width = ui.number("min_width", value=3, min=1, step=1, format="%d")
        max_width = ui.number("max_width", value=7, min=1, step=1, format="%d")

    with ui.row().classes("items-center gap-6 mt-2"):
        night_switch = ui.switch("nighttime", value=False)
        auto_switch = ui.switch("auto-regenerate", value=True)
        manual_button = ui.button("Regenerate now", color="primary")

    plot = ui.plotly(
        make_city_fig(
            num_buildings.value,
            min_height.value,
            max_height.value,
            min_width.value,
            max_width.value,
            night_switch.value,
        )
    ).classes("w-full h-[600px]")

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

        plot.figure = make_city_fig(
            num_buildings.value, mn_h, mx_h, mn_w, mx_w, night_switch.value
        )
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
