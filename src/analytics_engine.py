"""
Analytics engine for computing insights and trends from email data.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .analytics_db import get_analytics_db
from .config import JOB_CATEGORIES


class AnalyticsEngine:
    """Compute analytics and insights from email data"""
    
    def __init__(self, llm=None):
        """
        Initialize analytics engine
        
        Args:
            llm: Optional LLM instance for generating insights
        """
        self.db = get_analytics_db()
        self.llm = llm
    
    def get_summary_statistics(self, days: int = 30) -> Dict:
        """
        Get comprehensive summary statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with summary stats
        """
        emails = self.db.get_emails_by_date_range(days)
        category_counts = self.db.get_category_counts(days)
        important_stats = self.db.get_important_email_stats(days)
        top_senders = self.db.get_top_senders(days, limit=5)
        
        total_emails = len(emails)
        
        # Calculate averages
        avg_per_day = total_emails / days if days > 0 else 0
        
        # Find most common category
        most_common_category = max(category_counts.items(), key=lambda x: x[1]) if category_counts else ("None", 0)
        
        return {
            'period_days': days,
            'total_emails': total_emails,
            'average_per_day': round(avg_per_day, 1),
            'category_breakdown': category_counts,
            'most_common_category': most_common_category[0],
            'most_common_count': most_common_category[1],
            'important_emails': important_stats['important_emails'],
            'important_percentage': round(important_stats['important_percentage'], 1),
            'top_senders': top_senders,
            'all_time_total': self.db.get_total_email_count()
        }
    
    def get_email_volume_trends(self, days: int = 30) -> Dict:
        """
        Get email volume trends over time
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data
        """
        daily_volume = self.db.get_daily_volume(days)
        daily_by_category = self.db.get_daily_volume_by_category(days)
        
        # Fill in missing dates with zero counts
        start_date = datetime.now() - timedelta(days=days)
        date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days + 1)]
        
        # Create complete daily volume with zeros for missing dates
        volume_dict = {date: 0 for date in date_range}
        for date, count in daily_volume:
            if date in volume_dict:
                volume_dict[date] = count
        
        complete_daily_volume = [(date, volume_dict[date]) for date in sorted(volume_dict.keys())]
        
        # Calculate trend (simple: compare first half vs second half)
        if len(complete_daily_volume) >= 2:
            midpoint = len(complete_daily_volume) // 2
            first_half_avg = sum(count for _, count in complete_daily_volume[:midpoint]) / midpoint
            second_half_avg = sum(count for _, count in complete_daily_volume[midpoint:]) / (len(complete_daily_volume) - midpoint)
            
            if first_half_avg > 0:
                trend_percentage = ((second_half_avg - first_half_avg) / first_half_avg) * 100
            else:
                trend_percentage = 0
            
            trend_direction = "increasing" if trend_percentage > 5 else ("decreasing" if trend_percentage < -5 else "stable")
        else:
            trend_percentage = 0
            trend_direction = "insufficient data"
        
        return {
            'daily_volume': complete_daily_volume,
            'daily_by_category': daily_by_category,
            'trend_percentage': round(trend_percentage, 1),
            'trend_direction': trend_direction
        }
    
    def get_category_distribution(self, days: int = 30) -> Dict:
        """
        Get percentage distribution of email categories
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with category percentages
        """
        category_counts = self.db.get_category_counts(days)
        total = sum(category_counts.values())
        
        if total == 0:
            return {'categories': {}, 'total': 0}
        
        distribution = {
            category: {
                'count': count,
                'percentage': round((count / total) * 100, 1)
            }
            for category, count in category_counts.items()
        }
        
        # Sort by count
        sorted_distribution = dict(sorted(distribution.items(), key=lambda x: x[1]['count'], reverse=True))
        
        return {
            'categories': sorted_distribution,
            'total': total
        }
    
    def get_success_metrics(self, days: int = 30) -> Dict:
        """
        Calculate job search success metrics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with success metrics
        """
        category_counts = self.db.get_category_counts(days)
        
        # Map category labels to keys for easier lookup
        label_to_key = {v['label']: k for k, v in JOB_CATEGORIES.items()}
        
        # Get counts for specific categories
        applications = sum(count for label, count in category_counts.items() 
                          if label_to_key.get(label) == 'application_confirmed')
        interviews = sum(count for label, count in category_counts.items() 
                        if label_to_key.get(label) in ['interview_request', 'interview_reminder'])
        offers = sum(count for label, count in category_counts.items() 
                    if label_to_key.get(label) == 'offer')
        rejections = sum(count for label, count in category_counts.items() 
                        if label_to_key.get(label) == 'rejected')
        assessments = sum(count for label, count in category_counts.items() 
                         if label_to_key.get(label) == 'assessment')
        
        # Calculate conversion rates
        interview_rate = (interviews / applications * 100) if applications > 0 else 0
        offer_rate = (offers / interviews * 100) if interviews > 0 else 0
        overall_success_rate = (offers / applications * 100) if applications > 0 else 0
        
        return {
            'applications': applications,
            'interviews': interviews,
            'offers': offers,
            'rejections': rejections,
            'assessments': assessments,
            'interview_rate': round(interview_rate, 1),
            'offer_rate': round(offer_rate, 1),
            'overall_success_rate': round(overall_success_rate, 1)
        }
    
    def generate_insights(self, days: int = 30) -> str:
        """
        Generate AI-powered insights from email data
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Natural language insights text
        """
        if not self.llm:
            return "AI insights unavailable (LLM not configured)"
        
        # Gather data
        summary = self.get_summary_statistics(days)
        trends = self.get_email_volume_trends(days)
        distribution = self.get_category_distribution(days)
        success = self.get_success_metrics(days)
        
        # Create prompt for LLM
        prompt = f"""
