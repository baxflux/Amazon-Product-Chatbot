import re
import spacy
from sklearn.metrics.pairwise import cosine_similarity

from .data_loader import *

try:
    nlp = spacy.load("en_core_web_sm")
except OSError as e:
    print(f"Error: {e}")

if amazon_data is not None:
    avg_rating = amazon_data.groupby('asins')['reviews.rating'].mean().reset_index()
    avg_rating.columns = ['asins', 'average_rating']
    
    unique_products = amazon_data.drop_duplicates(subset=['asins'])[['asins', 'name', 'categories']]
    
    product_details_df = unique_products.merge(avg_rating, on='asins')
    product_details = product_details_df.set_index('asins')[['name', 'categories', 'average_rating']].to_dict('index')
else:
    product_details = {}

if sentiment_summary is not None and high_quality_products is not None:
    sentiment_dict = sentiment_summary.set_index('asins')['positive_ratio'].to_dict()
    high_quality_asins = high_quality_products['asins'].tolist()
    tfidf_asins = high_quality_products['asins'].tolist()
else:
    sentiment_dict = {}
    high_quality_asins = []
    tfidf_asins = []

if bitext_data is not None:
    bitext_intents = bitext_data.groupby('intent').agg({
        'response': lambda x: list(x)
    }).to_dict('index')
else:
    bitext_intents = {}

def predict_sentiment(text):
    if sentiment_tfidf is None or sentiment_model is None:
        return "unknown"
    text_tfidf = sentiment_tfidf.transform([text])
    sentiment = sentiment_model.predict(text_tfidf)[0]
    return sentiment

def extract_keywords(text):
    doc = nlp(text.lower())
    keywords = [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop]
    return ' '.join(keywords) if keywords else text

def get_product_info(asin):
    if asin in product_details and asin in sentiment_dict:
        product = product_details[asin]
        return {
            'name': product['name'],
            'categories': product['categories'],
            'average_rating': round(product['average_rating'], 2),
            'positive_ratio': round(sentiment_dict[asin], 2)
        }
    return None

def get_recommendations(keyword=None, top_n=3, min_rating=None, min_positive_ratio=None):
    if tfidf_matrix is None or tfidf is None or not high_quality_asins:
        return [{"error": "Product data is unavailable. Please check the files in the data/ directory."}]

    if not keyword:
        return [{"error": "Please provide a keyword for recommendations."}]

    keyword_tfidf = tfidf.transform([keyword])
    keyword_sim = cosine_similarity(keyword_tfidf, tfidf_matrix)
    keyword_scores = list(enumerate(keyword_sim[0]))
    keyword_scores = sorted(keyword_scores, key=lambda x: x[1], reverse=True)

    recommendations = []
    for idx, score in keyword_scores:
        if idx < len(tfidf_asins):
            asin = tfidf_asins[idx]
            if asin in product_details and asin in sentiment_dict:
                product = product_details[asin]
                positive_ratio = sentiment_dict[asin]
                rating = product['average_rating']

                if min_rating and rating < min_rating:
                    continue
                if min_positive_ratio and positive_ratio < min_positive_ratio:
                    continue

                recommendations.append({
                    'asins': asin,
                    'name': product['name'],
                    'categories': product['categories'],
                    'average_rating': round(rating, 2),
                    'positive_ratio': round(positive_ratio, 2),
                    'similarity_score': round(score, 2)
                })
        if len(recommendations) >= top_n:
            break

    if not recommendations:
        return [{"error": "No products found matching the criteria."}]
    return recommendations

def predict_intent(user_input):
    if intent_classifier is None:
        return None
    predicted_intent = intent_classifier.predict([user_input])[0]
    return predicted_intent

def parse_advanced_search(user_input):
    min_rating = None
    min_positive_ratio = None

    rating_pattern = r'rating\s*(?:>|above|at least)\s*(\d*\.?\d+)'
    rating_match = re.search(rating_pattern, user_input.lower())
    if rating_match:
        min_rating = float(rating_match.group(1))

    positive_pattern = r'(?:positive|positive ratio)\s*(?:>|above|at least)\s*(\d+)\s*(?:%|percent)?'
    positive_match = re.search(positive_pattern, user_input.lower())
    if positive_match:
        min_positive_ratio = float(positive_match.group(1))

    return min_rating, min_positive_ratio

def is_product_related_query(user_input):
    user_input_lower = user_input.lower()

    asin_pattern = r'(?:tell\s*me\s*about|cho\s*tôi\s*biết\s*về)\s*([A-Z0-9]{10})\b'
    asin_match = re.search(asin_pattern, user_input_lower, re.IGNORECASE)
    if asin_match:
        return True, asin_match.group(1).upper()

    general_asin_pattern = r'\b[A-Z0-9]{10}\b'
    if re.search(general_asin_pattern, user_input_lower):
        return True, re.search(general_asin_pattern, user_input_lower).group(0).upper()

    product_keywords = ['headphones', 'laptop', 'tablet', 'phone', 'camera', 'watch', 'speaker', 'tv', 'monitor']
    doc = nlp(user_input_lower)
    for token in doc:
        if token.text in product_keywords:
            return True, None

    if any(phrase in user_input_lower for phrase in ['recommend', 'suggest', 'find', 'looking for']):
        return True, None

    return False, None
