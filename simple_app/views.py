import stripe
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.parsers import JSONParser

from config import load_config
from .models import Item
from .models import OrderItem, Order
from .serializers import ItemSerializer

config = load_config(path='.env')


@csrf_exempt
def create_item(request):
    '''
    для обработки POST запроса на создание item
    '''
    if request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = ItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


def item_detail(request, id):
    item = get_object_or_404(Item, pk=id)
    config = load_config(path='.env', currency=item.currency)  # Загрузка конфигурации с учетом валюты
    context = {
        'item': item,
        'stripe_public_key': config.stripe.publishable_key  # Используйте ключ из StripeConfig
    }
    return render(request, 'item_detail.html', context)


def payment_success(request):
    """
    Функция для обработки успешного платежа
    """
    return render(request, 'payment_success.html')


def payment_cancel(request):
    """
    Функция для обработки отмененного платежа
    """
    return render(request, 'payment_cancel.html')


@require_POST
def add_to_order(request, item_id):
    """
    Добавляет товар в заказ

    """
    # Получаем или создаем новый заказ (можно связать с текущим пользователем)
    order, created = Order.objects.get_or_create(status='pending')
    request.session['cart_id'] = order.id  # Сохраняем ID заказа в сессии
    # Получаем товар
    item = get_object_or_404(Item, pk=item_id)

    # Проверяем, есть ли уже такой товар в заказе
    order_item, created = OrderItem.objects.get_or_create(order=order, item=item)

    if not created:
        # Если товар уже в заказе, увеличиваем количество
        order_item.quantity += int(request.POST.get('quantity', 1))
        order_item.save()
    else:
        # Если товара еще нет в заказе, устанавливаем начальное количество
        order_item.quantity = int(request.POST.get('quantity', 1))
        order_item.save()

    # Обновляем общую стоимость заказа
    order.calculate_total_price()

    return JsonResponse({'message': 'Товар добавлен в корзину!'}, status=200)


def cart_view(request):
    """
    Функция просмотра корзины заказов
    """
    order, created = Order.objects.get_or_create(status='pending')

    # Определение валюты на основе товаров в корзине (например, валюта первого товара)
    if order.order_items.exists():
        currency = order.order_items.first().item.currency
    else:
        currency = 'USD'  # Значение по умолчанию, если корзина пуста

    # Загрузка конфигурации Stripe в зависимости от валюты
    config = load_config(path='.env', currency=currency)

    context = {
        'order': order,
        'stripe_public_key': config.stripe.publishable_key  # Используйте ключ из StripeConfig
    }
    return render(request, 'cart.html', context)


