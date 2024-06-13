# -*- coding: utf-8 -*-
"""Reviews Analysis.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/17VODlLLa5zOFZA0HFU-gAdeQRqfA-ADM
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('/content/data.csv')

"""## Basic Analysis of the data"""

df.head()

df.columns

df = df[['rating','rating title','Review text','Review date','Date of Experience','rating_procesed','Year of review ','Year of experience','DIff in months ']]

df.head()

df.shape

df['rating'].value_counts()

df['DIff in months '].value_counts()

df['Review text'][0]

reviews = df['Review text'].tolist()



import string

def preprocess_text(text):
    # Lowercase, remove punctuation, etc.
    text.translate(str.maketrans('', '', string.punctuation))
    return text.lower()

cleaned_reviews = []
for review in reviews:
  cleaned_reviews.append(preprocess_text(review))

cleaned_reviews

!pip install spacy
!python -m spacy download en_core_web_sm

import spacy
nlp = spacy.load('en_core_web_sm')

def preprocess_spacy(doc):
    # Tokenization, removing punctuation, stop words, and lemmatization
    # doc.remove("novo")
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return " ".join(tokens)

cleaned_reviews = []
for review in reviews:
  doc = nlp(review.lower())
  cleaned_reviews.append(preprocess_spacy(doc))

from transformers import pipeline
sentiment_analyzer = pipeline("sentiment-analysis")



"""# Topic Modelling
  Used for finding out the most important topics in the the customer. Will be used for designing the customer support categories.
"""

!pip install transformers torch sentence-transformers sklearn

!pip install -U sentence-transformers

import torch
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

model_name = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(model_name)

reviews = cleaned_reviews

sentiments = sentiment_analyzer(reviews)

negative_reviews = [review for review, sentiment in zip(reviews, sentiments) if sentiment['label'] != 'POSITIVE']

print(len(reviews))
print(len(negative_reviews))

embeddings = model.encode(negative_reviews, convert_to_tensor=True)

vectorizer = CountVectorizer(max_features=1000)
X = vectorizer.fit_transform(negative_reviews)

lda = LatentDirichletAllocation(n_components=5, random_state=42)
lda.fit(X)

def display_topics(model, feature_names, no_top_words):
    for topic_idx, topic in enumerate(model.components_):
        print(f"Topic {topic_idx}:")
        print(" ".join([feature_names[i] for i in topic.argsort()[:-no_top_words - 1:-1]]))

no_top_words = 10
tf_feature_names = vectorizer.get_feature_names_out()
display_topics(lda, tf_feature_names, no_top_words)

zslda_output = lda.transform(X)
topic_assignments = np.argmax(lda_output, axis=1)

for review, topic in zip(negative_reviews, topic_assignments):
    print(f"Review: {review}\nAssigned Topic: {topic}\n")

"""# Predicting the Model Customer Support Using Defined Intents"""

taxonomy = {
    'Account -> Lost password': 0,
    'Checks -> Mobile deposits -> Void checks': 1,
    'Debit card -> Declined -> Unauthorized transactions -> fraud': 2,
    'Invoices -> sent -> unpaid -> conflict': 3,
    'Invoices -> sent -> paid': 4,
    'Invoices -> sent -> unpaid -> pending': 5,

}

def label_function(feedback):
    if 'account'  in feedback.lower():
        return taxonomy['Account -> Lost password']
    elif 'void' in feedback.lower():
        return taxonomy['Checks -> Mobile deposits -> Void checks']
    elif 'unauthorized' in feedback.lower() or 'fraud' in feedback.lower():
        return taxonomy['Debit card -> Declined -> Unauthorized transactions -> fraud']
    elif 'unpaid' in feedback.lower() and 'conflict' in feedback.lower():
        return taxonomy['Invoices -> sent -> unpaid -> conflict']
    elif 'paid' in feedback.lower():
        return taxonomy['Invoices -> sent -> paid']
    elif 'unpaid' in feedback.lower() and 'pending' in feedback.lower():
        return taxonomy['Invoices -> sent -> unpaid -> pending']
    else:
        return -1  # Label for unknown or uncategorized feedback

