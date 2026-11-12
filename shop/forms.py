from django import forms


class CheckoutForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        label="Имя",
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        max_length=100,
        label="Фамилия",
        widget=forms.TextInput(attrs={"autocomplete": "family-name"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    phone = forms.RegexField(
        regex=r"^[0-9+\-()\s]{10,20}$",
        label="Телефон",
        error_messages={"invalid": "Укажите телефон в формате +7 900 000-00-00."},
        widget=forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "+7 900 000-00-00"}),
    )
    address = forms.CharField(
        max_length=500,
        label="Адрес доставки",
        widget=forms.Textarea(attrs={"rows": 3, "autocomplete": "street-address"}),
    )
