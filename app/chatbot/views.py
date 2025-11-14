from django.shortcuts import render

import json
import pandas as pd
import joblib
import pickle
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import spacy
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
import re
from .models import ChatMessage
from django.db.models import Count

# Define base directory for data files
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = BASE_DIR / 'model'

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load precomputed data for product recommendations (Amazon dataset)
try:
    with open(MODEL_DIR / 'tfidf_matrix.pkl', 'rb') as f:
        tfidf_matrix = joblib.load(f)
    with open(MODEL_DIR / 'tfidf_vectorizer.pkl', 'rb') as f:
        tfidf = joblib.load(f)
    sentiment_summary = pd.read_csv(DATA_DIR / 'new-data/sentiment_summary.csv')
    high_quality_products = pd.read_csv(DATA_DIR / 'new-data/high_quality_products.csv')
    data = pd.read_csv(DATA_DIR / 'preprocessed-data/cleaned_amazon_reviews.csv')
except FileNotFoundError as e:
    print(f"Error loading Amazon files: {e}")
    tfidf_matrix = None
    tfidf = None
    sentiment_summary = None
    high_quality_products = None
    data = None

# Load cleaned Bitext dataset and trained intent classifier
try:
    bitext_data = pd.read_csv(DATA_DIR / 'preprocessed-data/bitext_cleaned.csv')
    intent_classifier = joblib.load(MODEL_DIR / 'intent_classifier.pkl')
except FileNotFoundError as e:
    print(f"Error loading Bitext dataset or model: {e}")
    bitext_data = None
    intent_classifier = None

# Load the trained sentiment model and TF-IDF vectorizer for sentiment analysis
try:
    with open(MODEL_DIR / 'tfidf_vectorizer_user.pkl', 'rb') as f:
        sentiment_tfidf = pickle.load(f)
    with open(MODEL_DIR / 'sentiment_model_user.pkl', 'rb') as f:
        sentiment_model = pickle.load(f)
except FileNotFoundError as e:
    print(f"Error loading sentiment model files: {e}")
    sentiment_tfidf = None
    sentiment_model = None

# Create a mapping of ASIN to product details (Amazon dataset)
if data is not None:
    product_details = data.drop_duplicates(subset=['asins']).set_index('asins')[
        ['name', 'categories', 'reviews.rating']
    ].to_dict('index')
else:
    product_details = {}

# Create a mapping of ASIN to sentiment data for correct indexing (Amazon dataset)
if sentiment_summary is not None and high_quality_products is not None:
    sentiment_dict = sentiment_summary.set_index('asins')['positive_ratio'].to_dict()
    high_quality_asins = high_quality_products['asins'].tolist()
    tfidf_asins = high_quality_products['asins'].tolist()
else:
    sentiment_dict = {}
    high_quality_asins = []
    tfidf_asins = []

# Create a mapping of intents to responses (Bitext dataset)
if bitext_data is not None:
    bitext_intents = bitext_data.groupby('intent').agg({
        'response': lambda x: list(x)
    }).to_dict('index')
else:
    bitext_intents = {}

# Function to predict sentiment
def predict_sentiment(text):
    if sentiment_tfidf is None or sentiment_model is None:
        return "unknown"
    text_tfidf = sentiment_tfidf.transform([text])
    sentiment = sentiment_model.predict(text_tfidf)[0]
    return sentiment

def extract_keywords(text):
    """Extract main keywords from user input."""
    doc = nlp(text.lower())
    keywords = [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop]
    return ' '.join(keywords) if keywords else text

def get_product_info(asin):
    """Get product information from Amazon dataset."""
    if asin in product_details and asin in sentiment_dict:
        product = product_details[asin]
        return {
            'name': product['name'],
            'categories': product['categories'],
            'average_rating': round(product['reviews.rating'], 2),
            'positive_ratio': round(sentiment_dict[asin], 2)
        }
    return None

def get_recommendations(keyword=None, top_n=3, min_rating=None, min_positive_ratio=None):
    """Generate product recommendations with advanced filtering."""
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
                rating = product['reviews.rating']

                # Apply filters if specified
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
    """Predict intent using the trained intent classifier."""
    if intent_classifier is None:
        return None
    predicted_intent = intent_classifier.predict([user_input])[0]
    return predicted_intent

