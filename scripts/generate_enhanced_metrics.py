#!/usr/bin/env python3
"""
Generate enhanced code metrics using radon and pygount.

This script analyzes the egeria-python codebase and generates comprehensive
metrics including:
- Accurate line counts (code, comments, blank)
- Cyclomatic complexity
- Maintainability index
- Halstead metrics
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

from radon.complexity import cc_visit, average_complexity
from radon.metrics import mi_visit, h_visit
from radon.raw import analyze as raw_analyze
from pygount import SourceAnalysis
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from advisor.config import settings


def analyze_file_with_radon(file_path: Path) -> Dict[str, Any]:
    """Analyze a single file with radon."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Cyclomatic complexity
        cc_results = cc_visit(code)
        
        # Maintainability index
        mi_score = mi_visit(code, multi=True)
        
        # Halstead metrics - returns a tuple of (total, functions)
        h_results = h_visit(code)
        h_total = h_results[0] if h_results and len(h_results) > 0 else None
        
        # Raw metrics
        raw = raw_analyze(code)
        
        return {
            'complexity': {
                'average': average_complexity(cc_results) if cc_results else 0,
                'total': sum(c.complexity for c in cc_results),
                'max': max((c.complexity for c in cc_results), default=0),
                'functions': [
                    {
                        'name': c.name,
                        'complexity': c.complexity,
                        'line': c.lineno,
                        'type': c.classname if hasattr(c, 'classname') else 'function'
                    }
                    for c in cc_results
                ]
            },
            'maintainability': {
                'index': mi_score,
                'rank': _get_mi_rank(mi_score)
            },
            'halstead': {
                'volume': h_total.volume if h_total else 0,
                'difficulty': h_total.difficulty if h_total else 0,
                'effort': h_total.effort if h_total else 0,
                'time': h_total.time if h_total else 0,
                'bugs': h_total.bugs if h_total else 0
            } if h_total else None,
            'raw': {
                'loc': raw.loc,
                'lloc': raw.lloc,
                'sloc': raw.sloc,
                'comments': raw.comments,
                'multi': raw.multi,
                'blank': raw.blank,
                'single_comments': raw.single_comments
            }
        }
    except Exception as e:
        logger.debug(f"Failed to analyze {file_path} with radon: {e}")
        return None


def analyze_file_with_pygount(file_path: Path) -> Dict[str, Any]:
    """Analyze a single file with pygount."""
    try:
        analysis = SourceAnalysis.from_file(str(file_path), "python")
        
        return {
            'code_count': analysis.code_count,
            'documentation_count': analysis.documentation_count,
            'empty_count': analysis.empty_count,
            'string_count': analysis.string_count,
            'line_count': analysis.line_count
        }
    except Exception as e:
        logger.warning(f"Failed to analyze {file_path} with pygount: {e}")
        return None


def _get_mi_rank(mi_score: float) -> str:
    """Get maintainability index rank."""
    if mi_score >= 20:
        return "A"  # Highly maintainable
    elif mi_score >= 10:
        return "B"  # Moderately maintainable
    elif mi_score >= 0:
        return "C"  # Difficult to maintain
    else:
        return "F"  # Extremely difficult to maintain


