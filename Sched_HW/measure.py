
import cv2, numpy as np
from cv_utils import *
from cv_learn import *
from sklearn.ensemble import RandomForestClassifier
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

class StickClassifier(Classifier):
    def __init__(self, modelfilename=None):
        super().__init__(modelfilename)
        # Add any desired initialization options
        # BEGIN STUDENT CODE
        # END STUDENT CODE

    def createModel(self):
        # If you want to use this class to train your model, fill in this function
        # Return an ML model to be trained to classify foliage
        model = None
        # BEGIN STUDENT CODE
        model = RandomForestClassifier(
            n_estimators=50,
            max_depth=15,
            class_weight="balanced",
            n_jobs=-1,
            random_state=22
        )
        # END STUDENT CODE
        return model

    def preprocessImage(self, image):
        # Process the image as needed in preparation for training, testing, and classifying
        #   (e.g., normalizing, reshaping, changing color space)
        # BEGIN STUDENT CODE
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        image = hsv.reshape(-1, 3).astype(np.float32)
        # END STUDENT CODE
        return image

    def preprocessMask(self, mask):
        # Process the mask as needed in preparation for training, testing, and classifying
        #   (e.g., reshaping)
        # BEGIN STUDENT CODE
        mask = (mask.reshape(-1) > 0).astype(np.uint8)
        # END STUDENT CODE
        return mask

    def postprocessMask(self, mask, orig_shape):
        # Add any fine-tuning steps (e.g., reshaping to the orig_shape, eliminating small patches/noise)
        # BEGIN STUDENT CODE
        mask = mask.reshape(orig_shape).astype(np.uint8)

        kernel = np.ones((3, 3), np.uint8)

        mask = cv2.morphologyEx(
            mask, cv2.MORPH_OPEN, kernel
        )

        # END STUDENT CODE
        return mask

