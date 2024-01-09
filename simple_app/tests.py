from unittest import mock
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from .models import Item, Order


class ItemDetailViewTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Test Item', price=10.99, currency='USD')

    def test_item_detail_view(self):
        """
        проверяет, что представление item_detail для деталей товара возвращает успешный HTTP-ответ,
        использует правильный шаблон, возвращает объект HttpResponse и что товар, полученный из контекста,
        совпадает с созданным фейковым товаром.
        """
        response = self.client.get(reverse('item_detail', args=[self.item.id]))

        self.assertEqual(response.status_code, 200)  # Проверяем, что статус код ответа равен 200 (успешно)
        self.assertTemplateUsed(response, 'item_detail.html')  # Проверяем, что был использован правильный шаблон
        self.assertIsInstance(response, HttpResponse)  # Проверяем, что возвращается объект HttpResponse
        self.assertEqual(response.context['item'],
                         self.item)  # Проверяем, что товар из контекста совпадает с созданным фейковым товаром


class AddToOrderViewTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Test Item', price=10.99, currency='USD')

    def test_add_to_order_view(self):
        '''
        Проверяет, что add_to_order view корректно добавляет товар в заказ с правильным количеством
        '''
        response = self.client.post(reverse('add_to_order', args=[self.item.id]), {'quantity': 2})
        self.assertEqual(response.status_code, 200)  # Ожидаем, что статус код будет 200
        order = Order.objects.get(status='pending')  # Получаем заказ со статусом 'pending'
        self.assertEqual(order.order_items.count(), 1)  # Проверяем, что в заказе только один товар
        self.assertEqual(order.order_items.first().item, self.item)  # Проверяем, что товар соответствует созданному
        self.assertEqual(order.order_items.first().quantity, 2)  # Проверяем, что количество товара равно 2


class CreatePaymentIntentViewTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Test Item', price=10.99, currency='USD')

    def test_create_payment_intent_view(self):
        '''
        Проверяет, что create_payment_intent возвращает 'client_secret' при успешном запросе
        '''
        response = self.client.post(reverse('create_payment_intent', args=[self.item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('client_secret', response.json())
        self.assertIsNotNone(response.json()['client_secret'])


class CreateCheckoutSessionForOrderViewTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Test Item', price=10.99, currency='USD')
        self.order = Order.objects.create(status='pending')
        self.order.order_items.create(item=self.item, quantity=1)

    def test_create_checkout_session_for_order_view(self):
        """
        Проверяет, что create_checkout_session_for_order view возвращает 'client_secret' при успешном запросе
        """
        response = self.client.post(reverse('create_checkout_session_for_order', args=[self.order.id]))
        self.assertEqual(response.status_code, 200)  # Ожидаем, что статус код будет 200
        self.assertIn('client_secret', response.json())  # Проверяем, что ответ содержит поле 'client_secret'
        self.assertIsNotNone(response.json()['client_secret'])  # Проверяем, что 'client_secret' не равен None


class CreateCheckoutSessionViewTest(TestCase):
    def setUp(self):
        # Создаем тестовый объект товара
        self.item = Item.objects.create(name='Test Item', price=10.99, currency='USD')

    def test_create_checkout_session_view(self):
        """
        Проверяет, что create_checkout_session view возвращает 'clientSecret' при успешном запросе
        """
        response = self.client.post(reverse('create_checkout_session', args=[self.item.id]))
        self.assertEqual(response.status_code, 200)  # Ожидаем, что статус код будет 200
        self.assertIn('clientSecret', response.json())  # Проверяем, что ответ содержит поле 'clientSecret'
        self.assertIsNotNone(response.json()['clientSecret'])  # Проверяем, что 'clientSecret' не равен None


class CartViewTest(TestCase):
    def test_cart_view(self):
        """
        проверяет, что представление cart_view возвращает успешный HTTP-ответ,
        в контексте которого есть объект заказа ('order') и ключ Stripe public key ('stripe_public_key').
        """
        order = Order.objects.create(status='pending')
        session = self.client.session
        session['cart_id'] = order.id
        session.save()

        response = self.client.get(reverse('cart_view'))  # Создаем фейковый GET-запрос для просмотра корзины
        self.assertEqual(response.status_code, 200)  # Проверяем, что статус код ответа равен 200 (успешно)
        self.assertTrue('order' in response.context)  # Проверяем, что в контексте есть объект заказа ('order')
        self.assertTrue(
            'stripe_public_key' in response.context)  # Проверяем, что в контексте есть ключ Stripe public key ('stripe_public_key')


class PaymentSuccessViewTest(TestCase):
    def test_payment_success_view(self):
        """
        проверяет, что представление payment_success возвращает успешный HTTP-ответ с правильным шаблоном.
        """
        response = self.client.get(reverse('payment_success'))

        self.assertEqual(response.status_code, 200)  # Проверяем, что статус код ответа равен 200 (успешно)
        self.assertTemplateUsed(response, 'payment_success.html')  # Проверяем, что был использован правильный шаблон
        self.assertIsInstance(response, HttpResponse)  # Проверяем, что возвращается объект HttpResponse


class PaymentCancelViewTest(TestCase):
    def test_payment_cancel_view(self):
        '''
        проверяет, что представление payment_cancel возвращает успешный HTTP-ответ с правильным шаблоном.
        '''
        response = self.client.get(reverse('payment_cancel'))

        self.assertEqual(response.status_code, 200)  # Проверяем, что статус код ответа равен 200 (успешно)
        self.assertTemplateUsed(response, 'payment_cancel.html')  # Проверяем, что был использован правильный шаблон
        self.assertIsInstance(response, HttpResponse)  # Проверяем, что возвращается объект HttpResponse


class CheckoutOrderViewTest(TestCase):
    @patch('simple_app.views.stripe.checkout.Session.create')
    def test_checkout_order_view(self, mock_checkout_create):
        """
         позволяет убедиться, что представление checkout_order правильно взаимодействует с Stripe API и
         возвращает ожидаемые данные в случае успешного запроса, не выполняя реальных запросов к Stripe
         во время выполнения теста.
        """
        mock_checkout_create.return_value.id = 'fake_session_id'

        order = Order.objects.create(status='pending')

        response = self.client.post(reverse('checkout_order', args=[order.id]))

        mock_checkout_create.assert_called_once_with(
            payment_method_types=['card'],
            line_items=mock.ANY,
            mode='payment',
            success_url=mock.ANY,
            cancel_url=mock.ANY,
        )
        self.assertEqual(response.status_code, 200)
