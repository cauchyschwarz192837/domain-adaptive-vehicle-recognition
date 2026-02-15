# End-to-End Night-Robust Vehicle Recognition Pipeline via GAN-Based Domain Augmentation and Multimodal Fine-Tuning, and Preliminary Web Scraping for Training Data Collection 

CycleGAN-augmented domain adaptation and vision-language fine-tuning for robust vehicle make, model, and color recognition under nighttime conditions, with web-scrape training data

---

## Overview

This project builds a domain-adaptive vehicle recognition pipeline capable of extracting:

- Vehicle **Make**
- Vehicle **Model**
- Vehicle **Exterior Color**

from car images — including **nighttime images**, where models trained only on daytime data typically fail.

The pipeline combines:

- Web scraping for labeled vehicle images
- CycleGAN day → night style transfer
- Synthetic data augmentation
- Vision-language fine-tuning (Microsoft Florence-2)
- Full fine-tuning and parameter-efficient methods (LoRA, Prefix Tuning)

---

## Motivation

Vehicle recognition models trained on dealership-style daytime images often degrade under:

- Low illumination
- Nighttime conditions
- Different lighting distributions

Instead of collecting a large labeled nighttime dataset, this project uses **unpaired image-to-image translation (CycleGAN)** to generate synthetic night images while preserving vehicle identity and labels.

This enables domain-adaptive fine-tuning without manual relabeling.

---

## Pipeline

1. Scrape labeled daytime vehicle images (make, model, color).
2. Train CycleGAN on unpaired day and night vehicle images.
3. Generate synthetic night images from labeled daytime images.
4. Fine-tune a multimodal vision-language model on both real and synthetic data.
5. Produce night-robust vehicle attribute predictions.

---

## Components

### Web Scraping

- Scrapes vehicle listings by make and model.
- Downloads images.
- Extracts color metadata.
- Deduplicates placeholder images using hashing.
- Saves structured JSON metadata.

---

### CycleGAN (Domain Adaptation)

Implements unpaired day ↔ night translation:

- ResNet-based Generator
- PatchGAN Discriminator
- Least-Squares GAN objective
- Cycle consistency loss
- Identity preservation loss

Files:
- generator_model.py
- discriminator_model.py
- dataset.py
- train.py
- config.py
- utils.py

---

### Vision-Language Fine-Tuning

Fine-tunes **Microsoft Florence-2** to generate captions like: "red Toyota Camry", "black BMW X5"


Three strategies implemented:

- `full_finetune.py` — Full model fine-tuning
- `lora_finetune.py` — Low-Rank Adaptation (LoRA)
- `prefix_finetune.py` — Prefix tuning

---

## Installation

```bash
git clone https://github.com/<your-username>/domain-adaptive-vehicle-recognition.git
cd domain-adaptive-vehicle-recognition
pip install -r requirements.txt

python train.py
python lora_finetune.py
python full_finetune.py
python prefix_finetune.py