df.head(2)

df['label'] = df['Review text'].apply(label_function)

df.head()

df['label'].value_counts()

from sklearn.model_selection import train_test_split

train_data, test_data = train_test_split(df, test_size=0.2, random_state=42)

!pip install datasets

import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

train_dataset = Dataset.from_pandas(train_data)
test_dataset = Dataset.from_pandas(test_data)

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

def tokenize_function(examples):
    return tokenizer(examples['Review text'], padding='max_length', truncation=True)

tokenized_train = train_dataset.map(tokenize_function, batched=True)
tokenized_test = test_dataset.map(tokenize_function, batched=True)

!pip install accelerate -U
!pip install transformers[torch]

!pip install transformers[torch] accelerate -U

# Model
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=5)  # num_classes = number of top-level categories
import accelerate


# Training
trainer = Trainer(
    model=model,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_test
)

!pip install torch==2.0.1
!pip install transformers==4.30.2
!pip install accelerate==0.21.0
!pip install datasets==2.14.1

df['feedback'] = df['Review text']

df.head()

from torch.utils.data import DataLoader, Dataset

from transformers import BertTokenizer, BertForSequenceClassification, AdamW
from sklearn.metrics import accuracy_score, f1_score

train_data, test_data = train_test_split(df, test_size=0.2, random_state=42)



# Tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

class FeedbackDataset(Dataset):
    def __init__(self, feedbacks, labels, tokenizer, max_len):
        self.feedbacks = feedbacks
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.feedbacks)

    def __getitem__(self, index):
        feedback = self.feedbacks[index]
        label = self.labels[index]

        encoding = self.tokenizer.encode_plus(
            feedback,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        return {
            'feedback_text': feedback,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

# Create Datasets
max_len = 128
train_dataset = FeedbackDataset(train_data['feedback'].to_numpy(), train_data['label'].to_numpy(), tokenizer, max_len)
test_dataset = FeedbackDataset(test_data['feedback'].to_numpy(), test_data['label'].to_numpy(), tokenizer, max_len)

# Create DataLoaders
batch_size = 16
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# Model
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=len(taxonomy))
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# Optimizer
optimizer = AdamW(model.parameters(), lr=2e-5, correct_bias=False)

# Training function
def train_epoch(model, data_loader, optimizer, device, scheduler, n_examples):
    model = model.train()
    losses = []
    correct_predictions = 0

    for batch in data_loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        loss = outputs.loss
        logits = outputs.logits
        _, preds = torch.max(logits, dim=1)
        correct_predictions += torch.sum(preds == labels)
        losses.append(loss.item())

        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

    return correct_predictions.double() / n_examples, np.mean(losses)

# Evaluation function
def eval_model(model, data_loader, device, n_examples):
    model = model.eval()
    losses = []
    correct_predictions = 0

    with torch.no_grad():
        for batch in data_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            loss = outputs.loss
            logits = outputs.logits
            _, preds = torch.max(logits, dim=1)
            correct_predictions += torch.sum(preds == labels)
            losses.append(loss.item())

    return correct_predictions.double() / n_examples, np.mean(losses)

# Training and Evaluation Loop
epochs = 3
for epoch in range(epochs):
    print(f'Epoch {epoch + 1}/{epochs}')
    print('-' * 10)

    train_acc, train_loss = train_epoch(
        model,
        train_loader,
        optimizer,
        device,
        None,
        len(train_dataset)
    )

    print(f'Train loss {train_loss} accuracy {train_acc}')

    val_acc, val_loss = eval_model(
        model,
        test_loader,
        device,
        len(test_dataset)
    )

    print(f'Val   loss {val_loss} accuracy {val_acc}')