def analyze_codebase(repo_path: Path) -> Dict[str, Any]:
    """Analyze entire codebase."""
    logger.info(f"Analyzing codebase at {repo_path}")
    
    # Directories to skip
    skip_dirs = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', 'build', 'dist', '.pytest_cache', '.mypy_cache'}
    
    # Find all Python files, excluding skip directories
    python_files = []
    for py_file in repo_path.rglob("*.py"):
        # Check if any parent directory is in skip_dirs
        if any(part in skip_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)
    
    logger.info(f"Found {len(python_files)} Python files (excluding virtual environments)")
    
    # Aggregate metrics
    total_metrics = {
        'files_analyzed': 0,
        'total_loc': 0,
        'total_sloc': 0,
        'total_code': 0,
        'total_comments': 0,
        'total_blank': 0,
        'total_complexity': 0,
        'avg_complexity': 0,
        'avg_maintainability': 0,
        'total_halstead_volume': 0,
        'total_halstead_bugs': 0,
        'complexity_distribution': defaultdict(int),
        'maintainability_distribution': defaultdict(int),
        'file_metrics': [],
        'by_folder': defaultdict(lambda: {
            'files': 0,
            'loc': 0,
            'sloc': 0,
            'code': 0,
            'comments': 0,
            'blank': 0,
            'complexity': 0,
            'maintainability': 0,
            'halstead_volume': 0,
            'halstead_bugs': 0
        })
    }
    
    for file_path in python_files:
        # Skip __pycache__ and other generated files
        if '__pycache__' in str(file_path) or 'deprecated' in str(file_path):
            continue
        
        logger.debug(f"Analyzing {file_path}")
        
        # Analyze with radon
        radon_metrics = analyze_file_with_radon(file_path)
        
        # Analyze with pygount
        pygount_metrics = analyze_file_with_pygount(file_path)
        
        if radon_metrics and pygount_metrics:
            total_metrics['files_analyzed'] += 1
            
            # Get folder (top-level directory)
            rel_path = file_path.relative_to(repo_path)
            folder = str(rel_path.parts[0]) if rel_path.parts else 'root'
            
            # Aggregate radon metrics
            total_metrics['total_loc'] += radon_metrics['raw']['loc']
            total_metrics['total_sloc'] += radon_metrics['raw']['sloc']
            total_metrics['total_comments'] += radon_metrics['raw']['comments']
            total_metrics['total_blank'] += radon_metrics['raw']['blank']
            total_metrics['total_complexity'] += radon_metrics['complexity']['total']
            total_metrics['avg_maintainability'] += radon_metrics['maintainability']['index']
            
            if radon_metrics['halstead']:
                total_metrics['total_halstead_volume'] += radon_metrics['halstead']['volume']
                total_metrics['total_halstead_bugs'] += radon_metrics['halstead']['bugs']
            
            # Aggregate pygount metrics
            total_metrics['total_code'] += pygount_metrics['code_count']
            
            # Aggregate by folder
            folder_metrics = total_metrics['by_folder'][folder]
            folder_metrics['files'] += 1
            folder_metrics['loc'] += radon_metrics['raw']['loc']
            folder_metrics['sloc'] += radon_metrics['raw']['sloc']
            folder_metrics['code'] += pygount_metrics['code_count']
            folder_metrics['comments'] += radon_metrics['raw']['comments']
            folder_metrics['blank'] += radon_metrics['raw']['blank']
            folder_metrics['complexity'] += radon_metrics['complexity']['total']
            folder_metrics['maintainability'] += radon_metrics['maintainability']['index']
            if radon_metrics['halstead']:
                folder_metrics['halstead_volume'] += radon_metrics['halstead']['volume']
                folder_metrics['halstead_bugs'] += radon_metrics['halstead']['bugs']
            
            # Complexity distribution
            avg_cc = radon_metrics['complexity']['average']
            if avg_cc <= 5:
                total_metrics['complexity_distribution']['simple'] += 1
            elif avg_cc <= 10:
                total_metrics['complexity_distribution']['moderate'] += 1
            elif avg_cc <= 20:
                total_metrics['complexity_distribution']['complex'] += 1
            else:
                total_metrics['complexity_distribution']['very_complex'] += 1
            
            # Maintainability distribution
            mi_rank = radon_metrics['maintainability']['rank']
            total_metrics['maintainability_distribution'][mi_rank] += 1
            
            # Store file-level metrics
            total_metrics['file_metrics'].append({
                'file': str(file_path.relative_to(repo_path)),
                'radon': radon_metrics,
                'pygount': pygount_metrics
            })
    
    # Calculate averages
    if total_metrics['files_analyzed'] > 0:
        total_metrics['avg_complexity'] = total_metrics['total_complexity'] / total_metrics['files_analyzed']
        total_metrics['avg_maintainability'] = total_metrics['avg_maintainability'] / total_metrics['files_analyzed']
    
    # Calculate folder averages
    for folder, metrics in total_metrics['by_folder'].items():
        if metrics['files'] > 0:
            metrics['avg_complexity'] = metrics['complexity'] / metrics['files']
            metrics['avg_maintainability'] = metrics['maintainability'] / metrics['files']
    
    # Convert defaultdict to regular dict for JSON serialization
    total_metrics['by_folder'] = dict(total_metrics['by_folder'])
    
    logger.success(f"Analysis complete: {total_metrics['files_analyzed']} files analyzed")
    
    return total_metrics


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Enhanced Metrics Generation")
    logger.info("=" * 60)
    
    # Get repo path
    repo_path = settings.advisor_data_path
    logger.info(f"Repository path: {repo_path}")
    
    # Analyze codebase
    metrics = analyze_codebase(repo_path)
    
    # Save to cache
    cache_dir = settings.advisor_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = cache_dir / "enhanced_metrics.json"
    logger.info(f"Saving metrics to {output_file}")
    
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("METRICS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Files analyzed: {metrics['files_analyzed']}")
    logger.info(f"Total lines: {metrics['total_loc']:,}")
    logger.info(f"Source lines (SLOC): {metrics['total_sloc']:,}")
    logger.info(f"Code lines: {metrics['total_code']:,}")
    logger.info(f"Comment lines: {metrics['total_comments']:,}")
    logger.info(f"Blank lines: {metrics['total_blank']:,}")
    logger.info(f"Average complexity: {metrics['avg_complexity']:.2f}")
    logger.info(f"Average maintainability: {metrics['avg_maintainability']:.2f}")
    logger.info(f"Total Halstead volume: {metrics['total_halstead_volume']:.0f}")
    logger.info(f"Estimated bugs: {metrics['total_halstead_bugs']:.2f}")
    
    logger.info("\nComplexity Distribution:")
    for level, count in metrics['complexity_distribution'].items():
        logger.info(f"  {level}: {count} files")
    
    logger.info("\nMaintainability Distribution:")
    for rank, count in metrics['maintainability_distribution'].items():
        logger.info(f"  Rank {rank}: {count} files")
    
    # Print folder breakdown
    logger.info("\n" + "=" * 60)
    logger.info("METRICS BY FOLDER")
    logger.info("=" * 60)
    
    # Sort folders by lines of code
    sorted_folders = sorted(
        metrics['by_folder'].items(),
        key=lambda x: x[1]['loc'],
        reverse=True
    )
    
    for folder, folder_metrics in sorted_folders[:10]:  # Top 10 folders
        logger.info(f"\n{folder}:")
        logger.info(f"  Files: {folder_metrics['files']}")
        logger.info(f"  Lines: {folder_metrics['loc']:,}")
        logger.info(f"  Code: {folder_metrics['code']:,}")
        logger.info(f"  Comments: {folder_metrics['comments']:,}")
        logger.info(f"  Avg Complexity: {folder_metrics.get('avg_complexity', 0):.1f}")
        logger.info(f"  Avg Maintainability: {folder_metrics.get('avg_maintainability', 0):.1f}")
    
    if len(sorted_folders) > 10:
        logger.info(f"\n... and {len(sorted_folders) - 10} more folders")
    
    logger.success(f"\n✓ Enhanced metrics saved to {output_file}")


if __name__ == "__main__":
    main()