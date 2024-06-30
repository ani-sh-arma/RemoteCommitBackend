# views.py
import base64
import json
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

class GitHubRepoUploadView(APIView):
    def post(self, request):
        base_url = 'https://api.github.com'
        username = settings.GITHUB_USERNAME
        token = settings.GITHUB_TOKEN
        
        repo_name = request.data.get('repo_name')
        repo_description = request.data.get('repo_description')
        project_structure = request.data.get('project_structure')
        
        if not all([repo_name, repo_description, project_structure]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create repository
        create_url = f"{base_url}/user/repos"
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        payload = {
            'name': repo_name,
            'description': repo_description,
            'private': False,
            'auto_init': True
        }
        response = requests.post(create_url, headers=headers, json=payload)
        
        if response.status_code != 201:
            return Response({"error": "Failed to create repository", "details": response.text}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        clone_url = response.json()['clone_url']
        
        # Upload files
        def upload_files(items, current_path=""):
            for item in items:
                if item['type'] == 'file':
                    file_path = f"{current_path}/{item['name']}" if current_path else item['name']
                    upload_url = f"{base_url}/repos/{username}/{repo_name}/contents/{file_path}"
                    
                    try:
                        decoded_content = base64.b64decode(item['content']).decode('utf-8')
                    except:
                        return Response({"error": f"Failed to decode content for {file_path}"}, 
                                        status=status.HTTP_400_BAD_REQUEST)
                    
                    payload = {
                        'message': f'Add {file_path}',
                        'content': base64.b64encode(decoded_content.encode('utf-8')).decode('utf-8'),
                        'branch': 'main'
                    }
                    response = requests.put(upload_url, headers=headers, json=payload)
                    
                    if response.status_code != 201:
                        return Response({"error": f"Failed to upload {file_path}", "details": response.text}, 
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                elif item['type'] == 'directory':
                    new_path = f"{current_path}/{item['name']}" if current_path else item['name']
                    result = upload_files(item['children'], new_path)
                    if isinstance(result, Response):
                        return result
        
        result = upload_files(json.loads(project_structure))
        if isinstance(result, Response):
            return result
        
        return Response({"message": "Repository created and files uploaded successfully", "clone_url": clone_url}, 
                        status=status.HTTP_201_CREATED)