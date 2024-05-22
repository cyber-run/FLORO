from typing import List, Optional, Tuple
import sqlite3
import os

class DatabaseManager:
    """Manages all database interactions for the application."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database manager with the path to the database file.
        
        Args:
            db_path (Optional[str]): The path to the SQLite database file. If None, defaults to project.sqlite3 in the script directory.
        """
        if db_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, "project.sqlite3")

        self.db_path = db_path

    def create_database(self, folder_path: str) -> None:
        """Creates and initializes the database with image paths from the given folder.
        
        Args:
            folder_path (str): The path to the folder containing images.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS images")
            cursor.execute("DROP TABLE IF EXISTS roi_table")
            cursor.execute("""
                CREATE TABLE images (
                    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE roi_table (
                    roi_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drug_name TEXT,
                    roi_points TEXT
                )
            """)
            image_paths = self.get_image_paths(folder_path)
            self.insert_image_paths(image_paths, conn)

    def insert_image_paths(self, image_paths: List[str], conn: sqlite3.Connection) -> None:
        """Insert image paths into the images table.
        
        Args:
            image_paths (List[str]): List of image paths to insert.
            conn (sqlite3.Connection): Active SQLite connection object.
        """
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO images (image_path) VALUES (?)",
            [(image_path,) for image_path in image_paths]
        )
        conn.commit()

    def get_image_paths(self, folder_path: str) -> List[str]:
        """Extracts all image file paths from the given folder.
        
        Args:
            folder_path (str): The path to the folder to scan for images.
        
        Returns:
            List[str]: List of image file paths.
        """
        image_extensions = [".bmp", ".png", ".jpg", ".tif"]
        return [
            os.path.join(folder_path, filename)
            for filename in os.listdir(folder_path)
            if os.path.splitext(filename)[1].lower() in image_extensions
        ]

    def save_roi(self, drug_name: str, roi_points: list) -> int:
        """Saves the ROI data to the database.
        
        Args:
            drug_name (str): Name of the drug associated with the ROI.
            roi_points (list): List of points defining the ROI.
        
        Returns:
            int: The newly created ROI's primary key ID.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO roi_table (drug_name, roi_points) VALUES (?, ?)",
                (drug_name, str(roi_points))
            )
            roi_id = cursor.lastrowid
            conn.commit()
        return roi_id

    def delete_roi(self, roi_points: List[Tuple[int, int]]) -> Optional[int]:
        """Deletes the ROI data from the database based on the given ROI points and returns the primary key of the deleted row.
        
        Args:
            roi_points (List[Tuple[int, int]]): The list of points defining the ROI to delete.
        
        Returns:
            Optional[int]: The primary key of the deleted row, or None if no row was deleted.
        """
        roi_points_str = str(roi_points)  # Convert list of points to a string as stored in the database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # First, fetch the primary key of the row that matches the ROI points
            cursor.execute("SELECT roi_id FROM roi_table WHERE roi_points = ?", (roi_points_str,))
            row = cursor.fetchone()
            if row is None:
                return None  # No matching row found
            
            roi_id = row[0]
            
            # Proceed with deletion
            cursor.execute("DELETE FROM roi_table WHERE roi_points = ?", (roi_points_str,))
            conn.commit()
            
            return roi_id  # Return the primary key of the deleted row

    def get_all_roi_data(self) -> List[Tuple[int, str]]:
        """Retrieves all ROI data from the database.
        
        Returns:
            List[Tuple[int, str]]: A list of tuples containing ROI ID and drug name.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT roi_id, drug_name FROM roi_table ORDER BY roi_id")
            roi_data = cursor.fetchall()
        return roi_data

    def get_image_paths_from_database(self) -> List[str]:
        """Retrieves all image paths stored in the database.
        
        Returns:
            List[str]: A list of image paths.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT image_path FROM images")
            image_paths = [row[0] for row in cursor.fetchall()]
        return image_paths
    
    def update_drug_name(self, roi_id: int, new_drug_name: str) -> None:
        """Updates the drug name in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE roi_table SET drug_name = ? WHERE roi_id = ?",
            (new_drug_name, roi_id)
        )
        conn.commit()
        conn.close()
