# -*- coding: utf-8 -*-
"""Лабораторная №1 LSTM

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/12pdq4pOxAsckiKHtCx-1ENSFgaJLrgb1

# Импорт библиотек
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer, SnowballStemmer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.models import Sequential
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.layers import Dense, Embedding, Activation, LSTM

nltk.download('stopwords')

"""# Загрузка датасета"""

from google.colab import drive
drive.mount('/content/drive')

df = pd.read_csv('/content/drive/MyDrive/Универ/Маш. обучение/Семестр 6/Combined Data.csv', index_col=0)

df1 = df.copy()
df1.dropna(inplace = True)
df1.head()

"""# Препроцессинг"""

def clean_text(text):

    # Convert to string and lowercase
    text = str(text).lower()

    # Remove text in square brackets
    text = re.sub(r'\[.*?\]', '', text)

    # Remove URLs (including markdown-style links)
    text = re.sub(r'https?://\S+|www\.\S+|\[.*?\]\(.*?\)', '', text)

    # Remove HTML tags
    text = re.sub(r'<.*?>+', '', text)
    # Remove handles (that start with '@')
    text = re.sub(r'@\w+', '', text)

    # Remove punctuation and other special characters
    text = re.sub(f'[{re.escape(string.punctuation)}]', '', text)

    # Remove newline characters
    text = re.sub(r'\n', ' ', text)

    # Remove words containing numbers
    text = re.sub(r'\w*\d\w*', '', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

stop_words = stopwords.words('english')
more_stopwords = ['u', 'im', 'c']
stop_words = stop_words + more_stopwords

stemmer = nltk.SnowballStemmer("english")

def preprocess_data(text):
    #Clean puntuation, urls, and so on
    text = clean_text(text)
    # Remove stopwords
    text = ' '.join(word for word in text.split(' ') if word not in stop_words)
    # Stemm all the words in the sentence
    text = ' '.join(stemmer.stem(word) for word in text.split(' '))

    return text

df2 = df1.copy()

df2['statement_clean'] = df2['statement'].apply(preprocess_data)

"""# Присвоение лейблов статусам"""

reviews = df2['statement_clean'].values
labels = df2['status'].values
encoder = LabelEncoder()
encoded_labels = encoder.fit_transform(labels)

for i, class_name in enumerate(encoder.classes_):
    print(f"Label {i} corresponds to status '{class_name}'")

"""# Разбиение лейблов и текста на обучающую и тестовую выборки"""

train_text, test_text, train_labels, test_labels = train_test_split(reviews, encoded_labels, stratify = encoded_labels, test_size=0.2)

"""# Токенизация текста и преобразование в последовательности числовых индексов"""

def get_max_length():
    review_length = []
    for review in train_text:
        review_length.append(len(review))

    return int(np.ceil(np.mean(review_length)))

token = Tokenizer(lower=False)
token.fit_on_texts(train_text)
train_text = token.texts_to_sequences(train_text)
test_text = token.texts_to_sequences(test_text)

max_length = get_max_length()

train_text = pad_sequences(train_text, maxlen=max_length, padding='post', truncating='post')
test_text = pad_sequences(test_text, maxlen=max_length, padding='post', truncating='post')

total_words = len(token.word_index) + 1   # add 1 because of 0 padding

print('Encoded Text Train\n', train_text, '\n')
print('Encoded Text Test\n', test_text, '\n')
print('Maximum review length: ', max_length)

"""# Построение LSTM модели"""

vec_size = 150

model = Sequential([
    Embedding(input_dim=total_words, output_dim=vec_size, input_length=max_length),
    LSTM(150),
    Dense(7,activation='softmax')
])
# Compile the model
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(train_text, train_labels, epochs=10, validation_data=(test_text, test_labels))

# Print model summary
model.summary()

"""# Оценка

**Accuracy, F1-score, Precision**
"""

probability = model.predict(test_text)
predicted_labels = np.argmax(probability, axis=1)

labels = encoder.classes_
print(classification_report(test_labels, predicted_labels, target_names=labels))

"""**Confusion matrix**"""

conf_matrix = confusion_matrix(test_labels, predicted_labels)

labels = encoder.classes_
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Greens', xticklabels=labels, yticklabels=labels)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

"""# Тестирование на новом тексте"""

txt = str(input(' '))

regex = re.compile(r'[^a-zA-Z\s]')
txt = regex.sub('', txt)
print('Cleaned: ', txt)

words = txt.split(' ')
filtered = [w for w in words if w not in stop_words]
filtered = ' '.join(filtered)
filtered = [filtered.lower()]

print('Filtered: ', filtered)

tokenize_words = token.texts_to_sequences(filtered)
padded_words = pad_sequences(tokenize_words, maxlen=max_length, padding='post', truncating='post')
print(padded_words)

probability = model.predict(padded_words)
emotion_labels = ['Anxiety', 'Bipolar', 'Depression', 'Normal', 'Personality Disorder', 'Stress', 'Suicidal']

# Выбор класса с максимальной вероятностью
prediction = np.argmax(probability)
print(f'Class:{emotion_labels[prediction]}')