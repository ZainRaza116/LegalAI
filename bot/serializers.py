from rest_framework import serializers
from .models import SuccessfulPayment,StripeCustomer


class SuccessfulPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuccessfulPayment
        fields = '__all__'


class StripeCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StripeCustomer
        fields = '__all__'
