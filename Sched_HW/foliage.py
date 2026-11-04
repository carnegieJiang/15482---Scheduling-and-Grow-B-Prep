# NEXT YEAR - SEE ABOUT USING PYTORCH DIRECTLY (PKL a pytorch model?)

import cv2, numpy as np
from cv_utils import *
from cv_learn import *
import torch
from torch import nn


# Detect the plants in the image using a classifier model (of type MLearn).
# If modelfilename is None, create a model, o/w load it in
class FoliageClassifier(Classifier):
    def __init__(self, modelfilename=None):
        super(FoliageClassifier, self).__init__(modelfilename)
        # Add any desired initialization options
        # BEGIN STUDENT CODE
        self.scale_factor = 0.25
        # END STUDENT CODE

    def createModel(self):
        # If you want to use this class to train your model, fill in this function
        # Return an ML model to be trained to classify foliage
        model = CNN_model()
        # BEGIN STUDENT CODE
        # END STUDENT CODE
        return model

    def preprocessImage(self, image):
        # Process the image as needed in preparation for training, testing, and classifying
        #   (e.g., normalizing, reshaping, changing color space)
        # BEGIN STUDENT CODE
        # print(f"ppi raw image shape: {image.shape}")
        resized = cv2.resize(image, None, fx = self.scale_factor, fy = self.scale_factor) # Order is width, height
        # print(f"ppi before shape: {resized.shape}")
        # Should change images from [246, 328, 3] to [3, 246, 328]
        resized_t = resized.transpose(2, 0, 1) 
        normalized = resized_t.astype(np.float32) / 255.0
        # print(f"ppi after shape: {normalized.shape}")
        # END STUDENT CODE
        return normalized

    def preprocessMask(self, mask):
        # Process the mask as needed in preparation for training, testing, and classifying
        #   (e.g., reshaping)
        # BEGIN STUDENT CODE
        # Masks should be 2d array and might have to be for autograder
        # print(f"prpm raw mask shape: {mask.shape}")
        resized = cv2.resize(mask, None, fx = self.scale_factor, fy = self.scale_factor) # Order is width, height
        resized = np.expand_dims(resized, axis=0)
        # Masks dimension is probably later converted to [N, 1, H, W] anyway
        normalized = resized.astype(np.float32) / 255.0
        # print(f"prpm after shape: {normalized.shape}")
        # print("prepm values")
        # print(normalized[0][100])
        # print(normalized[0][150])
        # print(normalized[0][50])
        # END STUDENT CODE
        return normalized

    def postprocessMask(self, mask, orig_shape):
        # Add any fine-tuning steps (e.g., reshaping to the orig_shape, eliminating small patches/noise)
        # BEGIN STUDENT CODE
        # Masks are inputted as 2d arrays? 
        # Masks might already be rescaled to 0 to 255
        # print(f"Orig shape{orig_shape}")
        # print(f"popm raw mask shape: {mask.shape}")
        resized = cv2.resize(mask, (orig_shape[1], orig_shape[0])) # Order is width, height
        # print(f"popm after shape: {resized.shape}")
        # END STUDENT CODE
        return resized

class CNN_model(nn.Module):
    def __init__(self):
        super().__init__()
        self.cnn_relu_stack = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 1, kernel_size=1),
        )
    
    def forward(self, x):
        # print(f"Input shape:{x.shape}")
        image_out = self.cnn_relu_stack(x)
        # For autograder output probably needs to be shape [n, 1, 246, 328]
        # print(f"Output shape:{image_out.shape}")
        return image_out

