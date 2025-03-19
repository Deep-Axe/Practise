import cv2
import torch
from torchvision import transforms
from torch import nn
import torch.nn.functional as F
from torchvision import models
import os
WEIGHTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
os.makedirs(WEIGHTS_DIR, exist_ok=True)

torch.hub.set_dir(WEIGHTS_DIR)

class DeePixBiS(nn.Module):
    def __init__(self, pretrained=True):
        super().__init__()
        weights = models.DenseNet161_Weights.IMAGENET1K_V1 if pretrained else None
        dense = models.densenet161(weights=weights)
        features = list(dense.features.children())
        self.enc = nn.Sequential(*features[:8])
        self.dec = nn.Conv2d(384, 1, kernel_size=1, stride=1, padding=0)
        self.linear = nn.Linear(14 * 14, 1)

    def forward(self, x):
        enc = self.enc(x)
        dec = self.dec(enc)
        out_map = F.sigmoid(dec)
        out = self.linear(out_map.view(-1, 14 * 14))
        out = F.sigmoid(out)
        out = torch.flatten(out)
        return out_map, out

class SpoofDetector:
    def __init__(self, model_path='models/DeePixBiS.pth', spoof_threshold=0.65, buffer_size = 5):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = DeePixBiS().to(self.device)
        state_dict = torch.load(model_path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state_dict)
        self.model.eval()
        #print(f"Spoof detector initialized on {self.device}")


        self.transforms = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])

        
        self.spoof_threshold = spoof_threshold
        self.buffer_size = buffer_size
        self.spoof_scores = []
        
    def reset_buffer(self):
        self.spoof_scores = []

    @torch.no_grad()
    def detect_spoof(self, face_region):

        try:
            if face_region is None or face_region.size == 0:
                raise ValueError("Invalid face region")

            face_region = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
            face_tensor = self.transforms(face_region).unsqueeze(0).to(self.device)
            
            mask, _ = self.model(face_tensor)
            score = torch.mean(mask).item()
            self.spoof_scores.append(score)
            if len(self.spoof_scores) > self.buffer_size:
                self.spoof_scores.pop(0)
                
            if len(self.spoof_scores) == self.buffer_size:
                mean_score = sum(self.spoof_scores) / self.buffer_size
                return mean_score >= self.spoof_threshold, mean_score
            
            return None, score 
            
        except Exception as e:
            print(f"Error in spoof detection: {str(e)}")
            return False, 0.0
