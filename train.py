# CycleGAN Style Transfer Training

import torch
from dataset import DayNightDataset
import sys
from utils import save_checkpoint, load_checkpoint
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim
import config
from tqdm import tqdm

from torchvision.utils import save_image
from discriminator_model import Discriminator
from generator_model import Generator


def train_fn(disc_N, disc_D, gen_D, gen_N, loader, opt_disc, opt_gen, l1, mse, d_scaler, g_scaler):
    N_reals = 0
    N_fakes = 0
    loop = tqdm(loader, leave=True)

    for idx, (day, night) in enumerate(loop):
        day = day.to(config.DEVICE)
        night = night.to(config.DEVICE)


        # Train Discriminators H and Z
        with torch.cuda.amp.autocast():
            fake_night = gen_N(day)

            D_N_real = disc_N(night)
            D_N_fake = disc_N(fake_night.detach()) #*

            N_reals += D_N_real.mean().item()
            N_fakes += D_N_fake.mean().item()

            D_N_real_loss = mse(D_N_real, torch.ones_like(D_N_real))
            D_N_fake_loss = mse(D_N_fake, torch.zeros_like(D_N_fake))
            D_N_loss = D_N_real_loss + D_N_fake_loss

            #-----------------------------------------------------------

            fake_day = gen_D(night)

            D_D_real = disc_D(day)
            D_D_fake = disc_D(fake_day.detach()) #*

            D_D_real_loss = mse(D_D_real, torch.ones_like(D_D_real))
            D_D_fake_loss = mse(D_D_fake, torch.zeros_like(D_D_fake))
            D_D_loss = D_D_real_loss + D_D_fake_loss

            #-----------------------------------------------------------

            D_loss = (D_N_loss + D_D_loss) / 2

        opt_disc.zero_grad()
        d_scaler.scale(D_loss).backward()
        d_scaler.step(opt_disc)
        d_scaler.update()


        # Train Generators H and Z
        with torch.cuda.amp.autocast():
            # adversarial loss for both generators
            D_N_fake = disc_N(fake_night)
            D_D_fake = disc_D(fake_day)
            
            loss_G_N = mse(D_N_fake, torch.ones_like(D_N_fake))
            loss_G_D = mse(D_D_fake, torch.ones_like(D_D_fake))

            # cycle loss
            cycle_day = gen_D(fake_night)
            cycle_night = gen_N(fake_day)
            cycle_day_loss = l1(day, cycle_day)
            cycle_night_loss = l1(night, cycle_night)

            # identity loss (remove these for efficiency if you set lambda_identity=0)
            identify_day = gen_D(day)
            identify_night = gen_N(night)
            identify_day_loss = l1(day, identify_day)
            identify_night_loss = l1(night, identify_night)

            # add all togethor
            G_loss = (
                loss_G_D
                + loss_G_N
                + cycle_day_loss * config.LAMBDA_CYCLE
                + cycle_night_loss * config.LAMBDA_CYCLE
                + identify_night_loss * config.LAMBDA_IDENTITY
                + identify_day_loss * config.LAMBDA_IDENTITY
            )

        opt_gen.zero_grad()
        g_scaler.scale(G_loss).backward()
        g_scaler.step(opt_gen)
        g_scaler.update()

        if idx % 200 == 0:
            save_image(fake_night * 0.5 + 0.5, f"saved_images/night_{idx}.png")
            save_image(fake_day * 0.5 + 0.5, f"saved_images/day_{idx}.png")

        loop.set_postfix(N_real=N_reals / (idx + 1), N_fake=N_fakes / (idx + 1))


def main():
    disc_N = Discriminator(in_channels=3).to(config.DEVICE)
    disc_D = Discriminator(in_channels=3).to(config.DEVICE)
    gen_D = Generator(img_channels=3, num_residuals=9).to(config.DEVICE)
    gen_N = Generator(img_channels=3, num_residuals=9).to(config.DEVICE)
    opt_disc = optim.Adam(
        list(disc_N.parameters()) + list(disc_D.parameters()),
        lr=config.LEARNING_RATE,
        betas=(0.5, 0.999),
    )

    opt_gen = optim.Adam(
        list(gen_D.parameters()) + list(gen_N.parameters()),
        lr=config.LEARNING_RATE,
        betas=(0.5, 0.999),
    )

    L1 = nn.L1Loss()
    mse = nn.MSELoss()

    if config.LOAD_MODEL:
        load_checkpoint(
            config.CHECKPOINT_GEN_N,
            gen_N,
            opt_gen,
            config.LEARNING_RATE,
        )
        load_checkpoint(
            config.CHECKPOINT_GEN_D,
            gen_D,
            opt_gen,
            config.LEARNING_RATE,
        )
        load_checkpoint(
            config.CHECKPOINT_CRITIC_N,
            disc_N,
            opt_disc,
            config.LEARNING_RATE,
        )
        load_checkpoint(
            config.CHECKPOINT_CRITIC_D,
            disc_D,
            opt_disc,
            config.LEARNING_RATE,
        )

    dataset = DayNightDataset(
        root_night=config.TRAIN_DIR + "/night",
        root_day=config.TRAIN_DIR + "/day",
        transform=config.transforms,
    )
    val_dataset = DayNightDataset(
        root_night="cyclegan_test/night1",
        root_day="cyclegan_test/day1",
        transform=config.transforms,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=1,
        shuffle=False,
        pin_memory=True,
    )
    loader = DataLoader(
        dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=True,
        num_workers=config.NUM_WORKERS,
        pin_memory=True,
    )
    g_scaler = torch.cuda.amp.GradScaler()
    d_scaler = torch.cuda.amp.GradScaler()

    for epoch in range(config.NUM_EPOCHS):
        train_fn(
            disc_N,
            disc_D,
            gen_D,
            gen_N,
            loader,
            opt_disc,
            opt_gen,
            L1,
            mse,
            d_scaler,
            g_scaler,
        )

        if config.SAVE_MODEL:
            save_checkpoint(gen_N, opt_gen, filename=config.CHECKPOINT_GEN_N)
            save_checkpoint(gen_D, opt_gen, filename=config.CHECKPOINT_GEN_D)
            save_checkpoint(disc_N, opt_disc, filename=config.CHECKPOINT_CRITIC_N)
            save_checkpoint(disc_D, opt_disc, filename=config.CHECKPOINT_CRITIC_D)


if __name__ == "__main__":
    main()