def checkout_order(request, order_id):
    """
    функция используется для создания сессии оплаты с помощью Stripe Checkout
    на основе товаров в заказе, включая расчет общей стоимости с учетом скидок и налогов, и указывает URL
    для успешного и отмененного платежей.
    """
    order = get_object_or_404(Order, pk=order_id)
    # Убедитесь, что общая стоимость заказа рассчитана
    order.calculate_total_price()

    try:
        # Создание line_items на основе товаров в заказе
        line_items = [{
            'price_data': {
                'currency': order.currency,
                'product_data': {
                    'name': item.item.name,
                },
                'unit_amount': int(item.get_cost() * 100),
            },
            'quantity': item.quantity,
        } for item in order.order_items.all()]

        # Расчет общей суммы скидки и налога
        discount_total = sum(discount.amount for discount in order.discount_set.all())
        tax_total = sum(((item.get_cost() - discount_total / order.order_items.count()) * tax.rate / 100) for item in
                        order.order_items.all() for tax in order.tax_set.all())

        # Добавление информации о скидках в line_items
        if discount_total > 0:
            line_items.append({
                'price_data': {
                    'currency': order.currency,
                    'product_data': {
                        'name': 'Discount',
                    },
                    'unit_amount': -int(discount_total * 100),
                },
                'quantity': 1,
            })

        # Добавление информации о налогах в line_items
        if tax_total > 0:
            line_items.append({
                'price_data': {
                    'currency': order.currency,
                    'product_data': {
                        'name': 'Tax',
                    },
                    'unit_amount': int(tax_total * 100),
                },
                'quantity': 1,
            })

        # Создание сессии оплаты для Stripe Checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success')),
            cancel_url=request.build_absolute_uri(reverse('payment_cancel')),
        )
        return JsonResponse({'sessionId': checkout_session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def create_checkout_session(request, item_id):
    """
    Используется для создания PaymentIntent с помощью Stripe для определенного товара,
    возвращая клиентский секрет (clientSecret) для последующего оформления платежа.
    """
    item = get_object_or_404(Item, pk=item_id)
    try:
        # Создаем PaymentIntent вместо Session
        payment_intent = stripe.PaymentIntent.create(
            amount=int(item.price * 100),  # Умножаем на 100, так как Stripe использует центы
            currency=item.currency,
            metadata={'item_id': item_id}
        )
        return JsonResponse({'clientSecret': payment_intent['client_secret']})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def create_checkout_session_for_order(request, order_id):
    """
    используется для создания PaymentIntent с помощью Stripe для определенного заказа,
    возвращая клиентский секрет (client_secret) для последующего оформления платежа.
    Функция также учитывает общую стоимость заказа, скидки и налоги, а также предоставляет
    опцию для сохранения данных карты для будущих платежей (setup_future_usage='off_session').
    """
    order = get_object_or_404(Order, pk=order_id)

    if not order.order_items.exists():
        return JsonResponse({'error': 'Заказ пуст'}, status=400)

    # Предположим, что валюта заказа определяется по первому товару в заказе.
    currency = order.order_items.first().item.currency
    config = load_config(path='.env', currency=currency)
    stripe.api_key = config.stripe.secret_key

    # Рассчитываем общую стоимость, скидки и налоги.
    order.calculate_total_price()
    total_amount = int(order.total_price * 100)  # Общая стоимость в центах.

    try:
        # Создаем PaymentIntent вместо Checkout Session
        payment_intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency=currency,
            metadata={'order_id': order_id},
            setup_future_usage='off_session'  # Опция для сохранения данных карты для будущих платежей

        )
        return JsonResponse({'client_secret': payment_intent.client_secret})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def create_payment_intent(request, item_id):
    """
     используется для создания PaymentIntent с помощью Stripe для определенного товара,
     возвращая клиентский секрет (client_secret) для последующего оформления платежа.
     Функция также учитывает сумму товара, валюту и предоставляет опцию для сохранения
     данных карты для будущих платежей (setup_future_usage='off_session').
    """
    item = get_object_or_404(Item, pk=item_id)
    stripe.api_key = config.stripe.secret_key  # Замените на ваш реальный ключ

    try:
        # Создание PaymentIntent с сохранением способа оплаты для будущего использования
        payment_intent = stripe.PaymentIntent.create(
            amount=int(item.price * 100),  # Stripe работает с суммами в центах
            currency=item.currency,
            metadata={'item_id': item.id},
            setup_future_usage='off_session'  # Опция для сохранения данных карты для будущих платежей
        )
        return JsonResponse({'client_secret': payment_intent.client_secret})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=403)


def clear_cart(request):
    """
    Очистка корзины заказов
    """
    order_id = request.session.get('cart_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id, status='pending')
            order.order_items.all().delete()
            order.total_price = 0
            order.save()
            del request.session['cart_id']  # Удаляем 'cart_id' из сессии
        except Order.DoesNotExist:
            print("Заказ не найден")
    else:
        print("ID заказа не найден в сессии")
    return redirect('cart_view')

# def create_stripe_session(request, id):
#     # Получение товара по ID
#     item = get_object_or_404(Item, pk=id)
#
#     # Создание Stripe Checkout Session для товара
#     session = stripe.checkout.Session.create(
#         payment_method_types=['card'],
#         line_items=[{
#             'price_data': {
#                 'currency': item.currency,
#                 'product_data': {
#                     'name': item.name,
#                 },
#                 'unit_amount': int(item.price * 100),
#             },
#             'quantity': 1,
#         }],
#         mode='payment',
#         success_url=request.build_absolute_uri('/payment/success/'),
#         cancel_url=request.build_absolute_uri('/payment/cancel/'),
#     )
#     # Возвращаем session_id в JSON-ответе
#     return JsonResponse({'sessionId': session.id})
