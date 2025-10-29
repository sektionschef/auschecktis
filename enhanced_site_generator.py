#!/usr/bin/env python3
"""
Enhanced Static Site Generator for Auscheckt Is
Can work with existing JSON files OR generate directly from master list
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
import re

class EnhancedHeurigenSiteGenerator:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "data")
        self.input_dir = os.path.join(base_dir, "input")
        self.output_dir = os.path.join(base_dir, "generated")
        
        # Load master heurigen data
        with open(os.path.join(self.input_dir, "heurigen_list.json"), 'r', encoding='utf-8') as f:
            self.heurigen_master = json.load(f)
    
    def scrape_opening_hours(self, heurigen_key: str, heurigen_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape opening hours directly from website and generate events"""
        events = []
        
        try:
            # Example implementation for different heuriger types
            if heurigen_key == "presshaus":
                events = self._scrape_presshaus(heurigen_data)
            elif heurigen_key == "wieninger":
                events = self._scrape_wieninger(heurigen_data)
            # Add more specific scrapers as needed
            else:
                events = self._scrape_generic(heurigen_key, heurigen_data)
                
        except Exception as e:
            print(f"Error scraping {heurigen_key}: {e}")
            # Fallback to existing JSON if available
            events = self._load_existing_json(heurigen_key)
        
        return events
    
    def _scrape_presshaus(self, heurigen_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Specific scraper for Presshaus"""
        events = []
        url = heurigen_data.get("link_opening_hours_page", "")
        
        if not url:
            return events
            
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for date patterns in the text
            text = soup.get_text()
            
            # Pattern for dates like "27.-29. Juni 2025"
            date_patterns = re.findall(r'(\d{1,2})\.-(\d{1,2})\.\s+(\w+)\s+(\d{4})', text)
            
            for start_day, end_day, month_name, year in date_patterns:
                # Convert German month names to numbers
                month_map = {
                    'Januar': 1, 'Februar': 2, 'März': 3, 'April': 4,
                    'Mai': 5, 'Juni': 6, 'Juli': 7, 'August': 8,
                    'September': 9, 'Oktober': 10, 'November': 11, 'Dezember': 12
                }
                
                month_num = month_map.get(month_name, 0)
                if month_num == 0:
                    continue
                
                # Generate events for the date range
                for day in range(int(start_day), int(end_day) + 1):
                    try:
                        date = datetime(int(year), month_num, day)
                        
                        # Friday starts at 16:00, Sat/Sun at 14:00
                        start_hour = 16 if date.weekday() == 4 else 14
                        
                        event = {
                            "title": heurigen_data["label"],
                            "start": f"{date.strftime('%Y-%m-%d')}T{start_hour:02d}:00:00",
                            "end": f"{date.strftime('%Y-%m-%d')}T23:00:00",
                            "allDay": False,
                            "url": heurigen_data["website"],
                            "extendedProps": {
                                "mapLink": heurigen_data["location"],
                                "lat": heurigen_data["lat"],
                                "lng": heurigen_data["lng"]
                            }
                        }
                        events.append(event)
                    except ValueError:
                        continue
                        
        except Exception as e:
            print(f"Error scraping Presshaus: {e}")
        
        return events
    
    def _scrape_generic(self, heurigen_key: str, heurigen_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generic scraper for heurigen with regular schedules"""
        events = []
        
        # Use comment field for regular schedules
        comment = heurigen_data.get("comment", "")
        
        if "Samstag und Sonntag" in comment and "16 Uhr bis 22 Uhr" in comment:
            # Generate weekend events for next 8 weeks
            today = datetime.now().date()
            for week in range(8):
                base_date = today + timedelta(weeks=week)
                
                # Find Saturday and Sunday of this week
                days_until_saturday = (5 - base_date.weekday()) % 7
                saturday = base_date + timedelta(days=days_until_saturday)
                sunday = saturday + timedelta(days=1)
                
                for date in [saturday, sunday]:
                    if date >= today:  # Only future dates
                        event = {
                            "title": heurigen_data["label"],
                            "start": f"{date.strftime('%Y-%m-%d')}T16:00:00",
                            "end": f"{date.strftime('%Y-%m-%d')}T22:00:00", 
                            "allDay": False,
                            "url": heurigen_data["website"],
                            "extendedProps": {
                                "mapLink": heurigen_data["location"],
                                "lat": heurigen_data["lat"],
                                "lng": heurigen_data["lng"]
                            }
                        }
                        events.append(event)
        
        return events
    
    def _load_existing_json(self, heurigen_key: str) -> List[Dict[str, Any]]:
        """Load existing JSON file as fallback"""
        file_path = os.path.join(self.data_dir, f"{heurigen_key}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def generate_mode_choice(self) -> str:
        """Ask user which generation mode to use"""
        print("\\n🏗️  Choose generation mode:")
        print("1. Use existing JSON files (data/*.json)")
        print("2. Generate directly from master list (scrape websites)")
        print("3. Hybrid: Use JSON files + fill gaps with scraping")
        
        while True:
            choice = input("\\nEnter choice (1/2/3): ").strip()
            if choice in ['1', '2', '3']:
                return choice
            print("Please enter 1, 2, or 3")
    
    def load_all_events(self, mode: str = "1") -> List[Dict[str, Any]]:
        """Load events based on chosen mode"""
        all_events = []
        
        if mode == "1":
            # Use existing JSON files
            all_events = self._load_from_json_files()
        elif mode == "2": 
            # Generate directly from master list
            all_events = self._generate_from_master_list()
        elif mode == "3":
            # Hybrid approach
            all_events = self._hybrid_generation()
        
        # Sort events by start date
        all_events.sort(key=lambda x: x['start'])
        return all_events
    
    def _load_from_json_files(self) -> List[Dict[str, Any]]:
        """Load events from existing JSON files (current approach)"""
        all_events = []
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json') and filename != 'archive':
                heurigen_key = filename.replace('.json', '')
                file_path = os.path.join(self.data_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        events = json.load(f)
                    
                    # Add heurigen metadata to each event
                    for event in events:
                        event['heurigen_key'] = heurigen_key
                        if heurigen_key in self.heurigen_master:
                            event['heurigen_data'] = self.heurigen_master[heurigen_key]
                        all_events.append(event)
                        
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        return all_events
    
    def _generate_from_master_list(self) -> List[Dict[str, Any]]:
        """Generate events directly from master list by scraping"""
        all_events = []
        
        for heurigen_key, heurigen_data in self.heurigen_master.items():
            print(f"📊 Generating events for {heurigen_data['label']}...")
            events = self.scrape_opening_hours(heurigen_key, heurigen_data)
            
            for event in events:
                event['heurigen_key'] = heurigen_key
                event['heurigen_data'] = heurigen_data
                all_events.append(event)
        
        return all_events
    
    def _hybrid_generation(self) -> List[Dict[str, Any]]:
        """Hybrid: Use JSON files where available, scrape where missing"""
        all_events = []
        
        # First, load existing JSON files
        existing_events = self._load_from_json_files()
        existing_keys = set(event['heurigen_key'] for event in existing_events)
        
        all_events.extend(existing_events)
        
        # Then, generate for missing heurigen
        for heurigen_key, heurigen_data in self.heurigen_master.items():
            if heurigen_key not in existing_keys:
                print(f"📊 Generating events for missing {heurigen_data['label']}...")
                events = self.scrape_opening_hours(heurigen_key, heurigen_data)
                
                for event in events:
                    event['heurigen_key'] = heurigen_key
                    event['heurigen_data'] = heurigen_data
                    all_events.append(event)
        
        return all_events

if __name__ == "__main__":
    generator = EnhancedHeurigenSiteGenerator()
    
    # Let user choose mode
    mode = generator.generate_mode_choice()
    
    print(f"\\n🏗️  Building static site in mode {mode}...")
    
    # Generate events
    events = generator.load_all_events(mode)
    print(f"📅 Generated {len(events)} events")
    
    # Use existing generation methods for HTML
    # (This would use the same generate_index_page, generate_daily_page methods)
    print("✅ Site generation would continue with HTML creation...")