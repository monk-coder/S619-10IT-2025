from django.shortcuts import render, redirect, get_object_or_404
cached.fetched_at = now
cached.save()
else:
CachedWeather.objects.create(city=data['city'], data=data, fetched_at=now)
weather = data
except OpenWeatherError as e:
error = str(e)


# история для пользователя
history = []
if request.user.is_authenticated:
history = CitySearchHistory.objects.filter(user=request.user)[:10]
tasks = Task.objects.filter(owner=request.user) if request.user.is_authenticated else []


return render(request, 'dashboard.html', {
'form': form,
'weather': weather,
'error': error,
'history': history,
'tasks': tasks,
})


@login_required
def task_list(request):
tasks = Task.objects.filter(owner=request.user)
return render(request, 'task_list.html', {'tasks': tasks})


@login_required
def task_create(request):
if request.method == 'POST':
form = TaskForm(request.POST)
if form.is_valid():
t = form.save(commit=False)
t.owner = request.user
t.save()
messages.success(request, 'Задача создана')
return redirect('task_list')
else:
form = TaskForm()
return render(request, 'task_form.html', {'form': form})


@login_required
def task_update(request, pk):
task = get_object_or_404(Task, pk=pk, owner=request.user)
if request.method == 'POST':
form = TaskForm(request.POST, instance=task)
if form.is_valid():
form.save()
messages.success(request, 'Задача обновлена')
return redirect('task_list')
else:
form = TaskForm(instance=task)
return render(request, 'task_form.html', {'form': form})


@login_required
def task_delete(request, pk):
task = get_object_or_404(Task, pk=pk, owner=request.user)
if request.method == 'POST':
task.delete()
messages.success(request, 'Задача удалена')
return redirect('task_list')
return render(request, 'task_form.html', {'form': None, 'task': task})