class MeasureHeight:
    def __init__(self, ref_image, stick_mask):
        self.ref_image = ref_image
        self.stick_mask = self.adjustStickMask(stick_mask)
        self.tickMarks = self.findTickMarks(self.ref_image, self.stick_mask)

    def adjustStickMask(self, stick_mask):
        # Do what you want to clean up the stick mask (e.g., erode, fill in any gaps)
        # BEGIN STUDENT CODE
        mask = stick_mask.astype(np.uint8)

        kernel = np.ones((3, 3), np.uint8)

        stick_mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            kernel
        )
        # Keep the main stick and trim uncertain edges before measuring overlap.
        count, labels, stats, _ = cv2.connectedComponentsWithStats(stick_mask, connectivity=8)
        if count > 1:
            largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            stick_mask = (labels == largest).astype(np.uint8) * 255
            widths = np.count_nonzero(stick_mask, axis=1)
            width = float(np.median(widths[widths > 0]))
            size = max(1, int(width * 0.15) // 2 * 2 + 1)
            stick_mask = cv2.erode(stick_mask, np.ones((size, size), np.uint8))
        # END STUDENT CODE
        return stick_mask

    def findTickMarks (self, ref_image, stick_mask):
        # Find the tick marks on the stick.  The tick marks appear every 1cm from the top (9cm)
        #   down to the bottom (1cm).  One way to do it is to mask out the stick in the image and
        #   find the darker areas of the stick, which are the tick marks.  Note that sometimes you
        #   won't be able to find all the marks, so you'll need to interpolate.  Also note that, due
        #   to the angle of the camera, the tick marks are not uniformly spread in the image.
        # See the handout for more hints about how to solve this
        tickMarks = []
        # BEGIN STUDENT CODE
        rows = np.flatnonzero(np.any(stick_mask > 0, axis=1))
        if len(rows) < 3:
            return tickMarks
        first, last = int(rows[0]), int(rows[-1])
        span = last - first + 1
        lightness = cv2.cvtColor(ref_image, cv2.COLOR_BGR2LAB)[:, :, 0]
        profile = np.full(span, np.nan)
        for row in rows:
            columns = np.flatnonzero(stick_mask[row] > 0)
            # Use the middle half of the stick, avoiding mask edges/background.
            trim = len(columns) // 4
            middle = columns[trim:len(columns) - trim]
            profile[row - first] = np.median(lightness[row, middle])
        valid = np.flatnonzero(np.isfinite(profile))
        profile = np.interp(np.arange(span), valid, profile[valid])
        smooth = gaussian_filter1d(profile, max(1.0, span / 700))
        background = gaussian_filter1d(profile, max(3.0, span / 25))
        # Relative local darkness adapts to both illumination and stick color.
        darkness = (background - smooth) / np.maximum(background, 1)
        peaks, properties = find_peaks(
            darkness, distance=max(1, span // 18),
            prominence=max(0.04, 0.15 * np.max(darkness)))
        # End caps and the soil boundary are not centimeter tick marks.
        interior = (peaks > 0.04 * span) & (peaks < 0.94 * span)
        peaks = peaks[interior]
        prominence = properties['prominences'][interior]
        # The usable scale has at most nine ticks (9 cm through 1 cm).
        # Prefer strong dark bands over extra shadows near the base.
        if len(peaks) > 9:
            peaks = np.sort(peaks[np.argsort(prominence)[-9:]])
        if 3 <= len(peaks) < 9:
            spacing = np.median(np.diff(peaks))
            inferred = []
            for left, right in zip(peaks[:-1], peaks[1:]):
                intervals = int(round((right - left) / spacing))
                if intervals >= 2:
                    inferred.extend(np.linspace(left, right, intervals + 1)[1:-1])
            if len(peaks) + len(inferred) <= 9:
                peaks = np.sort(np.r_[peaks, np.rint(inferred).astype(int)])
        tickMarks = [int(first + peak) for peak in peaks]
        # END STUDENT CODE
        return tickMarks


    def measure(self, foliage_mask):
        # Given the foliage mask (as would be returned from FoliageClassifer.classify),
        #   the stick mask, and the tick marks on the stick, find the tallest plant that 
        #   crosses in front of the measuring stick.  
        # NOTE: You don't need the actual image - all the information you need is contained in
        #   the foliage and stick masks
        # Basically, combine the foliage and the stick masks and find the highest point (lowest row)
        #   in which there is both the stick and foliage.
        # Based on the list of tick marks (from findTickMarks), calculate and return the height of 
        #    the tallest plant (in cms) and the row in the image where it appears; 
        #    If the plants cover the top of the stick, return 9cm (maximum tick mark)
        #    If no foliage overlaps the stick, return (None, None)
        stick_mask = self.stick_mask
        height = top_row = None
        # BEGIN STUDENT CODE
        overlap = (
            (stick_mask > 0) & (foliage_mask > 0)
        ).astype(np.uint8)

        widths = np.count_nonzero(stick_mask, axis=1)
        if not np.any(widths):
            return None, None
        width = float(np.median(widths[widths > 0]))
        size = max(1, int(width / 12) // 2 * 2 + 1)
        overlap = cv2.morphologyEx(
            overlap, cv2.MORPH_OPEN, np.ones((size, size), np.uint8))

        # Find connected components
        num_labels, labels, stats, centroids = \
            cv2.connectedComponentsWithStats(
                overlap,
                connectivity=8
            )

        # Remove small overlapping regions
        min_area = max(1, 0.3 * width ** 2)

        valid_components = []

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]

            if area >= min_area:
                valid_components.append(i)

        # No significant overlap
        if len(valid_components) == 0:
            return None, None

        # Find highest point among valid components
        top_row = min(
            stats[i, cv2.CC_STAT_TOP]
            for i in valid_components
        )

        top_row = int(top_row)

        # Convert row to height
        ticks = sorted(self.tickMarks)

        if len(ticks) < 2 or np.any(np.diff(ticks) <= 0):
            return None, None

        # Above 9cm
        if top_row <= ticks[0]:
            return 9.0, int(ticks[0])

        # Extrapolate below the last visible tick, using its local spacing.
        # Eight visible ticks end at 2 cm; nine visible ticks end at 1 cm.
        if top_row >= ticks[-1]:
            last_height = 9 - (len(ticks) - 1)
            fraction = (top_row - ticks[-1]) / (ticks[-1] - ticks[-2])
            return float(max(0.0, last_height - fraction)), top_row

        # Linear interpolation
        for i in range(len(ticks) - 1):
            upper = ticks[i]
            lower = ticks[i + 1]

            if upper <= top_row <= lower:

                upper_height = 9 - i
                lower_height = 8 - i

                ratio = (top_row - upper) / (lower - upper)

                height = upper_height + ratio * (
                    lower_height - upper_height
                )

                break
        # END STUDENT CODE
        return height, top_row

