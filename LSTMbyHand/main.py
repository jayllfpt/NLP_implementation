from typing import Any
from lightning.pytorch.utilities.types import STEP_OUTPUT
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam

import lightning as L
from torch.utils.data import DataLoader, TensorDataset

class LSTMbyHand(L.LightningModule):
    def __init__(self) :
        super().__init__()
        mean = torch.tensor(0.0)
        std = torch.tensor(1.0)
        self.wlr1  = nn.Parameter(torch.normal(mean = mean, std  = std), requires_grad = True)
        self.wlr2  = nn.Parameter(torch.normal(mean = mean, std  = std), requires_grad = True)
        self.blr1  = nn.Parameter(torch.tensor(0.), requires_grad = True)

        self.wpr1  = nn.Parameter(torch.normal(mean = mean, std  = std), requires_grad = True)
        self.wpr2  = nn.Parameter(torch.normal(mean = mean, std  = std), requires_grad = True)
        self.bpr1  = nn.Parameter(torch.tensor(0.), requires_grad = True)

        self.wp1  = nn.Parameter(torch.normal(mean = mean, std  = std), requires_grad = True)
        self.wp2  = nn.Parameter(torch.normal(mean = mean, std  = std), requires_grad = True)
        self.bp1  = nn.Parameter(torch.tensor(0.), requires_grad = True)

        self.wo1  = nn.Parameter(torch.normal(mean = mean, std  = std), requires_grad = True)
        self.wo2  = nn.Parameter(torch.normal(mean = mean, std  = std), requires_grad = True)
        self.bo1  = nn.Parameter(torch.tensor(0.), requires_grad = True)


    def lstm_unit(self, input_value, long_memory, short_memory):
        long_remember_percent = torch.sigmoid((short_memory *  self.wlr1) +
                                                (input_value * self.wlr2) + 
                                                self.blr1)
        
        potential_remember_percent = torch.sigmoid((short_memory * self.wpr1) +
                                                    (input_value * self.wpr2) +
                                                    self.bpr1)
        potential_memory = torch.tanh((short_memory * self.wp1) + 
                                      (input_value * self.wp2) +
                                      self.bp1)
        update_long_memory = ((long_memory * long_remember_percent) +
                              (potential_memory * potential_remember_percent))
        output_percent = torch.sigmoid((short_memory * self.wo1) + 
                                       (input_value * self.wo2) +
                                       self.bo1)
        update_short_memory = torch.tanh(update_long_memory) * output_percent
        return ([update_long_memory, update_short_memory])


    def forward(self, input):
        long_memory, short_memory = 0, 0
        long_memory, short_memory = self.lstm_unit(input[0], long_memory, short_memory)
        long_memory, short_memory = self.lstm_unit(input[1], long_memory, short_memory)
        long_memory, short_memory = self.lstm_unit(input[2], long_memory, short_memory)
        long_memory, short_memory = self.lstm_unit(input[3], long_memory, short_memory)
        return short_memory
        

    def configure_optimizers(self):
        return Adam(self.parameters())

    def training_step(self, batch, batch_idx):
        input_i, label_i = batch
        output_i = self.forward(input_i[0])
        loss = (output_i - label_i) **2

        self.log("train_loss", loss)
        if (label_i == 0):
            self.log("out_0", output_i)
        else:
            self.log("out_1",  output_i)
        
        return loss

model = LSTMbyHand()
inputs = torch.tensor([[0., 0.5, 0.25, 1.], [1., 0.5, 0.25, 1.]])
labels = torch.tensor([0., 1.])
dataset =  TensorDataset(inputs, labels)
dataloader = DataLoader(dataset)

trainer = L.Trainer(max_epochs= 2000)
trainer.fit(model, train_dataloaders= dataloader)

print("result: gt = 0. , predicted = ", 
      model(torch.tensor([0., 0.5, 0.25, 1.])).detach())
print("result: gt = 1. , predicted = ", 
      model(torch.tensor([1., 0.5, 0.25, 1.])).detach())
