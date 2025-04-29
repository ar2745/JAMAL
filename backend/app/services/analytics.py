import asyncio
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from event_loop import get_event_loop
from fastapi import WebSocket


class AnalyticsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._websocket_clients: Set[WebSocket] = set()
        self._client_topics: Dict[WebSocket, Set[str]] = defaultdict(set)
        self._update_lock = threading.Lock()
        
        # Get the configured event loop
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
        # Reset all analytics data on startup
        self._reset_analytics_data()
        
        # Start cleanup and broadcast threads
        self._cleanup_thread = threading.Thread(target=self._run_cleanup, daemon=True)
        self._cleanup_thread.start()
        self._broadcast_thread = threading.Thread(target=self._run_broadcast, daemon=True)
        self._broadcast_thread.start()

        # In-memory storage for analytics data
        self._chat_stats = defaultdict(lambda: {
            'message_count': 0,
            'last_activity': None,
            'document_count': 0,
            'link_count': 0,
            'active_users': set(),
            'message_history': [],
            'avg_response_time': [],
            'completion_status': defaultdict(int),  # 'completed', 'abandoned'
            'topics': defaultdict(int),  # Topic/intent tracking
            'satisfaction_scores': []  # User feedback scores
        })
        self._document_stats = defaultdict(lambda: {
            'count': 0,
            'total_size': 0,
            'types': defaultdict(int),
            'upload_history': [],
            'processing_times': [],
            'success_rate': {'success': 0, 'failure': 0},
            'access_count': defaultdict(int),  # Document reuse tracking
            'search_queries': []  # Search terms used
        })
        self._link_stats = defaultdict(lambda: {
            'count': 0,
            'domains': defaultdict(int),
            'share_history': [],
            'health_status': defaultdict(lambda: {'active': True, 'last_check': None}),
            'access_patterns': [],
            'processing_times': []
        })
        self._usage_stats = {
            'daily_active': set(),
            'weekly_active': set(),
            'monthly_active': set(),
            'peak_hours': [0] * 24,
            'concurrent_users': 0,
            'response_times': [],
            'error_rates': defaultdict(int),
            'session_durations': [],
            'feature_usage': defaultdict(int),
            'retention': {
                'daily': defaultdict(set),
                'weekly': defaultdict(set),
                'monthly': defaultdict(set)
            }
        }

    def _reset_analytics_data(self):
        """Reset all analytics data to initial state."""
        self._chat_stats = defaultdict(lambda: {
            'message_count': 0,
            'last_activity': None,
            'document_count': 0,
            'link_count': 0,
            'active_users': set(),
            'message_history': [],
            'avg_response_time': [],
            'completion_status': defaultdict(int),
            'topics': defaultdict(int),
            'satisfaction_scores': []
        })
        self._document_stats = defaultdict(lambda: {
            'count': 0,
            'total_size': 0,
            'types': defaultdict(int),
            'upload_history': [],  # Explicitly reset upload history
            'processing_times': [],
            'success_rate': {'success': 0, 'failure': 0},
            'access_count': defaultdict(int),
            'search_queries': []
        })
        self._link_stats = defaultdict(lambda: {
            'count': 0,
            'domains': defaultdict(int),
            'share_history': [],  # Explicitly reset share history
            'health_status': defaultdict(lambda: {'active': True, 'last_check': None}),
            'access_patterns': [],
            'processing_times': []
        })
        self._usage_stats = {
            'daily_active': set(),
            'weekly_active': set(),
            'monthly_active': set(),
            'peak_hours': [0] * 24,
            'concurrent_users': 0,
            'response_times': [],
            'error_rates': defaultdict(int),
            'session_durations': [],
            'feature_usage': defaultdict(int),
            'retention': {
                'daily': defaultdict(set),
                'weekly': defaultdict(set),
                'monthly': defaultdict(set)
            }
        }
        
        # Start cleanup and broadcast threads
        self._cleanup_thread = threading.Thread(target=self._run_cleanup, daemon=True)
        self._cleanup_thread.start()
        self._broadcast_thread = threading.Thread(target=self._run_broadcast, daemon=True)
        self._broadcast_thread.start()

    def _run_cleanup(self):
        """Run cleanup in a separate thread."""
        asyncio.run(self._periodic_cleanup())

    def _run_broadcast(self):
        """Run broadcast in a separate thread."""
        asyncio.run(self._periodic_broadcast())

    async def _periodic_cleanup(self):
        """Periodically clean up old data."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run cleanup every hour
                self.cleanup_old_data()
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _periodic_broadcast(self):
        """Periodically broadcast analytics updates to connected clients."""
        while True:
            try:
                await asyncio.sleep(5)  # Broadcast every 5 seconds
                # Broadcast updates to all connected clients
                for websocket in list(self._websocket_clients):
                    try:
                        await self._send_analytics_update(websocket)
                    except Exception as e:
                        self.logger.error(f"Error sending update to client: {e}")
                        await self.unregister_websocket(websocket)
            except Exception as e:
                self.logger.error(f"Error in periodic broadcast: {e}")
                await asyncio.sleep(1)  # Wait before retrying

    async def register_websocket(self, websocket: WebSocket):
        """Register a new WebSocket client."""
        self._websocket_clients.add(websocket)
        self._client_topics[websocket] = set()  # Initialize empty topic set
        self.logger.info("New WebSocket client registered")

    async def unregister_websocket(self, websocket: WebSocket):
        """Unregister a WebSocket client."""
        self._websocket_clients.discard(websocket)
        self._client_topics.pop(websocket, None)
        self.logger.info("WebSocket client unregistered")

    async def subscribe_to_topics(self, websocket: WebSocket, topics: List[str]):
        """Subscribe a WebSocket client to specific analytics topics."""
        if websocket in self._client_topics:
            self._client_topics[websocket].update(topics)
            self.logger.info(f"Client subscribed to topics: {topics}")

    async def unsubscribe_from_topics(self, websocket: WebSocket, topics: List[str]):
        """Unsubscribe a WebSocket client from specific analytics topics."""
        if websocket in self._client_topics:
            self._client_topics[websocket].difference_update(topics)
            self.logger.info(f"Client unsubscribed from topics: {topics}")

    async def broadcast_update(self, update_type: str, data: Dict):
        """Broadcast an update to all subscribed WebSocket clients."""
        disconnected_clients = set()

        for websocket in self._websocket_clients:
            try:
                # Check if client is subscribed to this update type
                if not self._client_topics[websocket] or update_type in self._client_topics[websocket]:
                    await websocket.send_json({
                        "type": update_type,
                        "data": data
                    })
            except Exception as e:
                self.logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(websocket)

        # Clean up disconnected clients
        for websocket in disconnected_clients:
            await self.unregister_websocket(websocket)

    def _serialize_for_json(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, defaultdict):
            return dict(obj)
        elif isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        return obj

    async def _send_analytics_update(self, websocket: WebSocket):
        """Send analytics update to a specific WebSocket client."""
        try:
            # Get all stats
            data = {
                'chatStats': self._serialize_for_json(self.get_chat_statistics()),
                'documentStats': self._serialize_for_json(self.get_document_statistics()),
                'linkStats': self._serialize_for_json(self.get_link_statistics()),
                'usageStats': self._serialize_for_json(self.get_usage_statistics()),
                'enhancedStats': self._serialize_for_json(self.get_enhanced_statistics())
            }

            # Filter based on subscribed topics
            if self._client_topics[websocket]:
                data = {k: v for k, v in data.items() 
                       if any(topic in k.lower() for topic in self._client_topics[websocket])}

            await websocket.send_json(data)
        except Exception as e:
            self.logger.error(f"Error sending analytics update: {e}")
            await self.unregister_websocket(websocket)

    def _broadcast_analytics_update(self):
        """Broadcast analytics update to all connected clients."""
        if not self._websocket_clients:
            return

        data = {
            'chatStats': self._serialize_for_json(self.get_chat_statistics()),
            'documentStats': self._serialize_for_json(self.get_document_statistics()),
            'linkStats': self._serialize_for_json(self.get_link_statistics()),
            'usageStats': self._serialize_for_json(self.get_usage_statistics()),
            'enhancedStats': self._serialize_for_json(self.get_enhanced_statistics())
        }

        # Create tasks for each client
        for websocket in list(self._websocket_clients):
            try:
                asyncio.run(websocket.send_json(data))
            except Exception as e:
                self.logger.error(f"Error broadcasting to client: {e}")
                self._websocket_clients.remove(websocket)

    def track_chat_activity(self, chat_id: str, message_count: int = 1, user_id: Optional[str] = None):
        """Track chat activity and message count."""
        with self._update_lock:
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
        
        # Track upload history with filename
        doc_stats['upload_history'].append({
            'id': f"doc_{datetime.now().timestamp()}",
            'name': f"Document {doc_stats['count']}",
            'timestamp': datetime.now(),
            'user_id': user_id,
            'file_type': file_type,
            'file_size': file_size
        })

    def track_link_share(self, chat_id: str, domain: str, user_id: Optional[str] = None, title: Optional[str] = None, url: Optional[str] = None):
        """Track link sharing statistics."""
        chat_stats = self._chat_stats[chat_id]
        link_stats = self._link_stats[chat_id]
        
        chat_stats['link_count'] += 1
        link_stats['count'] += 1
        link_stats['domains'][domain] += 1
        
        # Track share history with detailed information
        link_stats['share_history'].append({
            'id': f"link_{datetime.now().timestamp()}",
            'title': title or f"Link from {domain}",
            'url': url or f"https://{domain}",
            'timestamp': datetime.now(),
            'user_id': user_id,
            'domain': domain
        })
        
        # Ensure the share history is sorted by timestamp (newest first)
        link_stats['share_history'].sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Keep only the most recent 100 shares
        if len(link_stats['share_history']) > 100:
            link_stats['share_history'] = link_stats['share_history'][:100]

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

    def track_chat_completion(self, chat_id: str, status: str, response_time: float, topic: Optional[str] = None):
        """Track chat completion status and response metrics."""
        stats = self._chat_stats[chat_id]
        stats['completion_status'][status] += 1
        stats['avg_response_time'].append(response_time)
        if topic:
            stats['topics'][topic] += 1

    def track_document_processing(self, chat_id: str, doc_id: str, success: bool, processing_time: float):
        """Track document processing metrics."""
        stats = self._document_stats[chat_id]
        if success:
            stats['success_rate']['success'] += 1
        else:
            stats['success_rate']['failure'] += 1
        stats['processing_times'].append(processing_time)

    def track_document_access(self, chat_id: str, doc_id: str, search_query: Optional[str] = None):
        """Track document access and search patterns."""
        stats = self._document_stats[chat_id]
        stats['access_count'][doc_id] += 1
        if search_query:
            stats['search_queries'].append({
                'timestamp': datetime.now(),
                'query': search_query,
                'doc_id': doc_id
            })

    def track_link_health(self, chat_id: str, domain: str, is_active: bool):
        """Track link health status."""
        stats = self._link_stats[chat_id]
        stats['health_status'][domain] = {
            'active': is_active,
            'last_check': datetime.now()
        }

    def track_user_session(self, user_id: str, duration: float, features_used: List[str]):
        """Track user session metrics."""
        self._usage_stats['session_durations'].append({
            'user_id': user_id,
            'duration': duration,
            'timestamp': datetime.now()
        })
        for feature in features_used:
            self._usage_stats['feature_usage'][feature] += 1

    def track_user_retention(self, user_id: str):
        """Track user retention metrics."""
        today = datetime.now().date()
        week = today.isocalendar()[1]
        month = today.month

        self._usage_stats['retention']['daily'][today].add(user_id)
        self._usage_stats['retention']['weekly'][week].add(user_id)
        self._usage_stats['retention']['monthly'][month].add(user_id)

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
                {
                    'id': share['id'],
                    'title': share['title'],
                    'url': share['url'],
                    'timestamp': share['timestamp'].isoformat()
                }
                for share in stats['share_history']
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
                {
                    'id': share['id'],
                    'title': share['title'],
                    'url': share['url'],
                    'timestamp': share['timestamp'].isoformat()
                }
                for share in stats['share_history']
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

    def get_enhanced_statistics(self) -> Dict:
        """Get enhanced analytics including new metrics."""
        stats = {
            'chat_metrics': {
                'avg_response_time': self._calculate_average([
                    rt for stats in self._chat_stats.values()
                    for rt in stats['avg_response_time']
                ]),
                'completion_rates': self._aggregate_completion_rates(),
                'top_topics': self._get_top_items(
                    [topics for stats in self._chat_stats.values() 
                     for topics in stats['topics'].items()],
                    limit=5
                )
            },
            'document_metrics': {
                'processing_success_rate': self._calculate_success_rate(),
                'popular_types': self._get_top_items(
                    [t for stats in self._document_stats.values() 
                     for t in stats['types'].items()],
                    limit=5
                ),
                'most_accessed': self._get_top_items(
                    [acc for stats in self._document_stats.values() 
                     for acc in stats['access_count'].items()],
                    limit=5
                )
            },
            'user_metrics': {
                'retention_rates': self._calculate_retention_rates(),
                'avg_session_duration': self._calculate_average(
                    [s['duration'] for s in self._usage_stats['session_durations']]
                ),
                'popular_features': self._get_top_items(
                    self._usage_stats['feature_usage'].items(),
                    limit=5
                )
            }
        }
        return stats

    def _calculate_average(self, values: List[float]) -> float:
        """Calculate average of values."""
        return sum(values) / len(values) if values else 0

    def _get_top_items(self, items: List[Tuple[str, int]], limit: int = 5) -> Dict[str, int]:
        """Get top N items by count."""
        return dict(sorted(items, key=lambda x: x[1], reverse=True)[:limit])

    def _aggregate_completion_rates(self) -> Dict[str, float]:
        """Calculate chat completion rates."""
        total_completions = sum(
            sum(status.values()) 
            for stats in self._chat_stats.values() 
            for status in [stats['completion_status']]
        )
        if not total_completions:
            return {'completed': 0, 'abandoned': 0}

        completed = sum(
            status['completed'] 
            for stats in self._chat_stats.values() 
            for status in [stats['completion_status']]
        )
        return {
            'completed': completed / total_completions,
            'abandoned': (total_completions - completed) / total_completions
        }

    def _calculate_success_rate(self) -> float:
        """Calculate document processing success rate."""
        total_processed = sum(
            stats['success_rate']['success'] + stats['success_rate']['failure']
            for stats in self._document_stats.values()
        )
        if not total_processed:
            return 0
        
        successful = sum(
            stats['success_rate']['success']
            for stats in self._document_stats.values()
        )
        return successful / total_processed

    def _calculate_retention_rates(self) -> Dict[str, float]:
        """Calculate user retention rates."""
        today = datetime.now().date()
        week = today.isocalendar()[1]
        month = today.month

        return {
            'daily': len(self._usage_stats['retention']['daily'][today]) / 
                    len(self._usage_stats['daily_active']) if self._usage_stats['daily_active'] else 0,
            'weekly': len(self._usage_stats['retention']['weekly'][week]) / 
                     len(self._usage_stats['weekly_active']) if self._usage_stats['weekly_active'] else 0,
            'monthly': len(self._usage_stats['retention']['monthly'][month]) / 
                      len(self._usage_stats['monthly_active']) if self._usage_stats['monthly_active'] else 0
        }

    def cleanup_old_data(self, days: int = 30):
        """Clean up data older than specified days."""
        with self._update_lock:
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