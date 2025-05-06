from http.client import responses

from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests
import json
import re

from .forms import FilterForm, ExcelUploadForm, CriticalPointForm, UpdatePCForm

from datetime import datetime

import logging
logger = logging.getLogger(__name__)

from collections import defaultdict
from datetime import datetime

from collections import defaultdict
from datetime import datetime

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def custom_login_view(request):
    error_message = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')  # Или другой URL
        else:
            error_message = "Неверный логин или пароль"

    return render(request, 'main/login.html', {'error_message': error_message})


def analitic(request):
    actual_sys_info_list = fetch_actual_data_from_fastapi()

    dns_counts = {}
    kav_counts = {}
    mem_counts = {}
    osver_counts = {}
    boot_counts = defaultdict(int)  # Словарь для подсчета количества включений по датам

    # Обработка данных
    for item in actual_sys_info_list:
        param = item['param']
        value = item['value']

        # DNS
        if param == "dns":
            dns_counts[value] = dns_counts.get(value, 0) + 1
        # KAV Version
        elif param == "kav_ver":
            kav_counts[value] = kav_counts.get(value, 0) + 1
        # RAM (mem)
        elif param == "mem":
            mem_size = extract_mem_size(value)
            if mem_size:
                mem_counts[mem_size] = mem_counts.get(mem_size, 0) + 1
        # OS Version
        elif param == "osver":
            osver_counts[value] = osver_counts.get(value, 0) + 1
        # last_boot - подсчитываем количество включений по датам
        elif param == "last_boot":
            try:
                boot_date = datetime.strptime(value, '%d.%m.%Y %H:%M:%S').date()  # Преобразуем в формат даты
                boot_counts[boot_date] += 1
            except ValueError:
                continue  # Если дата неправильного формата, пропускаем

    # Преобразуем boot_counts в список для графика
    boot_dates = sorted(boot_counts.keys())
    boot_values = [boot_counts[date] for date in boot_dates]

    # Сортируем actual_sys_info_list по дате включения
    actual_sys_info_list.sort(key=lambda x: datetime.strptime(x['value'], '%d.%m.%Y %H:%M:%S') if x['param'] == 'last_boot' else datetime.min)

    context = {
        'actual_sys_info_list': actual_sys_info_list,
        'dns_json': json.dumps(dns_counts),
        'kav_json': json.dumps(kav_counts),
        'mem_json': json.dumps(mem_counts),
        'osver_json': json.dumps(osver_counts),
        'boot_dates': json.dumps([date.strftime('%d.%m.%Y') for date in boot_dates]),
        'boot_values': json.dumps(boot_values),
    }

    return render(request, 'main/analitic.html', context)



def extract_mem_size(value):
    """ Извлекаем только объем памяти в Gb/GB """
    import re
    match = re.search(r"(\d+(?:\.\d+)?)\s*(GB|Gb)", value, re.IGNORECASE)
    return match.group(1) if match else None




def fetch_data_from_fastapi(params):
    api_url = "http://127.0.0.1:8000/get-filtered-system-info/"
    # logger.debug(f"Sending request to {api_url} with params: {params}")
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        return response.json()
    # logger.error(f"Error: Received status code {response.status_code}")
    return []

def index(request):
    form = FilterForm(request.GET or None)
    sys_info_list = []
    # problematic_pcs = []
    params = {}
    if form.is_valid():
        # logger.debug("Form is valid. Processing data...")
        
        if form.cleaned_data['id']:
            params['id'] = form.cleaned_data['id'].split(',')
        if form.cleaned_data['hosts']:
            params['hosts'] = form.cleaned_data['hosts'].split(',')
        if form.cleaned_data['params']:
            params['params'] = form.cleaned_data['params'].split(',')
        if form.cleaned_data['values']:
            params['values'] = form.cleaned_data['values'].split(',')
        if form.cleaned_data['start_date']:
            params['start_date'] = form.cleaned_data['start_date']
        if form.cleaned_data['end_date']:
            params['end_date'] = form.cleaned_data['end_date']


    sys_info_list = fetch_data_from_fastapi(params)

    return render(request, 'main/index.html', {'form': form, 'sys_info_list': sys_info_list})






def fetch_actual_data_from_fastapi():
    api_url = "http://127.0.0.1:8000/get-actual-system-info/"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    return []

def update_pc_list(request):
    form = FilterForm(request.GET or None)
    all_sys_info_list = fetch_actual_data_from_fastapi()

    sys_info_list = []
    unique_hosts = set()
    for item in all_sys_info_list:
        host = item.get('host', '')
        if host not in unique_hosts:
            unique_hosts.add(host)
            sys_info_list.append(item)

    # Применяем фильтрацию по host из формы
    if form.is_valid():
        host_filter = form.cleaned_data.get('hosts')
        if host_filter:
            sys_info_list = [item for item in sys_info_list if host_filter.lower() in item['host'].lower()]

    return render(request, 'main/update_pc_list.html', {
        'sys_info_list': sys_info_list,
        'form': form
    })

