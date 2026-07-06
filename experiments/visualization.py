import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


def _fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return encoded


def generate_comparison_chart(experiments, chart_type='bar'):
    names = []
    privacy_scores = []
    accuracy_scores = []
    throughput_scores = []
    exec_times = []

    for exp in experiments:
        names.append(exp.name[:30])
        privacy_scores.append(exp.privacy_score or 0)
        accuracy_scores.append((exp.accuracy or 0) * 100)
        throughput_scores.append(exp.throughput or 0)
        exec_times.append(exp.execution_time or 0)

    if not names:
        return None

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#1E293B')
    ax.set_facecolor('#1E293B')

    x = np.arange(len(names))
    width = 0.2

    bars1 = ax.bar(x - 1.5 * width, privacy_scores, width, label='Privacy Score',
                   color='#8B5CF6', edgecolor='none')
    bars2 = ax.bar(x - 0.5 * width, accuracy_scores, width, label='Accuracy (%)',
                   color='#EC4899', edgecolor='none')
    bars3 = ax.bar(x + 0.5 * width, throughput_scores, width, label='Throughput',
                   color='#14B8A6', edgecolor='none')
    bars4 = ax.bar(x + 1.5 * width, exec_times, width, label='Exec Time (s)',
                   color='#F97316', edgecolor='none')

    ax.set_xlabel('Experiment', color='#CBD5E1', fontsize=11)
    ax.set_ylabel('Value', color='#CBD5E1', fontsize=11)
    ax.set_title('Experiment Comparison', color='#F1F5F9', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=35, ha='right', color='#CBD5E1', fontsize=9)
    ax.tick_params(axis='y', colors='#CBD5E1')
    ax.legend(loc='upper right', facecolor='#334155', edgecolor='#475569',
              labelcolor='#F1F5F9', fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#475569')
    ax.spines['bottom'].set_color('#475569')
    ax.grid(axis='y', color='#334155', linewidth=0.5)

    fig.tight_layout()
    return _fig_to_base64(fig)


def generate_radar_chart(experiments):
    categories = ['Privacy', 'Accuracy', 'Throughput', 'Speed', 'Anonymity', 'Security']
    num_vars = len(categories)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('#1E293B')
    ax.set_facecolor('#1E293B')

    color_cycle = ['#8B5CF6', '#EC4899', '#14B8A6', '#F97316', '#3B82F6']

    for idx, exp in enumerate(experiments):
        privacy = exp.privacy_score or 0
        accuracy = (exp.accuracy or 0) * 100
        throughput = exp.throughput or 0
        exec_time = exp.execution_time or 0
        speed = max(0, 100 - min(exec_time * 10, 100))
        anon = min((exp.anonymity_set_size or 0), 100)
        security = (getattr(exp.privacy_technique, 'security_level', 5) or 5) * 10

        values = [privacy, accuracy, throughput, speed, anon, security]
        values += values[:1]

        color = color_cycle[idx % len(color_cycle)]
        ax.plot(angles, values, 'o-', linewidth=2, label=exp.name[:25], color=color, markersize=5)
        ax.fill(angles, values, alpha=0.1, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, color='#CBD5E1', fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], color='#94A3B8', fontsize=8)
    ax.yaxis.grid(color='#334155', linewidth=0.5)
    ax.xaxis.grid(color='#334155', linewidth=0.5)
    ax.spines['polar'].set_color('#475569')

    ax.set_title('Technique Comparison Radar', color='#F1F5F9', fontsize=14,
                 fontweight='bold', pad=25)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1),
              facecolor='#334155', edgecolor='#475569',
              labelcolor='#F1F5F9', fontsize=9)

    fig.tight_layout()
    return _fig_to_base64(fig)


def generate_trend_chart(experiments_qs):
    data = (
        experiments_qs
        .filter(completed_at__isnull=False, status='completed')
        .order_by('completed_at')
        .values_list('completed_at__date', 'privacy_score')
    )

    if not data:
        return None

    dates = [str(d) for d, _ in data]
    scores = [round(s, 2) if s else 0 for _, s in data]

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor('#1E293B')
    ax.set_facecolor('#1E293B')

    ax.plot(dates, scores, color='#8B5CF6', linewidth=2.5, marker='o',
            markersize=6, markerfacecolor='#8B5CF6', markeredgecolor='#fff',
            markeredgewidth=1.5, zorder=5)
    ax.fill_between(dates, scores, alpha=0.15, color='#8B5CF6')

    avg = np.mean(scores) if scores else 0
    ax.axhline(y=avg, color='#EC4899', linestyle='--', linewidth=1, alpha=0.7, label=f'Avg: {avg:.2f}')

    ax.set_xlabel('Date', color='#CBD5E1', fontsize=11)
    ax.set_ylabel('Privacy Score', color='#CBD5E1', fontsize=11)
    ax.set_title('Privacy Score Trend', color='#F1F5F9', fontsize=14, fontweight='bold', pad=15)
    ax.tick_params(axis='x', colors='#CBD5E1', rotation=45)
    ax.tick_params(axis='y', colors='#CBD5E1')
    ax.legend(facecolor='#334155', edgecolor='#475569', labelcolor='#F1F5F9', fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#475569')
    ax.spines['bottom'].set_color('#475569')
    ax.grid(axis='y', color='#334155', linewidth=0.5)

    fig.tight_layout()
    return _fig_to_base64(fig)


def generate_privacy_breakdown(experiment):
    metrics = experiment.metrics if experiment.metrics else {}
    if not metrics:
        return None

    display_keys = {
        'privacy_score': 'Privacy Score',
        'accuracy': 'Accuracy',
        'throughput': 'Throughput',
        'anonymity_set_size': 'Anonymity Set',
        'unlinkability_score': 'Unlinkability',
        'zero_knowledge_property': 'Zero Knowledge',
        'collusion_resistance': 'Collusion Resist.',
        'hardware_isolated': 'HW Isolated',
        'ring_size': 'Ring Size',
        'pool_size': 'Pool Size',
        'num_parties': 'Num Parties',
        'threshold': 'Threshold',
    }

    labels = []
    values = []
    for key, label in display_keys.items():
        if key in metrics:
            val = metrics[key]
            if isinstance(val, (int, float)):
                labels.append(label)
                values.append(float(val))

    if not labels:
        return None

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#1E293B')
    ax.set_facecolor('#1E293B')

    colors = ['#8B5CF6', '#EC4899', '#14B8A6', '#F97316', '#3B82F6',
              '#F59E0B', '#10B981', '#EF4444', '#6366F1', '#84CC16',
              '#06B6D4', '#A855F7']

    bars = ax.barh(labels, values, color=colors[:len(labels)], edgecolor='none', height=0.6)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max(values) * 0.02, bar.get_y() + bar.get_height() / 2,
                f'{val:.2f}', va='center', ha='left', color='#CBD5E1', fontsize=10, fontweight='bold')

    ax.set_xlabel('Value', color='#CBD5E1', fontsize=11)
    ax.set_title(f'Privacy Breakdown — {experiment.name[:40]}',
                 color='#F1F5F9', fontsize=13, fontweight='bold', pad=15)
    ax.tick_params(axis='y', colors='#CBD5E1', labelsize=10)
    ax.tick_params(axis='x', colors='#CBD5E1')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#475569')
    ax.spines['bottom'].set_color('#475569')
    ax.grid(axis='x', color='#334155', linewidth=0.5)
    ax.invert_yaxis()

    fig.tight_layout()
    return _fig_to_base64(fig)
