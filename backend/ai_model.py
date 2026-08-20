import os
import io
from PIL import Image, ImageChops, ImageEnhance
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pth")

# Try loading PyTorch if installed, otherwise fallback to Lightweight Serverless Forensic Classifier
HAS_TORCH = False
try:
    import torch
    import torch.nn as nn
    from torchvision import transforms, models
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

class ForgeryClassifier:
    def __init__(self):
        self.has_torch = HAS_TORCH
        if self.has_torch:
            try:
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self.model = self._load_torch_model()
                self.transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                ])
                print("PyTorch MobileNetV2 Classifier initialized successfully!")
            except Exception as e:
                print(f"Error initializing PyTorch model: {e}. Falling back to Lightweight Forensic Classifier.")
                self.has_torch = False
        else:
            print("Running in Lightweight Vercel Serverless Mode (No PyTorch). Using ELA Feature Classifier.")

    def _load_torch_model(self):
        model = models.mobilenet_v2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, 2)

        if os.path.exists(MODEL_PATH):
            try:
                model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
                print(f"AI Classifier weights loaded from: {MODEL_PATH}")
            except Exception as e:
                print(f"Warning loading trained model weights: {e}")

        model.to(self.device)
        model.eval()
        return model

    def predict(self, pil_image):
        """
        Classifies input certificate image.
        Returns: (verdict_label, genuine_probability, suspicious_probability)
        """
        if self.has_torch:
            try:
                img_tensor = self.transform(pil_image.convert("RGB")).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    outputs = self.model(img_tensor)
                    probabilities = torch.softmax(outputs, dim=1)[0]
                    genuine_prob = float(probabilities[0].item())
                    suspicious_prob = float(probabilities[1].item())

                label = "Genuine" if genuine_prob >= suspicious_prob else "Suspicious"
                return label, round(genuine_prob * 100, 2), round(suspicious_prob * 100, 2)
            except Exception as e:
                print(f"PyTorch prediction error: {e}. Falling back to ELA Feature Classifier.")

        # Lightweight Serverless ELA & Noise Feature Classifier
        orig_pil = pil_image.convert("RGB")
        buffer = io.BytesIO()
        orig_pil.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)
        compressed_pil = Image.open(buffer)

        ela_diff = ImageChops.difference(orig_pil, compressed_pil)
        ela_np = np.array(ela_diff)
        mean_diff = float(np.mean(ela_np))
        max_diff = float(np.max(ela_np))

        # Genuine documents have low uniform ELA error (< 8.0), manipulated images exhibit high variance
        if mean_diff < 12.0 and max_diff < 120:
            genuine_prob = max(65.0, 95.0 - (mean_diff * 2.0))
        else:
            genuine_prob = max(10.0, 50.0 - (mean_diff * 2.5))

        genuine_prob = round(min(98.0, max(5.0, genuine_prob)), 2)
        suspicious_prob = round(100.0 - genuine_prob, 2)
        label = "Genuine" if genuine_prob >= suspicious_prob else "Suspicious"

        return label, genuine_prob, suspicious_prob

# Global Singleton Instance
classifier_instance = ForgeryClassifier()

def classify_certificate(pil_image):
    return classifier_instance.predict(pil_image)