You are an AI career advisor analyzing email data from a job seeker's inbox over the last {days} days.

EMAIL STATISTICS:
- Total emails: {summary['total_emails']}
- Average per day: {summary['average_per_day']}
- Important emails: {summary['important_emails']} ({summary['important_percentage']}%)
- Most common category: {summary['most_common_category']} ({summary['most_common_count']} emails)

CATEGORY BREAKDOWN:
{self._format_category_breakdown(distribution['categories'])}

EMAIL VOLUME TREND:
- Direction: {trends['trend_direction']}
- Change: {trends['trend_percentage']}%

JOB SEARCH METRICS:
- Applications confirmed: {success['applications']}
- Interviews: {success['interviews']}
- Offers: {success['offers']}
- Rejections: {success['rejections']}
- Interview rate: {success['interview_rate']}%
- Offer rate: {success['offer_rate']}%

Based on this data, provide 3-5 actionable insights and recommendations for the job seeker. 
Be specific, encouraging, and data-driven. Keep it concise (max 200 words).
"""
        
        try:
            response = self.llm.invoke(prompt)
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
        except Exception as e:
            return f"Error generating insights: {e}"
    
    def _format_category_breakdown(self, categories: Dict) -> str:
        """Format category breakdown for prompt"""
        lines = []
        for category, data in categories.items():
            lines.append(f"  - {category}: {data['count']} ({data['percentage']}%)")
        return "\n".join(lines) if lines else "  No data"
    
    def get_peak_activity_times(self, days: int = 30) -> Dict:
        """
        Identify when most emails are received
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with peak activity analysis
        """
        emails = self.db.get_emails_by_date_range(days)
        
        if not emails:
            return {'peak_day': 'N/A', 'peak_hour': 'N/A'}
        
        # Count by day of week
        day_counts = {}
        hour_counts = {}
        
        for email in emails:
            timestamp_str = email['timestamp']
            try:
                dt = datetime.fromisoformat(timestamp_str)
                day_name = dt.strftime('%A')
                hour = dt.hour
                
                day_counts[day_name] = day_counts.get(day_name, 0) + 1
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            except:
                continue
        
        peak_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else 'N/A'
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 'N/A'
        
        return {
            'peak_day': peak_day,
            'peak_hour': f"{peak_hour}:00" if peak_hour != 'N/A' else 'N/A',
            'day_distribution': day_counts,
            'hour_distribution': hour_counts
        }
