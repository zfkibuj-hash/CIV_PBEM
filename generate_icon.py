"""
Generate application icon: a speeding envelope with a floppy disk inside.
Run this script once to create icon.ico, then build the app.

Requirements: pip install Pillow
"""
from PIL import Image, ImageDraw, ImageFont
import math


def draw_icon(size: int) -> Image.Image:
    """Draw the icon at a given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Scale factor
    s = size / 256

    # === Speed lines (behind envelope) ===
    line_color = (100, 180, 255, 160)
    line_width = max(1, int(3 * s))
    for i, y_offset in enumerate([60, 128, 196]):
        y = int(y_offset * s)
        x_start = int(10 * s)
        x_end = int((50 + i * 15) * s)
        draw.line([(x_start, y), (x_end, y)], fill=line_color, width=line_width)

    # === Envelope body ===
    # Envelope rectangle (slightly tilted forward for "speed" feel)
    env_left = int(60 * s)
    env_top = int(55 * s)
    env_right = int(240 * s)
    env_bottom = int(200 * s)
    env_color = (240, 240, 240, 255)
    env_border = (80, 80, 80, 255)

    # Draw envelope body
    draw.rounded_rectangle(
        [env_left, env_top, env_right, env_bottom],
        radius=int(8 * s),
        fill=env_color,
        outline=env_border,
        width=max(1, int(3 * s))
    )

    # Envelope flap (triangle at top)
    flap_color = (220, 220, 220, 255)
    flap_points = [
        (env_left, env_top),
        (env_right, env_top),
        (int(150 * s), int(130 * s)),  # center point going down
    ]
    draw.polygon(flap_points, fill=flap_color, outline=env_border)

    # Envelope fold lines (V shape for the flap opening)
    mid_x = int(150 * s)
    draw.line(
        [(env_left, env_top), (mid_x, int(120 * s))],
        fill=env_border, width=max(1, int(2 * s))
    )
    draw.line(
        [(env_right, env_top), (mid_x, int(120 * s))],
        fill=env_border, width=max(1, int(2 * s))
    )

    # === Floppy disk (inside envelope, peeking out from top) ===
    floppy_left = int(110 * s)
    floppy_top = int(70 * s)
    floppy_right = int(190 * s)
    floppy_bottom = int(170 * s)
    floppy_color = (50, 50, 180, 255)  # Classic blue floppy
    floppy_border = (30, 30, 120, 255)

    # Floppy body
    draw.rounded_rectangle(
        [floppy_left, floppy_top, floppy_right, floppy_bottom],
        radius=int(4 * s),
        fill=floppy_color,
        outline=floppy_border,
        width=max(1, int(2 * s))
    )

    # Metal slider area (top of floppy)
    slider_left = int(125 * s)
    slider_top = int(70 * s)
    slider_right = int(175 * s)
    slider_bottom = int(100 * s)
    draw.rectangle(
        [slider_left, slider_top, slider_right, slider_bottom],
        fill=(180, 180, 180, 255),
        outline=(100, 100, 100, 255),
        width=max(1, int(1 * s))
    )

    # Slider slot
    slot_left = int(135 * s)
    slot_top = int(75 * s)
    slot_right = int(155 * s)
    slot_bottom = int(95 * s)
    draw.rectangle(
        [slot_left, slot_top, slot_right, slot_bottom],
        fill=(60, 60, 60, 255)
    )

    # Label area on floppy
    label_left = int(120 * s)
    label_top = int(115 * s)
    label_right = int(180 * s)
    label_bottom = int(165 * s)
    draw.rectangle(
        [label_left, label_top, label_right, label_bottom],
        fill=(240, 240, 240, 255),
        outline=(150, 150, 150, 255),
        width=max(1, int(1 * s))
    )

    # "CIV" text on label
    try:
        font_size = int(16 * s)
        font = ImageFont.truetype("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    text = "CIV"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (label_left + label_right) // 2 - tw // 2
    ty = (label_top + label_bottom) // 2 - th // 2
    draw.text((tx, ty), text, fill=(50, 50, 150, 255), font=font)

    # === More speed lines (in front, shorter) ===
    for i, y_offset in enumerate([80, 150, 175]):
        y = int(y_offset * s)
        x_start = int(15 * s)
        x_end = int((35 + i * 8) * s)
        draw.line([(x_start, y), (x_end, y)], fill=line_color, width=max(1, int(2 * s)))

    # === Small motion particles ===
    particle_color = (100, 180, 255, 120)
    for px, py in [(25, 100), (20, 140), (30, 180), (15, 110)]:
        cx = int(px * s)
        cy = int(py * s)
        r = int(3 * s)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=particle_color)

    return img


def main():
    """Generate multi-resolution .ico file."""
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [draw_icon(sz) for sz in sizes]

    # Save as ICO (Windows icon format)
    # The first image is used as the primary, all others as alternatives
    images[-1].save(
        "icon.ico",
        format="ICO",
        sizes=[(sz, sz) for sz in sizes],
        append_images=images[:-1]
    )
    print(f"Generated icon.ico with sizes: {sizes}")

    # Also save a PNG preview
    images[-1].save("icon_preview.png")
    print("Generated icon_preview.png (256x256 preview)")


if __name__ == "__main__":
    main()