def parse_advanced_search(user_input):
    """Parse advanced search query for min_rating and min_positive_ratio."""
    min_rating = None
    min_positive_ratio = None

    # Look for rating criteria (e.g., "rating > 4", "rating above 4")
    rating_pattern = r'rating\s*(?:>|above|at least)\s*(\d*\.?\d+)'
    rating_match = re.search(rating_pattern, user_input.lower())
    if rating_match:
        min_rating = float(rating_match.group(1))

    # Look for positive ratio criteria (e.g., "positive ratio > 80%", "positive above 80")
    positive_pattern = r'(?:positive|positive ratio)\s*(?:>|above|at least)\s*(\d+)\s*(?:%|percent)?'
    positive_match = re.search(positive_pattern, user_input.lower())
    if positive_match:
        min_positive_ratio = float(positive_match.group(1))

    return min_rating, min_positive_ratio

def is_product_related_query(user_input):
    """Check if the user input is likely a product-related query."""
    user_input_lower = user_input.lower()

    # Enhanced ASIN detection
    asin_pattern = r'(?:tell\s*me\s*about|cho\s*tôi\s*biết\s*về)\s*([A-Z0-9]{10})\b'
    asin_match = re.search(asin_pattern, user_input_lower, re.IGNORECASE)
    if asin_match:
        return True, asin_match.group(1).upper()

    general_asin_pattern = r'\b[A-Z0-9]{10}\b'
    if re.search(general_asin_pattern, user_input_lower):
        return True, re.search(general_asin_pattern, user_input_lower).group(0).upper()

    # Check for product-related keywords
    product_keywords = ['headphones', 'laptop', 'tablet', 'phone', 'camera', 'watch', 'speaker', 'tv', 'monitor']
    doc = nlp(user_input_lower)
    for token in doc:
        if token.text in product_keywords:
            return True, None

    # Check for phrases indicating product search
    if any(phrase in user_input_lower for phrase in ['recommend', 'suggest', 'find', 'looking for']):
        return True, None

    return False, None

@csrf_exempt
def chat_handler(request):
    """Handle chatbot Q&A logic with trained intent classifier and product recommendations."""
    if request.method == 'POST':
        if not request.session.session_key:
            request.session.create()

        data = json.loads(request.body)
        user_input = data.get('message', '').strip()

        if not user_input:
            return JsonResponse({'response': "Please enter a question or keyword!", 'sentiment': ''})

        # Predict sentiment for the user input
        sentiment = predict_sentiment(user_input)

        # Save user message to database
        ChatMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            message=user_input,
            is_user=True,
            sentiment=sentiment
        )

        # Check if this is a response to "Would you like to see similar products?"
        if user_input.lower() in ['yes', 'no', 'có', 'không']:
            if request.session.get('similar_products_offer', False):
                if user_input.lower() in ['yes', 'có']:
                    last_asin = request.session.get('last_asin', '')
                    if last_asin and last_asin in product_details:
                        keyword = extract_keywords(product_details[last_asin]['name'])
                        recommendations = get_recommendations(keyword, top_n=3)
                        if 'error' in recommendations[0]:
                            response = recommendations[0]['error']
                        else:
                            product_list = "\n".join([f"- {rec['name']} (Positive rating ratio: {rec['positive_ratio']}%, Average rating: {rec['average_rating']})" for rec in recommendations])
                            response = f"Here are some similar products:\n{product_list}\nWould you like more details?"
                    else:
                        response = "Sorry, I couldn't retrieve the previous product details. Please try asking about the product again."
                else:
                    response = "Alright, let me know if you need help with anything else!"
                request.session['similar_products_offer'] = False
                request.session['last_response'] = response

                # Save bot response to database
                ChatMessage.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key,
                    message=response,
                    is_user=False
                )

                return JsonResponse({'response': response, 'sentiment': sentiment})

        # Check if the input is a product-related query with advanced search
        is_product, detected_asin = is_product_related_query(user_input)
        if is_product:
            if detected_asin:
                if detected_asin in high_quality_asins:
                    info = get_product_info(detected_asin)
                    if info:
                        response = f"Here is the information about {info['name']}: Positive rating ratio {info['positive_ratio']}%, Average rating: {info['average_rating']}. Would you like to see similar products?"
                        request.session['last_asin'] = detected_asin
                        request.session['similar_products_offer'] = True
                        request.session['last_response'] = response
                    else:
                        response = f"Could not find detailed information about {detected_asin}. Try another ASIN or keyword!"
                else:
                    response = f"Could not find information about {detected_asin}. Try another ASIN or keyword!"
            else:
                # Handle advanced product search
                min_rating, min_positive_ratio = parse_advanced_search(user_input)
                keyword = extract_keywords(user_input)
                recommendations = get_recommendations(keyword, top_n=3, min_rating=min_rating, min_positive_ratio=min_positive_ratio)
                if 'error' in recommendations[0]:
                    response = recommendations[0]['error']
                else:
                    product_list = "\n".join([f"- {rec['name']} (Positive rating ratio: {rec['positive_ratio']}%, Average rating: {rec['average_rating']})" for rec in recommendations])
                    response = f"Based on your request, here are some highly rated products:\n{product_list}\nWould you like more details?"
            request.session['last_response'] = response

            # Save bot response to database
            ChatMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
                message=response,
                is_user=False
            )

            return JsonResponse({'response': response, 'sentiment': sentiment})

        # Predict intent using the trained classifier
        predicted_intent = predict_intent(user_input)
        if predicted_intent and predicted_intent in bitext_intents:
            responses = bitext_intents[predicted_intent]['response']
            bitext_response = responses[0]
            request.session['last_response'] = bitext_response
            request.session['similar_products_offer'] = False

            # Save bot response to database
            ChatMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
                message=bitext_response,
                is_user=False
            )

            return JsonResponse({'response': bitext_response, 'sentiment': sentiment})

        # Default conversational logic
        response = ""
        if any(keyword in user_input.lower() for keyword in ['hello', 'hi', 'chào']):
            response = "Hello! I'm Amazon's product recommendation chatbot. How can I assist you? Enter a keyword (e.g., 'headphones') or ask about a product!"
        elif any(keyword in user_input.lower() for keyword in ['help', 'trợ giúp', 'hỗ trợ']):
            response = "I can help you find high-quality products! Please enter a keyword (e.g., 'tablet') or ask for details (e.g., 'Tell me about B01AHB9CN2')."
        elif 'price' in user_input.lower() or 'giá' in user_input.lower():
            response = "I don't have specific price information, but I can recommend high-quality products. Please enter an ASIN or keyword to check!"
        else:
            response = "I'm not sure how to assist with that. Please try asking about a product (e.g., 'wireless headphones') or a specific ASIN (e.g., 'Tell me about B01AHB9CN2'), or let me know how I can help!"

        request.session['last_response'] = response
        request.session['similar_products_offer'] = False

        # Save bot response to database
        ChatMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            message=response,
            is_user=False
        )

        return JsonResponse({'response': response, 'sentiment': sentiment})

    return JsonResponse({'error': 'Method not supported.'})

