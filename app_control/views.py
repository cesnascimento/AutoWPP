import os
import time
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
import requests
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import csv
from io import StringIO

logger = logging.getLogger(__name__)


class HomePageView(TemplateView):
    template_name = 'base.html'


@csrf_exempt
def generate_token(request):
    url = f"http://localhost:21465/api/mySession/THISISMYSECURETOKEN/generate-token"
    response = requests.post(url)
    data = response.json()
    token = data['token']
    request.session['auth_token'] = token
    return token



def check_connection_session(request):
    token = request.session.get('auth_token')
    if not token:
        return render(request, 'error_page.html', {'message': 'No authentication token found'})

    headers = {'Authorization': f'Bearer {token}'}
    url = 'http://localhost:21465/api/mySession/check-connection-session'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return render(request, 'app/check_connection.html', {'data': data})
    else:
        return render(request, 'error_page.html', {'message': 'Failed to check connection', 'status_code': response.status_code})


def status_session(request):
    token = request.session.get('auth_token')
    headers = {
        'Authorization': f'Bearer {token}',
    }
    url = 'http://localhost:21465/api/mySession/status-session'
    response = requests.get(url, headers=headers)
    return response


def view_status_session(request):
    token = request.session.get('auth_token')
    headers = {'Authorization': f'Bearer {token}'}
    url = 'http://localhost:21465/api/mySession/status-session'
    response = requests.get(url, headers=headers)
    if not token:
        return render(request, 'adminlte_error.html', {'error': 'No token provided'})

    response = status_session(request)
    if response.status_code == 200:
        status_data = response.json()
        return render(request, 'app/status_session_page.html', {'status_data': status_data})
    else:
        return render(request, 'adminlte_error.html', {'error': 'Failed to retrieve status', 'status_code': response.status_code})


def start_session(request):
    token = generate_token(request)

    headers = {
        'Authorization': f'Bearer {token}',
    }

    url_qr_code = "http://localhost:21465/api/mySession/start-session"
    response = requests.post(url_qr_code, headers=headers)

    if response.status_code == 200:
        start_session_data = response.json()
        qr_code_base64 = start_session_data.get('qrcode', '')
        if qr_code_base64:
            qr_code_base64 = qr_code_base64.split("base64,")[-1]
            check_connection = check_connection_session(request)
            status_connection = status_session(request)
            return render(request, 'app/qrcode_page.html', {'qr_code_base64': qr_code_base64})
        else:
            return render(request, 'adminlte_error.html', {'error': 'QR code data not found'})
    else:
        return redirect('status_session')


@csrf_exempt
def create_group_view(request):
    if request.method == 'POST':
        group_names = request.POST.getlist('groupNames[]')
        participants = request.POST.getlist('participants[]')
        token = request.session.get('auth_token')
        
        if not token:
            return JsonResponse({'error': 'Token de autenticação não encontrado'}, status=401)

        url = 'http://localhost:21465/api/mySession/create-group'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        for group_name in group_names:
            data = {
                "name": group_name,
                "participants": participants
            }

            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 201:
                pass
            else:
                pass

            time.sleep(13)

        return redirect('list_groups')

    return render(request, 'app/create_group_form.html')


