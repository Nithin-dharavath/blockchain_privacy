from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Sum, Count
from django.utils import timezone
from .models import Experiment, ExperimentComparison
from .forms import ExperimentForm, ExperimentComparisonForm
from datasets.models import Dataset
from privacy_tools.models import PrivacyTechnique
import pandas as pd
import time
import json
import logging

from admin_panel.models import ExperimentErrorReport

from .visualization import (
    generate_comparison_chart,
    generate_radar_chart,
    generate_trend_chart,
    generate_privacy_breakdown,
    generate_scatter_chart,
)

# Import privacy techniques
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from privacy_tools.techniques.ring_signature import RingSignature
from privacy_tools.techniques.zero_knowledge_proof import ZeroKnowledgeProof
from privacy_tools.techniques.secure_mpc import SecureMultiPartyComputation
from privacy_tools.techniques.trusted_execution import TrustedExecutionEnvironment
from privacy_tools.techniques.crypto_mixer import CryptocurrencyMixer

exp_logger = logging.getLogger('experiments')

@login_required
def experiment_list(request):
    """List all user's experiments"""
    experiments = Experiment.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        experiments = experiments.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(experiments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'experiments': page_obj,
        'status_filter': status_filter
    }
    return render(request, 'experiments/experiment_list.html', context)

