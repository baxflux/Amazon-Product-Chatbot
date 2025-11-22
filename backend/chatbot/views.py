import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from .models import ChatMessage

from .services.chatbot_logic import handle_user_input

@csrf_exempt
def chat_handler(request):
    if request.method == 'POST':
        if not request.session.session_key:
            request.session.create()

        data = json.loads(request.body)
        user_input = data.get('message', '').strip()

        if not user_input:
            return JsonResponse({'response': "Please enter a question or keyword!", 'sentiment': ''})

        response, sentiment = handle_user_input(user_input, request.session)

        ChatMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            message=user_input,
            is_user=True,
            sentiment=sentiment
        )

        ChatMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            message=response,
            is_user=False
        )

        return JsonResponse({'response': response, 'sentiment': sentiment})

    return JsonResponse({'error': 'Method not supported.'})

def chatbot_view(request):
    if not request.session.session_key:
        request.session.create()

    session_key = request.GET.get('session_key')
    if session_key:
        chat_history = ChatMessage.objects.filter(session_key=session_key)
    else:
        chat_history = ChatMessage.objects.filter(session_key=request.session.session_key)

    sessions = ChatMessage.objects.values('session_key').annotate(message_count=Count('id')).order_by('-message_count')

    initial_response = "Hello! I'm Amazon Product Chatbot. Enter a keyword 'tablet' or ask me 'Tell me about B01AHB9CN2' to get started!"
    return render(request, 'chatbot.html', {
        'response': initial_response,
        'chat_history': chat_history,
        'sessions': sessions,
        'current_session': request.session.session_key
    })

@csrf_exempt
def new_chat(request):
    if request.method == 'POST':
        request.session.flush()
        request.session.create()
        return JsonResponse({'status': 'success', 'session_key': request.session.session_key})
    return JsonResponse({'error': 'Method not supported.'})
