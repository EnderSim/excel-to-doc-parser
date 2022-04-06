import csv
import os.path
import shutil
import time
import urllib
from difflib import SequenceMatcher
from os import listdir
from os.path import isfile, join
from wsgiref.util import FileWrapper

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from docxtpl import DocxTemplate

from excel_to_doc_parser.models import CustomUser, Role, Document, Module
from excel_to_doc_parser.py.parser import get_info_from_excel
from excel_to_doc_parser.py.parser_plane import get_info_from_education_plane
from parser_server.settings import BASE_DIR


def check_number(num):
    if num % 10 == 1 and num != 11:
        return '1'
    elif 1 < num % 10 < 5 and (num > 19 or num < 5):
        return '2'
    else:
        return '3'


@login_required(login_url='/login/')
def index(request):
    context = {}
    if request.user.is_authenticated:
        context["custom_user"] = CustomUser.objects.get(user=request.user)
        context["role"] = Role.objects.get(pk=context["custom_user"].role_id)
        context["modules"] = Document.objects.all()
        context["sections"] = Module.objects.all()
        if request.method == "POST":
            if request.POST.get("new_section"):
                header = request.POST.get('new_header')
                description = request.POST.get('new_description')
                classwork_hours = request.POST.get('new_classwork')
                homework_hours = request.POST.get('new_homework')
                module = request.POST.get('new_module')
                new_module = Module(module=module, header=header, description=description,
                                    classwork_hours=classwork_hours, homework_hours=homework_hours)
                new_module.save()
            else:
                pk = request.POST.get('pk')
                header = request.POST.get('header')
                description = request.POST.get('description')
                classwork_hours = request.POST.get('classwork')
                homework_hours = request.POST.get('homework')
                module = Module.objects.filter(pk=pk)
                module.update(header=header, description=description, classwork_hours=classwork_hours, homework_hours=homework_hours)
                with open(join(str(BASE_DIR), 'excel_to_doc_parser/media/temporary_text/{}.csv'.format(str(request.user) + '_' + header)), 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(['header', 'description', 'classwork_hours', 'homework_hours'])
                    writer.writerow([header, description, classwork_hours, homework_hours])
        # path = join(str(BASE_DIR), "excel_to_doc_parser/media/excel")
        # files_dict = {}
        # folder = join(str(BASE_DIR), "excel_to_doc_parser/media/generated_files")
        # for filename in os.listdir(folder):
        #     file_path = os.path.join(folder, filename)
        #     if filename == ".gitkeep":
        #         continue
        #     try:
        #         if os.path.isfile(file_path) or os.path.islink(file_path):
        #             os.unlink(file_path)
        #         elif os.path.isdir(file_path):
        #             shutil.rmtree(file_path)
        #     except Exception as e:
        #         print('An error appear ' + str(e))
        # for file in listdir(join(path, "matrices")):
        #     if isfile(join(path, "matrices", file)):
        #         files_dict[" ".join(file.split(',')[1][:-5].split("_")[2:])] = file
        # if request.method == "GET":
        #     context['step'] = 1
        #     profiles = []
        #     for key in files_dict:
        #         profiles.append(key)
        #     context['profiles'] = profiles
        # if request.method == "POST":
        #     context['step'] = 2
        #     data = get_info_from_excel(
        #         path + "/matrices/" + files_dict[request.POST.get("profile")])
        #     context['data'] = data
        #     context['profile'] = request.POST.get('profile')
        #     if request.POST.get('discipline'):
        #         context['step'] = 3
        #         discipline = request.POST.get('discipline')
        #         try:
        #             context_plane = get_info_from_education_plane(path + "/planes/03-5190 - ВЕБ 2020 (1).xlsx")[
        #                 discipline]
        #         except KeyError:
        #             for error_key in get_info_from_education_plane(path + "/planes/planes/03-5190 - ВЕБ 2020 (1).xlsx"):
        #                 if SequenceMatcher(None, discipline, error_key).ratio() >= 0.75:
        #                     context_plane = \
        #                         get_info_from_education_plane(path + "/planes/planes/03-5190 - ВЕБ 2020 (1).xlsx")[
        #                             error_key]
        #                     break
        #         context_plane['intensity_ZET_check'] = check_number(context_plane['intensity_ZET'])
        #         context_plane['intensity_hours_check'] = check_number(context_plane['intensity_hours'])
        #         context_plane['total_homework_hours_check'] = check_number(context_plane['total_homework_hours'])
        #         for i, _ in enumerate(context_plane['courses']):
        #             context_plane['courses'][i]['ZET_check'] = check_number(context_plane['courses'][i]['ZET'])
        #             context_plane['courses'][i]['hours_check'] = check_number(context_plane['courses'][i]['hours'])
        #             context_plane['courses'][i]['homework_time_check'] = check_number(
        #                 context_plane['courses'][i]['homework_time'])
        #         doc = DocxTemplate(
        #             join(str(BASE_DIR), "excel_to_doc_parser/templates/template.docx"))
        #         doc.render(dict(data[discipline], **context_plane))
        #         for i in range(len(doc.tables)):
        #             table = doc.tables[i]._tbl
        #             for row in doc.tables[i].rows:
        #                 if len(row.cells[0].text.strip()) == 0 and len(set(row.cells)) == 1:
        #                     table.remove(row._tr)
        #         doc.save(join(str(BASE_DIR), "excel_to_doc_parser/media/generated_files/{}.docx".format(
        #             data[discipline]['program_name'])))
        #         context['path'] = "excel_to_doc_parser/media/generated_files/{}.docx".format(
        #             data[discipline]['program_name'])
        #         context['name'] = data[discipline]['program_name'] + '.docx'
    else:
        return HttpResponseForbidden()
    return render(request, "main.html", context)


def download(request):
    file = join(str(BASE_DIR), request.GET.get('file'))
    print(file)
    name = urllib.parse.quote(request.GET.get('name'), encoding='utf-8')
    filename = open(file, 'rb')
    content = FileWrapper(filename)
    response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml'
                                                  '.document')
    response['Content-Length'] = os.path.getsize(file)
    response['Content-Disposition'] = 'attachment; filename*=utf-8\'\'{}'.format(
        name)
    print(response['Content-Disposition'])
    return response


def login_view(request):
    if request.user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        username = request.POST.get('login')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            print("Error")
    return render(request, "authorization.html")


def logout_view(request):
    logout(request)
    if not request.user.is_authenticated:
        return redirect("/")
    return render(request, "authorization.html")
