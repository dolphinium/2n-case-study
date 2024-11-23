The error you're encountering:

```
TemplateSyntaxError at /auth/leave/balance/
add requires 2 arguments, 1 provided
```

is due to an incorrect usage of the `add` filter in your Django template. Specifically, the template line:

```html
<p><strong>Remaining Leave:</strong> {{ total_leave|add:"-{{ used_leave }}" }} days</p>
```

is syntactically incorrect because Django's template filters do not support nested template tags like `{{ used_leave }}` within filter arguments. The `add` filter expects a single argument, not a template variable within a string.

## **Solution Overview**

To resolve this issue, you should perform the calculation of **Remaining Leave** in your Django view rather than in the template. This approach adheres to the **separation of concerns** principle, ensuring that **business logic** resides in the **backend** while the **frontend** remains focused on presentation.

## **Step-by-Step Fix**

### **1. Update the `view_leave_balance` View**

Modify your `view_leave_balance` view to calculate the **Remaining Leave** and pass it to the template context.

```python
# backend/employees/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum  # Correctly imported
from django.conf import settings
from .models import LeaveRequest, Notification
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

def is_personnel(user):
    return user.is_authenticated and not user.is_authorized

@login_required(login_url='personnel_login')
@user_passes_test(is_personnel)
def view_leave_balance(request):
    user = request.user
    profile = user.profile
    total_leave = float(profile.annual_leave_balance)  # Convert Decimal to float for arithmetic
    # Calculate used leave
    used_leave = LeaveRequest.objects.filter(employee=user, status='A').aggregate(total=Sum('days')).get('total') or 0
    used_leave = float(used_leave)  # Ensure it's a float
    remaining_leave = total_leave - used_leave  # Calculate remaining leave
    
    context = {
        'total_leave': total_leave,
        'used_leave': used_leave,
        'remaining_leave': remaining_leave  # Pass remaining_leave to the template
    }
    return render(request, 'employees/view_leave_balance.html', context)
```

**Key Changes:**

1. **Import `Sum` Correctly:**
   - Ensure that `Sum` is imported from `django.db.models` to perform aggregation.
   
2. **Convert `Decimal` to `float`:**
   - Since `annual_leave_balance` and `used_leave` might be `Decimal` types (from `DecimalField`), converting them to `float` ensures compatibility with arithmetic operations in Python.
   
3. **Calculate `remaining_leave`:**
   - Perform the subtraction (`total_leave - used_leave`) within the view and pass the result to the template.

### **2. Modify the Template to Use `remaining_leave`**

Update your `view_leave_balance.html` template to utilize the newly calculated `remaining_leave` variable.

```html
<!-- backend/employees/templates/employees/view_leave_balance.html -->

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Leave Balance</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h2>Your Leave Balance</h2>
        {% if messages %}
            <div class="alert alert-info">
                {% for message in messages %}
                    <p>{{ message }}</p>
                {% endfor %}
            </div>
        {% endif %}
        <p><strong>Total Leave:</strong> {{ total_leave }} days</p>
        <p><strong>Used Leave:</strong> {{ used_leave }} days</p>
        <p><strong>Remaining Leave:</strong> {{ remaining_leave }} days</p>
        <a href="{% url 'request_leave' %}" class="btn btn-primary">Request Leave</a>
        <a href="{% url 'personnel_dashboard' %}" class="btn btn-secondary">Back to Dashboard</a>
    </div>
</body>
</html>
```

**Key Changes:**

- **Remove Incorrect `add` Filter:**
  - Replace `{{ total_leave|add:"-{{ used_leave }}" }}` with the pre-calculated `{{ remaining_leave }}`.

### **3. Ensure Proper Handling of Data Types**

Since `annual_leave_balance` and `days` in `LeaveRequest` are `DecimalField`, ensuring they are converted to `float` in the view guarantees that arithmetic operations behave as expected. This avoids potential issues with template filters expecting numeric types.

### **4. Verify and Apply Migrations**

If you made any changes to your models (e.g., adding the `days` field to the `LeaveRequest` model), ensure you create and apply migrations.

```bash
python manage.py makemigrations employees
python manage.py migrate
```

**Note:** Since you've already performed migrations earlier, ensure that these new changes are captured.

### **5. Test the Changes**

1. **Run the Development Server:**

   ```bash
   python manage.py runserver
   ```

