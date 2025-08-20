import math

import numpy as np
import plotly.express as px

STAR_DENSITY = 0.01  # fraction of sky pixels that become stars at night

# One master palette for all colors (IDs -> RGB)
colour_dict = {
    0: [70, 70, 70],  # buildings: black
    1: [86, 162, 255],  # day sky: light blue
    2: [255, 215, 0],  # yellow/gold (sun, moon, or windows at night)
    3: [255, 255, 255],  # white (windows at day, stars, etc.)
    4: [10, 20, 60],  # night sky: very dark blue,
    5: [255, 255, 150],  # stars
}


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
    Return a (size x size) uint8 array with a circular sun and radial spikes on a bg background.
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


def sprinkle_stars(
    canvas: np.ndarray,
    sky_code: int,
    star_code: int,
    density: float,
    rng: np.random.Generator,
    min_star_height: int,
):
    """Randomly set ~density fraction of sky pixels to star_code (1px stars)."""
    sky_mask = canvas == sky_code
    sky_coords = np.argwhere(sky_mask)
    sky_coords = sky_coords[sky_coords[:, 0] > min_star_height]
    if sky_coords.size == 0:
        return
    n = max(1, int(len(sky_coords) * density))
    n = min(n, len(sky_coords))
    idx = rng.choice(len(sky_coords), size=n, replace=False)
    sel = sky_coords[idx]
    canvas[sel[:, 0], sel[:, 1]] = star_code


def add_clouds(
    canvas: np.ndarray,
    sky_code: int,
    cloud_code: int,
    n_clouds: int = 6,
    rng: np.random.Generator | None = None,
    min_circles_per_cloud: int = 3,
    max_circles_per_cloud: int = 7,
    min_radius: int = 4,
    max_radius: int = 10,
    min_y: int = 0,
    max_y: int | None = None,
    margin_x: int = 10,
):
    """
    Add fluffy white clouds with flat bottoms.
    Each cloud = several overlapping circles, then cropped flat along a baseline.
    """

    if rng is None:
        rng = np.random.default_rng()

    H, W = canvas.shape
    if max_y is None:
        max_y = H

    for _ in range(max(0, int(n_clouds))):
        # choose baseline row (cloud bottom)
        base_y = int(rng.integers(max(min_y, 0), max(max_y, H)))
        cx = int(rng.integers(margin_x, max(W - margin_x, margin_x + 1)))

        # temporary mask for the cloud
        mask = np.zeros_like(canvas, dtype=bool)

        # place overlapping circles above the baseline
        k = int(rng.integers(min_circles_per_cloud, max_circles_per_cloud + 1))
        for _ in range(k):
            r = int(rng.integers(min_radius, max_radius + 1))
            jx = int(rng.integers(-r, r + 1))
            jy = int(rng.integers(-r // 2, 1))  # jitter upward, not downward
            cx_i, cy_i = cx + jx, base_y + jy
            if not (0 <= cx_i < W and 0 <= cy_i < H):
                continue
            y0, y1 = max(cy_i - r, 0), min(cy_i + r + 1, H)
            x0, x1 = max(cx_i - r, 0), min(cx_i + r + 1, W)
            yy, xx = np.ogrid[y0:y1, x0:x1]
            mask[y0:y1, x0:x1] |= (xx - cx_i) ** 2 + (yy - cy_i) ** 2 <= r * r

        # enforce flat bottom: clear everything below baseline
        mask[0:base_y, :] = False

        # paint onto canvas only where it's sky
        canvas[mask & (canvas == sky_code)] = cloud_code


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
    CLOUD = 3

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
    canvas = np.full((canvas_height, canvas_width), SKY, dtype=np.uint8)  # 1 = sky blue background

    # tiny sun (values use the palette: 1=blue, 2=yellow, etc.)

    # add sun/moon (top-right, 1px margin)
    if nighttime:
        moon = make_moon(size=20, radius=7, offset=4, bg=SKY, moon_val=CELESTIAL)
        canvas[-moon.shape[0] - 1 : -1, -moon.shape[1] - 1 : -1] = moon
        sprinkle_stars(
            canvas,
            sky_code=SKY,
            star_code=STARS,
            density=STAR_DENSITY,
            rng=rng,
            min_star_height=min_h,
        )

    else:
        sun = make_spiky_sun(
            size=18,
            core_radius=6,
            spike_len=3,
            num_spikes=12,
            bg=SKY,
            sun_val=CELESTIAL,
        )
        canvas[-sun.shape[0] - 1 : -1, -sun.shape[1] - 1 : -1] = sun
        add_clouds(
            canvas,
            sky_code=SKY,
            cloud_code=CLOUD,
            n_clouds=round(num_buildings / 4),
            rng=rng,
            min_circles_per_cloud=2,
            max_circles_per_cloud=7,
            min_radius=1,
            max_radius=round(max_w + max_h) / 4,
            min_y=canvas.shape[0] // 2,  # avoid very low clouds (optional)
            max_y=canvas.shape[0] - 5,  # avoid top 5 rows (optional)
            margin_x=12,
        )

    # center the row of buildings
    total_with_gaps = sum(widths + 1) - 1  # width + 1-gap per building, minus last gap
    x = max(0, math.floor(canvas.shape[1] / 2 - total_with_gaps / 2))

    # draw buildings
    for w, h in zip(widths, heights, strict=False):
        if h > 0 and w > 0:
            # building body: 0 = black
            canvas[0:h, x : x + w] = BUILDING

            # 1x1 windows: set to 3 (white) at columns 1,3,5,... and rows 1,3,5,...
            for xo in range(1, max(1, w - 1), 2):
                for yo in range(1, max(1, h - 1), 2):
                    canvas[yo, x + xo] = WINDOW

            roof_style = rng.choice(["flat", "round", "pointy"])

            if roof_style != "flat":
                # nothing extra, just the rectangular top
                height = max(2, w // 2)
                iterator = range(0, height, 2) if roof_style == "round" else range(height)
                for dy in iterator:
                    span = int((height - dy) * 2) if w % 2 == 0 else int((height - dy) * 2 - 1)

                    xl = max(x + (w - span) // 2, 0)
                    xr = min(xl + span, canvas.shape[1])
                    y = h + (dy // 2 if roof_style == "round" else dy)
                    if y < canvas.shape[0]:
                        canvas[y, xl:xr] = BUILDING

        x += w + gap

    # map to RGB pixels and plot
    rgb = to_rgb(canvas, colour_dict)  # (H,W,3) uint8
    fig = px.imshow(rgb, origin="lower", aspect="equal")

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        # title=f"Buildings: {num_buildings}, heights {min_h}-{max_h}, widths {min_w}-{max_w}",
        xaxis_visible=False,
        yaxis_visible=False,
        autosize=True,
    )
    return fig
