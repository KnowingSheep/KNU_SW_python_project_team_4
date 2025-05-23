from django.shortcuts import render

import subprocess
from django.http import HttpResponse

# Create your views here.
def danger_map_view(request):
    return render(request, 'accident_map/danger_map.html')

def cluster_map_view(request):
    return render(request, 'accident_map/cluster_map.html')

def run_danger_map(request):
    subprocess.run(['python', 'scripts/1_generate_danger_map.py'])
    return HttpResponse("교통사고 위험지도 생성 완료")

def run_cluster_map(request):
    subprocess.run(['python', 'scripts/2_generate_cluster_map.py'])
    return HttpResponse("시군구 사고클러스터 지도 생성 완료!")

def index(request):
    return render(request, 'accident_map/index.html')