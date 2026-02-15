#-----------------------------------------------------------------------------------------

# 3. PREFIX FINE-TUNING

import os
import json
import torch
from peft import PrefixTuningConfig, get_peft_model
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor
from transformers import (AdamW, AutoProcessor, get_scheduler)
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from tqdm import tqdm

REVISION = 'refs/pr/6'

class CarDataset(Dataset):
    def __init__(self, json_path, image_dir, prompt="Describe the color, make and model of this car."):
        self.image_dir = image_dir
        self.prompt = prompt

        with open(json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.data = [item for item in self.data if item["validity"] != "INVALID"]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx: int):
        item = self.data[idx]

        image_path = os.path.join(self.image_dir, item["image"])
        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")

        description = item["description"]

        return self.prompt, description, image


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = AutoModelForCausalLM.from_pretrained("microsoft/Florence-2-base", trust_remote_code=True).to(device)
processor = AutoProcessor.from_pretrained("microsoft/Florence-2-base", trust_remote_code=True)
    
train_dataset = CarDataset(
    json_path="carfax_images/train/train.json",
    image_dir="carfax_images/train"
)

val_dataset = CarDataset(
    json_path="carfax_images/val/val.json",
    image_dir="carfax_images/val"
)

test_dataset = CarDataset(
    json_path="carfax_images/test/test.json",
    image_dir="carfax_images/test"
)

def collate_fn(batch):
    prompts, descriptions, images = zip(*batch)
    inputs = processor(text=list(prompts), images=list(images), return_tensors="pt", padding=True).to(device)
    return inputs, descriptions

batch_size = 2
num_workers = 0

train_loader = DataLoader(train_dataset, batch_size=batch_size, collate_fn=collate_fn, num_workers=num_workers, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, collate_fn=collate_fn, num_workers=num_workers)

#-----------------------------------------------------------------------------------------

config = PrefixTuningConfig(
    task_type="CAUSAL_LM",
    num_virtual_tokens=30,
    inference_mode=False,
    encoder_hidden_size=768,
    tokenizer_name_or_path="microsoft/Florence-2-base"
)

peft_model = get_peft_model(model, config)
peft_model.print_trainable_parameters()

torch.cuda.empty_cache()

#-----------------------------------------------------------------------------------------

def train_model(train_loader, val_loader, model, processor, epochs=10, lr=5e-6):
    optimizer = AdamW([p for p in peft_model.parameters() if p.requires_grad], lr=lr)
    num_training_steps = epochs * len(train_loader)
    lr_scheduler = get_scheduler(
        name="linear",
        optimizer=optimizer,
        num_warmup_steps=0,
        num_training_steps=num_training_steps,
    )

    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for batch in tqdm(train_loader, desc=f"Training Epoch {epoch + 1}/{epochs}"):
            inputs, descriptions = batch

            input_ids = inputs["input_ids"]
            pixel_values = inputs["pixel_values"]
            labels = processor.tokenizer(text=list(descriptions), return_tensors="pt", padding=True, return_token_type_ids=False).input_ids.to(device)

            outputs = model(input_ids=input_ids, pixel_values=pixel_values, labels=labels)
            loss = outputs.loss

            loss.backward()
            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad()

            train_loss += loss.item()

        avg_train_loss = train_loss / len(train_loader)
        print(f"Average Training Loss: {avg_train_loss}")


        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch in tqdm(val_loader, desc=f"Validation Epoch {epoch + 1}/{epochs}"):
                inputs, descriptions = batch

                input_ids = inputs["input_ids"]
                pixel_values = inputs["pixel_values"]
                labels = processor.tokenizer(text=list(descriptions), return_tensors="pt", padding=True, return_token_type_ids=False).input_ids.to(device)

                outputs = model(input_ids=input_ids, pixel_values=pixel_values, labels=labels)
                loss = outputs.loss

                val_loss += loss.item()

        avg_val_loss = val_loss / len(val_loader)
        print(f"Average Validation Loss: {avg_val_loss}")


        output_dir = f"./model_checkpoints/prefix/epoch_{epoch+1}"
        os.makedirs(output_dir, exist_ok=True)
        model.save_pretrained(output_dir)
        processor.save_pretrained(output_dir)


train_model(train_loader, val_loader, peft_model, processor)

#-----------------------------------------------------------------------------------------

# WRITE TEST FUNCTION