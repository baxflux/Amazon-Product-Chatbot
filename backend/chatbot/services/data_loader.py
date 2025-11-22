import pandas as pd
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = BASE_DIR / 'model'

# Part 1: Product Recommendation System
try:    
    amazon_data = pd.read_csv(DATA_DIR / 'cleaned_amazon_reviews.csv')

    sentiment_summary = pd.read_csv(DATA_DIR / 'sentiment_summary.csv')
    high_quality_products = pd.read_csv(DATA_DIR / 'high_quality_products.csv')

    tfidf = joblib.load(MODEL_DIR / 'tfidf_vectorizer_product.pkl')
    tfidf_matrix = joblib.load(MODEL_DIR / 'tfidf_matrix_product.pkl')
    

except FileNotFoundError as e:
    print(f"Error: {e}")
    data = None
    sentiment_summary = None
    high_quality_products = None
    tfidf = None
    tfidf_matrix = None
    
# Part 2: Intent Classification
try:
    bitext_data = pd.read_csv(DATA_DIR / 'cleaned_bitext_intents.csv')
    
    intent_classifier = joblib.load(MODEL_DIR / 'intent_classifier.pkl')

except FileNotFoundError as e:
    print(f"Error: {e}")
    bitext_data = None
    intent_classifier = None

# Part 3: Sentiment Analysis
try:
    sentiment_tfidf = joblib.load(MODEL_DIR / 'tfidf_vectorizer_user.pkl')
    sentiment_model = joblib.load(MODEL_DIR / 'sentiment_model_user.pkl')

except FileNotFoundError as e:
    print(f"Error: {e}")
    sentiment_tfidf = None
    sentiment_model = None
