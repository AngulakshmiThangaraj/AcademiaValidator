import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
from PIL import Image
import numpy as np
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, accuracy_score

DATASET_DIR = os.path.join(os.path.dirname(__file__), "data")
GENUINE_DIR = os.path.join(DATASET_DIR, "genuine")
FORGED_DIR = os.path.join(DATASET_DIR, "forged")
MODEL_SAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "model.pth")
METRICS_SAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "metrics.json")

class CertificateDataset(Dataset):
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        image = Image.open(img_path).convert("RGB")
        label = self.labels[idx]

        if self.transform:
            image = self.transform(image)

        return image, label

def get_transforms():
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomRotation(5),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    return train_transform, val_transform

def build_mobilenet_model():
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    # Replace final classification head
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, 2)
    return model

def train_and_evaluate():
    # Make sure dataset exists
    if not os.path.exists(GENUINE_DIR) or len(os.listdir(GENUINE_DIR)) == 0:
        print("Dataset not found. Generating dataset first...")
        from generate_dataset import create_dataset
        create_dataset(300)

    genuine_files = [os.path.join(GENUINE_DIR, f) for f in os.listdir(GENUINE_DIR) if f.endswith(('.jpg', '.png'))]
    forged_files = [os.path.join(FORGED_DIR, f) for f in os.listdir(FORGED_DIR) if f.endswith(('.jpg', '.png'))]

    all_paths = genuine_files + forged_files
    all_labels = [0] * len(genuine_files) + [1] * len(forged_files) # 0: Genuine, 1: Forged

    # Shuffle and split 70% Train, 15% Val, 15% Test
    np.random.seed(42)
    indices = np.arange(len(all_paths))
    np.random.shuffle(indices)

    num_samples = len(indices)
    train_end = int(num_samples * 0.7)
    val_end = int(num_samples * 0.85)

    train_idx = indices[:train_end]
    val_idx = indices[train_end:val_end]
    test_idx = indices[val_end:]

    train_paths, train_labels = [all_paths[i] for i in train_idx], [all_labels[i] for i in train_idx]
    val_paths, val_labels = [all_paths[i] for i in val_idx], [all_labels[i] for i in val_idx]
    test_paths, test_labels = [all_paths[i] for i in test_idx], [all_labels[i] for i in test_idx]

    train_transform, val_transform = get_transforms()

    train_dataset = CertificateDataset(train_paths, train_labels, transform=train_transform)
    val_dataset = CertificateDataset(val_paths, val_labels, transform=val_transform)
    test_dataset = CertificateDataset(test_paths, test_labels, transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

    print(f"Dataset Split -> Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset)}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")

    model = build_mobilenet_model().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.0003)

    epochs = 4
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        epoch_loss = running_loss / total
        epoch_acc = correct / total
        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {epoch_loss:.4f}, Accuracy: {epoch_acc:.4f}")

    # Evaluate on Test Set
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.numpy())

    cm = confusion_matrix(all_targets, all_preds)
    acc = accuracy_score(all_targets, all_preds)
    prec = precision_score(all_targets, all_preds, zero_division=0)
    rec = recall_score(all_targets, all_preds, zero_division=0)
    f1 = f1_score(all_targets, all_preds, zero_division=0)

    print("\n--- Model Evaluation Results ---")
    print(f"Accuracy  : {acc * 100:.2f}%")
    print(f"Precision : {prec * 100:.2f}%")
    print(f"Recall    : {rec * 100:.2f}%")
    print(f"F1-Score  : {f1 * 100:.2f}%")
    print("Confusion Matrix:\n", cm)

    # Save model weights
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"Model saved to: {MODEL_SAVE_PATH}")

    # Save metrics
    metrics_data = {
        "model_architecture": "MobileNetV2 Transfer Learning",
        "dataset_size": len(all_paths),
        "train_size": len(train_dataset),
        "val_size": len(val_dataset),
        "test_size": len(test_dataset),
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "confusion_matrix": cm.tolist(),
        "classes": ["Genuine", "Suspicious / Forged"]
    }
    with open(METRICS_SAVE_PATH, "w") as f:
        json.dump(metrics_data, f, indent=2)

    print(f"Metrics saved to: {METRICS_SAVE_PATH}")

if __name__ == "__main__":
    train_and_evaluate()
