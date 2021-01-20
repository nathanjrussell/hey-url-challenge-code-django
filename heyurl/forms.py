from .models import Url
from django.forms import ModelForm
from django.core.validators import URLValidator

class UrlForm(ModelForm):
    class Meta:
        model=Url
        fields=['original_url']

    def clean_original_url(self):
        supp_protocols = ["https://","http://"]
        original_url = self.cleaned_data.get('original_url')
        protocol_bool = False
        for p in supp_protocols:
            pl = len(p)
            if original_url[0:pl] == p:
                protocol_bool = True
                break
        if not protocol_bool:
            original_url = "https://" + original_url
        return original_url

    def is_valid(self):
        valid = super(UrlForm,self).is_valid()
        original_url = self.cleaned_data.get('original_url')
        val = URLValidator()
        try:
            val(original_url)
            return True
        except:
            self._errors['INVALID URL'] = " - The address provided is not a valid URL."
