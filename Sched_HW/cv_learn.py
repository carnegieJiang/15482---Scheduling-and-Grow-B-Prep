import numpy as np, dill
from cv_utils import *
from sklearn.model_selection import cross_val_score, KFold
from sklearn.base import BaseEstimator
import torch, torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

def is_torch(model):
    assert model != None, "Model has not been created!"
    if isinstance(model, nn.Module): return True
    elif isinstance(model, BaseEstimator): return False
    else: raise Exception(f"Model is of type {type(model)}, which is not supported")

def _device(model): return next(model.parameters()).device

def loadImages(image_names, directory=""):
    return np.array([readImage(f"{directory}/{image}") for image in image_names])
            
def loadMasks(mask_names, directory=""):
    return np.array([readMask(f"{directory}/{mask}") for mask in mask_names])

def loadModel(modelfilename):
    with open(modelfilename, "rb") as infile:
        model = dill.load(infile)
    if not isinstance(model, nn.Module) and not isinstance(model, BaseEstimator):
        raise Exception(f"{modelfilename} is of type {type(model)}, which is not handled")
    return model

def saveModel(model, modelfilename):
    assert model != None, "Model has not been created!"
    with open(modelfilename, "wb") as outfile:
        dill.dump(model, outfile)

# Model-specific functions needed by Classifier class
class ClassifierHelper:
    def preprocessImages(self, processed_images):
        raise Exception("Need to implement _preprocessImages!")
    def preprocessMasks(self, processed_masks):
        raise Exception("Need to implement _preprocessMasks!")    
    def train(self, model, images, masks): raise Exception("Need to implement _train!")
    def score(self, model, images, masks): raise Exception("Need to implement _score!")
    def test(self, model, images, masks): raise Exception("Need to implement _score!")
    def classify(self, model, image): raise Exception("Need to implement _predict!")
    def crossValidate(self, model, images, masks, cv=10): 
        raise Exception("Need to implement _crossValidate!")

class SklearnHelper(ClassifierHelper):

    def preprocessImages(self, processed_images):
        return np.concatenate(processed_images, axis=0).astype(np.float32)

    def preprocessMasks(self, processed_masks):
        return np.concatenate(processed_masks, axis=0).astype(np.float32)

    def train(self, model, train_images, train_masks, epochs=None):
        model.fit(train_images, train_masks)
        return self.score(model, train_images, train_masks)

    def score(self, model, images, masks):
        return model.score(images, masks)

    def test(self, model, test_images, test_masks):
        return self.score(model, test_images, test_masks)

    def classify(self, model, processed_image):
        mask = model.predict(processed_image)
        return (mask >= 0.5).astype(np.uint8).squeeze() * 255

    def crossValidate(self, model, processed_images, processed_masks, cv=10):
         return cross_val_score(model, processed_images, processed_masks, cv=cv)

