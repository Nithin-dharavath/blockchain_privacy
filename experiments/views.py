from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Experiment, ExperimentComparison
from .forms import ExperimentForm, ExperimentComparisonForm
from datasets.models import Dataset
from privacy_tools.models import PrivacyTechnique
import pandas as pd
import time
import json
import logging

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
    """View experiment details and results"""
    experiment = get_object_or_404(Experiment, pk=pk, user=request.user)
    
    # Parse metrics if available
    metrics = experiment.metrics if experiment.metrics else {}
    
    context = {
        'experiment': experiment,
        'metrics': metrics
    }
    return render(request, 'experiments/experiment_detail.html', context)

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
    
    # Prepare comparison data
    comparison_data = []
    for exp in experiments:
        comparison_data.append({
            'name': exp.name,
            'technique': exp.privacy_technique.name,
            'privacy_score': exp.privacy_score or 0,
            'execution_time': exp.execution_time or 0,
            'accuracy': exp.accuracy or 0,
            'throughput': exp.throughput or 0,
            'anonymity_set_size': exp.anonymity_set_size or 0,
        })
    
    context = {
        'comparison': comparison,
        'experiments': experiments,
        'comparison_data': comparison_data
    }
    return render(request, 'experiments/comparison_detail.html', context)

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
