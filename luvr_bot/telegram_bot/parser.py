import os.path
import tempfile
import numpy as np
import pandas as pd
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from .models import Training


@csrf_exempt
def parse(request):
    path = os.path.join(tempfile.mkdtemp(), 'import.xlsx')
    with open(path, 'wb+') as f:
        for chunk in request.FILES['file'].chunks():
            f.write(chunk)
    df = pd.read_excel(path, dtype=str)
    df = df.replace(np.nan, None)

    for line in df.to_dict('records'):
        employee = Training.objects.filter(iin=line['ИИН'])
        if employee:
            employee.update(full_name=line['Имя'], iin=line['ИИН'])
        else:
            Training.objects.create(full_name=line['Имя'], iin=line['ИИН'])
    return HttpResponse('OK')
