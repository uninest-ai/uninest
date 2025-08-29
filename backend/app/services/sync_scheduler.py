import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List
import logging
import os
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.multi_source_fetcher import MultiSourceFetcher
from app.services.realtor16_fetcher import Realtor16Fetcher
from app.models import Property, LandlordProfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PropertySyncScheduler:
    """
    Automated property data synchronization scheduler
    Handles periodic updates from multiple real estate APIs
    """
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.sync_config = {
            'daily_sync_hour': 6,        # 6 AM daily sync
            'hourly_sync_minutes': 0,    # Top of the hour
            'batch_size': 25,            # Properties per sync
            'max_retries': 3,
            'cleanup_days': 30           # Remove old properties after 30 days
        }
        
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        self.is_running = True
        
        # Schedule daily comprehensive sync at 6 AM
        schedule.every().day.at("06:00").do(self._run_comprehensive_sync)
        
        # Schedule hourly incremental updates
        schedule.every().hour.at(":00").do(self._run_incremental_sync)
        
        # Schedule weekly cleanup at 3 AM on Sundays
        schedule.every().sunday.at("03:00").do(self._run_cleanup)
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_worker, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Property sync scheduler started")
        
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            
        logger.info("Property sync scheduler stopped")
        
    def _scheduler_worker(self):
        """Background worker that runs the scheduled jobs"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler worker error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes on error
                
    def _run_comprehensive_sync(self):
        """Run comprehensive daily sync from all sources"""
        logger.info("Starting comprehensive daily property sync")
        
        try:
            db_gen = get_db()
            db = next(db_gen)
            
            api_key = os.getenv("RAPIDAPI_KEY")
            if not api_key:
                logger.error("RAPIDAPI_KEY not configured")
                return
                
            fetcher = MultiSourceFetcher(api_key)
            result = fetcher.get_comprehensive_property_data(db=db, limit=50)
            
            if result['success']:
                logger.info(f"Comprehensive sync completed: {result.get('saved_count', 0)} properties saved from {len(result.get('api_sources_used', []))} sources")
                
                # Log statistics
                self._log_sync_stats(result, "comprehensive")
            else:
                logger.error(f"Comprehensive sync failed: {result.get('errors', [])}")
                
        except Exception as e:
            logger.error(f"Error in comprehensive sync: {str(e)}")
        finally:
            try:
                db.close()
            except:
                pass
                
    def _run_incremental_sync(self):
        """Run incremental hourly sync (smaller batch)"""
        logger.info("Starting incremental property sync")
        
        try:
            db_gen = get_db()
            db = next(db_gen)
            
            api_key = os.getenv("RAPIDAPI_KEY")
            if not api_key:
                logger.warning("RAPIDAPI_KEY not configured for incremental sync")
                return
                
            # Use primary source only for incremental updates
            fetcher = Realtor16Fetcher(api_key)
            result = fetcher.get_real_properties_with_landlords(db=db, limit=15)
            
            if result['success']:
                logger.info(f"Incremental sync completed: {result.get('saved_count', 0)} properties saved")
                
                # Log statistics
                self._log_sync_stats(result, "incremental")
            else:
                logger.warning(f"Incremental sync had issues: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in incremental sync: {str(e)}")
        finally:
            try:
                db.close()
            except:
                pass
                
    def _run_cleanup(self):
        """Run weekly cleanup of old properties"""
        logger.info("Starting weekly property cleanup")
        
        try:
            db_gen = get_db()
            db = next(db_gen)
            
            # Mark old properties as inactive
            cutoff_date = datetime.utcnow() - timedelta(days=self.sync_config['cleanup_days'])
            
            old_properties = db.query(Property).filter(
                Property.created_at < cutoff_date,
                Property.is_active == True
            ).all()
            
            cleanup_count = 0
            for prop in old_properties:
                prop.is_active = False
                cleanup_count += 1
                
            db.commit()
            
            logger.info(f"Cleanup completed: {cleanup_count} old properties marked as inactive")
            
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")
            db.rollback()
        finally:
            try:
                db.close()
            except:
                pass
                
    def _log_sync_stats(self, result: Dict, sync_type: str):
        """Log detailed sync statistics"""
        stats = {
            'sync_type': sync_type,
            'timestamp': datetime.utcnow().isoformat(),
            'total_fetched': result.get('total_fetched', 0),
            'saved_count': result.get('saved_count', 0),
            'created_landlords': result.get('created_landlords', 0),
            'api_sources_used': result.get('api_sources_used', []),
            'errors': result.get('errors', [])
        }
        
        logger.info(f"Sync Stats [{sync_type}]: {stats}")
        
        # Could be extended to save to database or external monitoring system
        
    def get_sync_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'next_comprehensive_sync': schedule.next_run(),
            'scheduled_jobs': len(schedule.jobs),
            'config': self.sync_config
        }
        
    def force_sync_now(self, sync_type: str = "incremental") -> Dict:
        """Manually trigger a sync operation"""
        logger.info(f"Manual {sync_type} sync triggered")
        
        try:
            if sync_type == "comprehensive":
                self._run_comprehensive_sync()
            elif sync_type == "cleanup":
                self._run_cleanup()
            else:
                self._run_incremental_sync()
                
            return {
                'success': True,
                'message': f'{sync_type.title()} sync completed',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Manual sync failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global scheduler instance
property_scheduler = PropertySyncScheduler()

# Startup functions
def start_property_sync():
    """Start the property synchronization scheduler"""
    property_scheduler.start_scheduler()
    
def stop_property_sync():
    """Stop the property synchronization scheduler"""
    property_scheduler.stop_scheduler()
    
def get_scheduler_status():
    """Get scheduler status"""
    return property_scheduler.get_sync_status()
    
def manual_sync(sync_type: str = "incremental"):
    """Manually trigger a sync"""
    return property_scheduler.force_sync_now(sync_type)