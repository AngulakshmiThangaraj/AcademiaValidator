import os
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pth")

class ForgeryClassifier:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model()
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def _load_model(self):
        model = models.mobilenet_v2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, 2)

        if os.path.exists(MODEL_PATH):
            try:
                model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
                print(f"AI Classifier loaded successfully from: {MODEL_PATH}")
            except Exception as e:
                print(f"Warning loading trained model: {e}. Initializing default MobileNetV2 architecture.")
        else:
            print("Model weights file 'model.pth' not found. Using initialized MobileNetV2 network.")

        model.to(self.device)
        model.eval()
        return model

    def predict(self, pil_image):
        """
        Classifies input certificate image.
        Returns: (verdict_label, genuine_probability, suspicious_probability)
        """
        img_tensor = self.transform(pil_image.convert("RGB")).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(img_tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]
            genuine_prob = float(probabilities[0].item())
            suspicious_prob = float(probabilities[1].item())

        label = "Genuine" if genuine_prob >= suspicious_prob else "Suspicious"
        return label, round(genuine_prob * 100, 2), round(suspicious_prob * 100, 2)

# Global Singleton Instance
classifier_instance = ForgeryClassifier()

def classify_certificate(pil_image):
    return classifier_instance.predict(pil_image)
