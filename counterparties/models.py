from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator


class Counterparty(models.Model):
    """Контрагент (Отправитель/Получатель)"""
    
    TYPE_CHOICES = [
        ('legal', 'Юридическое лицо (ООО, АО)'),
        ('entrepreneur', 'Индивидуальный предприниматель (ИП)'),
        ('individual', 'Физическое лицо'),
        ('self_employed', 'Самозанятый'),
    ]
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='legal',
        verbose_name='Тип контрагента'
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='Наименование/ФИО'
    )
    full_name = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name='Полное наименование'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Телефон'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email'
    )
    address = models.TextField(
        verbose_name='Юридический адрес'
    )
    actual_address = models.TextField(
        blank=True,
        null=True,
        verbose_name='Фактический адрес'
    )
    
    inn = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        verbose_name='ИНН',
        validators=[
            RegexValidator(
                regex='^[0-9]{10,12}$',
                message='ИНН должен содержать 10 или 12 цифр'
            )
        ]
    )
    kpp = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        verbose_name='КПП',
        validators=[
            RegexValidator(
                regex='^[0-9]{9}$',
                message='КПП должен содержать 9 цифр'
            )
        ]
    )
    ogrn = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        verbose_name='ОГРН/ОГРНИП',
        validators=[
            RegexValidator(
                regex='^[0-9]{13,15}$',
                message='ОГРН должен содержать 13 или 15 цифр'
            )
        ]
    )
    
    passport_series = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        verbose_name='Серия паспорта'
    )
    passport_number = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        verbose_name='Номер паспорта'
    )
    passport_issued_by = models.TextField(
        blank=True,
        null=True,
        verbose_name='Кем выдан паспорт'
    )
    passport_issued_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Дата выдачи паспорта'
    )
    
    director_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='ФИО руководителя'
    )
    contact_person = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Контактное лицо'
    )
    bank_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Банк'
    )
    bank_account = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Расчетный счет'
    )
    bank_bik = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        verbose_name='БИК'
    )
    bank_correspondent_account = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Корреспондентский счет'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активный'
    )
    is_supplier = models.BooleanField(
        default=False,
        verbose_name='Поставщик'
    )
    is_customer = models.BooleanField(
        default=False,
        verbose_name='Покупатель'
    )
    is_carrier = models.BooleanField(
        default=False,
        verbose_name='Перевозчик'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Примечания'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['inn']),
            models.Index(fields=['type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        counterparty_type = dict(self.TYPE_CHOICES).get(self.type, self.type)
        return f"{self.name} ({counterparty_type})"
    
    def get_short_info(self):
        """Краткая информация для отображения в выпадающих списках"""
        info = self.name
        if self.inn:
            info += f", ИНН: {self.inn}"
        if self.type == 'legal' and self.kpp:
            info += f", КПП: {self.kpp}"
        return info
    
    def get_full_info(self):
        """Полная информация о контрагенте"""
        info = f"{self.name}\n"
        if self.full_name:
            info += f"Полное наименование: {self.full_name}\n"
        
        info += f"Тип: {dict(self.TYPE_CHOICES).get(self.type)}\n"
        info += f"Адрес: {self.address}\n"
        
        if self.actual_address:
            info += f"Фактический адрес: {self.actual_address}\n"
        
        if self.inn:
            info += f"ИНН: {self.inn}\n"
        
        if self.type == 'legal' and self.kpp:
            info += f"КПП: {self.kpp}\n"
        
        if self.ogrn:
            info += f"ОГРН: {self.ogrn}\n"
        
        if self.phone:
            info += f"Телефон: {self.phone}\n"
        
        if self.email:
            info += f"Email: {self.email}\n"
        
        if self.contact_person:
            info += f"Контактное лицо: {self.contact_person}\n"
        
        return info