@login_required
def results_dashboard(request):
    qs = Experiment.objects.filter(user=request.user)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    technique_id = request.GET.get('technique')
    dataset_id = request.GET.get('dataset')

    if date_from:
        qs = qs.filter(completed_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(completed_at__date__lte=date_to)
    if technique_id:
        qs = qs.filter(privacy_technique_id=technique_id)
    if dataset_id:
        qs = qs.filter(dataset_id=dataset_id)

    completed = qs.filter(status='completed')
    stats = {
        'total_experiments': qs.count(),
        'completed_count': completed.count(),
        'failed_count': qs.filter(status='failed').count(),
        'avg_privacy_score': round(completed.aggregate(avg=Avg('privacy_score'))['avg'] or 0, 2),
        'avg_accuracy': round((completed.aggregate(avg=Avg('accuracy'))['avg'] or 0) * 100, 1),
        'total_compute_time': round(completed.aggregate(total=Sum('execution_time'))['total'] or 0, 2),
    }

    trend_data = (
        completed
        .filter(completed_at__isnull=False)
        .order_by('completed_at')
        .values_list('completed_at__date', 'privacy_score')
    )
    trend_labels = [str(d) for d, _ in trend_data]
    trend_values = [round(s, 2) if s else 0 for _, s in trend_data]

    techniques = PrivacyTechnique.objects.filter(
        experiments__in=completed
    ).distinct()
    radar_axes = ['Privacy', 'Accuracy', 'Throughput', 'Speed', 'Anonymity', 'Security']
    radar_datasets = []
    colors = [
        ('139, 92, 246', '0.7'),
        ('236, 72, 153', '0.7'),
        ('20, 184, 166', '0.7'),
        ('249, 115, 22', '0.7'),
        ('59, 130, 246', '0.7'),
    ]
    for idx, tech in enumerate(techniques):
        tech_exps = completed.filter(privacy_technique=tech)
        avg_privacy = round(tech_exps.aggregate(avg=Avg('privacy_score'))['avg'] or 0, 2)
        avg_accuracy = round((tech_exps.aggregate(avg=Avg('accuracy'))['avg'] or 0) * 100, 2)
        avg_throughput = round(tech_exps.aggregate(avg=Avg('throughput'))['avg'] or 0, 2)
        avg_exec = tech_exps.aggregate(avg=Avg('execution_time'))['avg'] or 0
        speed_score = round(max(0, 100 - min(avg_exec * 10, 100)), 2)
        avg_anon = round(tech_exps.aggregate(avg=Avg('anonymity_set_size'))['avg'] or 0, 2)
        security = round(tech.security_level * 10, 2)
        color = colors[idx % len(colors)]
        radar_datasets.append({
            'label': tech.name,
            'data': [avg_privacy, avg_accuracy, avg_throughput, speed_score, avg_anon, security],
            'borderColor': f'rgba({color[0]}, 1)',
            'backgroundColor': f'rgba({color[0]}, {color[1]})',
        })

    status_counts = qs.values('status').annotate(count=Count('id')).order_by('status')
    pie_labels = [s['status'].title() for s in status_counts]
    pie_values = [s['count'] for s in status_counts]
    pie_colors = []
    for s in [sc['status'] for sc in status_counts]:
        if s == 'completed':
            pie_colors.append("'rgba(16, 185, 129, 0.8)'")
        elif s == 'failed':
            pie_colors.append("'rgba(239, 68, 68, 0.8)'")
        elif s == 'running':
            pie_colors.append("'rgba(245, 158, 11, 0.8)'")
        else:
            pie_colors.append("'rgba(148, 163, 184, 0.8)'")

    all_techniques = PrivacyTechnique.objects.filter(is_active=True)
    all_datasets = Dataset.objects.filter(uploaded_by=request.user, status='approved')

    comparison_chart = generate_comparison_chart(completed[:8])
    radar_chart = generate_radar_chart(completed[:5])
    trend_chart = generate_trend_chart(qs)

    context = {
        'stats': stats,
        'trend_labels': json.dumps(trend_labels),
        'trend_values': json.dumps(trend_values),
        'radar_labels': json.dumps(radar_axes),
        'radar_datasets': json.dumps(radar_datasets),
        'pie_labels': json.dumps(pie_labels),
        'pie_values': json.dumps(pie_values),
        'pie_colors': json.dumps(pie_colors),
        'all_techniques': all_techniques,
        'all_datasets': all_datasets,
        'selected_technique': technique_id or '',
        'selected_dataset': dataset_id or '',
        'date_from': date_from or '',
        'date_to': date_to or '',
        'comparison_chart': comparison_chart,
        'radar_chart': radar_chart,
        'trend_chart': trend_chart,
    }
    return render(request, 'experiments/results_dashboard.html', context)

@login_required
def experiment_create(request):
    """Create new experiment"""
    if request.method == 'POST':
        form = ExperimentForm(request.POST, user=request.user)
        if form.is_valid():
            experiment = form.save(commit=False)
            experiment.user = request.user
            experiment.status = 'pending'
            experiment.save()
            
            messages.success(request, 'Experiment created successfully!')
            return redirect('experiments:run', pk=experiment.pk)
    else:
        form = ExperimentForm(user=request.user)
    
    context = {
        'form': form,
        'available_datasets': Dataset.objects.filter(
            uploaded_by=request.user,
            status='approved'
        ),
        'privacy_techniques': PrivacyTechnique.objects.filter(is_active=True)
    }
    return render(request, 'experiments/experiment_create.html', context)

@login_required
def experiment_detail(request, pk):
    """View experiment details and results with charts and analysis"""
    experiment = get_object_or_404(Experiment, pk=pk, user=request.user)

    metrics = experiment.metrics if experiment.metrics else {}

    # Historical runs: same technique, different experiments
    historical_runs = (
        Experiment.objects
        .filter(
            user=request.user,
            privacy_technique=experiment.privacy_technique,
            status='completed',
        )
        .exclude(pk=experiment.pk)
        .order_by('-completed_at')[:20]
    )

    # Charts (only if completed)
    scatter_chart = None
    privacy_breakdown_chart = None
    if experiment.status == 'completed':
        # Scatter needs at least the current experiment + any historical for context
        scatter_qs = Experiment.objects.filter(
            user=request.user,
            status='completed',
            privacy_technique=experiment.privacy_technique,
        )
        if scatter_qs.count() >= 2:
            scatter_chart = generate_scatter_chart(scatter_qs[:15])
        else:
            scatter_chart = generate_scatter_chart([experiment])
        privacy_breakdown_chart = generate_privacy_breakdown(experiment)

    # Config impact: build a summary of config params and their observed effect
    config_impact = []
    if experiment.configuration:
        for param, value in experiment.configuration.items():
            config_impact.append({
                'param': param.replace('_', ' ').title(),
                'value': value,
            })

    context = {
        'experiment': experiment,
        'metrics': metrics,
        'historical_runs': historical_runs,
        'scatter_chart': scatter_chart,
        'privacy_breakdown_chart': privacy_breakdown_chart,
        'config_impact': config_impact,
    }
    return render(request, 'experiments/experiment_detail.html', context)


@login_required
def experiment_export(request, pk):
    """Export experiment as CSV or JSON"""
    import csv as csv_mod
    from django.http import HttpResponse

    experiment = get_object_or_404(Experiment, pk=pk, user=request.user)
    fmt = request.GET.get('format', 'json')
    metrics = experiment.metrics if experiment.metrics else {}

    row = {
        'name': experiment.name,
        'technique': experiment.privacy_technique.name,
        'dataset': experiment.dataset.name,
        'status': experiment.status,
        'privacy_score': experiment.privacy_score,
        'accuracy': experiment.accuracy,
        'execution_time': experiment.execution_time,
        'throughput': experiment.throughput,
        'anonymity_set_size': experiment.anonymity_set_size,
        'created_at': experiment.created_at.isoformat() if experiment.created_at else '',
        'completed_at': experiment.completed_at.isoformat() if experiment.completed_at else '',
        'configuration': json.dumps(experiment.configuration),
        'metrics': json.dumps(metrics),
    }

    filename = f"experiment_{experiment.pk}"

    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        writer = csv_mod.DictWriter(response, fieldnames=row.keys())
        writer.writeheader()
        writer.writerow(row)
    else:
        response = HttpResponse(
            json.dumps(row, indent=2),
            content_type='application/json',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.json"'

    return response

@login_required
def run_experiment(request, pk):
    """Execute an experiment using real implementations"""
    from django.utils import timezone
    from .experiment_runner import PrivacyExperimentRunner
    
    experiment = get_object_or_404(Experiment, pk=pk, user=request.user)
    
    if experiment.status == 'completed':
        messages.info(request, 'This experiment has already been completed.')
        return redirect('experiments:detail', pk=pk)
    
    # Update status
    experiment.status = 'running'
    experiment.started_at = timezone.now()
    experiment.save()
    exp_logger.info("Experiment %s started by %s", experiment.pk, request.user.username)
    
    try:
        # Load dataset
        df = experiment.dataset.get_data()
        
        if df is None or len(df) == 0:
            raise Exception("Failed to load dataset or dataset is empty")
        
        # Run experiment with real implementation
        runner = PrivacyExperimentRunner(experiment, df)
        results = runner.run()
        
        # Save results
        experiment.privacy_score = results['privacy_score']
        experiment.execution_time = results['execution_time']
        experiment.accuracy = results['accuracy']
        experiment.throughput = results['throughput']
        experiment.anonymity_set_size = results['anonymity_set_size']
        experiment.metrics = results['metrics']
        
        experiment.status = 'completed'
        experiment.completed_at = timezone.now()
        experiment.save()
        exp_logger.info(
            "Experiment %s completed in %.3fs (privacy=%.4f, accuracy=%.4f)",
            experiment.pk, experiment.execution_time,
            experiment.privacy_score, experiment.accuracy,
        )
        
        messages.success(request, f'Experiment "{experiment.name}" completed successfully!')
    
    except Exception as e:
        experiment.status = 'failed'
        experiment.error_message = str(e)
        experiment.completed_at = timezone.now()
        experiment.save()
        exp_logger.error("Experiment %s failed: %s", experiment.pk, str(e))
        try:
            ExperimentErrorReport.objects.create(
                experiment=experiment,
                technique=experiment.privacy_technique,
                error_message=str(e),
            )
        except Exception:
            pass
        messages.error(request, f'Experiment failed: {str(e)}')
    
    return redirect('experiments:detail', pk=pk)



@login_required
def experiment_run(request, pk):
    """Run experiment and generate results"""
    experiment = get_object_or_404(Experiment, pk=pk, user=request.user)
    
    if experiment.status == 'completed':
        messages.info(request, 'This experiment has already been completed.')
        return redirect('experiments:detail', pk=pk)
    
    # Update status
    experiment.status = 'running'
    experiment.started_at = timezone.now()
    experiment.save()
    exp_logger.info("Experiment %s started by %s", experiment.pk, request.user.username)
    
    try:
        # Load dataset
        dataset = experiment.dataset
        df = pd.read_csv(dataset.file.path)
        
        # Get technique
        technique = experiment.privacy_technique
        
        # Run experiment based on technique type
        start_time = time.time()
        
        if technique.technique_type == 'ring_signature':
            results = run_ring_signature_experiment(df, experiment.configuration)
        elif technique.technique_type == 'zkp':
            results = run_zkp_experiment(df, experiment.configuration)
        elif technique.technique_type == 'smpc':
            results = run_smpc_experiment(df, experiment.configuration)
        elif technique.technique_type == 'tee':
            results = run_tee_experiment(df, experiment.configuration)
        elif technique.technique_type == 'mixer':
            results = run_mixer_experiment(df, experiment.configuration)
        else:
            raise ValueError(f"Unknown technique type: {technique.technique_type}")
        
        execution_time = time.time() - start_time
        
        # Update experiment with results
        experiment.status = 'completed'
        experiment.completed_at = timezone.now()
        experiment.execution_time = execution_time
        experiment.privacy_score = results.get('privacy_score', 0)
        experiment.accuracy = results.get('accuracy', 0)
        experiment.throughput = results.get('throughput', 0)
        experiment.anonymity_set_size = results.get('anonymity_set_size', 0)
        experiment.metrics = results
        experiment.save()
        exp_logger.info(
            "Experiment %s completed in %.3fs (privacy=%.4f, accuracy=%.4f)",
            experiment.pk, experiment.execution_time,
            experiment.privacy_score, experiment.accuracy,
        )
        
        messages.success(request, 'Experiment completed successfully!')
        
    except Exception as e:
        experiment.status = 'failed'
        experiment.error_message = str(e)
        experiment.completed_at = timezone.now()
        experiment.save()
        exp_logger.error("Experiment %s failed: %s", experiment.pk, str(e))
        try:
            ExperimentErrorReport.objects.create(
                experiment=experiment,
                technique=experiment.privacy_technique,
                error_message=str(e),
            )
        except Exception:
            pass
        messages.error(request, f'Experiment failed: {str(e)}')
    
    return redirect('experiments:detail', pk=pk)

def run_ring_signature_experiment(df, config):
    """Run Ring Signature experiment"""
    ring_size = config.get('ring_size', 5)
    num_transactions = min(len(df), config.get('num_transactions', 100))
    
    rs = RingSignature(ring_size=ring_size)
    
    # Simulate transactions with ring signatures
    successful_signatures = 0
    total_time = 0
    
    for i in range(num_transactions):
        try:
            # Generate keys
            private_key, public_key = rs.generate_key_pair()
            ring = rs.generate_ring(public_key, num_decoys=ring_size-1)
            
            # Sign message
            message = f"Transaction {i}".encode()
            start = time.time()
            signature = rs.sign(message, private_key, ring)
            
            # Verify
            verified = rs.verify(message, signature, ring)
            total_time += time.time() - start
            
            if verified:
                successful_signatures += 1
        except:
            pass
    
    # Evaluate privacy
    privacy_metrics = rs.evaluate_privacy(ring_size, num_transactions)
    
    accuracy = successful_signatures / num_transactions if num_transactions > 0 else 0
    throughput = num_transactions / total_time if total_time > 0 else 0
    
    return {
        'privacy_score': privacy_metrics['privacy_score'],
        'accuracy': accuracy,
        'throughput': throughput,
        'anonymity_set_size': privacy_metrics['anonymity_set_size'],
        'unlinkability_score': privacy_metrics['unlinkability_score'],
        'ring_size': ring_size,
        'successful_operations': successful_signatures,
        'total_operations': num_transactions
    }

def run_zkp_experiment(df, config):
    """Run Zero-Knowledge Proof experiment"""
    num_proofs = min(len(df), config.get('num_proofs', 50))
    
    zkp = ZeroKnowledgeProof()
    
    successful_proofs = 0
    total_time = 0
    total_proof_size = 0
    
    for i in range(num_proofs):
        try:
            secret_value = int(df.iloc[i % len(df)].iloc[0]) if len(df) > 0 else i
            
            start = time.time()
            proof = zkp.generate_proof(secret_value, "prove_knowledge")
            verified = zkp.verify_proof(proof)
            total_time += time.time() - start
            
            total_proof_size += len(str(proof))
            
            if verified:
                successful_proofs += 1
        except:
            pass
    
    avg_proof_size_kb = (total_proof_size / num_proofs / 1024) if num_proofs > 0 else 0
    privacy_metrics = zkp.evaluate_privacy(num_proofs, avg_proof_size_kb)
    
    accuracy = successful_proofs / num_proofs if num_proofs > 0 else 0
    throughput = num_proofs / total_time if total_time > 0 else 0
    
    return {
        'privacy_score': privacy_metrics['privacy_score'],
        'accuracy': accuracy,
        'throughput': throughput,
        'anonymity_set_size': 1,
        'zero_knowledge_property': privacy_metrics['zero_knowledge_property'],
        'avg_proof_size_kb': avg_proof_size_kb,
        'successful_operations': successful_proofs,
        'total_operations': num_proofs
    }

def run_smpc_experiment(df, config):
    """Run Secure Multi-Party Computation experiment"""
    num_parties = config.get('num_parties', 3)
    threshold = config.get('threshold', 2)
    num_computations = min(len(df), config.get('num_computations', 20))
    
    smpc = SecureMultiPartyComputation(num_parties=num_parties, threshold=threshold)
    
    successful_computations = 0
    total_time = 0
    
    for i in range(num_computations):
        try:
            # Generate random values for parties
            values = [int(abs(hash(f"{i}_{j}")) % 1000) for j in range(num_parties)]
            
            start = time.time()
            result = smpc.secure_sum(values)
            total_time += time.time() - start
            
            # Verify result
            expected_sum = sum(values) % smpc.prime
            if result == expected_sum:
                successful_computations += 1
        except:
            pass
    
    privacy_metrics = smpc.evaluate_privacy(num_parties, threshold, num_computations)
    
    accuracy = successful_computations / num_computations if num_computations > 0 else 0
    throughput = num_computations / total_time if total_time > 0 else 0
    
    return {
        'privacy_score': privacy_metrics['privacy_score'],
        'accuracy': accuracy,
        'throughput': throughput,
        'anonymity_set_size': num_parties,
        'num_parties': num_parties,
        'threshold': threshold,
        'collusion_resistance': privacy_metrics['collusion_resistance'],
        'successful_operations': successful_computations,
        'total_operations': num_computations
    }

def run_tee_experiment(df, config):
    """Run Trusted Execution Environment experiment"""
    num_operations = min(len(df), config.get('num_operations', 50))
    data_size_mb = config.get('data_size_mb', 1)
    
    tee = TrustedExecutionEnvironment()
    
    # Create enclave
    code_hash = "test_code_hash_12345"
    enclave = tee.create_enclave(code_hash)
    
    successful_operations = 0
    total_time = 0
    
    for i in range(num_operations):
        try:
            # Seal data
            data = {'values': [i, i+1, i+2], 'operation': 'sum'}
            
            start = time.time()
            sealed = tee.seal_data(data)
            
            # Compute in enclave
            result = tee.secure_compute('sum', sealed)
            
            # Unseal result
            unsealed = tee.unseal_data(result)
            total_time += time.time() - start
            
            successful_operations += 1
        except:
            pass
    
    privacy_metrics = tee.evaluate_privacy(num_operations, data_size_mb)
    
    accuracy = successful_operations / num_operations if num_operations > 0 else 0
    throughput = num_operations / total_time if total_time > 0 else 0
    
    return {
        'privacy_score': privacy_metrics['privacy_score'],
        'accuracy': accuracy,
        'throughput': throughput,
        'anonymity_set_size': 1,
        'hardware_isolated': privacy_metrics['hardware_isolated'],
        'enclave_id': privacy_metrics['enclave_id'],
        'successful_operations': successful_operations,
        'total_operations': num_operations
    }

def run_mixer_experiment(df, config):
    """Run Cryptocurrency Mixer experiment"""
    pool_size = config.get('pool_size', 10)
    num_transactions = min(len(df), config.get('num_transactions', 50))
    
    mixer = CryptocurrencyMixer(pool_size=pool_size, min_delay=1, max_delay=5)
    
    successful_mixes = 0
    total_time = 0
    
    # Create deposits
    deposits = []
    for i in range(num_transactions):
        sender = mixer.generate_address()
        recipient = mixer.generate_address()
        amount = 1.0 + (i % 10)
        
        deposit_id = mixer.create_deposit(sender, amount, recipient)
        deposits.append(deposit_id)
    
    # Mix transactions
    start = time.time()
    mix_result = mixer.mix_transactions()
    total_time = time.time() - start
    
    if mix_result['status'] == 'success':
        successful_mixes = mix_result['num_mixed']
    
    privacy_metrics = mixer.evaluate_privacy(num_transactions, pool_size)
    
    accuracy = successful_mixes / num_transactions if num_transactions > 0 else 0
    throughput = num_transactions / total_time if total_time > 0 else 0
    
    return {
        'privacy_score': privacy_metrics['privacy_score'],
        'accuracy': accuracy,
        'throughput': throughput,
        'anonymity_set_size': privacy_metrics['anonymity_set_size'],
        'unlinkability_score': privacy_metrics['unlinkability_score'],
        'pool_size': pool_size,
        'successful_operations': successful_mixes,
        'total_operations': num_transactions
    }

@login_required
def experiment_compare(request):
    """Compare multiple experiments"""
    if request.method == 'POST':
        form = ExperimentComparisonForm(request.POST, user=request.user)
        if form.is_valid():
            comparison = form.save(commit=False)
            comparison.user = request.user
            comparison.save()
            form.save_m2m()
            
            messages.success(request, 'Comparison created successfully!')
            return redirect('experiments:comparison_detail', pk=comparison.pk)
    else:
        form = ExperimentComparisonForm(user=request.user)
    
    context = {
        'form': form,
        'completed_experiments': Experiment.objects.filter(
            user=request.user,
            status='completed'
        ).order_by('-created_at')
    }
    return render(request, 'experiments/experiment_compare.html', context)

@login_required
def comparison_detail(request, pk):
    """View comparison results"""
    comparison = get_object_or_404(ExperimentComparison, pk=pk, user=request.user)
    experiments = comparison.experiments.all()
    
    # Prepare comparison data with actual best values computed
    comparison_data = []
    best_privacy_score = 0
    best_accuracy = 0
    best_throughput = 0
    fastest_execution_time = float('inf')
    
    for exp in experiments:
        privacy_score = exp.privacy_score or 0
        execution_time = exp.execution_time or 0
        accuracy = exp.accuracy or 0
        throughput = exp.throughput or 0
        
        comparison_data.append({
            'name': exp.name,
            'technique': exp.privacy_technique.name,
            'privacy_score': privacy_score,
            'execution_time': execution_time,
            'accuracy': accuracy,
            'throughput': throughput,
            'anonymity_set_size': exp.anonymity_set_size or 0,
            'metrics': exp.metrics or {},
        })
        
        # Compute actual best values
        if privacy_score > best_privacy_score:
            best_privacy_score = privacy_score
        if accuracy > best_accuracy:
            best_accuracy = accuracy
        if throughput > best_throughput:
            best_throughput = throughput
        if execution_time < fastest_execution_time and execution_time > 0:
            fastest_execution_time = execution_time
    
    # Reset fastest_execution_time if no valid time found
    if fastest_execution_time == float('inf'):
        fastest_execution_time = 0
    
    # Generate charts
    radar_chart = generate_radar_chart(experiments)
    comparison_chart = generate_comparison_chart(experiments, chart_type='grouped_bar')
    
    # Generate ranking data with color coding
    ranking_data = []
    for data in comparison_data:
        ranking_data.append({
            'name': data['name'],
            'technique': data['technique'],
            'privacy_score': data['privacy_score'],
            'execution_time': data['execution_time'],
            'accuracy': data['accuracy'],
            'throughput': data['throughput'],
            'anonymity_set_size': data['anonymity_set_size'],
            'is_best_privacy': data['privacy_score'] == best_privacy_score and best_privacy_score > 0,
            'is_worst_privacy': data['privacy_score'] == min(d['privacy_score'] for d in comparison_data) if comparison_data else False,
            'is_fastest': data['execution_time'] == fastest_execution_time and fastest_execution_time > 0,
            'is_slowest': data['execution_time'] == max(d['execution_time'] for d in comparison_data) if comparison_data else False,
            'is_most_accurate': data['accuracy'] == best_accuracy and best_accuracy > 0,
            'is_least_accurate': data['accuracy'] == min(d['accuracy'] for d in comparison_data) if comparison_data else False,
            'is_highest_throughput': data['throughput'] == best_throughput and best_throughput > 0,
            'is_lowest_throughput': data['throughput'] == min(d['throughput'] for d in comparison_data) if comparison_data else False,
        })
    
    # Find best for privacy and performance
    best_privacy_exp = max(comparison_data, key=lambda x: x['privacy_score']) if comparison_data else None
    best_performance_exp = min(comparison_data, key=lambda x: x['execution_time'] if x['execution_time'] > 0 else float('inf')) if comparison_data else None
    
    context = {
        'comparison': comparison,
        'experiments': experiments,
        'comparison_data': comparison_data,
        'best_privacy_score': best_privacy_score,
        'fastest_execution_time': fastest_execution_time,
        'best_accuracy': best_accuracy,
        'best_throughput': best_throughput,
        'radar_chart': radar_chart,
        'comparison_chart': comparison_chart,
        'ranking_data': ranking_data,
        'best_privacy_exp': best_privacy_exp,
        'best_performance_exp': best_performance_exp,
    }
    return render(request, 'experiments/comparison_detail.html', context)

@login_required
def export_comparison(request, pk):
    """Export comparison data to CSV or PDF"""
    comparison = get_object_or_404(ExperimentComparison, pk=pk, user=request.user)
    experiments = comparison.experiments.all()
    
    format_type = request.GET.get('format', 'csv')
    
    # Prepare data
    data = []
    for exp in experiments:
        data.append({
            'name': exp.name,
            'technique': exp.privacy_technique.name,
            'privacy_score': exp.privacy_score or 0,
            'execution_time': exp.execution_time or 0,
            'accuracy': exp.accuracy or 0,
            'throughput': exp.throughput or 0,
            'anonymity_set_size': exp.anonymity_set_size or 0,
        })
    
    df = pd.DataFrame(data)
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="comparison_{comparison.pk}.csv"'
        df.to_csv(response, index=False)
        return response
    elif format_type == 'pdf':
        # For PDF, we'll return a simple HTML response that can be printed to PDF
        # In a real implementation, you'd use a library like reportlab
        from django.template.loader import render_to_string
        
        # Prepare context for template
        context = {
            'comparison': comparison,
            'comparison_data': data,
            'best_privacy_score': max(d['privacy_score'] for d in data) if data else 0,
            'fastest_execution_time': min(d['execution_time'] for d in data if d['execution_time'] > 0) if data else 0,
        }
        html_content = render_to_string('experiments/comparison_pdf_template.html', context)
        
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="comparison_{comparison.pk}.html"'
        return response
    
    messages.error(request, 'Invalid format specified.')
    return redirect('experiments:comparison_detail', pk=pk)

@login_required
def experiment_delete(request, pk):
    """Delete experiment"""
    experiment = get_object_or_404(Experiment, pk=pk, user=request.user)
    
    if request.method == 'POST':
        experiment.delete()
        messages.success(request, 'Experiment deleted successfully.')
        return redirect('experiments:list')
    
    context = {'experiment': experiment}
    return render(request, 'experiments/experiment_confirm_delete.html', context)
