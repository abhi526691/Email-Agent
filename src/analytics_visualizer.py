"""
Analytics visualization module for generating charts and graphs.
Uses matplotlib to create visual representations of email analytics.
"""
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import os
from .analytics_engine import AnalyticsEngine
from .config import JOB_CATEGORIES


class AnalyticsVisualizer:
    """Generate charts and visualizations for email analytics"""
    
    def __init__(self, analytics_engine: AnalyticsEngine, chart_dir: str = "charts"):
        """
        Initialize visualizer
        
        Args:
            analytics_engine: AnalyticsEngine instance
            chart_dir: Directory to save generated charts
        """
        self.engine = analytics_engine
        self.chart_dir = chart_dir
        
        # Create chart directory if it doesn't exist
        os.makedirs(chart_dir, exist_ok=True)
        
        # Color scheme matching categories
        self.category_colors = {
            'Interview 📅': '#FF6B6B',
            'Interview Reminder ⏰': '#FFA07A',
            'Job Offer 🎉': '#4ECDC4',
            'Applied ✓': '#95E1D3',
            'Rejected ❌': '#F38181',
            'Assessment 📝': '#AA96DA',
            'Follow-up 💬': '#FCBAD3',
            'Job Alert 🔔': '#FFFFD2',
            'Newsletter 📰': '#A8E6CF',
            'Spam 🗑️': '#C7CEEA',
            'Other 📧': '#DCDCDC'
        }
    
    def generate_volume_trend_chart(self, days: int = 30) -> str:
        """
        Generate line chart showing email volume over time
        
        Args:
            days: Number of days to visualize
            
        Returns:
            Path to generated chart image
        """
        trends = self.engine.get_email_volume_trends(days)
        daily_volume = trends['daily_volume']
        
        if not daily_volume:
            return self._generate_no_data_chart("No email data available")
        
        # Prepare data
        dates = [datetime.strptime(date, '%Y-%m-%d') for date, _ in daily_volume]
        counts = [count for _, count in daily_volume]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot line
        ax.plot(dates, counts, marker='o', linewidth=2, markersize=6, 
                color='#4ECDC4', label='Daily Emails')
        
        # Fill area under curve
        ax.fill_between(dates, counts, alpha=0.3, color='#4ECDC4')
        
        # Formatting
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Emails', fontsize=12, fontweight='bold')
        ax.set_title(f'Email Volume Trend (Last {days} Days)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 10)))
        plt.xticks(rotation=45)
        
        # Add trend annotation
        trend_text = f"Trend: {trends['trend_direction'].title()} ({trends['trend_percentage']:+.1f}%)"
        ax.text(0.02, 0.98, trend_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        # Save
        filepath = os.path.join(self.chart_dir, f'volume_trend_{days}d.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def generate_category_pie_chart(self, days: int = 30) -> str:
        """
        Generate pie chart showing category distribution
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Path to generated chart image
        """
        distribution = self.engine.get_category_distribution(days)
        categories = distribution['categories']
        
        if not categories:
            return self._generate_no_data_chart("No category data available")
        
        # Prepare data
        labels = list(categories.keys())
        sizes = [data['count'] for data in categories.values()]
        colors = [self.category_colors.get(label, '#CCCCCC') for label in labels]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors,
                                           autopct='%1.1f%%', startangle=90,
                                           textprops={'fontsize': 10})
        
        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(f'Email Category Distribution (Last {days} Days)', 
                     fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # Save
        filepath = os.path.join(self.chart_dir, f'category_pie_{days}d.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def generate_category_bar_chart(self, days: int = 30) -> str:
        """
        Generate horizontal bar chart comparing categories
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Path to generated chart image
        """
        distribution = self.engine.get_category_distribution(days)
        categories = distribution['categories']
        
        if not categories:
            return self._generate_no_data_chart("No category data available")
        
        # Prepare data (sorted by count)
        sorted_items = sorted(categories.items(), key=lambda x: x[1]['count'])
        labels = [item[0] for item in sorted_items]
        counts = [item[1]['count'] for item in sorted_items]
        colors = [self.category_colors.get(label, '#CCCCCC') for label in labels]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create horizontal bar chart
        bars = ax.barh(labels, counts, color=colors, edgecolor='black', linewidth=0.5)
        
        # Add value labels on bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count + max(counts) * 0.01, i, str(count),
                   va='center', fontsize=10, fontweight='bold')
        
        # Formatting
        ax.set_xlabel('Number of Emails', fontsize=12, fontweight='bold')
        ax.set_title(f'Emails by Category (Last {days} Days)', 
                     fontsize=14, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        # Save
        filepath = os.path.join(self.chart_dir, f'category_bar_{days}d.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def generate_stacked_area_chart(self, days: int = 30) -> str:
        """
        Generate stacked area chart showing category trends over time
        
        Args:
            days: Number of days to visualize
            
        Returns:
            Path to generated chart image
        """
        trends = self.engine.get_email_volume_trends(days)
        daily_by_category = trends['daily_by_category']
        
        if not daily_by_category:
            return self._generate_no_data_chart("No trend data available")
        
        # Prepare date range
        start_date = datetime.now() - timedelta(days=days)
        date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') 
                     for i in range(days + 1)]
        dates = [datetime.strptime(d, '%Y-%m-%d') for d in date_range]
        
        # Prepare data for each category
        category_data = {}
        for category, data_points in daily_by_category.items():
            counts = {date: 0 for date in date_range}
            for date, count in data_points:
                if date in counts:
                    counts[date] = count
            category_data[category] = [counts[date] for date in date_range]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Stack the areas
        categories = list(category_data.keys())
        data_matrix = [category_data[cat] for cat in categories]
        colors = [self.category_colors.get(cat, '#CCCCCC') for cat in categories]
        
        ax.stackplot(dates, *data_matrix, labels=categories, colors=colors, alpha=0.8)
        
        # Formatting
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Emails', fontsize=12, fontweight='bold')
        ax.set_title(f'Email Category Trends (Last {days} Days)', 
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 10)))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Save
        filepath = os.path.join(self.chart_dir, f'stacked_area_{days}d.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def generate_success_metrics_chart(self, days: int = 30) -> str:
        """
        Generate funnel chart for job search success metrics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Path to generated chart image
        """
        metrics = self.engine.get_success_metrics(days)
        
        # Prepare data
        stages = ['Applications', 'Interviews', 'Offers']
        values = [metrics['applications'], metrics['interviews'], metrics['offers']]
        colors = ['#95E1D3', '#FF6B6B', '#4ECDC4']
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create horizontal bar chart (funnel-style)
        bars = ax.barh(stages, values, color=colors, edgecolor='black', linewidth=1.5)
        
        # Add value labels and percentages
        for i, (bar, value) in enumerate(zip(bars, values)):
            ax.text(value + max(values) * 0.02, i, f'{value}',
                   va='center', fontsize=12, fontweight='bold')
        
        # Add conversion rates
        if metrics['applications'] > 0:
            ax.text(0.98, 0.95, f"Interview Rate: {metrics['interview_rate']:.1f}%",
                   transform=ax.transAxes, fontsize=11, ha='right',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
        if metrics['interviews'] > 0:
            ax.text(0.98, 0.88, f"Offer Rate: {metrics['offer_rate']:.1f}%",
                   transform=ax.transAxes, fontsize=11, ha='right',
                   bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
        
        # Formatting
        ax.set_xlabel('Count', fontsize=12, fontweight='bold')
        ax.set_title(f'Job Search Success Funnel (Last {days} Days)', 
                     fontsize=14, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        # Save
        filepath = os.path.join(self.chart_dir, f'success_funnel_{days}d.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def _generate_no_data_chart(self, message: str) -> str:
        """
        Generate a placeholder chart when no data is available
        
        Args:
            message: Message to display
            
        Returns:
            Path to generated chart image
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, message, ha='center', va='center',
                fontsize=16, fontweight='bold', color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        filepath = os.path.join(self.chart_dir, 'no_data.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def cleanup_old_charts(self, max_age_hours: int = 24):
        """
        Remove old chart files to save space
        
        Args:
            max_age_hours: Maximum age of charts to keep
        """
        if not os.path.exists(self.chart_dir):
            return
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for filename in os.listdir(self.chart_dir):
            filepath = os.path.join(self.chart_dir, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_time:
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        print(f"Error removing old chart {filename}: {e}")
