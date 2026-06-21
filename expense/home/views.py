from django.shortcuts import render,redirect
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from datetime import date
from django.db.models import Sum
import matplotlib.pyplot as plt
import io
import urllib,base64
import csv
from django.http import HttpResponse

@login_required
def home(request):
    profile = Profile.objects.filter(user = request.user).first()
    expenses = Expense.objects.filter(user = request.user,is_deleted=False)

    today = date.today()

    monthly_income = Expense.objects.filter(
        user=request.user,
        expense_type="Positive",
        date__month=today.month,
        date__year=today.year
    ).aggregate(total=Sum('amount'))['total'] or 0

    monthly_expense = Expense.objects.filter(
        user=request.user,
        expense_type="Negative",
        date__month=today.month,
        date__year=today.year
    ).aggregate(total=Sum('amount'))['total'] or 0

    monthly_savings = monthly_income-monthly_expense

    category_data = Expense.objects.filter(
        user=request.user,
        expense_type="Negative").values('category').annotate(total=Sum('amount'))
    
    labels = []
    sizes = []

    for item in category_data:
        labels.append(item['category'])
        sizes.append(item['total'])
    chart = None

    if sizes:
        plt.figure(figsize=(5,5))
        plt.pie(sizes,labels=labels,autopct='%1.1f%%')

        buffer = io.BytesIO()
        plt.savefig(buffer,format='png')
        buffer.seek(0)

        string = base64.b64encode(buffer.read())
        chart = urllib.parse.quote(string)

        buffer.close()
        plt.close()

    selected_category = request.GET.get('category')

    if selected_category:
        expenses = expenses.filter(category=selected_category)

    search_query = request.GET.get('search')
    print("SEARCH =",search_query)
    if search_query:
        expenses = expenses.filter(name__icontains=search_query)
    
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        expenses = expenses.filter(date__gte=from_date)
    if to_date:
        expenses = expenses.filter(date__lte=to_date)

    if request.method == 'POST':
        print(request.POST)
        text = request.POST.get('text')
        amount = request.POST.get('amount')
        expense_type = request.POST.get('expense_type')
        category = request.POST.get('category')

        expense = Expense(
            name=text , 
            amount=amount , 
            expense_type=expense_type , 
            category=category,
            user=request.user,
        )
        expense.save()

        if expense_type == 'Positive':
            profile.income += float(amount)
            profile.balance += float(amount)
        else:
            profile.expenses += float(amount)
            profile.balance -= float(amount)

        profile.save()
        return redirect('/')
        
    context = { 
        'profile' : profile,
        'expenses' : expenses, 
        'monthly_income' : monthly_income,
        'monthly_expense':monthly_expense,
        'monthly_savings':monthly_savings,
        'category_data':category_data,
        'chart':chart
    }
    print(category_data)
    return render(request, 'home.html', context)


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            return redirect('/register')
        
        user = User.objects.create_user(
            username=username,
            password=password
        )

        Profile.objects.create(
            user=user,
            income=0,
            expenses=0,
            balance=0
        )
        login(request, user)

        return redirect('/')
    
    return render(request, 'registration/register.html')

def delete_expense(request,id):

    expense = Expense.objects.get(id=id, user=request.user)
    profile = Profile.objects.get(user=request.user)

    if expense.expense_type == "Positive":
        profile.income -= expense.amount
        profile.balance -= expense.amount
    else:
        profile.expenses -= expense.amount
        profile.balance += expense.amount

    profile.save()
    expense.is_deleted = True
    expense.save()

    return redirect('/')

@login_required
def recycle_bin(request):
    
    expenses = Expense.objects.filter(user=request.user,is_deleted=True)

    return render(request,"recycle_bin.html",{"expenses":expenses})

def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)

    writer.writerow([
        'Name',
        'Amount',
        'Type',
        'Category'
    ])

    expenses = Expense.objects.filter(user=request.user)

    for expense in expenses:
        writer.writerow([
            expense.name,
            expense.amount,
            expense.expense_type,
            expense.category
        ])
    return response

@login_required
def edit_expense(request, id):

    expense = Expense.objects.get(id=id, user=request.user)
    profile = Profile.objects.get(user=request.user)

    if request.method == "POST":

        expense.name = request.POST.get("text")
        expense.amount = float(request.POST.get("amount"))
        expense.category = request.POST.get("category")
        expense.expense_type = request.POST.get("expense_type")

        if expense.expense_type == "Positive":
            profile.income += expense.amount
            profile.balance += expense.amount
        else:
            profile.expenses += expense.amount
            profile.balance -= expense.amount

        profile.save()
        expense.save()

        return redirect('/')

    context = {'expense': expense}
    return render(request, 'edit_expense.html', context)

@login_required
def restore_expense(request, id):
    expense = Expense.objects.get(id=id,user=request.user)
    profile = Profile.objects.get(user=request.user)
    expense.is_deleted = False
    expense.save()

    if expense.expense_type == "Positive":
        profile.income += expense.amount
        profile.balance += expense.amount
    else:
        profile.expenses += expense.amount
        profile.balance -= expense.amount

    profile.save()
    return redirect('home')