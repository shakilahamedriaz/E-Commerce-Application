import json
from urllib import response
import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


# this function generates the SSLCommerz payment URL
def generate_sslcommerz_payment(order, request):
    """Generate SSLCommerz payment URL"""
    post_data = {
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
        'total_amount': float(order.get_total_cost()),
        'currency': 'BDT',
        'tran_id': str(order.id),
        'success_url': request.build_absolute_uri(f'/payment/success/{order.id}/'),
        'fail_url': request.build_absolute_uri(f'/payment/fail/{order.id}/'),
        'cancel_url': request.build_absolute_uri(f'/payment/cancel/{order.id}/'),
        'cus_name': f"{order.first_name} {order.last_name}",
        'cus_email': order.email,
        'cus_add1': order.address,
        'cus_city': order.city,
        'cus_postcode': order.postal_code,
        'cus_country': 'Bangladesh',
        'shipping_method': 'NO',
        'product_name': 'Products from our store',
        'product_category': 'General',
        'product_profile': 'General',
    }

    response = requests.post(settings.SSLCOMMERZ_PAYMENT_URL, data=post_data)
    return json.loads(response.text)



# Send order confirmation email with HTML content
def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    try:
        subject = f"Order Confirmation - Order #{order.id}"
        message = render_to_string('shop/order_confirmation_email.html', {'order': order})
        to = order.email
        from_email = settings.DEFAULT_FROM_EMAIL
        
        send_email = EmailMultiAlternatives(subject, '', from_email, [to])
        send_email.attach_alternative(message, "text/html")
        send_email.send()
        print(f"✅ Order confirmation email sent to {to} for order #{order.id}")
        print(f"📧 Email content preview: Order #{order.id}, Total: ${order.get_total_cost()}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email for order #{order.id}: {str(e)}")
        print(f"📧 Email would have been sent to: {order.email}")
        print(f"💡 Check your email settings and Gmail App Password if using SMTP backend")
        return False