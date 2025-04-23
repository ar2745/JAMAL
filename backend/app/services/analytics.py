import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional, Set


class AnalyticsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # In-memory storage for analytics data
        self._chat_stats = defaultdict(lambda: {
            'message_count': 0,
            'last_activity': None,
            'document_count': 0,
            'link_count': 0,
            'active_users': set(),
            'message_history': []
        })
        self._document_stats = defaultdict(lambda: {
            'count': 0,
            'total_size': 0,
            'types': defaultdict(int),
            'upload_history': []
        })
        self._link_stats = defaultdict(lambda: {
            'count': 0,
            'domains': defaultdict(int),
            'share_history': []
        })
        self._usage_stats = {
            'daily_active': set(),
            'weekly_active': set(),
            'monthly_active': set(),
            'peak_hours': [0] * 24,
            'concurrent_users': 0,
            'response_times': [],
            'error_rates': defaultdict(int)
        }
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()

    def _periodic_cleanup(self):
        """Periodically clean up old data."""
        while True:
            self.cleanup_old_data()
            time.sleep(3600)  # Run cleanup every hour

    def track_chat_activity(self, chat_id: str, message_count: int = 1, user_id: Optional[str] = None):
        """Track chat activity and message count."""
        stats = self._chat_stats[chat_id]
        stats['message_count'] += message_count
        stats['last_activity'] = datetime.now()
        
        if user_id:
            stats['active_users'].add(user_id)
            
        # Track message history
        stats['message_history'].append({
            'timestamp': datetime.now(),
            'user_id': user_id,
            'count': message_count
        })

    def track_document_upload(self, chat_id: str, file_type: str, file_size: int, user_id: Optional[str] = None):
        """Track document upload statistics."""
        chat_stats = self._chat_stats[chat_id]
        doc_stats = self._document_stats[chat_id]
        
        chat_stats['document_count'] += 1
        doc_stats['count'] += 1
        doc_stats['total_size'] += file_size
        doc_stats['types'][file_type] += 1
        
        # Track upload history
        doc_stats['upload_history'].append({
            'timestamp': datetime.now(),
            'user_id': user_id,
            'file_type': file_type,
            'file_size': file_size
        })

    def track_link_share(self, chat_id: str, domain: str, user_id: Optional[str] = None):
        """Track link sharing statistics."""
        chat_stats = self._chat_stats[chat_id]
        link_stats = self._link_stats[chat_id]
        
        chat_stats['link_count'] += 1
        link_stats['count'] += 1
        link_stats['domains'][domain] += 1
        
        # Track share history
        link_stats['share_history'].append({
            'timestamp': datetime.now(),
            'user_id': user_id,
            'domain': domain
        })

    def track_user_activity(self, user_id: str):
        """Track user activity for engagement metrics."""
        now = datetime.now()
        
        # Update daily active users
        self._usage_stats['daily_active'].add(user_id)
        
        # Update weekly active users
        if now.weekday() == 0:  # Monday
            self._usage_stats['weekly_active'].clear()
        self._usage_stats['weekly_active'].add(user_id)
        
        # Update monthly active users
        if now.day == 1:  # First day of month
            self._usage_stats['monthly_active'].clear()
        self._usage_stats['monthly_active'].add(user_id)
        
        # Track peak hours
        hour = now.hour
        self._usage_stats['peak_hours'][hour] += 1
        
        # Update concurrent users
        self._usage_stats['concurrent_users'] = len(self._usage_stats['daily_active'])

    def track_response_time(self, response_time: float):
        """Track response time for performance monitoring."""
        self._usage_stats['response_times'].append({
            'timestamp': datetime.now(),
            'response_time': response_time
        })
        # Keep only last 1000 response times
        if len(self._usage_stats['response_times']) > 1000:
            self._usage_stats['response_times'] = self._usage_stats['response_times'][-1000:]

    def track_error(self, error_type: str):
        """Track error occurrences."""
        self._usage_stats['error_rates'][error_type] += 1

    def get_chat_statistics(self, chat_id: Optional[str] = None) -> Dict:
        """Get chat statistics for a specific chat or all chats."""
        if chat_id:
            stats = dict(self._chat_stats[chat_id])
            # Add real-time metrics
            stats['active_users_count'] = len(stats['active_users'])
            stats['recent_messages'] = [
                msg for msg in stats['message_history']
                if (datetime.now() - msg['timestamp']).total_seconds() < 3600
            ]
            return stats
        
        total_stats = {
            'total_chats': len(self._chat_stats),
            'total_messages': sum(stats['message_count'] for stats in self._chat_stats.values()),
            'total_documents': sum(stats['document_count'] for stats in self._chat_stats.values()),
            'total_links': sum(stats['link_count'] for stats in self._chat_stats.values()),
            'active_chats': sum(1 for stats in self._chat_stats.values() 
                              if stats['last_activity'] and 
                              (datetime.now() - stats['last_activity']).days < 7),
            'total_active_users': len(set().union(*[stats['active_users'] 
                                                  for stats in self._chat_stats.values()]))
        }
        return total_stats

    def get_document_statistics(self, chat_id: Optional[str] = None) -> Dict:
        """Get document statistics for a specific chat or all chats."""
        if chat_id:
            stats = dict(self._document_stats[chat_id])
            # Add real-time metrics
            stats['recent_uploads'] = [
                upload for upload in stats['upload_history']
                if (datetime.now() - upload['timestamp']).total_seconds() < 3600
            ]
            return stats
        
        total_stats = {
            'total_documents': sum(stats['count'] for stats in self._document_stats.values()),
            'total_size': sum(stats['total_size'] for stats in self._document_stats.values()),
            'types': defaultdict(int),
            'recent_uploads': []
        }
        
        for stats in self._document_stats.values():
            for file_type, count in stats['types'].items():
                total_stats['types'][file_type] += count
            # Add recent uploads from all chats
            total_stats['recent_uploads'].extend([
                upload for upload in stats['upload_history']
                if (datetime.now() - upload['timestamp']).total_seconds() < 3600
            ])
                
        return total_stats

    def get_link_statistics(self, chat_id: Optional[str] = None) -> Dict:
        """Get link statistics for a specific chat or all chats."""
        if chat_id:
            stats = dict(self._link_stats[chat_id])
            # Add real-time metrics
            stats['recent_shares'] = [
                share for share in stats['share_history']
                if (datetime.now() - share['timestamp']).total_seconds() < 3600
            ]
            return stats
        
        total_stats = {
            'total_links': sum(stats['count'] for stats in self._link_stats.values()),
            'domains': defaultdict(int),
            'recent_shares': []
        }
        
        for stats in self._link_stats.values():
            for domain, count in stats['domains'].items():
                total_stats['domains'][domain] += count
            # Add recent shares from all chats
            total_stats['recent_shares'].extend([
                share for share in stats['share_history']
                if (datetime.now() - share['timestamp']).total_seconds() < 3600
            ])
                
        return total_stats

    def get_usage_statistics(self) -> Dict:
        """Get usage statistics including active users and peak hours."""
        # Calculate average response time for last hour
        recent_response_times = [
            rt['response_time'] for rt in self._usage_stats['response_times']
            if (datetime.now() - rt['timestamp']).total_seconds() < 3600
        ]
        avg_response_time = sum(recent_response_times) / len(recent_response_times) if recent_response_times else 0
        
        return {
            'daily_active_users': len(self._usage_stats['daily_active']),
            'weekly_active_users': len(self._usage_stats['weekly_active']),
            'monthly_active_users': len(self._usage_stats['monthly_active']),
            'concurrent_users': self._usage_stats['concurrent_users'],
            'peak_hours': self._usage_stats['peak_hours'],
            'average_response_time': avg_response_time,
            'error_rates': dict(self._usage_stats['error_rates'])
        }

    def cleanup_old_data(self, days: int = 30):
        """Clean up data older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up chat stats
        for chat_id, stats in list(self._chat_stats.items()):
            if stats['last_activity'] and stats['last_activity'] < cutoff_date:
                del self._chat_stats[chat_id]
                if chat_id in self._document_stats:
                    del self._document_stats[chat_id]
                if chat_id in self._link_stats:
                    del self._link_stats[chat_id]
            else:
                # Clean up message history
                stats['message_history'] = [
                    msg for msg in stats['message_history']
                    if msg['timestamp'] > cutoff_date
                ]
        
        # Clean up document stats
        for stats in self._document_stats.values():
            stats['upload_history'] = [
                upload for upload in stats['upload_history']
                if upload['timestamp'] > cutoff_date
            ]
        
        # Clean up link stats
        for stats in self._link_stats.values():
            stats['share_history'] = [
                share for share in stats['share_history']
                if share['timestamp'] > cutoff_date
            ]
        
        # Clean up usage stats
        if datetime.now().day == 1:  # First day of month
            self._usage_stats['monthly_active'].clear()
        if datetime.now().weekday() == 0:  # Monday
            self._usage_stats['weekly_active'].clear()
        if datetime.now().hour == 0:  # Midnight
            self._usage_stats['daily_active'].clear()
            self._usage_stats['peak_hours'] = [0] * 24
            
        # Clean up response times
        self._usage_stats['response_times'] = [
            rt for rt in self._usage_stats['response_times']
            if rt['timestamp'] > cutoff_date
        ] 