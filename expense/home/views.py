from django.shortcuts import render,redirect
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login

@login_required

def home(request):
    profile = Profile.objects.filter(user = request.user).first()
    expenses = Expense.objects.filter(user = request.user)

    selected_category = request.GET.get('category')

    if selected_category:
        expenses = expenses.filter(category=selected_category)

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
        
    context = { 'profile' : profile , 'expenses' : expenses}
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
    expense.delete()

    return redirect('/')