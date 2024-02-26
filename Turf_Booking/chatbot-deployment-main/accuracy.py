import numpy as np
import random
import json

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Assuming these functions are defined in your code
from nltk_utils import bag_of_words, tokenize, stem
from model import NeuralNet

# Load intents from intents.json
with open('intents.json', 'r') as f:
    intents = json.load(f)

# Initialize empty lists for all_words and tags
all_words = []
tags = []

# loop through each sentence in our intents patterns
for intent in intents['intents']:
    tag = intent['tag']
    # add to tag list
    tags.append(tag)
    for pattern in intent['patterns']:
        # tokenize each word in the sentence
        w = tokenize(pattern)
        # add to our words list
        all_words.extend(w)

# stem and lower each word
ignore_words = ['?', '.', '!']
all_words = [stem(w) for w in all_words if w not in ignore_words]
# remove duplicates and sort
all_words = sorted(set(all_words))
tags = sorted(set(tags))
print(len(tags), "tags:", tags)
print(len(all_words), "unique stemmed words:", all_words)
# Create training data
X_train = []
y_train = []

for intent in intents['intents']:
    tag = intent['tag']
    for pattern in intent['patterns']:
        w = tokenize(pattern)
        w = [stem(word) for word in w if word not in ignore_words]
        bag = bag_of_words(w, all_words)
        X_train.append(bag)
        label = tags.index(tag)
        y_train.append(label)

X_train = np.array(X_train)
y_train = np.array(y_train)

# Define the ChatDataset class
class ChatDataset(Dataset):
    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.n_samples

# Initialize the dataset and data loader
dataset = ChatDataset()
train_loader = DataLoader(dataset=dataset, batch_size=8, shuffle=True, num_workers=0)

# Hyper-parameters
num_epochs = 1000
batch_size = 8
learning_rate = 0.001
input_size = len(X_train[0])
hidden_size = 8
output_size = len(tags)

# Initialize the device (GPU or CPU)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Initialize the model, criterion, and optimizer
model = NeuralNet(input_size, hidden_size, output_size).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

# Train the model
for epoch in range(num_epochs):
    for (words, labels) in train_loader:
        words = words.to(device)
        labels = labels.to(dtype=torch.long).to(device)
        outputs = model(words)
        loss = criterion(outputs, labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    if (epoch+1) % 100 == 0:
        print (f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

print(f'Final loss: {loss.item():.4f}')

# Save the model
data = {
    "model_state": model.state_dict(),
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "all_words": all_words,
    "tags": tags
}

FILE = "data.pth"
torch.save(data, FILE)
print(f'Training complete. Model saved to {FILE}')

# Generate X_test and y_test
X_test = []
y_test = []

for intent in intents['intents']:
    tag = intent['tag']
    for pattern in intent['patterns']:
        w = tokenize(pattern)
        w = [stem(word) for word in w if word not in ignore_words]
        bag = bag_of_words(w, all_words)
        X_test.append(bag)
        label = tags.index(tag)
        y_test.append(label)

X_test = np.array(X_test)
y_test = np.array(y_test)

# Load the trained model
data = torch.load(FILE)
model = NeuralNet(data['input_size'], data['hidden_size'], data['output_size'])
model.load_state_dict(data['model_state'])
model.eval()

# Convert test data to PyTorch tensors
X_test = torch.from_numpy(X_test).float()
y_test = torch.from_numpy(y_test).long()

# Forward pass on the test data
with torch.no_grad():
    outputs = model(X_test)

# Get predicted labels
_, predicted = torch.max(outputs, 1)

# Calculate accuracy
total = y_test.size(0)
correct = (predicted == y_test).sum().item()
accuracy = correct / total * 100
print(f'Accuracy: {accuracy:.2f}%')

# True Positives (TP)
TP = ((predicted == 1) & (y_test == 1)).sum().item()

# False Positives (FP)
FP = ((predicted == 1) & (y_test == 0)).sum().item()

# False Negatives (FN)
FN = ((predicted == 0) & (y_test == 1)).sum().item()

# True Negatives (TN)
TN = ((predicted == 0) & (y_test == 0)).sum().item()

# Precision, Recall, and F1-Score
precision = TP / (TP + FP)
recall = TP / (TP + FN)
f1_score = 2 * (precision * recall) / (precision + recall)

print(f'Precision: {precision:.4f}')
print(f'Recall: {recall:.4f}')
print(f'F1-Score: {f1_score:.4f}')