class TorchHelper(ClassifierHelper):
    def preprocessImages(self, processed_images):
        return np.stack(processed_images).astype(np.float32)

    def preprocessMasks(self, processed_masks):
        return np.stack(processed_masks).astype(np.float32)

    def _dataset(self, images, masks):
        x = torch.as_tensor(images, dtype=torch.float32).cpu()
        y = torch.as_tensor(masks, dtype=torch.float32).cpu()
        if y.ndim == 3: y = y.unsqueeze(1)  # (N, H, W) -> (N, 1, H, W)
        return TensorDataset(x, y)

    @torch.inference_mode()
    def score(self, model, dataset, batch_size=4):
        loader = DataLoader(dataset, batch_size=batch_size, num_workers=0)
        model.eval()
        correct, total = 0, 0
        for x, y in loader:
            x, y = x.to(_device(model)), y.to(_device(model))
            logits = model(x)
            if logits.shape != y.shape:
                raise ValueError(f"Output shape {logits.shape} != mask shape {y.shape}")
            # sigmoid(logits) >= 0.5 is equivalent to logits >= 0
            predictions = logits >= 0
            correct += (predictions == (y >= 0.5)).sum().item()
            total += y.numel()
        return correct / total

    def _fit(self, model, dataset, batch_size=4, epochs=10, lr=1e-3):
        loader = DataLoader(dataset, batch_size=batch_size, num_workers=0)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        criterion = nn.BCEWithLogitsLoss()
        model.train()
        for i in range(epochs):
            loss_total = 0
            for x, y in loader:
                x, y = x.to(_device(model)), y.to(_device(model))
                optimizer.zero_grad(set_to_none=True)
                logits = model(x)
                loss = criterion(logits, y)
                loss.backward()
                optimizer.step()
                loss_total += loss.item()
            print(f"Epoch {i}: Average loss: {loss_total/len(loader)}")

    def train(self, model, train_images, train_masks, batch_size=4, epochs=10, lr=1e-3):
        dataset = self._dataset(train_images, train_masks)
        self._fit(model, dataset, batch_size=batch_size, epochs=epochs, lr=lr)
        return self.score(model, dataset)

    def test(self, model, test_images, test_masks):
        dataset = self._dataset(test_images, test_masks)
        return self.score(model, dataset)

    def classify(self, model, image):
        model.eval()
        x = torch.as_tensor(image, dtype=torch.float32).to(_device(model))
        with torch.no_grad():
            logits = model(x.unsqueeze(0))
        return (logits >= 0).to(torch.uint8).cpu().numpy().squeeze() * 255

    def crossValidate(self, model_fn, images, masks, cv=10,
                      batch_size=4, epochs=10, lr=1e-3):
        splitter = KFold(n_splits=cv, shuffle=True, random_state=42)
        scores = []
        try:
            for train_idx, test_idx in splitter.split(images):
                train_data = self._dataset([images[i] for i in train_idx],
                                           [masks[i] for i in train_idx])
                test_data = self._dataset([images[i] for i in test_idx],
                                          [masks[i] for i in test_idx])
                # Each fold needs an independent model and optimizer.
                model = model_fn()
                self._fit(model, train_data, epochs, batch_size, lr)
                scores.append(self._score(model, test_data, batch_size))
                del model
        except:
            pass
        return np.asarray(scores)

# A simple class for creating classifiers.  Subclasses for sklearn and torch
# If modelfilename is None, create a model, o/w load it in
class Classifier():
    def __init__(self, modelfilename=None):
        self.model = self.createModel() if modelfilename is None else loadModel(modelfilename) 
        self._helper =  TorchHelper() if is_torch(self.model) else SklearnHelper()
        # Try to make things repeatable
        if ('random_state' in dir(self.model)): self.model.random_state = 42

    def createModel(self):
        # Create a model for training and return the model
        assert False, "Need to implement createModel!"

    def preprocessImage(self, image):
        # Process the image as needed (e.g., normalizing, reshaping, changing color space)
        assert False, "Need to implement preprocessImage!"

    def preprocessImages(self, images):
        processed = [self.preprocessImage(image) for image in images]
        return self._helper.preprocessImages(processed)

    def preprocessMask(self, mask):
        # Process the mask as needed (e.g., reshaping)
        assert False, "Need to implement preprocessMask!"

    def preprocessMasks(self, masks):
        processed = [self.preprocessMask(mask) for mask in masks]
        return self._helper.preprocessMasks(processed)

    def postprocessMask(self, mask, orig_shape):
        # Add any fine-tuning steps (e.g., reshaping to the orig_shape, eliminating small patches/noise)
        assert False, "Need to implement postprocessMask!"

    def train(self, train_images, train_masks, epochs=10):
        score = self._helper.train(self.model, self.preprocessImages(train_images),
                                   self.preprocessMasks(train_masks), epochs=epochs)
        print("Training score: %0.4f" %score)
        return score

    def test(self, test_images, test_masks):
        score = self._helper.score(self.model, self.preprocessImages(test_images),
                                   self.preprocessMasks(test_masks))
        print("Testing score: %0.4f" %score)
        return score

    def classify(self, image):
        mask = self._helper.classify(self.model, self.preprocessImage(image))
        return self.postprocessMask(mask, image.shape[:2])      

    def crossValidate(self, images, masks, cv=10):
        scores = self._helper.crossValidate(self.model, self.preprocessImages(images),
                                            self.preprocessMask(masks), cv)
        print("Crossfold score: %0.4f (std %0.4f)" %(scores.mean(), scores.std()))
        return scores.mean()