def fetch_actual_pc(id_raw):
    api_url = f"http://127.0.0.1:8000/get-system-info/{id_raw}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.text
    return []

def update_pc(request, id_raw): 
    actual_pc = fetch_actual_pc(id_raw)

    if isinstance(actual_pc, str):
        actual_pc = json.loads(actual_pc)

    if request.method == 'POST':
        form = UpdatePCForm(request.POST, data=actual_pc)

        if form.is_valid():
            updated_data = actual_pc.copy()  # Копируем оригинальные данные

            # Удаляем параметр из данных, если он очищен
            for key, value in form.cleaned_data.items():
                if value.strip():  # Если значение есть, обновляем
                    updated_data[key] = value.strip()
                else:  # Если поле пустое, удаляем параметр
                    updated_data.pop(key, None)

            # Обработка новых параметров
            new_param = request.POST.get("new-param", "").strip()
            new_value = request.POST.get("new-value", "").strip()
            if new_param and new_value:
                updated_data[new_param] = new_value  # Добавляем новый параметр

            # Удаляем пустые параметры перед отправкой в FastAPI
            updated_data = {k: v for k, v in updated_data.items() if v.strip()}

            # Отправляем обновлённые данные на API FastAPI
            api_url = f"http://127.0.0.1:8000/update-pc/{id_raw}"
            response = requests.put(api_url, json={"data": updated_data})

            if response.status_code == 200:
                return redirect('update_pc_list')
            else:
                return render(request, 'main/update_pc.html', {'form': form, 'error': 'Ошибка при обновлении данных'})
    else:
        form = UpdatePCForm(data=actual_pc)

    return render(request, 'main/update_pc.html', {'form': form, 'id_raw': id_raw})




def problem_pc_list(request):
    form = FilterForm(request.GET or None)
    problematic_pcs = []
    params = {}
    if form.is_valid():
        # logger.debug("Form is valid. Processing data...")
        
        if form.cleaned_data['id']:
            params['id'] = form.cleaned_data['id'].split(',')
        if form.cleaned_data['hosts']:
            params['hosts'] = form.cleaned_data['hosts'].split(',')
        if form.cleaned_data['params']:
            params['params'] = form.cleaned_data['params'].split(',')
        if form.cleaned_data['values']:
            params['values'] = form.cleaned_data['values'].split(',')
        if form.cleaned_data['start_date']:
            params['start_date'] = form.cleaned_data['start_date']
        if form.cleaned_data['end_date']:
            params['end_date'] = form.cleaned_data['end_date']

    sys_info_list = fetch_data_from_fastapi(params)

    critical_points = fetch_critical_points()
    problematic_pcs = analyze_critical_points(sys_info_list, critical_points)

 

    return render(request, 'main/problem_pc_list.html', {'form': form, 'problematic_pcs': problematic_pcs})

def upload_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            files = {'file': (excel_file.name, excel_file, excel_file.content_type)}

            api_url = "http://127.0.0.1:8000/upload-excel/"
            response = requests.post(api_url, files=files)

            if response.status_code == 200:
                logger.debug("File successfully uploaded and processed.")
                return redirect('index')
            else:
                logger.error(f"Error: Received status code {response.status_code}")
                return render(request, 'main/upload_excel.html', {'form': form, 'error': 'Failed to upload file'})
    else:
        form = ExcelUploadForm()

    return render(request, 'main/upload_excel.html', {'form': form})

def fetch_critical_points():
    api_url = "http://127.0.0.1:8000/critical-points/"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error: Received status code {response.status_code}")
    return []

def manage_critical_points(request):
    critical_points = fetch_critical_points()

    if request.method == 'POST':
        form = CriticalPointForm(request.POST)
        if form.is_valid():
            data = {
                "param": form.cleaned_data['param'],
                "check_type": form.cleaned_data['check_type'],  
                "min_value": form.cleaned_data['min_value'],
                "max_value": form.cleaned_data['max_value'],
                "exact_value": form.cleaned_data['exact_value'],
                "measure_of_calculation": form.cleaned_data['measure_of_calculation'], 
                "day_count": form.cleaned_data['day_count'],
                "string_value": form.cleaned_data['string_value']
            }
            api_url = "http://127.0.0.1:8000/critical-points/"
            response = requests.post(api_url, json=data)
      
            if response.status_code == 200:
                logger.debug("Critical point successfully added.")
                return redirect('manage_critical_points')
            else:
               
                logger.error(f"Error: Received status code {response.status_code}")
                return render(request, 'main/manage_critical_points.html', {'form': form, 'critical_points': critical_points, 'error': 'Failed to add critical point'})
    else:
        form = CriticalPointForm()
    
    return render(request, 'main/manage_critical_points.html', {'form': form, 'critical_points': critical_points})

