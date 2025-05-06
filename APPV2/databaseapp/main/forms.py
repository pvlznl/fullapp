from django import forms

class FilterForm(forms.Form):
    id = forms.CharField(required=False, label="id", widget=forms.TextInput(attrs={'placeholder': 'Введите id'}))
    hosts = forms.CharField(required=False, label="Hosts", widget=forms.TextInput(attrs={'placeholder': 'Введите host'}))
    params = forms.CharField(required=False, label="Parameters", widget=forms.TextInput(attrs={'placeholder': 'Введите param'}))
    values = forms.CharField(required=False, label="Values", widget=forms.TextInput(attrs={'placeholder': 'Введите value'}))
    start_date = forms.DateField(required=False, label="Start Date", widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, label="End Date", widget=forms.DateInput(attrs={'type': 'date'}))

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label="Выберете Excel файл")

class UpdatePCForm(forms.Form):
    def __init__(self, *args, **kwargs):
        data = kwargs.pop('data', {})  # Получаем переданные данные
        super(UpdatePCForm, self).__init__(*args, **kwargs)

        for key, value in data.items():
            self.fields[key] = forms.CharField(
                label=key,
                initial=value,
                required=False,
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )


class CriticalPointForm(forms.Form):
    
    param = forms.CharField(label="Имя параметра", max_length=100)
    check_type = forms.ChoiceField(label='Тип ограничения', choices=[('borders','Мин/Макс'),
                                                                     ('exact_value','Точное значение (Float)'),
                                                                     ('string_value', 'Точное значение (String)'),
                                                                     ('day_count', 'Дней до сегодняшнего')])
    min_value = forms.FloatField(label="Минимальное значение (Float)", required=False)
    max_value = forms.FloatField(label="Максимальное значение (Float)", required=False)
    exact_value = forms.FloatField(label="Точное значение (Float)", required=False, widget=forms.TextInput(attrs={'id': 'visible_exact_value'}))
    measure_of_calculation = forms.ChoiceField(label="Мера исчисления", choices=[('None', 'Просто число'),
                                                                                 ('GB', 'Gb')])
    day_count = forms.IntegerField(label="Кол-во дней до сегодняшнего", required=False)
    string_value = forms.CharField(label="Точное значение (String)", required=False, max_length=100)