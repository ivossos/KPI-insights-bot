
#!/usr/bin/env python3
"""
Simple Web Scraper using Apify
First web scraping example for IA Fiscal Capivari
"""

import asyncio
import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from src.scraping.apify_client import ApifyClientManager

class SimpleWebScraper:
    """Simple web scraper using Apify"""
    
    def __init__(self):
        # Set your Apify token
        os.environ['APIFY_API_TOKEN'] = os.getenv('APIFY_API_TOKEN', 'your_token_here')
        
        self.apify_client = ApifyClientManager()
        self.results_dir = Path("data/scraping_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    async def scrape_municipal_portals(self):
        """Scrape Betha municipal transparency portals"""
        print("🕷️ Starting web scraping with Apify...")
        
        try:
            # Test Apify connection first
            print("🔧 Testing Apify actor...")
            test_result = await self.apify_client.test_actor()
            
            if test_result['success']:
                print("✅ Apify actor test successful!")
            else:
                print(f"❌ Actor test failed: {test_result.get('error', 'Unknown error')}")
                return
            
            # Run the scraper for all portals
            print("🚀 Running full scraper...")
            run_result = await self.apify_client.run_scraper()
            
            print(f"📊 Scraper run status: {run_result['status']}")
            print(f"🕐 Started at: {run_result['started_at']}")
            
            if run_result['status'] == 'SUCCEEDED':
                print("✅ Scraping completed successfully!")
                
                # Save results
                results_file = self.results_dir / f"scraping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(run_result, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"💾 Results saved to: {results_file}")
                
                # Process results if available
                if 'results' in run_result:
                    await self.process_results(run_result['results'])
                    
            else:
                print(f"❌ Scraping failed: {run_result['status']}")
                
        except Exception as e:
            print(f"💥 Error during scraping: {str(e)}")
            
    async def scrape_specific_portal(self, portal_name):
        """Scrape a specific portal"""
        print(f"🎯 Scraping specific portal: {portal_name}")
        
        try:
            # Run scraper for specific portal
            run_result = await self.apify_client.run_scraper([portal_name])
            
            print(f"📊 Status: {run_result['status']}")
            
            if run_result['status'] == 'SUCCEEDED':
                print(f"✅ Successfully scraped {portal_name}!")
                return run_result
            else:
                print(f"❌ Failed to scrape {portal_name}")
                return None
                
        except Exception as e:
            print(f"💥 Error scraping {portal_name}: {str(e)}")
            return None
            
    async def process_results(self, results):
        """Process scraping results"""
        print("🔄 Processing scraping results...")
        
        for item in results:
            portal = item.get('portal', 'unknown')
            record_count = item.get('recordCount', 0)
            
            print(f"  📋 {portal}: {record_count} records")
            
        print("✅ Results processing completed!")
        
    async def get_scraping_history(self):
        """Get recent scraping runs"""
        print("📜 Getting scraping history...")
        
        try:
            recent_runs = await self.apify_client.get_recent_runs(limit=5)
            
            if recent_runs:
                print("Recent scraping runs:")
                for run in recent_runs:
                    status = "✅" if run['success'] else "❌"
                    duration = run['runtime_millis'] / 1000 if run['runtime_millis'] else 0
                    print(f"  {status} {run['id'][:8]}... - {run['status']} ({duration:.1f}s)")
            else:
                print("No recent runs found")
                
        except Exception as e:
            print(f"💥 Error getting history: {str(e)}")
            
    async def monitor_active_runs(self):
        """Monitor currently running scrapers"""
        print("👀 Monitoring active runs...")
        
        try:
            active_runs = await self.apify_client.monitor_runs()
            
            if active_runs:
                print("Active runs:")
                for run in active_runs:
                    duration = run['runtime_millis'] / 1000 if run['runtime_millis'] else 0
                    print(f"  🔄 {run['id'][:8]}... - {run['status']} ({duration:.1f}s)")
            else:
                print("No active runs")
                
        except Exception as e:
            print(f"💥 Error monitoring runs: {str(e)}")
            
    async def schedule_daily_scraping(self):
        """Schedule daily scraping"""
        print("⏰ Setting up daily scraping schedule...")
        
        try:
            schedule_id = await self.apify_client.schedule_daily_run()
            print(f"✅ Daily schedule created: {schedule_id}")
            
        except Exception as e:
            print(f"💥 Error creating schedule: {str(e)}")
            
    def get_usage_info(self):
        """Get Apify usage information"""
        print("📊 Getting Apify usage info...")
        
        client_info = self.apify_client.get_client_info()
        print(f"Actor ID: {client_info['actor_id']}")
        print(f"Has Token: {client_info['has_token']}")
        print(f"Default Portals: {client_info['default_input']['portals']}")

async def main():
    """Main function to run the scraper"""
    print("=" * 60)
    print("🕷️  APIFY WEB SCRAPER - IA FISCAL CAPIVARI")
    print("    Municipal Transparency Portals Scraper")
    print("=" * 60)
    
    scraper = SimpleWebScraper()
    
    # Show usage info
    scraper.get_usage_info()
    print()
    
    # Get scraping history
    await scraper.get_scraping_history()
    print()
    
    # Check for active runs
    await scraper.monitor_active_runs()
    print()
    
    # Ask user what to do
    print("Choose an option:")
    print("1. 🚀 Run full scraping (all portals)")
    print("2. 🎯 Scrape specific portal")
    print("3. ⏰ Schedule daily scraping")
    print("4. 📊 Check usage stats")
    print("5. 🔧 Test actor connection")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            await scraper.scrape_municipal_portals()
            
        elif choice == "2":
            print("\nAvailable portals:")
            print("- folha (employee payroll)")
            print("- despesas (expenses)")
            print("- contratos (contracts)")
            
            portal = input("Enter portal name: ").strip().lower()
            if portal in ['folha', 'despesas', 'contratos']:
                await scraper.scrape_specific_portal(portal)
            else:
                print("❌ Invalid portal name")
                
        elif choice == "3":
            await scraper.schedule_daily_scraping()
            
        elif choice == "4":
            usage_stats = await scraper.apify_client.get_usage_stats()
            print("💰 Usage Statistics:")
            print(f"  Credits: {usage_stats.get('usage_credits', 'N/A')}")
            print(f"  Plan: {usage_stats.get('plan', 'N/A')}")
            
        elif choice == "5":
            test_result = await scraper.apify_client.test_actor()
            if test_result['success']:
                print("✅ Actor connection successful!")
            else:
                print(f"❌ Connection failed: {test_result.get('error')}")
                
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n👋 Scraping cancelled by user")
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")

if __name__ == "__main__":
    # Check if token is set
    if not os.getenv('APIFY_API_TOKEN'):
        print("⚠️  Warning: APIFY_API_TOKEN not set!")
        print("   Set it in Replit Secrets or environment variables")
        print()
    
    asyncio.run(main())