def all_groups_view(request):
    token = request.session.get('auth_token')
    if not token:
        return JsonResponse({'error': 'Authentication token not found'}, status=401)

    url = f'http://localhost:21465/api/mySession/list-chats'
    headers = {
        'Authorization': f'Bearer {token}'
    }

    data = {
        'onlyGroups': 'true'
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        all_groups = response.json()

        groups_list = []
        for group in all_groups:
            group_metadata = group.get('groupMetadata', {})
            group_id_info = group.get('id', {})
            total_participants = len(group_metadata.get('participants', []))

            serialized_id = group_id_info.get('user', '')

            invite_link_url = f'http://localhost:21465/api/mySession/group-invite-link/{serialized_id}'
            data = {
                'groupId': f'{serialized_id}'  # Atribua "true" para obter apenas grupos
            }
            invite_response = requests.get(invite_link_url, headers=headers, data=data)

            invite_link = ''
            if invite_response.status_code == 200:
                invite_link_data = invite_response.json()
                invite_link = invite_link_data.get('response', '')
            groups_list.append({
                'name': group.get('name', ''),
                'serialized_id': serialized_id,
                'total_participants': total_participants,
                'invite_link': invite_link
            })

        return render(request, 'app/common_groups.html', {'groups': groups_list})
    else:
        return JsonResponse({'error': 'Failed to retrieve data', 'status_code': response.status_code}, status=response.status_code)


def list_groups_view(request):
    token = request.session.get('auth_token')
    session_id = 'mySession'

    if not token:
        return JsonResponse({'error': 'Token de autenticação não encontrado'}, status=401)

    url = f'http://localhost:21465/api/{session_id}/list-chats'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    payload = {"onlyGroups": True}
    response = requests.post(url, json=payload, headers=headers).json()
    groups = []
    group_names = {}

    for group in response:
        group_metadata = group.get('groupMetadata', {})
        group_name = group_metadata.get('subject', '')

        group_info = {
            'id': group_metadata.get('id', {}).get('user', ''),
            'serialized': group_metadata.get('id', {}).get('_serialized', ''),
            'name': group_name,
            'participants_count': len(group_metadata.get('participants', [])),
            'is_announce': group_metadata.get('announce', False)
        }

        if group_name in group_names:
            group_names[group_name] = group_info
        else:
            group_names[group_name] = group_info

    groups = list(group_names.values())

    return render(request, 'app/list_groups.html', {'groups': groups})


def add_people_to_group_view(request, group_id):
    token = request.session.get('auth_token')
    session_id = 'mySession'

    if not token:
        return JsonResponse({'error': 'Token de autenticação não encontrado'}, status=401)

    url = f'http://localhost:21465/api/{session_id}/all-contacts'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        contacts_data = response.json().get('response', [])
        seen_names = set()
        filtered_contacts = []

        for contact in contacts_data:
            if contact.get('isUser', False):
                formatted_name = contact.get('formattedName', '')

                if formatted_name in seen_names:
                    continue

                seen_names.add(formatted_name)
                if contact['id']['server'] == 'c.us':
                    filtered_contacts.append({
                        'id': contact['id']['user'],
                        'formattedName': formatted_name
                    })

        return render(request, 'app/add_people_to_group.html', {'contacts': filtered_contacts, 'group_id': group_id})
    else:
        return JsonResponse({'error': 'Falha ao buscar contatos', 'status_code': response.status_code}, status=response.status_code)


def submit_add_people_to_group_view(request, group_id):
    if request.method == 'POST':
        token = request.session.get('auth_token')
        session_id = 'mySession'

        if not token:
            return JsonResponse({'error': 'Token de autenticação não encontrado'}, status=401)

        contacts = request.POST.getlist('contacts[]')
        print(contacts)
        url = f'http://localhost:21465/api/{session_id}/add-participant-group'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        for phone in contacts:
            data = {
                'groupId': f'{group_id}@g.us',
                'phone': phone
            }
            response = requests.post(url, json=data, headers=headers)

            if response.status_code != 201:
                return JsonResponse({'error': f'Falha ao adicionar {phone} ao grupo', 'status_code': response.status_code}, status=response.status_code)

        return redirect('list_groups')


def generate_invite_link_ajax(request, group_id):
    token = request.session.get('auth_token')
    session_id = 'mySession'

    if not token:
        return JsonResponse({'error': 'Token de autenticação não encontrado'}, status=401)
    

    url = f'http://localhost:21465/api/{session_id}/group-invite-link/{group_id}'
    url2 = f'http://localhost:21465/api/{session_id}/group-members-ids/{group_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    data = {
        "groupId": f"{group_id}"
    }

    response = requests.get(url, headers=headers, data=data)
    response2 = requests.get(url2, headers=headers, data=data)

    if response.status_code == 200:
        invite_link = response.json().get('response', '')
        return JsonResponse({'invite_link': invite_link})
    else:
        return JsonResponse({'error': 'Falha ao gerar o link de convite', 'status_code': response.status_code}, status=response.status_code)


