#!/usr/bin/env python3
"""BlueStacks Instagram Aesthetic & Keyword Search Harvester.

Connects to BlueStacks via ADB (HD-Adb) to drive the mobile Instagram app:
- Performs mobile-exclusive semantic keyword search (for aesthetics, reels, formats, topics)
- Extracts post content, captions, usernames, and high-res preview screenshots
- Optionally resolves post URLs into rich PostData objects
- Saves output into workspace/<brand>/research/ and workspace/<brand>/storyboards/
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("bluestacks_ig")

BLUESTACKS_CONF = Path(r"C:\ProgramData\BlueStacks_nxt\bluestacks.conf")
DEFAULT_HD_ADB = Path(r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe")
IG_PACKAGE = "com.instagram.android"
IG_ACTIVITY = "com.instagram.mainactivity.MainActivity"


def find_adb_executable() -> Path:
    """Find the best available ADB binary (HD-Adb or PATH adb)."""
    if DEFAULT_HD_ADB.exists():
        return DEFAULT_HD_ADB
    # Fallback to system adb
    import shutil
    sys_adb = shutil.which("adb")
    if sys_adb:
        return Path(sys_adb)
    raise FileNotFoundError("Could not find BlueStacks HD-Adb.exe or system adb.exe.")


def get_bluestacks_adb_info() -> Tuple[bool, int]:
    """Read bluestacks.conf to check if ADB is enabled and find the port."""
    enabled = False
    port = 5555
    if BLUESTACKS_CONF.exists():
        try:
            content = BLUESTACKS_CONF.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                if 'bst.enable_adb_access="1"' in line:
                    enabled = True
                m_port = re.search(r'bst\.instance\.\w+\.status\.adb_port="(\d+)"', line)
                if m_port:
                    port = int(m_port.group(1))
        except Exception as e:
            logger.warning(f"Could not read {BLUESTACKS_CONF}: {e}")
    return enabled, port


class BlueStacksInstagramScraper:
    def __init__(self, brand: str = "general", output_dir: Optional[Path] = None):
        self.brand = brand
        self.adb = find_adb_executable()
        self.enabled, self.port = get_bluestacks_adb_info()
        self.device_serial = f"127.0.0.1:{self.port}"
        self.repo_root = Path(__file__).resolve().parents[1]
        self.output_dir = output_dir or (self.repo_root / "workspace" / brand / "inspiration")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir = self.output_dir / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    def run_adb(self, *args, timeout: int = 15) -> subprocess.CompletedProcess:
        """Run an ADB command with device targeting."""
        cmd = [str(self.adb), "-s", self.device_serial] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def run_shell(self, shell_cmd: str, timeout: int = 20) -> str:
        """Execute a shell command on the Android device."""
        res = self.run_adb("shell", shell_cmd, timeout=timeout)
        if res.returncode != 0 and "error" in res.stderr.lower():
            logger.error(f"ADB Shell error: {res.stderr.strip()}")
        return res.stdout.strip()

    def connect(self) -> bool:
        """Connect to BlueStacks ADB daemon."""
        logger.info(f"Connecting to BlueStacks on {self.device_serial} via {self.adb.name}...")
        subprocess.run([str(self.adb), "connect", self.device_serial], capture_output=True, timeout=10)
        
        # Verify connection
        devices_out = subprocess.run([str(self.adb), "devices"], capture_output=True, text=True).stdout
        if self.device_serial in devices_out and "offline" not in devices_out:
            logger.info("Successfully connected to BlueStacks device!")
            return True
            
        # Try fallback serial emulator-5554
        if "emulator-5554\tdevice" in devices_out:
            self.device_serial = "emulator-5554"
            logger.info("Connected via emulator-5554!")
            return True

        if not self.enabled:
            logger.error(
                "\n" + "=" * 60 + "\n"
                "ACTION REQUIRED IN BLUESTACKS:\n"
                "Android Debug Bridge (ADB) is currently OFF in BlueStacks.\n"
                "To enable it:\n"
                "  1. In BlueStacks, click Settings (Gear icon at bottom right)\n"
                "  2. Click 'Advanced'\n"
                "  3. Toggle 'Android Debug Bridge (ADB)' to ON\n"
                "  4. Click 'Save changes'\n"
                + "=" * 60 + "\n"
            )
        return False

    def check_instagram(self) -> bool:
        """Check if Instagram is installed."""
        out = self.run_shell("pm list packages com.instagram.android")
        if "com.instagram.android" in out:
            logger.info("Instagram app found on device.")
            return True
        logger.error("Instagram app (com.instagram.android) is not installed in BlueStacks!")
        return False

    def launch_instagram(self):
        """Bring Instagram to the foreground."""
        logger.info("Opening Instagram...")
        self.run_shell(f"am start -n {IG_PACKAGE}/{IG_ACTIVITY}")
        time.sleep(3)

    def open_search(self, query: str):
        """Navigate to the search / explore tab and enter search query."""
        logger.info(f"Navigating to search for: '{query}'")
        # Direct deep link to explore tab
        self.run_shell("am start -a android.intent.action.VIEW -d 'instagram://explore'")
        time.sleep(2.5)

        # In Instagram explore, search bar is at the top
        # Tap search bar area (standard 1080x1920 or scaled coordinates)
        # We can also dump hierarchy to locate the search view directly
        xml_dump = self.dump_hierarchy()
        search_elem = self.find_node_by_text_or_desc(xml_dump, ["Search", "Search and explore", "search_bar"])
        
        if search_elem is not None and "bounds" in search_elem.attrib:
            bounds = self.parse_bounds(search_elem.attrib["bounds"])
            center_x, center_y = (bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2
            logger.info(f"Found search bar at ({center_x}, {center_y}), tapping...")
            self.run_shell(f"input tap {center_x} {center_y}")
        else:
            # Fallback tap near top search bar
            logger.info("Tapping default search bar position...")
            self.run_shell("input tap 300 120")
            
        time.sleep(1.5)
        
        # Type the search keyword
        # Replace spaces with %s for adb input text
        safe_query = query.replace(" ", "%s")
        logger.info(f"Typing search query: {query}")
        self.run_shell(f"input text '{safe_query}'")
        time.sleep(1.5)
        
        # Press enter to submit search
        self.run_shell("input keyevent 66")  # KEYCODE_ENTER
        time.sleep(3)

    def select_tab(self, tab_name: str = "Reels"):
        """Select a tab like 'Reels', 'Top', 'Tags', 'Accounts' in search results."""
        logger.info(f"Selecting search tab: '{tab_name}'")
        xml_dump = self.dump_hierarchy()
        node = self.find_node_by_text_or_desc(xml_dump, [tab_name])
        if node is not None and "bounds" in node.attrib:
            bounds = self.parse_bounds(node.attrib["bounds"])
            center_x, center_y = (bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2
            self.run_shell(f"input tap {center_x} {center_y}")
            time.sleep(2)
        else:
            logger.warning(f"Could not locate tab '{tab_name}' in UI hierarchy.")

    def dump_hierarchy(self) -> Optional[ET.Element]:
        """Dump the current UI hierarchy XML from the device."""
        try:
            self.run_shell("uiautomator dump /sdcard/window_dump.xml")
            cat_out = self.run_shell("cat /sdcard/window_dump.xml")
            if cat_out.startswith("<?xml") or "<hierarchy" in cat_out:
                return ET.fromstring(cat_out)
        except Exception as e:
            logger.debug(f"Hierarchy dump failed: {e}")
        return None

    def parse_bounds(self, bounds_str: str) -> Tuple[int, int, int, int]:
        """Parse bounds string '[x1,y1][x2,y2]' into tuple (x1, y1, x2, y2)."""
        m = re.findall(r"\d+", bounds_str)
        if len(m) >= 4:
            return int(m[0]), int(m[1]), int(m[2]), int(m[3])
        return 0, 0, 0, 0

    def find_node_by_text_or_desc(self, root: Optional[ET.Element], targets: List[str]) -> Optional[ET.Element]:
        """Search XML tree for a node matching text or content-desc."""
        if root is None:
            return None
        targets_lower = [t.lower() for t in targets]
        for node in root.iter():
            text = (node.attrib.get("text") or "").strip().lower()
            desc = (node.attrib.get("content-desc") or "").strip().lower()
            res_id = (node.attrib.get("resource-id") or "").strip().lower()
            for t in targets_lower:
                if t in text or t in desc or t in res_id:
                    return node
        return None

    def scroll_down(self, distance: int = 800):
        """Scroll down to load more results."""
        self.run_shell(f"input swipe 500 {distance + 300} 500 300 350")
        time.sleep(2)

    def capture_results(self, query: str, scroll_count: int = 3) -> List[Dict]:
        """Collect visible posts, captions, and screenshots from the search grid."""
        collected_items = []
        seen_texts = set()

        for step in range(scroll_count):
            logger.info(f"Extracting search results view #{step + 1}/{scroll_count}...")
            
            # Take a high-res screenshot of the aesthetic grid
            screenshot_name = f"search_{int(time.time())}_step{step}.png"
            screenshot_path = self.screenshots_dir / screenshot_name
            self.run_shell(f"screencap -p /sdcard/{screenshot_name}")
            self.run_adb("pull", f"/sdcard/{screenshot_name}", str(screenshot_path))
            self.run_shell(f"rm /sdcard/{screenshot_name}")
            
            # Extract readable text / elements from hierarchy
            root = self.dump_hierarchy()
            if root is not None:
                for node in root.iter():
                    desc = node.attrib.get("content-desc") or ""
                    text = node.attrib.get("text") or ""
                    content = desc if desc else text
                    if content and len(content) > 10 and content not in seen_texts:
                        seen_texts.add(content)
                        collected_items.append({
                            "type": "search_result",
                            "query": query,
                            "content": content,
                            "screenshot": str(screenshot_path.relative_to(self.repo_root)),
                            "bounds": node.attrib.get("bounds", ""),
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        })

            if step < scroll_count - 1:
                self.scroll_down()

        # Save collected results to JSON
        output_file = self.output_dir / f"inspiration_{re.sub(r'[^a-zA-Z0-9_]', '_', query)}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "brand": self.brand,
                "query": query,
                "total_items": len(collected_items),
                "items": collected_items,
            }, f, indent=2)
            
        logger.info(f"\n[DONE] Saved {len(collected_items)} aesthetic references to {output_file}")
        logger.info(f"Screenshots saved in {self.screenshots_dir}")
        return collected_items


def main():
    parser = argparse.ArgumentParser(description="Scrape Instagram search & aesthetic feeds via BlueStacks ADB.")
    parser.add_argument("--query", "-q", required=True, help="Topic, format, or aesthetic to search (e.g. 'moody coffee reels')")
    parser.add_argument("--tab", "-t", default="Reels", choices=["Reels", "Top", "Accounts", "Tags"], help="Search tab to target")
    parser.add_argument("--brand", "-b", default="general", help="Brand slug for organizing workspace files")
    parser.add_argument("--scrolls", "-s", type=int, default=3, help="Number of scroll cycles to capture")
    args = parser.parse_args()

    scraper = BlueStacksInstagramScraper(brand=args.brand)
    if not scraper.connect():
        sys.exit(1)

    if not scraper.check_instagram():
        sys.exit(1)

    scraper.launch_instagram()
    scraper.open_search(args.query)
    if args.tab != "Top":
        scraper.select_tab(args.tab)

    scraper.capture_results(args.query, scroll_count=args.scrolls)


if __name__ == "__main__":
    main()
