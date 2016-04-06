from django import forms


class SearchForm(forms.Form):
    h = forms.CharField(label='magnet link or torrent hash', max_length=100)