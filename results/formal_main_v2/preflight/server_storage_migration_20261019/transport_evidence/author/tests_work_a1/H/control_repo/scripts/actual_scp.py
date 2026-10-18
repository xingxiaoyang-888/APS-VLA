import subprocess
subprocess.run(['scp','-q','results/upload_source.json','tongji-cvpr:/share/home/u15016/XXY_CVPR/CTI-VLA/storage_migration_candidates/server_transport_v1/tests_work_a1/P/results/transport_upload.json'],check=True)
subprocess.run(['scp','-q','tongji-cvpr:/share/home/u15016/XXY_CVPR/CTI-VLA/storage_migration_candidates/server_transport_v1/tests_work_a1/P/results/transport_upload.json','results/transport_back.json'],check=True)
subprocess.run(['scp','-q','results/upload_source.json','tongji-cvpr:/share/home/u15016/XXY_CVPR/CTI-VLA/storage_migration_candidates/server_transport_v1/tests_work_a1/P/results/transport_upload.json'],check=True)
