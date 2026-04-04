from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Dataset
from .forms import DatasetUploadForm
import pandas as pd
import os

@login_required
def dataset_list(request):
    """List all user's datasets"""
    datasets = Dataset.objects.filter(uploaded_by=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(datasets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'datasets': page_obj
    }
    return render(request, 'datasets/dataset_list.html', context)

@login_required
def dataset_upload(request):
    """Upload new dataset"""
    if request.method == 'POST':
        form = DatasetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.uploaded_by = request.user
            
            # Get file information
            uploaded_file = request.FILES['file']
            dataset.file_size = uploaded_file.size
            
            # Try to read CSV and get dimensions
            try:
                df = pd.read_csv(uploaded_file)
                dataset.row_count = len(df)
                dataset.column_count = len(df.columns)
                
                # Reset file pointer
                uploaded_file.seek(0)
            except Exception as e:
                messages.warning(request, f'Could not read file structure: {str(e)}')
            
            dataset.save()
            messages.success(request, 'Dataset uploaded successfully! Waiting for approval.')
            return redirect('datasets:list')
    else:
        form = DatasetUploadForm()
    
    context = {'form': form}
    return render(request, 'datasets/dataset_upload.html', context)

@login_required
def dataset_detail(request, pk):
    """View dataset details"""
    dataset = get_object_or_404(Dataset, pk=pk, uploaded_by=request.user)
    
    # Try to read sample data
    sample_data = None
    columns = []
    
    if dataset.status == 'approved':
        try:
            df = pd.read_csv(dataset.file.path)
            sample_data = df.head(10).to_dict('records')
            columns = df.columns.tolist()
        except Exception as e:
            messages.warning(request, f'Could not load dataset preview: {str(e)}')
    
    context = {
        'dataset': dataset,
        'sample_data': sample_data,
        'columns': columns
    }
    return render(request, 'datasets/dataset_detail.html', context)

@login_required
def dataset_delete(request, pk):
    """Delete dataset"""
    dataset = get_object_or_404(Dataset, pk=pk, uploaded_by=request.user)
    
    if request.method == 'POST':
        # Delete file
        if dataset.file:
            if os.path.isfile(dataset.file.path):
                os.remove(dataset.file.path)
        
        dataset.delete()
        messages.success(request, 'Dataset deleted successfully.')
        return redirect('datasets:list')
    
    context = {'dataset': dataset}
    return render(request, 'datasets/dataset_confirm_delete.html', context)