@csrf_exempt
def new_chat(request):
    """Create a new chat session."""
    if request.method == 'POST':
        # Flush the current session and create a new one
        request.session.flush()
        request.session.create()
        return JsonResponse({'status': 'success', 'session_key': request.session.session_key})
    return JsonResponse({'error': 'Method not supported.'})

def chatbot_view(request):
    """Display the initial chatbot interface with chat history."""
    if not request.session.session_key:
        request.session.create()

    # Get session_key from query parameter if provided
    session_key = request.GET.get('session_key')
    if session_key:
        # Filter chat history by the specified session_key without changing the current session
        chat_history = ChatMessage.objects.filter(session_key=session_key)
    else:
        # Use the current session if no session_key is provided
        chat_history = ChatMessage.objects.filter(session_key=request.session.session_key)

    # Get list of all sessions (distinct session keys) with message count
    sessions = ChatMessage.objects.values('session_key').annotate(message_count=Count('id')).order_by('-message_count')

    initial_response = "Hello! I'm Amazon's product recommendation chatbot. Enter a keyword (e.g., 'headphones') or ask me (e.g., 'Tell me about B01AHB9CN2') to get started!"
    return render(request, 'pomato/chatbot.html', {
        'response': initial_response,
        'chat_history': chat_history,
        'sessions': sessions,
        'current_session': request.session.session_key
    })

def home_view(request):
    """Display the home page (index.html from pomato template)."""
    return render(request, 'pomato/index.html')

def special_view(request):
    """Display the special page (special.html from pomato template)."""
    return render(request, 'pomato/special.html')

def brand_view(request):
    """Display the brand page (brand.html from pomato template)."""
    return render(request, 'pomato/brand.html')

def product_view(request):
    """Display the product page (product.html from pomato template)."""
    return render(request, 'pomato/product.html')

def cart_view(request):
    """Display the cart page (cart.html from pomato template)."""
    return render(request, 'pomato/cart.html')
def contact_view(request):
    
    """Display the contact page (contact.html from pomato template)."""
    return render(request, 'pomato/contact.html')
