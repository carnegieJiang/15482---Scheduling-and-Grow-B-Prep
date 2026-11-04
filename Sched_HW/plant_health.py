import foliage, measure
import cv2
import numpy as np
from cv_utils import overlayMask
# Given an image, an instance of foliage.FoliageClassifier, and
#    an instance of mesure.MeasureHeight, return three values:
# 1. An image with all non-foliage parts masked out
# 2. The original image with overlaid with the stick mask and
#    a line at the height of the foliage, if any
# 3. The height of the foliage
def foliageImages (target_image, classifier, measurer):
    foliage_image, height_image, height = None, None, -1
    # BEGIN STUDENT CODE
    # Classify each pixel as foliage or background.
    foliage_mask = classifier.classify(target_image)

    # Convert the mask to a binary uint8 image.
    foliage_mask = (foliage_mask >= 128).astype(np.uint8) * 255

    # Keep the original colors only where the mask indicates foliage.
    foliage_image = cv2.bitwise_and(
        target_image,
        target_image,
        mask=foliage_mask
    )

    height, top_row = measurer.measure(foliage_mask)

    # Highlight the reference stick region on the original image.
    height_image = overlayMask(
        target_image,
        measurer.stick_mask,
        color=(0, 255, 255),
        alpha=0.5
    )

    # Draw the measured height only when a valid row is available.
    if top_row is not None:
        columns = np.flatnonzero(measurer.stick_mask[top_row] > 0)

        if columns.size > 0:
            left = max(0, int(columns[0]) - 10)
            right = min(target_image.shape[1] - 1, int(columns[-1]) + 10)

            cv2.line(
                height_image,
                (left, top_row),
                (right, top_row),
                color=(0, 0, 255),
                thickness=5
            )
    # END STUDENT CODE
    return foliage_image, height_image, height

# Given an image, return two values:
# 1. The percentage of foliage in the image
# 2. The height of the plans
# 2. An estimate of the plant health (as a string), compared to the reference
#    foliage percentage and height.
def plantHealth (target_image, classifier, measurer, prev_greenery, prev_height):
    greenery, height, health_msg = 0, 0, ""
    # BEGIN STUDENT CODE
    # Detect foliage and convert the prediction to a binary mask.
    foliage_mask = classifier.classify(target_image)
    foliage_mask = (foliage_mask >= 128).astype(np.uint8) * 255

    # Calculate the fraction of image pixels classified as foliage.
    greenery = np.count_nonzero(foliage_mask) / foliage_mask.size

    # Measure the height of foliage overlapping the reference stick.
    height, _ = measurer.measure(foliage_mask)

    if prev_greenery == 0 and prev_height == 0:
        health_msg = "ok: initial measurement; no previous comparison"

    else:
        increases = []
        decreases = []

        greenery_change = greenery - prev_greenery

        if greenery_change >= 0.01:
            increases.append("foliage coverage increased")
        elif greenery_change <= -0.01:
            decreases.append("foliage coverage decreased")

        # None means height could not be measured, rather than zero height.
        if height is not None and prev_height is not None:
            height_change = height - prev_height

            if height_change >= 0.5:
                increases.append("plant height increased")
            elif height_change <= -0.5:
                decreases.append("plant height decreased")

        if increases and decreases:
            # The two measurements show conflicting changes.
            health_msg = (
                "ok: mixed changes; "
                + "; ".join(increases + decreases)
            )
        elif decreases:
            health_msg = "bad: " + "; ".join(decreases)
        elif increases:
            health_msg = "good: " + "; ".join(increases)
        else:
            health_msg = "ok: no substantial measured change"
        
        if height is None or prev_height is None:
            health_msg += "; height comparison unavailable"
    # END STUDENT CODE
    return greenery, height, health_msg

