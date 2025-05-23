# -*- coding: utf-8 -*-
"""Лабораторная 3 ML (предобученные эмбеддинги)

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1tKBzooS4k1XduGJcVTgT4NG1_wVxRxqz

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
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.models import Sequential
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.layers import Dense, Conv1D, MaxPool1D, Dropout, GlobalMaxPool1D, LayerNormalization, GlobalAveragePooling1D, BatchNormalization
from sentence_transformers import SentenceTransformer
from tensorflow.keras.regularizers import l2
from sklearn.utils.class_weight import compute_class_weight
from sklearn.utils import resample
from tensorflow.keras.callbacks import EarlyStopping

nltk.download('stopwords')

"""# Загрузка датасета"""

from google.colab import drive
drive.mount('/content/drive')

df = pd.read_csv('/content/drive/MyDrive/Combined Data 1.csv', index_col=0)

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

def preprocess_data(text):
    #Clean puntuation, urls, and so on
    text = clean_text(text)
    # Remove stopwords
    text = ' '.join(word for word in text.split(' ') if word not in stop_words)

    return text

df2 = df1.copy()

df2['statement_clean'] = df2['statement'].apply(preprocess_data)

"""# Балансировка классов"""

min_samples = df2['status'].value_counts().min()

balanced_dfs = []
for class_name in df2['status'].unique():
    class_df = df2[df2['status'] == class_name]
    # Оставляем только min_samples случайных строк
    undersampled = resample(class_df,
                            replace=False,  # Без повторений
                            n_samples=min_samples,
                            random_state=42)
    balanced_dfs.append(undersampled)

# Собираем сбалансированный датасет
balanced_df = pd.concat(balanced_dfs)

#class_distribution = balanced_df['status'].value_counts()
#print(class_distribution)

"""# Векторизация (BERT)"""

bert_model = SentenceTransformer('all-mpnet-base-v2')  # или другой подходящий
texts = balanced_df['statement_clean'].tolist()  # или 'tokens', если хотите использовать токенизированный текст
embeddings = bert_model.encode(texts, show_progress_bar=True)

"""# Присвоение лейблов статусам"""

labels = balanced_df['status'].values
encoder = LabelEncoder()
encoded_labels = encoder.fit_transform(labels)

#for i, class_name in enumerate(encoder.classes_):
    #print(f"Label {i} corresponds to status '{class_name}'")

"""# Настройка параметров модели"""

maximum_features = 5000  # Maximum number of words to consider as features
maximum_length = 100  # Maximum length of input sequences
word_embedding_dims = 250  # Dimension of word embeddings
no_of_filters = 500  # Number of filters in the convolutional layer
kernel_size = 3  # Size of the convolutional filters
hidden_dims = 250  # Number of neurons in the hidden layer
batch_size = 32  # Batch size for training
epochs = 50  # Number of training epochs

"""# Разбиение лейблов и текста на обучающую и тестовую выборки"""

train_text, test_text, train_labels, test_labels = train_test_split(embeddings, encoded_labels, stratify = encoded_labels, test_size=0.2)

train_text = np.expand_dims(train_text, axis=2)
test_text = np.expand_dims(test_text, axis=2)

"""# Построение CNN модели"""

model = Sequential([
    # Первый сверточный блок
    Conv1D(filters=no_of_filters,
           kernel_size=7,
           activation='relu',
           padding='same',
           input_shape=(768, 1)),  #  размерность эмбеддингов
    BatchNormalization(),
    MaxPool1D(2),
    Dropout(0.3),

    # Второй сверточный блок
    Conv1D(filters=no_of_filters,
           kernel_size=5,
           activation='relu',
           padding='same'),
    BatchNormalization(),
    MaxPool1D(2),
    Dropout(0.3),

    # Третий сверточный блок
    Conv1D(filters=no_of_filters,
           kernel_size=kernel_size,
           activation='relu',
           padding='same'),
    BatchNormalization(),
    GlobalMaxPool1D(),
    Dropout(0.3),

    # Полносвязные слои с использованием HIDDEN_DIMS
    Dense(hidden_dims, activation='relu', kernel_regularizer=l2(0.01)),
    BatchNormalization(),
    Dropout(0.5),

    Dense(hidden_dims, activation='relu', kernel_regularizer=l2(0.01)),  # 125
    BatchNormalization(),
    Dropout(0.5),

    # Выходной слой (7 классов)
    Dense(7, activation='softmax')
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

early_stopping = EarlyStopping(
    monitor='val_loss',    # Мониторим потерю на валидации
    patience=5,           # Количество эпох без улучшения перед остановкой
    restore_best_weights=True  # Восстанавливает веса лучшей модели
)

# Обучение модели с Early Stopping
history = model.fit(
    train_text,
    train_labels,
    batch_size=batch_size,
    epochs=epochs,
    validation_data=(test_text, test_labels),
    callbacks=[early_stopping]  # Добавляем callback здесь
)


print(model.summary())

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

new_text = input("Введите текст для анализа: ")

# Очистка текста
cleaned_text = preprocess_data(new_text)
print('Cleaned:', cleaned_text)

# Векторизация через Sentence-BERT
new_embedding = bert_model.encode([cleaned_text])  # Модель из блока SentenceTransformer

# Добавим размерность (768, 1), как делали для train/test
new_embedding = np.expand_dims(new_embedding, axis=2)

# Предсказание
probability = model.predict(new_embedding)
predicted_class = np.argmax(probability)

# Классы
emotion_labels = ['Anxiety', 'Bipolar', 'Depression', 'Normal', 'Personality Disorder', 'Stress', 'Suicidal']
print(f'Класс: {emotion_labels[predicted_class]}')