def update_critical_point(request, param):
    if request.method == 'POST':
        form = CriticalPointForm(request.POST)
        if form.is_valid():
            data = {
                "param": form.cleaned_data['param'],
                "check_type": form.cleaned_data['check_type'],  
                "min_value": form.cleaned_data['min_value'],
                "max_value": form.cleaned_data['max_value'],
                "exact_value": form.cleaned_data['exact_value'],
                "measure_of_calculation": form.cleaned_data['measure_of_calculation'], 
                "day_count": form.cleaned_data['day_count'],
                "string_value": form.cleaned_data['string_value']
            }
            api_url = f"http://127.0.0.1:8000/critical-points/{param}"
            response = requests.put(api_url, json=data)

            if response.status_code == 200:
                logger.debug("Critical point successfully updated.")
                return redirect('manage_critical_points')
            else:
                logger.error(f"Error: Received status code {response.status_code}")
                return render(request, 'main/update_critical_point.html', {'form': form, 'error': 'Failed to update critical point'})
    else:
        critical_points = fetch_critical_points()
        initial_data = next((cp for cp in critical_points if cp['param'] == param), None)
        form = CriticalPointForm(initial=initial_data)

    return render(request, 'main/update_critical_point.html', {'form': form, 'param': param})

def delete_critical_point(request, param):
    api_url = f"http://127.0.0.1:8000/critical-points/{param}"
    response = requests.delete(api_url)

    if response.status_code == 200:
        logger.debug("Critical point successfully deleted.")
        return redirect('manage_critical_points')
    else:
        logger.error(f"Error: Received status code {response.status_code}")
        return render(request, 'main/manage_critical_points.html', {'error': 'Failed to delete critical point'})

def analyze_critical_points(sys_info_list, critical_points):
    problematic_pcs = []
    # print(f'Весь sys_info_list {sys_info_list}')
    for pc in sys_info_list:
        issues = []
        # logger.debug(f"Analyzing PC: {pc}")
        for criterion in critical_points:
            
            param_value = None

            # Найти значение параметра для текущего ПК
            if pc['param'] == criterion['param']:
                param_value = pc['value']
                print(f'нашел критический параметр: {pc['param']}')

            # Если значение параметра в таблцие не пустое
            if param_value is not None:
                #Если выбрали границы
                if criterion['check_type'] == 'borders':
                    value = float(param_value)
                    
                    #Если выбрали GB
                    if criterion['measure_of_calculation'] == 'GB':
                        value = float(param_value.replace(' GB', ''))
                    else:
                        value = float(param_value)


                    if (criterion['min_value'] is not None and value < criterion['min_value']) or \
                        (criterion['max_value'] is not None and value > criterion['max_value']):
                        issues.append({'param': criterion['param'],
                                       'expected': criterion,
                                       'actual': param_value})
                

                #Если выбрали точное значение 
                elif criterion['check_type'] == 'exact_value':
                    if criterion['measure_of_calculation'] == 'GB':
                        value = float(param_value.replace(' GB', ''))
                    else:
                        value = float(param_value)

                    print(f"Неправильное значение {pc['param']} = {value}")

                    if (criterion['exact_value'] is not None and value != criterion['exact_value']):
                        issues.append({'param': criterion['param'],
                                       'expected': criterion,
                                       'actual': param_value})

                #Если выбрали точное значение строки
                elif criterion['check_type'] == 'string_value':
                    value = str(param_value)
                    print(f"Неправильное значение {pc['param']} = {value}")


                    # if (criterion['string_value'] is not None and value != criterion['string_value']):
                    if (criterion['string_value'] is not None and value.find(str(criterion['string_value']))) == -1:

                        issues.append({'param': criterion['param'],
                                       'expected': criterion,
                                       'actual': param_value})

                #Если выбрали кол-во дней до сегодняшнего  
                elif criterion['check_type'] == 'day_count':
                    value = datetime.now().date() - datetime.strptime(param_value.split(' ')[0], "%d.%m.%Y").date()
                    value = value.days
                    print(f"Неправильное значение {pc['param']} = {param_value}")
                    if (criterion['day_count']) is not None and value >= criterion['day_count']:
                        issues.append({'param': criterion['param'],
                                       'expected': criterion,
                                       'actual': param_value})
                        
                
                
        if issues:
            problematic_pcs.append({
                'host': pc['host'],
                'issues': issues,
                'value': pc['value']

            })

    return problematic_pcs