from .nlp_engine import *

# Chatbot Logic 1: Handle ASIN or Keyword Response
def handle_product_query(user_input, session):
    is_product, detected_asin = is_product_related_query(user_input)
    if not is_product:
        return None

    if detected_asin:
        if detected_asin in high_quality_asins:
            info = get_product_info(detected_asin)
            if info:
                response = f"Here is the information about {info['name']}: Positive rating ratio {info['positive_ratio']}%, Average rating: {info['average_rating']}. Would you like to see similar products?"
                session['last_asin'] = detected_asin
                session['similar_products_offer'] = True
            else:
                response = f"Could not find detailed information about {detected_asin}. Try another ASIN or keyword!"
        else:
            response = f"Could not find information about {detected_asin}. Try another ASIN or keyword!"
    else:
        min_rating, min_positive_ratio = parse_advanced_search(user_input)
        keyword = extract_keywords(user_input)
        recommendations = get_recommendations(keyword, top_n=3, min_rating=min_rating, min_positive_ratio=min_positive_ratio)
        if 'error' in recommendations[0]:
            response = recommendations[0]['error']
        else:
            product_list = "\n".join([f"- {rec['name']} (Positive rating ratio: {rec['positive_ratio']}%, Average rating: {rec['average_rating']})" for rec in recommendations])
            response = f"Based on your request, here are some highly rated products:\n{product_list}\nWould you like more details?"
    return response

# Chatbot Logic 2: Handle Yes/No Response
def handle_similar_products_response(user_input, session):
    if user_input.lower() in ['yes', 'có']:
        last_asin = session.get('last_asin', '')
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
    session['similar_products_offer'] = False
    return response

# Chatbot Logic 3: Handle Intent-Based Responses
def handle_intent_response(user_input, session):
    predicted_intent = predict_intent(user_input)
    if predicted_intent and predicted_intent in bitext_intents:
        responses = bitext_intents[predicted_intent]['response']
        response = responses[0]
        session['similar_products_offer'] = False
        return response
    return None

# Chatbot Logic 4: Default Conversational Responses
def handle_default_conversation(user_input, session):
    if any(keyword in user_input.lower() for keyword in ['hello', 'hi', 'chào']):
        response = "Hello! I'm Amazon's product recommendation chatbot. How can I assist you? Enter a keyword (e.g., 'headphones') or ask about a product!"
    elif any(keyword in user_input.lower() for keyword in ['help', 'trợ giúp', 'hỗ trợ']):
        response = "I can help you find high-quality products! Please enter a keyword (e.g., 'tablet') or ask for details (e.g., 'Tell me about B01AHB9CN2')."
    elif 'price' in user_input.lower() or 'giá' in user_input.lower():
        response = "I don't have specific price information, but I can recommend high-quality products. Please enter an ASIN or keyword to check!"
    else:
        response = "I'm not sure how to assist with that. Please try asking about a product (e.g., 'wireless headphones') or a specific ASIN (e.g., 'Tell me about B01AHB9CN2'), or let me know how I can help!"
    session['similar_products_offer'] = False
    return response

# Main Chatbot Logic: Handle User Input
def handle_user_input(user_input, session):
    sentiment = predict_sentiment(user_input)

    if user_input.lower() in ['yes', 'no', 'có', 'không'] and session.get('similar_products_offer', False):
        response = handle_similar_products_response(user_input, session)
    elif is_product_related_query(user_input)[0]:
        response = handle_product_query(user_input, session)
    elif predict_intent(user_input) and predict_intent(user_input) in bitext_intents:
        response = handle_intent_response(user_input, session)
    else:
        response = handle_default_conversation(user_input, session)

    session['last_response'] = response
    return response, sentiment
