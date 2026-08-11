import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CSVConverter")

def convert_jsonl_to_csv(directory_path: str):
    logger.info(f"Looking for .jsonl files in {directory_path}...")
    if not os.path.exists(directory_path):
        logger.error(f"Directory {directory_path} does not exist.")
        return

    for filename in os.listdir(directory_path):
        if filename.endswith(".jsonl"):
            jsonl_path = os.path.join(directory_path, filename)
            csv_path = os.path.join(directory_path, filename.replace(".jsonl", ".csv"))
            
            logger.info(f"Converting {filename} to CSV...")
            try:
                # Read JSONL into DataFrame
                df = pd.read_json(jsonl_path, lines=True)
                # Save DataFrame to CSV
                df.to_csv(csv_path, index=False, encoding='utf-8')
                logger.info(f"Successfully saved {csv_path}")
            except Exception as e:
                logger.error(f"Failed to convert {filename}: {e}")

if __name__ == "__main__":
    # Convert the strict production dataset
    target_dir = "data/training/v1_strict"
    convert_jsonl_to_csv(target_dir)