def upload_group_photo_view(request, group_id):
    if request.method == 'POST':
        token = request.session.get('auth_token')
        session_id = 'mySession'

        if not token:
            return JsonResponse({'error': 'Token de autenticação não encontrado'}, status=401)

        image_path = request.POST.get('image_path')

        url = f'http://localhost:21465/api/{session_id}/group-pic'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        data = {
            'groupId': group_id,
            'path': image_path
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            return JsonResponse({'message': 'Foto do grupo atualizada com sucesso!'})
        else:
            return JsonResponse({'error': 'Falha ao atualizar a foto do grupo', 'status_code': response.status_code}, status=response.status_code)

    return render(request, 'app/upload_group_photo.html', {'group_id': group_id})


def send_message_view(request, group_id):
    if request.method == 'POST':
        token = request.session.get('auth_token')
        session_id = 'mySession'  # Substitua pelo identificador correto

        if not token:
            return JsonResponse({'error': 'Token de autenticação não encontrado'}, status=401)

        message_type = request.POST.get('message_type')
        message = request.POST.get('message', '')
        image_path = request.POST.get('image_path', '')
        caption = request.POST.get('caption', '')

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        if message_type == 'text_only':
            
            url = f'http://localhost:21465/api/{session_id}/send-message'
            data = {
                'phone': f'{group_id}@g.us',
                'isGroup': 'true',
                'message': message
            }
        elif message_type == 'text_with_image':
            if not os.path.isfile(image_path):
                return JsonResponse({'error': f'O arquivo {image_path} não foi encontrado'}, status=400)

            url = f'http://localhost:21465/api/{session_id}/send-image'
            data = {
                'phone': f'{group_id}@g.us',
                'isGroup': 'true',
                'filename': image_path,
                'caption': caption
            }
        else:
            return JsonResponse({'error': 'Tipo de mensagem inválido'}, status=400)

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 201:
            return JsonResponse({'message': 'Mensagem enviada com sucesso!'})
        else:
            return JsonResponse({'error': 'Falha ao enviar a mensagem', 'status_code': response.status_code}, status=response.status_code)

    return render(request, 'app/send_message.html', {'group_id': group_id})


@csrf_exempt
def create_community_view(request):
    if request.method == 'POST':
        token = request.session.get('auth_token')
        session_id = 'mySession'

        if not token:
            return JsonResponse({'error': 'Token de autenticação não encontrado'}, status=401)

        names = request.POST.getlist('name[]')
        descriptions = request.POST.getlist('description[]')

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        for name, description in zip(names, descriptions):
            url = f'http://localhost:21465/api/{session_id}/create-community'
            data = {
                'name': name,
                'description': description,
                'groupIds': []
            }

            response = requests.post(url, json=data, headers=headers)
            if response.status_code != 200:
                return JsonResponse({'error': f'Falha ao criar comunidade {response.text}', 'status_code': response.status_code}, status=response.status_code)

            time.sleep(13)

        return redirect('success_page')

    return render(request, 'app/create_community_form.html')

def get_contact_community_view(request, group_id):
    token = request.session.get('auth_token')
    headers = {
        'Authorization': f'Bearer {token}',
    }
    data = {
                'groupId': group_id,
            }
    session_id = 'mySession'
    url = f'http://localhost:21465/api/{session_id}/group-members-ids/{group_id}'
    response = requests.get(url, data=data, headers=headers)
    data = response.json()
    if response.status_code == 200:
        serialized_values = [item['_serialized'] for item in data['response']]

        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)

        csv_writer.writerow(['_serialized'])
        for value in serialized_values:
            csv_writer.writerow([value])

        response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=participantes.csv'

        return response
