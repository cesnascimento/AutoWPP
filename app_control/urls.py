from django.urls import path
from .views import HomePageView, add_people_to_group_view, all_groups_view, check_connection_session, create_community_view, generate_invite_link_ajax, generate_token, list_groups_view, send_message_view, start_session, submit_add_people_to_group_view, upload_group_photo_view, view_status_session, create_group_view


urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('generate-token/', generate_token, name='generate_token'),
    path('start-session/', start_session, name='start_session'),
    path('status-session/', view_status_session, name='status_session'),
    path('create-group/', create_group_view, name='create_group'),
    path('all-groups/', all_groups_view, name='all_groups'),
    path('check-connection/', check_connection_session, name='check_connection'),
    path('list-groups/', list_groups_view, name='list_groups'),
    path('group/<slug:group_id>/add-people/', add_people_to_group_view, name='add_people_to_group'),
    path('group/<slug:group_id>/submit-add-people/', submit_add_people_to_group_view, name='submit_add_people'),
    path('group/<slug:group_id>/ajax-invite-link/', generate_invite_link_ajax, name='generate_invite_link_ajax'),
    path('group/<slug:group_id>/upload-photo/', upload_group_photo_view, name='upload_group_photo'),
    path('group/<slug:group_id>/send-message/', send_message_view, name='send_message'),
    path('create-community/', create_community_view, name='create_community'),
]