2. **Access the Leave Balance Page:**
   - Navigate to `http://127.0.0.1:8000/auth/leave/balance/`.
   - Ensure that **Total Leave**, **Used Leave**, and **Remaining Leave** are displayed correctly without any errors.

3. **Verify Calculations:**
   - Create some **Approved Leave** (`status='A'`) entries for a user.
   - Confirm that the `used_leave` reflects the correct sum of `days`.
   - Ensure that `remaining_leave` equals `total_leave - used_leave`.

## **Alternative Approach: Using Custom Template Tags**

If you prefer to handle calculations within the template, you can create **custom template filters**. However, this introduces additional complexity and is generally less maintainable than computing values in the view.

### **1. Create a Custom Template Filter**

1. **Create a `templatetags` Directory:**

   ```bash
   mkdir backend/employees/templatetags
   touch backend/employees/templatetags/__init__.py
   touch backend/employees/templatetags/custom_tags.py
   ```

2. **Define the `subtract` Filter:**

   ```python
   # backend/employees/templatetags/custom_tags.py

   from django import template

   register = template.Library()

   @register.filter
   def subtract(value, arg):
       try:
           return float(value) - float(arg)
       except (ValueError, TypeError):
           return ''
   ```

### **2. Use the Custom Filter in Your Template**

1. **Load the Custom Tags:**

   At the top of your `view_leave_balance.html` template, load the `custom_tags`.

   ```html
   {% load custom_tags %}
   ```

2. **Use the `subtract` Filter:**

   Replace the faulty line with:

   ```html
   <p><strong>Remaining Leave:</strong> {{ total_leave|subtract:used_leave }} days</p>
   ```

### **3. Benefits and Drawbacks**

- **Benefits:**
  - Keeps templates free from complex logic.
  - Reusable across different templates.

- **Drawbacks:**
  - Adds complexity to the template.
  - Maintaining custom filters can be cumbersome.

## **Recommendation**

While it's possible to perform arithmetic operations within templates using custom filters, it's **best practice** to handle such logic in the **views**. This approach ensures that your **templates remain simple** and focused solely on **presentation**, enhancing **maintainability** and **clarity**.

## **Final Corrected Code Snippets**

### **Updated `views.py`:**

```python
# backend/employees/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum  # Correctly imported
from django.conf import settings
from .models import LeaveRequest, Notification
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

def is_personnel(user):
    return user.is_authenticated and not user.is_authorized

@login_required(login_url='personnel_login')
@user_passes_test(is_personnel)
def view_leave_balance(request):
    user = request.user
    profile = user.profile
    total_leave = float(profile.annual_leave_balance)  # Convert Decimal to float for arithmetic
    # Calculate used leave
    used_leave = LeaveRequest.objects.filter(employee=user, status='A').aggregate(total=Sum('days')).get('total') or 0
    used_leave = float(used_leave)  # Ensure it's a float
    remaining_leave = total_leave - used_leave  # Calculate remaining leave
    
    context = {
        'total_leave': total_leave,
        'used_leave': used_leave,
        'remaining_leave': remaining_leave  # Pass remaining_leave to the template
    }
    return render(request, 'employees/view_leave_balance.html', context)
```

### **Updated `view_leave_balance.html`:**

```html
<!-- backend/employees/templates/employees/view_leave_balance.html -->

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Leave Balance</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h2>Your Leave Balance</h2>
        {% if messages %}
            <div class="alert alert-info">
                {% for message in messages %}
                    <p>{{ message }}</p>
                {% endfor %}
            </div>
        {% endif %}
        <p><strong>Total Leave:</strong> {{ total_leave }} days</p>
        <p><strong>Used Leave:</strong> {{ used_leave }} days</p>
        <p><strong>Remaining Leave:</strong> {{ remaining_leave }} days</p>
        <a href="{% url 'request_leave' %}" class="btn btn-primary">Request Leave</a>
        <a href="{% url 'personnel_dashboard' %}" class="btn btn-secondary">Back to Dashboard</a>
    </div>
</body>
</html>
```

## **Conclusion**

By moving the **calculation of Remaining Leave** to the **view** and passing the result to the template, you've resolved the `TemplateSyntaxError` and adhered to Django's best practices. This approach ensures that your templates remain clean and focused on presentation, while your views handle the necessary business logic.

If you encounter any further issues or have additional questions, feel free to ask!