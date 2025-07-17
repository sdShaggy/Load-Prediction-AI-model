import subprocess
import logging
import sys

logging.basicConfig(filename='pipeline.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def run_script(script_name):
    try:
        logging.info(f"Starting {script_name}")
        result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Error running {script_name}: {result.stderr}")
        else:
            logging.info(f"Finished {script_name} successfully")
    except Exception as e:
        logging.error(f"Exception running {script_name}: {str(e)}")

if __name__ == "__main__":
    run_script("scraper.py")
    run_script("model.py")
    
