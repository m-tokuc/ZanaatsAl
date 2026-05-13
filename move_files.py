import os
import shutil

backend_files = ['main.py', 'orchestrator_service.py', 'serper_service.py', 'vision_test.py', 'api_contract.py', '.env', '.env.example', 'ipad_case.jpeg']
frontend_files = ['lib', 'android', 'ios', 'linux', 'macos', 'test', 'web', 'windows', 'pubspec.yaml', 'pubspec.lock', 'analysis_options.yaml', '.metadata']

for f in backend_files:
    if os.path.exists(f):
        os.system(f"git mv {f} backend/")

for f in frontend_files:
    if os.path.exists(f):
        os.system(f"git mv {f} frontend/")
