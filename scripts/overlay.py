from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


BOX_COLORS = {
    "A": (230, 57, 70),
    "B": (0, 155, 210),
    "C": (38, 166, 91),
    "D": (170, 80, 210),
    "E": (242, 142, 43),
    "F": (40, 90, 220),
    "G": (190, 45, 110),
    "H": (0, 130, 120),
    "I": (125, 95, 40),
    "J": (80, 80, 80),
    "K": (110, 145, 20),
    "L": (210, 80, 20),
}


def _scaled_box(
    bbox: dict[str, Any],
    *,
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
) -> tuple[int, int, int, int]:
    scale_x = target_width / source_width
    scale_y = target_height / source_height
    x1 = round(float(bbox["x"]) * scale_x)
    y1 = round(float(bbox["y"]) * scale_y)
    x2 = round((float(bbox["x"]) + float(bbox["width"])) * scale_x)
    y2 = round((float(bbox["y"]) + float(bbox["height"])) * scale_y)
    return (
        max(0, min(x1, target_width - 1)),
        max(0, min(y1, target_height - 1)),
        max(1, min(x2, target_width)),
        max(1, min(y2, target_height)),
    )


def draw_labeled_boxes(
    image_path: str | Path,
    record: dict[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    """Render grounded A-L boxes without changing the underlying image."""
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=max(14, round(min(image.size) * 0.035)))
    source_width = int(record.get("image_width") or image.width)
    source_height = int(record.get("image_height") or image.height)
    stroke = max(3, round(min(image.size) * 0.007))
    label_padding = max(3, stroke)
    rendered_boxes = []

    color_palette = tuple(BOX_COLORS.values())
    for box_index, box in enumerate(record["boxes"]):
        label = str(box["label"])
        color = BOX_COLORS.get(
            label,
            color_palette[box_index % len(color_palette)],
        )
        coordinates = _scaled_box(
            box["bbox"],
            source_width=source_width,
            source_height=source_height,
            target_width=image.width,
            target_height=image.height,
        )
        draw.rectangle(coordinates, outline=color, width=stroke)
        rendered_boxes.append(
            {
                "label": label,
                "color": color,
                "source_bbox": box["bbox"],
                "rendered_bbox": list(coordinates),
            }
        )

    occupied_badges: list[tuple[int, int, int, int]] = []
    for rendered in rendered_boxes:
        label = str(rendered["label"])
        color = rendered.pop("color")
        coordinates = tuple(rendered["rendered_bbox"])
        text_bbox = draw.textbbox((0, 0), label, font=font, stroke_width=1)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        badge_width = text_width + 2 * label_padding
        badge_height = text_height + 2 * label_padding
        x1, y1, x2, y2 = coordinates
        anchors = [
            (x1, y1 - badge_height),
            (x1, y1),
            (x2 - badge_width, y1 - badge_height),
            (x2 - badge_width, y1),
            (x1, y2 - badge_height),
            (x2 - badge_width, y2 - badge_height),
        ]

        candidates = []
        for anchor_x, anchor_y in anchors:
            badge_x = max(0, min(anchor_x, image.width - badge_width))
            badge_y = max(0, min(anchor_y, image.height - badge_height))
            badge = (
                badge_x,
                badge_y,
                badge_x + badge_width,
                badge_y + badge_height,
            )
            overlap = sum(
                max(0, min(badge[2], other[2]) - max(badge[0], other[0]))
                * max(0, min(badge[3], other[3]) - max(badge[1], other[1]))
                for other in occupied_badges
            )
            candidates.append((overlap, badge))
        _, badge = min(candidates, key=lambda candidate: candidate[0])
        badge_x, badge_y = badge[:2]
        draw.rectangle(badge, fill=color)
        draw.text(
            (badge_x + label_padding, badge_y + label_padding),
            label,
            fill=(255, 255, 255),
            font=font,
            stroke_width=1,
            stroke_fill=(0, 0, 0),
        )
        occupied_badges.append(badge)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    return {
        "output_path": str(output),
        "width": image.width,
        "height": image.height,
        "rendered_boxes": rendered_boxes,
    }
